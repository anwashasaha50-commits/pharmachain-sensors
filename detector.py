"""Anomaly detector combining Isolation Forest model and range rules."""
import joblib
import numpy as np

class AnomalyDetector:
    def __init__(self, model_path="model.joblib", consecutive=3):
        try:
            self.model = joblib.load(model_path)
        except Exception:
            self.model = None
        self.consecutive = consecutive
        self.history = []

    """Isolation Forest + safe-range rule + 'N in a row' filter."""
import joblib
from sensor_sim import SAFE_MIN, SAFE_MAX

MODEL_PATH = "model.joblib"
CONSECUTIVE = 3  # anomalous readings in a row before we call it a breach

def features(temp, humidity, prev_temp):
    """The three numbers the forest looks at for each reading."""
    return [temp, humidity, temp - prev_temp]

class BreachDetector:
    def __init__(self, model_path=MODEL_PATH, consecutive=CONSECUTIVE, mode="combined"):
        self.model = joblib.load(model_path)
        self.consecutive = consecutive
        self.mode = mode  # "combined", "forest" or "range"
        self.prev_temp = None
        self.run = 0

    def flags(self, reading):
        temp, hum = reading["temp"], reading["humidity"]
        prev = temp if self.prev_temp is None else self.prev_temp
        self.prev_temp = temp
        forest = self.model.predict([features(temp, hum, prev)])[0] == -1
        out_of_range = temp < SAFE_MIN or temp > SAFE_MAX
        return bool(forest), bool(out_of_range)

    def check(self, reading):
        """Returns (anomalous, breach, forest_flag, range_flag)."""
        forest, out_of_range = self.flags(reading)
        if self.mode == "forest":
            anomalous = forest
        elif self.mode == "range":
            anomalous = out_of_range
        else:
            anomalous = forest or out_of_range

        self.run = self.run + 1 if anomalous else 0
        return anomalous, self.run >= self.consecutive, forest, out_of_range
