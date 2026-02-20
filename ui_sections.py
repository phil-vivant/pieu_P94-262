import math
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

import geotech_module.utils as utils
from geotech_module.soil import Soil

ROUND_FORCE = 1
ROUND_DEPL = 2


def render_header():
    st.divider()
    colA, colB = st.columns([8, 2])
    with colA:
        title = "Dimensionnement d'une fondation profonde isolée "
        title += "suivant la norme NF P94-262"
        st.title(title)
    with colB:
        st.image("img/pieu_1.png", width="stretch")
    st.divider()


def build_pile_sidebar_inputs():
    st.sidebar.title("Définition du pieu")

    level_top_msg = "Niveau supérieur du pieu [NGF]"
    level_bot_msg = "Niveau inférieur du pieu [NGF]"
    categorie_msg = "Catégorie du pieu au sens du tableau A1:"
    Eb_msg = "Module de Young du pieu [MPa]"
    pieu_dp_msg = "Diamètre équivalent du pieu pour l'effort de pointe [mm]"
    pieu_ds_msg = "Diamètre équivalent du pieu pour le frottement [mm]"
    interval_msg = "Discretisation du pieu [mm]"

    level_top = st.sidebar.number_input(level_top_msg, key="pile_top")
    level_bot = st.sidebar.number_input(level_bot_msg, key="pile_bot")
    categorie = int(
        st.sidebar.number_input(
            categorie_msg,
            min_value=1,
            step=1,
            key="pile_cat",
        )
    )
    Eb = st.sidebar.number_input(Eb_msg, key="pile_Eb")
    pieu_dp = st.sidebar.number_input(pieu_dp_msg, key="pile_dp")
    pieu_ds = st.sidebar.number_input(pieu_ds_msg, key="pile_ds")
    interval = st.sidebar.number_input(interval_msg, key="pile_int")

    return {
        "level_top": level_top,
        "level_bot": level_bot,
        "categorie": categorie,
        "Eb": Eb,
        "pieu_dp": pieu_dp,
        "pieu_ds": pieu_ds,
        "interval": interval,
    }


