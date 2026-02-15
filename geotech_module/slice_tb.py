from dataclasses import dataclass
import math

import utils
from soil import Soil
from solver import NewtonRaphson11


@dataclass
class SliceTB:
    z_top: float
    delta_h: float
    soil: Soil
    data_pieu: dict

    # état (debug)
    Q_top: float = 0.0
    Q_bott: float = 0.0
    Q_middle: float = 0.0
    dz_top: float = 0.0
    dz_bott: float = 0.0
    dz_middle: float = 0.0
    qs: float = 0.0

    @property
    def Eb(self): return self.data_pieu["Eb"]
    @property
    def Dp(self): return self.data_pieu["Dp"]
    @property
    def Ds(self): return self.data_pieu["Ds"]
    @property
    def pile_category(self): return self.data_pieu["Categorie"]

    @property
    def A(self): return math.pi * self.Dp**2 / 4
    @property
    def EA(self): return self.Eb * self.A
    @property
    def P(self): return math.pi * self.Ds

    @property
    def qs_max(self): return self.soil.frottement_maxi(self.pile_category)

    @property
    def qs_lim(self):
        alpha = self.soil.alpha_pieu_sol(self.pile_category)
        qs = alpha * self.soil.fonction_fsol
        return min(qs, self.qs_max)

    @property
    def kt(self):
        return self.soil.module_kt(self.Ds)

    def tau(self, w_mid: float) -> float:
        return utils.skin_friction_law(w_mid, self.qs_lim, self.kt)

    def propagate(
            self,
            direction: str,
            Q_in: float, w_in: float,
            wmid_guess: float | None = None
    ):
        """
        direction:
          - "bottom_to_top": entrée (Q_bott, w_bott) -> sortie (Q_top, w_top)
          - "top_to_bottom": entrée (Q_top, w_top) -> sortie (Q_bott, w_bott)
        """

        if direction not in ("bottom_to_top", "top_to_bottom"):
            raise ValueError("direction must be 'bottom_to_top' or 'top_to_bottom'")

        if wmid_guess is None:
            wmid_guess = w_in

        dh = self.delta_h
        P  = self.P
        EA = self.EA
        half = 0.5 * P * dh

        # Définition de Qm(wm) et de F(wm)
        if direction == "bottom_to_top":
            Qb = Q_in
            wb = w_in

            def Qm(wm):
                return Qb + half * self.tau(wm)

            def F(wm):
                return wb + (dh / (2 * EA)) * Qm(wm) - wm

            # solve wm
            wm = NewtonRaphson11(F, [0.0], [wmid_guess]).final_roots
            tau_m = self.tau(wm)
            Qm_ = Qm(wm)

            Qt = Qm_ + half * tau_m
            wt = wb + (dh / EA) * Qm_

            # stock état
            self.Q_bott, self.dz_bott = Qb, wb
            self.dz_middle, self.qs = wm, tau_m
            self.Q_middle = Qm_
            self.Q_top, self.dz_top = Qt, wt
            return Qt, wt

        else:  # top_to_bottom
            Qt = Q_in
            wt = w_in

            def Qm(wm):
                return Qt - half * self.tau(wm)

            def F(wm):
                return wt - (dh / (2 * EA)) * Qm(wm) - wm

            wm = NewtonRaphson11(F, [0.0], [wmid_guess]).final_roots
            tau_m = self.tau(wm)
            Qm_ = Qm(wm)

            Qb = Qm_ - half * tau_m
            wb = wt - (dh / EA) * Qm_

            # stock état
            self.Q_top, self.dz_top = Qt, wt
            self.dz_middle, self.qs = wm, tau_m
            self.Q_middle = Qm_
            self.Q_bott, self.dz_bott = Qb, wb
            return Qb, wb
