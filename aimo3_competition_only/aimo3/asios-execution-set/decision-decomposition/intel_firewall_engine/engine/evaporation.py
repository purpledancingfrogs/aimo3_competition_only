import time

class EvaporationModel:
    def __init__(self, half_life: float):
        self.half_life = half_life

    def decay(self, value: float, dt: float) -> float:
        return value * (0.5 ** (dt / self.half_life))
