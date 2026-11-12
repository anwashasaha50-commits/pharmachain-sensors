import json
import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from detector import features, MODEL_PATH, CONSECUTIVE
from sensor_sim import SensorSimulator, SAFE_MIN, SAFE_MAX

TRAIN_READINGS = 5000
RUN_LENGTH = 120
SCENARIO_START = 60
RUNS_PER_CASE = 30
SCENARIOS = ("door_open", "power_failure", "compressor_fault", "spike", "none")
MODES = ("range", "forest", "combined")

def feature_matrix(readings):
    rows, prev = [], None
    for r in readings:
        prev = r["temp"] if prev is None else prev
        rows.append(features(r["temp"], r["humidity"], prev))
    return np.array(rows)

def train():
    sim = SensorSimulator(seed=1)
    readings = [sim.read() for _ in range(TRAIN_READINGS)]
    model = IsolationForest(n_estimators=200, contamination=0.005, random_state=42)
    model.fit(feature_matrix(readings))
    joblib.dump(model, MODEL_PATH)
    print("Trained on %d normal readings -> %s" % (TRAIN_READINGS, MODEL_PATH))
    return model

def first_breach(flags, consecutive=CONSECUTIVE):
    """Index of the reading where consecutive anomalies in a row is reached."""
    run = 0
    for i, f in enumerate(flags):
        run = run + 1 if f else 0
        if run >= consecutive:
            return i - consecutive + 1
    return None

def simulate(scenario, seed):
    sim = SensorSimulator(seed=seed)
    if scenario != "none":
        sim.set_scenario(scenario, SCENARIO_START)
    readings, truth = [], []
    for _ in range(RUN_LENGTH):
        readings.append(sim.read())
        truth.append(sim.active)
    return readings, np.array(truth)
def evaluate(model):
    stats = {}
    tp = fp = fn = tn = 0
    for scenario in SCENARIOS:
        for i in range(RUNS_PER_CASE):
            readings, truth = simulate(scenario, 1000 + i)
            forest = model.predict(feature_matrix(readings)) == -1
            temps = np.array([r["temp"] for r in readings])
            rng = (temps < SAFE_MIN) | (temps > SAFE_MAX)
            by_mode = {"range": rng, "forest": forest, "combined": forest | rng}
            for mode, flags in by_mode.items():
                tick = first_breach(flags)
                s = stats.setdefault((scenario, mode), {"hits": 0, "delays": []})
                if tick is not None and (scenario == "none" or tick >= SCENARIO_START):
                    s["hits"] += 1
                if scenario != "none" and tick is not None:
                    s["delays"].append(tick - SCENARIO_START)
            c = by_mode["combined"]
            tp += int((truth & c).sum())
            fp += int((~truth & c).sum())
            fn += int((truth & ~c).sum())
            tn += int((~truth & ~c).sum())
    print(
        "\nEvent-level results (%d runs per case, scenario starts at tick %d)"
        % (RUNS_PER_CASE, SCENARIO_START)
    )
    print("%-17s %-9s %-10s %-12s" % ("Case", "Detector", "Detected", "Avg delay"))
    out = {}
    for (scenario, mode), s in stats.items():
        avg = "%.1f ticks" % np.mean(s["delays"]) if s["delays"] else "-"
        print("%-17s %-9s %2d/%-7d %-12s" % (scenario, mode, s["hits"], RUNS_PER_CASE, avg))
        out[str((scenario, mode))] = {
            "runs": RUNS_PER_CASE,
            "detected": s["hits"],
            "avg_delay": float(np.mean(s["delays"])) if s["delays"] else None,
        }
    print(
        "\nReading-level (combined detector, before the %d-in-a-row filter)"
        % CONSECUTIVE
    )
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0.0
    )
    print("TP=%d FP=%d FN=%d TN=%d" % (tp, fp, fn, tn))
    print("Precision=%.3f Recall=%.3f F1=%.3f" % (precision, recall, f1))
    out["reading_level"] = {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }
    with open("metrics.json", "w") as f:
        json.dump(out, f, indent=2)
    print("\nSaved metrics.json")

if __name__ == "__main__":
    evaluate(train())