def lithology_ui():
    st.subheader("Lithologie")

    SOIL_COLS = ["name", "zinf", "curve", "pf", "pl", "Em", "alpha",
                 "type_frot", "type_pointe"]

    def default_soils():
        return pd.DataFrame([
            {
                "name": "Marnes", "zinf": -5.0, "curve": "Q4",
                "pf": 0.7, "pl": 1.0, "Em": 5.0, "alpha": 2/3,
                "type_frot": "granulaire", "type_pointe": "fin",
            },
            {
                "name": "Marnes", "zinf": -12.0, "curve": "Q4",
                "pf": 2.5, "pl": 5.0, "Em": 20.0, "alpha": 1/2,
                "type_frot": "granulaire", "type_pointe": "fin",
            },
        ])[SOIL_COLS]

    def normalize_soils_df(df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()

        for c in SOIL_COLS:
            if c not in out.columns:
                out[c] = None
        out = out[SOIL_COLS]

        for c in ["zinf", "pf", "pl", "Em", "alpha"]:
            out[c] = pd.to_numeric(out[c], errors="coerce")

        out = out.dropna(subset=["zinf"], how="all").reset_index(drop=True)

        out["name"] = out["name"].fillna("").astype(str)
        out.loc[out["name"].str.strip() == "", "name"] = "Couche"

        defaults_fill = {
            "curve": "Q1",
            "pf": 0.0,
            "pl": 0.0,
            "Em": 0.0,
            "alpha": 2/3,
            "type_frot": "granulaire",
            "type_pointe": "fin",
        }
        for c, v in defaults_fill.items():
            out[c] = out[c].fillna(v)

        return out

    def validate_soils_df(df: pd.DataFrame, z1_sup_value: float) -> list[str]:
        errors = []

        if len(df) == 0:
            errors.append("La lithologie est vide (aucune couche définie).")
            return errors

        z_prev = float(z1_sup_value)
        for i, row in df.iterrows():
            zi = row["zinf"]
            if pd.isna(zi):
                errors.append(f"Ligne {i+1} : z_inf manquant.")
                continue

            if float(zi) >= z_prev:
                msg = f"Ligne {i+1} : z_inf = {float(zi):.2f} doit être "
                msg += f"inférieur au z_sup de la couche ({z_prev:.2f})."
                errors.append(msg)

            a = float(row["alpha"])
            if not (0.0 <= a <= 1.0):
                msg = f"Ligne {i+1} : alpha = {a:.3f} hors intervalle [0 ; 1]."
                errors.append(msg)

            z_prev = float(zi)

        return errors

    def soils_equal_for_status(
            df_edit: pd.DataFrame, df_applied: pd.DataFrame,
    ) -> bool:
        try:
            a = normalize_soils_df(df_edit)
            b = normalize_soils_df(df_applied)

            for c in ["zinf", "pf", "pl", "Em", "alpha"]:
                a[c] = pd.to_numeric(a[c], errors="coerce")
                b[c] = pd.to_numeric(b[c], errors="coerce")

            for c in ["name", "curve", "type_frot", "type_pointe"]:
                a[c] = a[c].fillna("").astype(str)
                b[c] = b[c].fillna("").astype(str)

            return a.reset_index(drop=True).equals(b.reset_index(drop=True))
        except Exception:
            return False

    # init
    if "soil_df" not in st.session_state:
        st.session_state["soil_df"] = default_soils()

    ctl1, ctl2 = st.columns([3, 2])

    with ctl1:
        z1_sup = st.number_input(
            "Niveau supérieur de la première couche [NGF]",
            key="z1_sup",
            step=0.01,
        )

    edited = st.data_editor(
        st.session_state["soil_df"],
        key="soil_editor",
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "name": st.column_config.TextColumn("Description", required=True),
            "curve": st.column_config.SelectboxColumn(
                "Courbe", options=["Q1", "Q12", "Q2", "Q3", "Q4", "Q5"], required=True
            ),
            "type_frot": st.column_config.SelectboxColumn(
                "Frottement", options=["granulaire", "fin"], required=True
            ),
            "type_pointe": st.column_config.SelectboxColumn(
                "Pointe", options=["granulaire", "fin"], required=True
            ),
            "zinf": st.column_config.NumberColumn("z_inf [m]", format="%.2f", step=0.01),
            "pf": st.column_config.NumberColumn("pf [MPa]", format="%.2f", min_value=0.0, step=0.01),
            "pl": st.column_config.NumberColumn("pl [MPa]", format="%.2f", min_value=0.0, step=0.01),
            "Em": st.column_config.NumberColumn("Em [MPa]", format="%.1f", min_value=0.0, step=0.1),
            "alpha": st.column_config.NumberColumn("α", format="%.2f", min_value=0.0, max_value=1.0, step=0.01),
        },
    )

    is_applied = soils_equal_for_status(edited, st.session_state["soil_df"])

    with ctl2:
        st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
        lith_msg = "✅ Lithologie à jour"
        wrng_msg = "⚠️ Appliquer la lithologie"
        button_label = lith_msg if is_applied else wrng_msg
        apply_clicked = st.button(
            button_label, use_container_width=True, disabled=is_applied,
        )

    if is_applied:
        succes_msg = "✅ Lithologie appliquée (les calculs utilisent bien "
        succes_msg += "la saisie actuelle)."
        st.success(succes_msg)
    else:
        warning_msg = "⚠️ Modifications non appliquées. Cliquez sur"
        warning_msg += " **Appliquer** pour mettre à jour les calculs."
        st.warning(warning_msg)

    msg = f"{len(st.session_state['soil_df'])} couche(s) appliquée(s)"
    msg += f" • z1_sup = {float(z1_sup):.2f} NGF"
    st.caption(msg)

    if apply_clicked:
        df_candidate = normalize_soils_df(edited)
        errors = validate_soils_df(df_candidate, z1_sup)

        if errors:
            for msg in errors:
                st.error(msg)
        else:
            st.session_state["soil_df"] = df_candidate
            st.toast("Lithologie appliquée ✅")
            st.rerun()

    # Build Soil objects
    couches_sols = []
    z = float(z1_sup)

    for row in st.session_state["soil_df"].to_dict("records"):
        sol = Soil(
            name=row["name"],
            level_sup=z,
            level_inf=float(row["zinf"]),
            courbe_frottement=row["curve"],
            pf=float(row["pf"]),
            pl=float(row["pl"]),
            Em=float(row["Em"]),
            alpha=float(row["alpha"]),
            friction_type=row["type_frot"],
            end_type=row["type_pointe"],
        )
        couches_sols.append(sol)
        z = float(row["zinf"])

    st.divider()
    return couches_sols, z1_sup


