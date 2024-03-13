from dataclasses import dataclass
import math
import numpy as np

from geotech_module.utils import trapezoidal_integration, mean_value


TAB_F421 = {
    '1' : {'Q1': 1.15, 'Q12': 1.10, 'Q2': 1.10, 'Q3': 1.45, 'Q4': 1.45, 'Q5': 1.45},
    '2' : {'Q1': 1.30, 'Q12': 1.65, 'Q2': 1.65, 'Q3': 1.60, 'Q4': 1.60, 'Q5': 2.00},
    '3' : {'Q1': 1.55, 'Q12': 3.20, 'Q2': 3.20, 'Q3': 2.35, 'Q4': 2.10, 'Q5': 2.10},
    '4' : {'Q1': 1.35, 'Q12': 3.10, 'Q2': 3.10, 'Q3': 2.30, 'Q4': 2.30, 'Q5': 2.30},
    '5' : {'Q1': 1.00, 'Q12': 1.90, 'Q2': 1.90, 'Q3': 1.40, 'Q4': 1.40, 'Q5': 1.20},
    '6' : {'Q1': 1.20, 'Q12': 3.10, 'Q2': 3.10, 'Q3': 1.70, 'Q4': 2.20, 'Q5': 1.50},
    '7' : {'Q1': 1.00, 'Q12': 1.00, 'Q2': 1.00, 'Q3': 1.00, 'Q4': 1.00, 'Q5': 1.20},
    '8' : {'Q1': 1.15, 'Q12': 1.10, 'Q2': 1.10, 'Q3': 1.45, 'Q4': 1.45, 'Q5': 1.45},
}

TAB_F521 = {
    '1' : {'Q1': 1.10, 'Q12': 1.0, 'Q2': 1.0, 'Q3': 1.8, 'Q4': 1.5, 'Q5': 1.6},
    '2' : {'Q1': 1.25, 'Q12': 1.4, 'Q2': 1.4, 'Q3': 1.8, 'Q4': 1.5, 'Q5': 1.6},
    '3' : {'Q1': 0.70, 'Q12': 0.6, 'Q2': 0.6, 'Q3': 0.5, 'Q4': 0.9, 'Q5': '-'},
    '4' : {'Q1': 1.25, 'Q12': 1.4, 'Q2': 1.4, 'Q3': 1.7, 'Q4': 1.4, 'Q5': '-'},
    '5' : {'Q1': 1.30, 'Q12': '-', 'Q2': '-', 'Q3': '-', 'Q4': '-', 'Q5': '-'},
    '6' : {'Q1': 1.50, 'Q12': 1.8, 'Q2': 1.8, 'Q3': 2.1, 'Q4': 1.6, 'Q5': 1.6},
    '7' : {'Q1': 1.90, 'Q12': 2.1, 'Q2': 2.1, 'Q3': 1.7, 'Q4': 1.7, 'Q5': '-'},
    '8' : {'Q1': 0.60, 'Q12': 0.6, 'Q2': 0.6, 'Q3': 1.0, 'Q4': 0.7, 'Q5': '-'},
    '9' : {'Q1': 1.10, 'Q12': 1.4, 'Q2': 1.4, 'Q3': 1.0, 'Q4': 0.9, 'Q5': '-'},
    '10': {'Q1': 2.00, 'Q12': 2.1, 'Q2': 2.1, 'Q3': 1.9, 'Q4': 1.6, 'Q5': '-'},
    '11': {'Q1': 1.20, 'Q12': 1.4, 'Q2': 1.4, 'Q3': 2.1, 'Q4': 1.0, 'Q5': '-'},
    '12': {'Q1': 0.80, 'Q12': 1.2, 'Q2': 1.2, 'Q3': 0.4, 'Q4': 0.9, 'Q5': '-'},
    '13': {'Q1': 1.20, 'Q12': 0.7, 'Q2': 0.7, 'Q3': 0.5, 'Q4': 1.0, 'Q5': 1.0},
    '14': {'Q1': 1.10, 'Q12': 1.0, 'Q2': 1.0, 'Q3': 0.4, 'Q4': 1.0, 'Q5': 0.9},
    '15': {'Q1': 2.70, 'Q12': 2.9, 'Q2': 2.9, 'Q3': 2.4, 'Q4': 2.4, 'Q5': 2.4},
    '16': {'Q1': 0.90, 'Q12': 0.8, 'Q2': 0.8, 'Q3': 0.4, 'Q4': 1.2, 'Q5': 1.2},
    '17': {'Q1':  '-', 'Q12': '-', 'Q2': '-', 'Q3': '-', 'Q4': '-', 'Q5': '-'},
    '18': {'Q1':  '-', 'Q12': '-', 'Q2': '-', 'Q3': '-', 'Q4': '-', 'Q5': '-'},
    '19': {'Q1': 2.70, 'Q12': 2.9, 'Q2': 2.9, 'Q3': 2.4, 'Q4': 2.4, 'Q5': 2.4},
    '20': {'Q1': 3.40, 'Q12': 3.8, 'Q2': 3.8, 'Q3': 3.1, 'Q4': 3.1, 'Q5': 3.1},
}

