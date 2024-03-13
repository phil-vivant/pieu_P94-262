import math


class Tolerance:

    def __init__(self, values: list[float]):
        self.values = values

    def _list_of_values(self):
        list_of_values = []
        for i in self.values:
            if not math.isclose(i, 0):
                list_of_values.append(i)
        return list_of_values

    @property
    def _small(self):
        try:
            return min(self._list_of_values())
        except ValueError:
            return 0.1

    @property
    def _big(self):
        try:
            return min(self._list_of_values())
        except ValueError:
            return 1.

    @property
    def value(self):
        return min(abs(self._small), abs(self._big)) / 10_000

    def __str__(self):
        result = f"Tolérance prise en compte pour la convergence: {self.value:4f}"
        return result