def render_settlement_section(pieu):
    title = "Courbe de tassement pieu - Méthode de Franck & Zhao - Annexe L.3"
    st.subheader(title)

    tog_tass = st.toggle("Tracer la courbe de tassement", key="tog_tass")

    if not tog_tass:
        st.divider()
        return

    tassement = pieu.settlement_curve()
    dz = tassement[0]  # y
    Q = tassement[1]   # x = Qtete

    pairs = [(1000 * q, 1000 * d) for q, d in zip(Q, dz)]  # MN->kN and m->mm

    neg = [(q, d) for (q, d) in pairs if q <= 0]
    pos = [(q, d) for (q, d) in pairs if q >= 0]

    def ensure_origin(lst):
        if not any(abs(q) < 1e-12 and abs(d) < 1e-12 for (q, d) in lst):
            lst = lst + [(0.0, 0.0)]
        return lst

    neg = sorted(ensure_origin(neg), key=lambda t: t[0])
    pos = sorted(ensure_origin(pos), key=lambda t: t[0])

    x_acc_neg = [round(q, ROUND_FORCE) for (q, d) in neg]
    y_acc_neg = [round(d, ROUND_DEPL) for (q, d) in neg]
    x_acc_pos = [round(q, ROUND_FORCE) for (q, d) in pos]
    y_acc_pos = [round(d, ROUND_DEPL) for (q, d) in pos]

    eps = 1e-6
    x_kz_acc_neg = [q for (q, d) in neg if abs(d) > eps]
    kz_acc_neg = [q / d for (q, d) in neg if abs(d) > eps]

    x_kz_acc_pos = [round(q, ROUND_FORCE) for (q, d) in pos if abs(d) > eps]
    kz_acc_pos = [round(q / d, ROUND_DEPL) for (q, d) in pos if abs(d) > eps]

    col1, col2 = st.columns(2)

    with col1:
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            x=x_acc_neg, y=y_acc_neg,
            line={"color": "teal", "dash": "dash"},
            name="Traction"
        ))
        fig1.add_trace(go.Scatter(
            x=x_acc_pos, y=y_acc_pos,
            line={"color": "teal"},
            name="Compression"
        ))
        fig1.layout.title.text = "Déplacement vertical en tête de pieu"
        fig1.layout.xaxis.title = "Charge verticale en tête de pieu [kN]"
        fig1.layout.yaxis.title = "δz [mm]"
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=x_kz_acc_neg, y=kz_acc_neg,
            line={"color": "slateblue", "dash": "dash", "width": 2},
            name="Kz_neg"
        ))
        fig2.add_trace(go.Scatter(
            x=x_kz_acc_pos, y=kz_acc_pos,
            line={"color": "slateblue", "width": 2},
            name="Kz_pos"
        ))
        fig2.layout.title.text = "Courbe de raideur axiale en tête de pieu"
        fig2.layout.xaxis.title = "Charge verticale en tête de pieu [kN]"
        fig2.layout.yaxis.title = "Kz [MN/ml]"
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()


def render_equilibrium_section(pieu):
    st.subheader("Équilibre pour un chargement vertical donné")

    tog_equ = st.toggle("Recherche de l'équilibre", key="tog_equ")
    if not tog_equ:
        st.divider()
        return

    resistance_mini = math.floor(-1000 * pieu.resistance_skin_friction)
    resistance_maxi = math.floor(1000 * pieu.resistance_totale)

    q_target = st.slider(
        "Charge verticale en tête de pieu [kN] :",
        min_value=resistance_mini,
        max_value=resistance_maxi,
        value=int(st.session_state.get("q_target", 1500)),
        key="q_target",
    )

    equilibre = pieu.equilibre_top_down_Qtete(q_target / 1000)

    z_acc, Q_acc, Q_sol = [], [], []
    dz_acc, dz_sol = [], []
    qs_acc, qs_lim = [], []
    qs_max = -math.inf

    for sl in equilibre[2]:
        z_acc.append(sl.z_top)
        Q_acc.append(sl.Q_top * 1000)
        Q_sol.append(q_target - sl.Q_top * 1000)
        dz_acc.append(sl.dz_middle * 1000)
        dz_sol.append(0)
        qs_acc.append(sl.qs * 1000)
        qs_lim.append(sl.qs_lim * 1000)
        qs_max = max(qs_max, sl.qs)

    st.markdown(
        f"""
    | Principaux résultats                                  |                 |                                  |
    |:---                                                   |---:             |---:                              |
    | Effort vertical en tête de pieu :                     | $Q_{{top}}$ =   | {q_target: .1f} kN               |
    | Effort de pointe :                                    | $Q_{{bot}}$ =   | {1000 * equilibre[1][0]: .1f} kN |
    | Déplacement vertical en tête de pieu :                | $dz_{{top}}$ =  | {1000 * equilibre[0]: .2f} mm    |
    | Déplacement vertical au niveau de la pointe du pieu : | $dz_{{bot}}$ =  | {1000 * equilibre[1][1]: .2f} mm |
    | Frottement maximum sur la hauteur du pieu :           | $q_{{s,max}}$ = | {1000 * qs_max: .2f} kPa         |
    """
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            x=dz_acc, y=z_acc,
            line={"color": "teal", "width": 2},
            name="δz pieu"
        ))
        fig1.add_trace(go.Scatter(
            x=dz_sol, y=z_acc,
            line={"color": "slateblue", "width": 1, "dash": "dash"},
            name="δz sol"
        ))
        fig1.layout.title.text = "Tassement pieu/sol"
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=qs_acc, y=z_acc,
            line={"color": "teal", "width": 2},
            name="qs"
        ))
        fig2.add_trace(go.Scatter(
            x=qs_lim, y=z_acc,
            line={"color": "slateblue", "width": 1, "dash": "dash"},
            name="qs_lim"
        ))
        fig2.layout.title.text = "Frottement pieu/sol"
        st.plotly_chart(fig2, use_container_width=True)

    with col3:
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=Q_acc, y=z_acc,
            line={"color": "teal", "width": 2},
            name="Qpieu(z)"
        ))
        fig3.add_trace(go.Scatter(
            x=Q_sol, y=z_acc,
            line={"color": "slateblue", "width": 1, "dash": "dash"},
            name="Qsol(z)"
        ))
        fig3.layout.title.text = "Effort dans le pieu"
        st.plotly_chart(fig3, use_container_width=True)

    st.divider()