TAB_F522 = {
    'Q1' : {'a': 0.003, 'b': 0.04, 'c': 3.5},
    'Q12': {'a': 0.010, 'b': 0.06, 'c': 1.2},
    'Q2' : {'a': 0.010, 'b': 0.06, 'c': 1.2},
    'Q3' : {'a': 0.007, 'b': 0.07, 'c': 1.3},
    'Q4' : {'a': 0.008, 'b': 0.08, 'c': 3.0},
    'Q5' : {'a': 0.010, 'b': 0.08, 'c': 3.0},
}

TAB_F523 = {
    '1' : {'Q1': 90., 'Q12': 90., 'Q2': 90., 'Q3': 200, 'Q4': 170, 'Q5': 200},
    '2' : {'Q1': 90., 'Q12': 90., 'Q2': 90., 'Q3': 200, 'Q4': 170, 'Q5': 200},
    '3' : {'Q1': 50., 'Q12': 50., 'Q2': 50., 'Q3': 50., 'Q4': 90., 'Q5': '-'},
    '4' : {'Q1': 90., 'Q12': 90., 'Q2': 90., 'Q3': 170, 'Q4': 170, 'Q5': '-'},
    '5' : {'Q1': 90., 'Q12': 90., 'Q2': '-', 'Q3': '-', 'Q4': '-', 'Q5': '-'},
    '6' : {'Q1': 90., 'Q12': 90., 'Q2': 170, 'Q3': 200, 'Q4': 200, 'Q5': 200},
    '7' : {'Q1': 130, 'Q12': 130, 'Q2': 200, 'Q3': 170, 'Q4': 170, 'Q5': '-'},
    '8' : {'Q1': 50., 'Q12': 50., 'Q2': 90., 'Q3': 90., 'Q4': 90., 'Q5': '-'},
    '9' : {'Q1': 130, 'Q12': 130, 'Q2': 130, 'Q3': 90., 'Q4': 90., 'Q5': '-'},
    '10': {'Q1': 170, 'Q12': 170, 'Q2': 260, 'Q3': 200, 'Q4': 200, 'Q5': '-'},
    '11': {'Q1': 90., 'Q12': 90., 'Q2': 130, 'Q3': 260, 'Q4': 200, 'Q5': '-'},
    '12': {'Q1': 90., 'Q12': 90., 'Q2': 90., 'Q3': 50., 'Q4': 90., 'Q5': '-'},
    '13': {'Q1': 90., 'Q12': 90., 'Q2': 50., 'Q3': 50., 'Q4': 90., 'Q5': 90.},
    '14': {'Q1': 90., 'Q12': 90., 'Q2': 130, 'Q3': 50., 'Q4': 90., 'Q5': 90.},
    '15': {'Q1': 200, 'Q12': 200, 'Q2': 380, 'Q3': 320, 'Q4': 320, 'Q5': 320},
    '16': {'Q1': 90., 'Q12': 90., 'Q2': 50., 'Q3': 50., 'Q4': 90., 'Q5': 90.},
    '17': {'Q1': '-', 'Q12': '-', 'Q2': '-', 'Q3': '-', 'Q4': '-', 'Q5': '-'},
    '18': {'Q1': '-', 'Q12': '-', 'Q2': '-', 'Q3': '-', 'Q4': '-', 'Q5': '-'},
    '19': {'Q1': 200, 'Q12': 200, 'Q2': 380, 'Q3': 320, 'Q4': 320, 'Q5': 320},
    '20': {'Q1': 200, 'Q12': 200, 'Q2': 440, 'Q3': 440, 'Q4': 440, 'Q5': 500},
}


