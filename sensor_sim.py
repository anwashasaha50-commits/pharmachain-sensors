"""Simulate sensor streams with optional excursion scenarios."""
import random

class SensorSimulator:
    def __init__(self, scenario="none", start_after=10):
        self.scenario = scenario
        self.start_after = start_after
        self.tick = 0

    def read(self):
        self.tick += 1
        temp = random.gauss(5.0, 0.5)
        humidity = random.gauss(50.0, 2.0)

        """Simulated cold-chain sensor. Swap read() for real hardware later."""
import random
from datetime import datetime, timezone

SAFE_MIN, SAFE_MAX = 2.0, 8.0  # vaccine cold-chain range in deg C
SETPOINT = 5.0  # normal fridge temperature
HUM_SETPOINT = 45.0  # normal relative humidity (%)
DEFAULT_DURATION = {"spike": 1, "door_open": 12, "power_failure": 30, "compressor_fault": 20}

class SensorSimulator:
    """Returns one reading per call to read(). Normal readings wander gently
    around the setpoint; a scenario adds an excursion on top."""
    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self.temp = SETPOINT
        self.hum = HUM_SETPOINT
        self.tick = 0
        self.scenario = "none"
        self.start = 0
        self.duration = 0
        self.active = False  # True while a scenario is affecting the reading

    def set_scenario(self, name, start, duration=None):
        self.scenario = name
        self.start = start
        self.duration = duration or DEFAULT_DURATION.get(name, 0)

    def offset(self):
        t = self.tick - self.start
        if self.scenario == "none" or t < 0 or t >= self.duration:
            return 0.0
        if self.scenario == "spike":  # one bad reading
            return 6.0
        if self.scenario == "door_open":  # warms fast, then stays warm
            return min(1.8 * (t + 1), 7.0)
        if self.scenario == "power_failure":  # slow steady drift upward
            return 0.5 * (t + 1)
        if self.scenario == "compressor_fault":  # swings 3C <-> 7C; always "in range"
            return 2.0 if t % 2 == 0 else -2.0
        return 0.0

    def read(self):
        self.temp += 0.3 * (SETPOINT - self.temp) + self.rng.gauss(0, 0.25)
        self.hum += 0.3 * (HUM_SETPOINT - self.hum) + self.rng.gauss(0, 1.2)
        offset = self.offset()
        self.active = offset > 0.0
        hum_extra = 1.5 * offset if self.scenario == "door_open" else 0.0
        self.tick += 1
        return {
            "temp": round(self.temp + offset, 2),
            "humidity": round(self.hum + hum_extra, 1),
            "time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