def render_transverse_section(pieu, level_top):
    st.subheader("Comportement transversal de la fondation  ⚠️ En cours !")

    with st.expander("Données :"):
        _Eb_trans = st.number_input("Module d'Young du pieu [MPa] :", key="trans_Eb")
        _largeur = st.number_input("Largeur perpendiculaire au sens de déplacement [m] :", key="trans_largeur")
        _inertia = st.number_input("Moment d'inertie du pieu [m4] :", key="trans_inertia")
        force = st.number_input("Force horizontale en tête de pieu [kN] :", key="trans_force")
        bending = st.number_input("Moment fléchissant en tête de pieu [kN.m] :", key="trans_bending")
        comb_situation = st.selectbox(
            "Situation :",
            ["court terme", "long terme", "ELU", "sismique"],
            key="trans_situation",
        )

    tog_transversal = st.toggle("Lancer le calcul", key="tog_transversal")
    if not tog_transversal:
        return

    situation = str(comb_situation)
    horizontal_force = force / 1000
    bending_moment = bending / 1000

    pile_model = pieu.get_fe_model(horizontal_force, bending_moment, situation)
    pile_model.analyze_linear()

    abscisse, moment_raw, shear_raw, deflection_raw = utils.get_model_curves(pile_model, level_top)
    moment = [m * 1000 for m in moment_raw]
    shear = [v * 1000 for v in shear_raw]
    deflection = [d * 1000 for d in deflection_raw]

    z_top = utils.max_list(abscisse)
    z_bott = utils.min_list(abscisse)

    cola, colb = st.columns([3, 2])
    with cola:
        st.write("Moment fléchissant maximum :")
        st.write("Moment fléchissant minimum :")
        st.write("Effort tranchant maximum :")
        st.write("Effort tranchant minimum :")
        st.write("Déplacement horizontal maximum :")
        st.write("Déplacement horizontal minimum :")
    with colb:
        st.write(f"M_max = {utils.max_list(moment): .2f} kN.m")
        st.write(f"M_min = {utils.min_list(moment): .2f} kN.m")
        st.write(f"V_max = {utils.max_list(shear): .2f} kN")
        st.write(f"V_min = {utils.min_list(shear): .2f} kN")
        st.write(f"dy_max = {utils.max_list(deflection): .2f} mm")
        st.write(f"dy_min = {utils.min_list(deflection): .2f} mm")

    col1, col2, col3 = st.columns(3)

    with col1:
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            x=moment, y=abscisse,
            line={"color": "teal", "width": 2},
            name="M [kN.m]"
        ))
        fig1.add_trace(go.Scatter(
            x=[0, 0], y=[z_bott, z_top],
            line={"color": "slateblue", "width": 1, "dash": "dash"},
            name="0"
        ))
        fig1.layout.title.text = "Moment fléchissant"
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=shear, y=abscisse,
            line={"color": "teal", "width": 2},
            name="V [kN]"
        ))
        fig2.add_trace(go.Scatter(
            x=[0, 0], y=[z_bott, z_top],
            line={"color": "slateblue", "width": 1, "dash": "dash"},
            name="0"
        ))
        fig2.layout.title.text = "Effort tranchant"
        st.plotly_chart(fig2, use_container_width=True)

    with col3:
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=deflection, y=abscisse,
            line={"color": "teal", "width": 2},
            name="δy [mm]"
        ))
        fig3.add_trace(go.Scatter(
            x=[0, 0], y=[z_bott, z_top],
            line={"color": "slateblue", "width": 1, "dash": "dash"},
            name="0"
        ))
        fig3.layout.title.text = "Déplacement horizontal"
        st.plotly_chart(fig3, use_container_width=True)