@dataclass
class Soil:
    """
    Couche de sol, définie par les paramètres pressiométriques renseignés.
    """
    name: str
    level_sup: float
    level_inf: float
    courbe_frottement: str
    pf: float
    pl: float
    Em: float
    alpha: float
    soil_type: str='granulaire'

    def check_courbe_frottement(self) -> bool:
        """
        Vérification de la validité du paramètres "Courbe_frottement".
        Doit être parmi ['Q1', 'Q12', 'Q2', 'Q3', 'Q4', 'Q5'].
        """
        courbes = ['Q1', 'Q12', 'Q2', 'Q3', 'Q4', 'Q5']
        return self.courbe_frottement.upper() in courbes

    def check_soil_type(self) -> bool:
        """
        Vérification de la validité du paramètres "type de sol", au sens de l'annexe L de la norme
        Doit être parmi ['fin', 'granulaire'].
        """
        types = ['fin', 'granulaire']
        return self.soil_type in types

    def alpha_pieu_sol(self, categorie_pieu: int) -> float:
        """
        Paramètre adimensionnel alpha_pieu_sol fonction de la catégorie du pieu, suivant le tableau F.5.2.1 de la NF P94-262.
        """
        return TAB_F521[str(categorie_pieu)][self.courbe_frottement.upper()]
    
    def kp_max(self, classe_pieu: int) -> float:
        """
        Facteur de portance pressiométrique fonction de la classe du pieu, suivant le tableau F.4.2.1 de la NF P94-262.
        """
        return TAB_F421[str(classe_pieu)][self.courbe_frottement.upper()]

    @property
    def _a_parameter(self) -> float:
        """
        Paramètre a pour calculs de la fonction f_sol, suivant le tableau F.5.2.2 de la NF P94-262.
        """
        return TAB_F522[self.courbe_frottement.upper()]['a']
    
    @property
    def _b_parameter(self) -> float:
        """
        Paramètre b pour calculs de la fonction f_sol, suivant le tableau F.5.2.2 de la NF P94-262.
        """
        return TAB_F522[self.courbe_frottement.upper()]['b']

    @property
    def _c_parameter(self) -> float:
        """
        Paramètre c pour calculs de la fonction f_sol, suivant le tableau F.5.2.2 de la NF P94-262.
        """
        return TAB_F522[self.courbe_frottement.upper()]['c']

    @property
    def fonction_fsol(self) -> float:
        """
        Fonction fsol suivant l'article F.5.2 (3) de la NF P94-262.
        """
        fsol = (self._a_parameter * self.pl + self._b_parameter) * (1 - math.exp(-self._c_parameter * self.pl))
        return fsol

    def frottement_maxi(self, categorie_pieu: int) -> float:
        """
        Valeur du frottement axial unitaire maximal, fonction de la catégorie du pieu - suivant le tableau F.5.2.3 de la NF P94-262.
        """
        try:
            return TAB_F523[str(categorie_pieu)][self.courbe_frottement.upper()] / 1000
        except TypeError:
            return 0.
    
    def module_kt(self, B: float) -> float:
        """
        Module kt suivant l'annexe L de la NF P94-262, fonction du type de sol (fin ou granulaire).
        Permet de définir la loi de mobilisation du frottement axial.
        """
        if self.soil_type == 'fin':
            return 2.0 * self.Em / B
        elif self.soil_type == 'granulaire':
            return 0.8 * self.Em / B
        else:
            return None

    def module_kq(self, B: float) -> float:
        """
        Module kq suivant l'annexe L de la NF P94-262, fonction du type de sol (fin ou granulaire).
        Permet de définir la loi de mobilisation de l'effort de pointe.
        """
        if self.soil_type == 'fin':
            return 11. * self.Em / B
        elif self.soil_type == 'granulaire':
            return 4.8 * self.Em / B
        else:
            return None

    def module_kf(self, B: float) -> float:
        """
        Module kf suivant l'annexe I.1.3 de la NF P94-262, fonction du type de sol (fin ou granulaire).
        Permet de définir la loi d'interaction vis-à-vis des sollicitations horizontales.
        """
        B0 = 0.60
        if B >= B0:
            return 12 * self.Em / (4/3 * B0 / B * (2.65 * B / B0)**self.alpha + self.alpha)
        else:
            return 12 * self.Em / (4/3 * 2.65 ** self.alpha + self.alpha)


