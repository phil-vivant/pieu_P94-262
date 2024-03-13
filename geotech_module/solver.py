import numpy as np
import math
from numpy.linalg import inv, det

from geotech_module.tolerance import Tolerance

# Delta à appliquer sur les racines
delta_1 = 0.00001


class NewtonRaphson11:

    def __init__(self, function, target_value: list[float], initial_guess: float=[0.0]):
        self.function = function
        self.target_value = target_value
        self.initial_guess = initial_guess

        self.ensure_valid_data()
        self.result = self.solve()

    def ensure_valid_data(self):
        if not self.target_value_length():
            raise ValueError(f"Need 1 value")

    def target_value_length(self) -> bool:
        return len(self.target_value) == 1 and len(self.initial_guess) == 1

    @property
    def tolerance(self) -> float:
        return Tolerance(self.target_value)

    @property
    def convergence(self) -> bool:
        return self.result[0]

    @property
    def number_of_iterations(self) -> int:
        return self.result[1]

    @property
    def final_roots(self) -> list[float]:
        return self.result[2]

    @property
    def final_targets(self) -> list[float]:
        return self.result[3]

    def operator_phi_11(self, variables: list[float]):
        if len(variables) != 1:
            raise ValueError('Need 1 value')
        variable_1 = variables[0]

        design_point_1 = self.function(variable_1 + delta_1)
        design_point_2 = self.function(variable_1 - delta_1)

        a11 = (design_point_1 - design_point_2) / (2 * delta_1)

        operator = np.array([[a11]])

        return operator
    
    def solve(self):
        i = 0
        condition = 0
        calculated_value = 0
        tolerance_value = self.tolerance.value
        roots_i = self.initial_guess
        target_1 = self.target_value[0]
        matrix_roots_i = np.array([[roots_i[0]]])

        while i <= 20:
            i += 1
            root_1 = matrix_roots_i[0][0]

            calculated_value = self.function(root_1)
            calculated_value_1 = calculated_value

            operator_phi = self.operator_phi_11([root_1])

            if det(operator_phi) == 0:
                break
            else:
                inverse_operator_phi = inv(operator_phi)

            matrix_result_i = np.array([[target_1 - calculated_value_1]])

            matrix_roots_i += + np.dot(inverse_operator_phi, matrix_result_i)

            condition_1 = math.isclose(target_1, calculated_value_1, abs_tol=tolerance_value)

            condition = condition_1

            if condition == 1:
                break

        final_target = calculated_value
        final_root = (matrix_roots_i[0][0])

        if condition != 1:
            final_target = [0.0]
            final_root = [0.0]

        return condition, i, final_root, final_target

    def __str__(self) -> str:
        if self.convergence:
            result = f"Méthode de Newton-Raphson - 1 x 1:\n"
            result += f"\tL'équilibre est obtenu après {self.number_of_iterations} itérations.\n"
            result += f"\t{self.tolerance}\n"
            result += f"\tRappel de la valeur cible:\n"
            result += f"\t\tValeur_01 :   {self.final_targets[0]:.1f}\n"
            result += f"\tDéfinition de la racine:\n"
            result += f"\t\tRacine_01 :   {self.final_roots[0]:.9f}\n"
            return result
        else:
            result = "Aucune solution trouvée !\n"
            return result