def render_pile_summary(pieu):
    colA, colB, colC = st.columns(3)

    with colA:
        st.subheader("Description du pieu")
        st.markdown(
            f"""
        | Tableau A1 de la NF P94-262 |                         |
        |:---                         |---:                     |
        | Catégorie du pieu :         | {pieu.category}         |
        | Classe du pieu :            | {pieu.pile_classe}      |
        | {pieu.description} :        | {pieu.abreviation_pieu} |
        """
        )

    with colB:
        st.subheader("Paramètres de calculs")
        ple = round(pieu.ple_etoile, 3)
        d_ef = round(pieu.hauteur_encastrement_effective, 3)

        st.markdown(
            f"""
        | Description                           |              |               |
        |:---                                   |---:          |---:           |
        | Pression limite nette équivalente :   | $p_{{le*}}$ =| {ple} MPa     |
        | Hauteur d'encastrement effective :    | $D_{{ef}}$ = | {d_ef} m      |
        | Facteur de portance pressiométrique : | $k_{{p}}$ =  | {pieu.kp_util}|
        """
        )

    with colC:
        st.subheader("Coefficients partiels")
        st.markdown(
            f"""
        | Tableau F.2.1           |                    |                       |
        |:---                     |---:                |---:                   |
        | Pour la compression :   | $Ɣ_{{Rd1,comp}}$ = | {pieu.gamma_rd1_comp} |
        | Pour la traction :      | $Ɣ_{{Rd1,trac}}$ = | {pieu.gamma_rd1_trac} |
        | Compression & Traction :| $Ɣ_{{Rd2}}$ =      | {pieu.gamma_rd2}      |
        """
        )

    st.divider()


def render_resistance_section(pieu):
    st.subheader("Capacités résistantes du pieu")

    colA, colB, colC = st.columns(3)

    with colA:
        st.markdown(
            f"""
        | Valeurs caractéristiques         |                  |                                                |
        |:---                              |---:              |---:                                            |
        | Résistance de pointe :           | $R_{{b}}$ =      | {1000 * pieu.resistance_pointe: .1f} kN        |
        | Résistance de frottement axial : | $R_{{s}}$ =      | {1000 * pieu.resistance_skin_friction: .1f} kN |
        | Charge de fluage (compr.) :      | $R_{{c;cr;k}}$ = | {1000 * pieu.portance_fluage_car: .1f} kN      |
        | Charge de fluage (traction) :    | $R_{{t;cr;k}}$ = | {1000 * pieu.traction_fluage_car: .1f} kN      |
        """
        )

    with colB:
        st.markdown(
            f"""
        | Compression                 |                  |                                        |
        |:---                         |---:              |---:                                    |
        | ELS Quasi-Permanent :       | $R_{{c;cr;d}}$ = | {1000 * pieu.portance_ELS_QP: .1f} kN  |
        | ELS Caractéristique :       | $R_{{c;cr;d}}$ = | {1000 * pieu.portance_ELS_Car: .1f} kN |
        | ELU Structural :            | $R_{{cd}}$ =     | {1000 * pieu.portance_ELU_Str: .1f} kN |
        | ELU Accidentel :            | $R_{{cd}}$ =     | {1000 * pieu.portance_ELU_Acc: .1f} kN |
        """
        )

    with colC:
        st.markdown(
            f"""
        | Traction                    |                  |                                        |
        |:---                         |---:              |---:                                    |
        | ELS Quasi-Permanent :       | $R_{{t;cr;d}}$ = | {1000 * pieu.traction_ELS_QP: .1f} kN  |
        | ELS Caractéristique :       | $R_{{t;cr;d}}$ = | {1000 * pieu.traction_ELS_Car: .1f} kN |
        | ELU Structural :            | $R_{{td}}$ =     | {1000 * pieu.traction_ELU_Str: .1f} kN |
        | ELU Accidentel :            | $R_{{td}}$ =     | {1000 * pieu.traction_ELU_Acc: .1f} kN |
        """
        )

    st.divider()