@dataclass
class LogPressio:
    """
    Classe definissant les enregistrements d'un essai pressiométrique Ménard
    """
    levels_ngf: list[float]
    cb_pf: list[float]
    cb_pl: list[float]
    cb_Em: list[float]

    @property
    def top_level(self):
        return max(self.levels_ngf)

    def __post_init__(self):
        self.depths = self.get_depths()

    def get_depths(self) -> list[float]:
        depth_acc = []
        for level in self.levels_ngf:
            depth = self.level_to_depth(level, self.top_level)
            depth_acc.append(depth)
        return depth_acc

    def depth_to_level(self, depth: float, top_level: float) -> float:
        return top_level - depth

    def level_to_depth(self, level, top_level) -> float:
        return top_level - level

    def pf_at_z(self, z: float) -> float:
        """
        Retourne la valeur de pf (pression de fluage) pour une valeur de z donnée.
        """
        return np.interp(z, self.depths, self.cb_pf)

    def pf_at_level(self, level: float) -> float:
        """
        Retourne la valeur de pf (pression de fluage) pour un niveau NGF donné.
        """
        return np.interp(self.level_to_depth(level, self.top_level), self.depths, self.cb_pf)

    def pl_at_z(self, z: float) -> float:
        """
        Retourne la valeur de pl (pression limite) pour une valeur de z donnée.
        """
        return np.interp(z, self.depths, self.cb_pl)

    def pl_at_level(self, level: float) -> float:
        """
        Retourne la valeur de pl (pression limite) pour un niveau NGF donné.
        """
        return np.interp(self.level_to_depth(level, self.top_level), self.depths, self.cb_pl)

    def Em_at_z(self, z: float) -> float:
        """
        Retourne la valeur de Em (module pressiométrique) pour une valeur de z donnée.
        """
        return np.interp(z, self.depths, self.cb_Em)

    def Em_at_level(self, level: float) -> float:
        """
        Retourne la valeur de Em (module pressiométrique) pour une valeur de z donnée.
        """
        return np.interp(self.level_to_depth(level, self.top_level), self.depths, self.cb_Em)

    def pression_fluage_moyenne_z(self, z1: float, z2: float) -> float:
        """
        Retourne la pression de fluage moyenne entre deux niveaux.
        """
        return mean_value(self.depths, self.cb_pf, z1, z2)

    def pression_fluage_moyenne_ngf(self, level_1: float, level_2: float) -> float:
        """
        Retourne la pression de fluage moyenne entre deux niveaux.
        """
        z1 = self.level_to_depth(level_1, self.top_level)
        z2 = self.level_to_depth(level_2, self.top_level)
        return mean_value(self.depths, self.cb_pf, z1, z2)

    def pression_limite_moyenne_z(self, z1: float, z2: float) -> float:
        """
        Retourne la pression limite moyenne entre deux niveaux.
        """
        return mean_value(self.depths, self.cb_pl, z1, z2)

    def pression_limite_moyenne_ngf(self, level_1: float, level_2: float) -> float:
        """
        Retourne la pression limite moyenne entre deux niveaux.
        """
        z1 = self.level_to_depth(level_1, self.top_level)
        z2 = self.level_to_depth(level_2, self.top_level)
        return mean_value(self.depths, self.cb_pl, z1, z2)

    def module_pressio_moyen_z(self, z1: float, z2: float) -> float:
        """
        Retourne le module pressiométrique moyen entre deux niveaux.
        """
        return mean_value(self.depths, self.cb_Em, z1, z2)

    def module_pressio_moyen_ngf(self, level_1: float, level_2: float) -> float:
        """
        Retourne le module pressiométrique moyen entre deux niveaux.
        """
        z1 = self.level_to_depth(level_1, self.top_level)
        z2 = self.level_to_depth(level_2, self.top_level)
        return mean_value(self.depths, self.cb_Em, z1, z2)


levels_ngf = [97, 95.5, 94, 92.5, 91., 89.5, 88., 86.5, 85., 83.5, 82., 80.5]
pression_f = [0.78, 0.84, 1.01, 0.81, 0.4, 0.61, 0.83, 1.10, 0.62, 1.72, 1.12, 1.13]
pression_l = [1.06, 1.13, 1.50, 1.09, 0.74, 1.13, 1.52, 2.06, 1.28, 3.12, 2.17, 1.81]
module_em = [6.2, 10.6, 9.2, 8.3, 5.8, 7.5, 9.3, 14.8, 8.0, 29.5, 15.5, 12.1]

SP2 = LogPressio(
    levels_ngf,
    pression_f,
    pression_l,
    module_em,
)


@dataclass
class SoilPressio:
    """
    Couche de sol, définie par les paramètres pressiométriques calculés à partir des logs pressio.
    """
    name: str
    level_sup: float
    level_inf: float
    courbe: str
    pressio: LogPressio

    @property
    def pf_mean(self):
        return self.pressio.pression_fluage_moyenne_ngf(self.level_sup, self.level_inf)

    @property
    def pl_mean(self):
        return self.pressio.pression_limite_moyenne_ngf(self.level_sup, self.level_inf)

    @property
    def Em_mean(self):
        return self.pressio.module_pressio_moyen_ngf(self.level_sup, self.level_inf)
