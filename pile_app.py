import math
import json
from datetime import datetime
import streamlit as st
import plotly.graph_objects as go
import hashlib

from geotech_module.pieu import Pile
from geotech_module.soil import Soil
import geotech_module.utils as utils


st.set_page_config(
    page_title="Appli Pieu",
    layout="wide",
    initial_sidebar_state="expanded",
)


APP_STATE_KEYS = [
    # Pieu
    "pile_top", "pile_bot", "pile_cat", "pile_Eb", "pile_dp", "pile_ds", "pile_int",

    # Lithologie
    "soil_nb_layers",

    # Sol A
    "soil_a_name", "soil_a_zsup", "soil_a_zinf", "soil_a_curve", "soil_a_pf", "soil_a_pl", "soil_a_Em", "soil_a_alpha", "soil_a_type",

    # Sol B
    "soil_b_name", "soil_b_zsup", "soil_b_zinf", "soil_b_curve", "soil_b_pf", "soil_b_pl", "soil_b_Em", "soil_b_alpha", "soil_b_type",

    # Sol C
    "soil_c_name", "soil_c_zsup", "soil_c_zinf", "soil_c_curve", "soil_c_pf", "soil_c_pl", "soil_c_Em", "soil_c_alpha", "soil_c_type",

    # Sol D
    "soil_d_name", "soil_d_zsup", "soil_d_zinf", "soil_d_curve", "soil_d_pf", "soil_d_pl", "soil_d_Em", "soil_d_alpha", "soil_d_type",

    # Sol E
    "soil_e_name", "soil_e_zsup", "soil_e_zinf", "soil_e_curve", "soil_e_pf", "soil_e_pl", "soil_e_Em", "soil_e_alpha", "soil_e_type",

    # Toggles / actions
    "tog_tass",
    "tog_equ", "q_target",

    # Transversal
    "trans_Eb", "trans_largeur", "trans_inertia", "trans_force", "trans_bending", "trans_situation",
    "tog_transversal",
]

ROUND_FORCE = 1
ROUND_DEPL = 2


def export_state(keys):
    return {k: st.session_state.get(k) for k in keys if k in st.session_state}

def import_state(payload, keys):
    for k in keys:
        if k in payload:
            st.session_state[k] = payload[k]

def persistence_ui(keys=APP_STATE_KEYS):
    with st.sidebar.expander("💾 Sauvegarde / Chargement", expanded=False):
        name = st.text_input("Nom du cas", value="cas_pieu", key="case_name")

        # Sauvegarde
        data = export_state(keys)
        stamp = datetime.now().strftime("%Y-%m-%d - %Hh%Mmin%Ss")
        st.download_button(
            "⬇️ Sauver (.json)",
            data=json.dumps(data, ensure_ascii=False, indent=2),
            file_name=f"{name}_{stamp}.json",
            mime="application/json",
            use_container_width=True,
        )

        # --- Chargement ---
        # Si un run précédent a demandé à "vider" l'uploader, on le fait AVANT d'instancier le widget
        if st.session_state.get("_clear_state_file", False):
            st.session_state.pop("state_file", None)
            st.session_state["_clear_state_file"] = False

        up = st.file_uploader("⬆️ Charger (.json)", type=["json"], key="state_file")

        if up is not None:
            if st.button("✅ Appliquer le fichier", use_container_width=True, key="apply_state"):
                try:
                    file_bytes = up.getvalue()
                    file_hash = hashlib.sha256(file_bytes).hexdigest()

                    payload = json.loads(file_bytes.decode("utf-8"))
                    import_state(payload, keys)

                    # Mémorise que ce fichier a été chargé (optionnel mais utile)
                    st.session_state["_last_loaded_hash"] = file_hash

                    # IMPORTANT : on demandera à vider l'uploader AU PROCHAIN run
                    st.session_state["_clear_state_file"] = True

                    st.toast("Paramètres chargés ✅")
                    st.rerun()
                except Exception as e:
                    st.error(f"Fichier invalide : {e}")

st.divider()
st.title("Dimensionnement d'une fondation profonde isolée suivant la norme NF P94-262")
st.divider()

persistence_ui()

###  ----------------- Définition du Pieu  ----------------- ###

# Pieu
st.sidebar.title('Définition du pieu')
level_top = st.sidebar.number_input("Niveau supérieur du pieu [NGF]", value=0.0, key="pile_top")
level_bot = st.sidebar.number_input("Niveau inférieur du pieu [NGF]", value=-14.0, key="pile_bot")
categorie = st.sidebar.number_input("Catégorie du pieu au sens du tableau A1:", value=19, key="pile_cat")
Eb = st.sidebar.number_input("Module de Young du pieu [MPa]", value=210_000, key="pile_Eb")
pieu_dp = st.sidebar.number_input("Diamètre équivalent du pieu pour l'effort de pointe [mm]", value=46.3, key="pile_dp")
pieu_ds = st.sidebar.number_input("Diamètre équivalent du pieu pour le frottement [mm]", value=88.9, key="pile_ds")
interval = st.sidebar.number_input("Discretisation du pieu [mm]", value=200, key="pile_int")


###  ----------------- Définition des couches de sols  ----------------- ###

st.subheader('Lithologie')
nb_couches = st.number_input("Nombre de couches de sol à considérer pour l'étude du pieu (maxi 5) :", value = 4, key="soil_nb_layers")
couches_sols = []

# Sol A
with st.expander("Couche de sol 'A'"):
    sol_a_name = st.text_input("Sol 'A' - Descriptif de la couche de sol :", key="soil_a_name")
    sol_a_level_sup = st.number_input("Sol 'A' - Niveau supérieur de la couche de sol :", value=0.0, key="soil_a_zsup")
    sol_a_level_inf = st.number_input("Sol 'A' - Niveau inférieur de la couche de sol :", value=-1.0, key="soil_a_zinf")
    sol_a_courbe_frottement = st.selectbox("Sol 'A' - Courbe de frottement :", ['Q1', 'Q12', 'Q2', 'Q3', 'Q4', 'Q5'], key="soil_a_curve")
    sol_a_pf = st.number_input("Sol 'A' - Pression de fluage moyenne [MPa] :", value=0.0, key="soil_a_pf")
    sol_a_pl = st.number_input("Sol 'A' - Pression limite moyenne [MPa] :", value=0.0, key="soil_a_pl")
    sol_a_Em = st.number_input("Sol 'A' - Module pressiométrique moyen [MPa] :", value=5.0, key="soil_a_Em")
    sol_a_alpha = st.number_input("Sol 'A' - Coefficient alpha - suivant étude géotechnique :", value=0.67, key="soil_a_alpha")
    sol_a_type = st.selectbox("Sol 'A' - Type de sol :", ['granulaire', 'fin'], key="soil_a_type")

    sol_A = Soil(
        name=sol_a_name,
        level_sup=sol_a_level_sup,
        level_inf=sol_a_level_inf,
        courbe_frottement=sol_a_courbe_frottement,
        pf=sol_a_pf,
        pl=sol_a_pl,
        Em=sol_a_Em,
        alpha=sol_a_alpha,
        soil_type=sol_a_type,
    )
    couches_sols.append(sol_A)

if nb_couches >=2:
    with st.expander("Couche de sol 'B'"):
        sol_b_name = st.text_input("Sol 'B' - Descriptif de la couche de sol :", key="soil_b_name")
        sol_b_level_sup = st.number_input("Sol 'B' - Niveau supérieur de la couche de sol :", value=sol_a_level_inf, key="soil_b_zsup")
        sol_b_level_inf = st.number_input("Sol 'B' - Niveau inférieur de la couche de sol :", value=-8.0, key="soil_b_zinf")
        sol_b_courbe_frottement = st.selectbox("Sol 'B' - Courbe de frottement :", ['Q1', 'Q12', 'Q2', 'Q3', 'Q4', 'Q5'], key="soil_b_curve")
        sol_b_pf = st.number_input("Sol 'B' - Pression de fluage moyenne [MPa] :", value=0.8, key="soil_b_pf")
        sol_b_pl = st.number_input("Sol 'B' - Pression limite moyenne [MPa] :", value=1.2, key="soil_b_pl")
        sol_b_Em = st.number_input("Sol 'B' - Module pressiométrique moyen [MPa] :", value=8.0, key="soil_b_Em")
        sol_b_alpha = st.number_input("Sol 'B' - Coefficient alpha - suivant étude géotechnique :", value=0.67, key="soil_b_alpha")
        sol_b_type = st.selectbox("Sol 'B' - Type de sol :", ['granulaire', 'fin'], key="soil_b_type")

        sol_B = Soil(
            name=sol_b_name,
            level_sup=sol_b_level_sup,
            level_inf=sol_b_level_inf,
            courbe_frottement=sol_b_courbe_frottement,
            pf=sol_b_pf,
            pl=sol_b_pl,
            Em=sol_b_Em,
            alpha=sol_b_alpha,
            soil_type=sol_b_type,
        )
    couches_sols.append(sol_B)

if nb_couches >=3:
    with st.expander("Couche de sol 'C'"):
        sol_c_name = st.text_input("Sol 'C' - Descriptif de la couche de sol :", key="soil_c_name")
        sol_c_level_sup = st.number_input("Sol 'C' - Niveau supérieur de la couche de sol :", value=sol_b_level_inf, key="soil_c_zsup")
        sol_c_level_inf = st.number_input("Sol 'C' - Niveau inférieur de la couche de sol :", value=-12.0, key="soil_c_zinf")
        sol_c_courbe_frottement = st.selectbox("Sol 'C' - Courbe de frottement :", ['Q1', 'Q12', 'Q2', 'Q3', 'Q4', 'Q5'], key="soil_c_curve")
        sol_c_pf = st.number_input("Sol 'C' - Pression de fluage moyenne [MPa] :", value=0.6, key="soil_c_pf")
        sol_c_pl = st.number_input("Sol 'C' - Pression limite moyenne [MPa] :", value=0.8, key="soil_c_pl")
        sol_c_Em = st.number_input("Sol 'C' - Module pressiométrique moyen [MPa] :", value=6.0, key="soil_c_Em")
        sol_c_alpha = st.number_input("Sol 'C' - Coefficient alpha - suivant étude géotechnique :", value=0.67, key="soil_c_alpha")
        sol_c_type = st.selectbox("Sol 'C' - Type de sol :", ['granulaire', 'fin'], key="soil_c_type")

        sol_C = Soil(
            name=sol_c_name,
            level_sup=sol_c_level_sup,
            level_inf=sol_c_level_inf,
            courbe_frottement=sol_c_courbe_frottement,
            pf=sol_c_pf,
            pl=sol_c_pl,
            Em=sol_c_Em,
            alpha=sol_c_alpha,
            soil_type=sol_c_type,
        )
    couches_sols.append(sol_C)

if nb_couches >=4:
    with st.expander("Couche de sol 'D'"):
        sol_d_name = st.text_input("Sol 'D' - Descriptif de la couche de sol :", key="soil_d_name")
        sol_d_level_sup = st.number_input("Sol 'D' - Niveau supérieur de la couche de sol :", value=sol_c_level_inf, key="soil_d_zsup")
        sol_d_level_inf = st.number_input("Sol 'D' - Niveau inférieur de la couche de sol :", value=-20.0, key="soil_d_zinf")
        sol_d_courbe_frottement = st.selectbox("Sol 'D' - Courbe de frottement :", ['Q1', 'Q12', 'Q2', 'Q3', 'Q4', 'Q5'], key="soil_d_curve")
        sol_d_pf = st.number_input("Sol 'D' - Pression de fluage moyenne [MPa] :", value=1.3, key="soil_d_pf")
        sol_d_pl = st.number_input("Sol 'D' - Pression limite moyenne [MPa] :", value=1.8, key="soil_d_pl")
        sol_d_Em = st.number_input("Sol 'D' - Module pressiométrique moyen [MPa] :", value=10.0, key="soil_d_Em")
        sol_d_alpha = st.number_input("Sol 'D' - Coefficient alpha - suivant étude géotechnique :", value=0.67, key="soil_d_alpha")
        sol_d_type = st.selectbox("Sol 'D' - Type de sol :", ['granulaire', 'fin'], key="soil_d_type")

        sol_D = Soil(
            name=sol_d_name,
            level_sup=sol_d_level_sup,
            level_inf=sol_d_level_inf,
            courbe_frottement=sol_d_courbe_frottement,
            pf=sol_d_pf,
            pl=sol_d_pl,
            Em=sol_d_Em,
            alpha=sol_d_alpha,
            soil_type=sol_d_type,
        )
    couches_sols.append(sol_D)

if nb_couches >=5:
    with st.expander("Couche de sol 'E'"):
        sol_e_name = st.text_input("Sol 'E' - Descriptif de la couche de sol :", key="soil_e_name")
        sol_e_level_sup = st.number_input("Sol 'E' - Niveau supérieur de la couche de sol :", value=sol_d_level_inf, key="soil_e_zsup")
        sol_e_level_inf = st.number_input("Sol 'E' - Niveau inférieur de la couche de sol :", value=-30.0, key="soil_e_zinf")
        sol_e_courbe_frottement = st.selectbox("Sol 'E' - Courbe de frottement :", ['Q1', 'Q12', 'Q2', 'Q3', 'Q4', 'Q5'], key="soil_e_curve")
        sol_e_pf = st.number_input("Sol 'E' - Pression de fluage moyenne [MPa] :", value=1.3, key="soil_e_pf")
        sol_e_pl = st.number_input("Sol 'E' - Pression limite moyenne [MPa] :", value=1.8, key="soil_e_pl")
        sol_e_Em = st.number_input("Sol 'E' - Module pressiométrique moyen [MPa] :", value=10.0, key="soil_e_Em")
        sol_e_alpha = st.number_input("Sol 'E' - Coefficient alpha - suivant étude géotechnique :", value=0.67, key="soil_e_alpha")
        sol_e_type = st.selectbox("Sol 'E' - Type de sol :", ['granulaire', 'fin'], key="soil_e_type")

        sol_E = Soil(
            name=sol_e_name,
            level_sup=sol_e_level_sup,
            level_inf=sol_e_level_inf,
            courbe_frottement=sol_e_courbe_frottement,
            pf=sol_e_pf,
            pl=sol_e_pl,
            Em=sol_e_Em,
            alpha=sol_e_alpha,
            soil_type=sol_e_type,
        )
    couches_sols.append(sol_E)

st.divider()

pieu = Pile(
    category=categorie,
    level_top=level_top,
    level_bott=level_bot,
    Eb=Eb,
    Dp=pieu_dp / 1000,
    Ds=pieu_ds / 1000,
    lithology=couches_sols,
    thickness=interval / 1000
)

colA, colB, colC = st.columns(3)
with colA:
    st.subheader('Description du pieu')
    st.markdown(
        f"""
    | Tableau A1 de la NF P94-262 |                         |
    |:---                         |---:                     |
    | Catégorie du pieu :         | {str(pieu.category)}    |
    | Classe du pieu :            | {str(pieu.pile_classe)} |
    | {pieu.description} :        | {pieu.abreviation_pieu} |
    """
    )
with colB:
    st.subheader('Paramètres de calculs')
    st.markdown(
        f"""
    | Description                            |               |                                                   |
    |:---                                    |---:           |---:                                               |
    | Pression limite nette équivalente :    | $p_{{le*}}$ = | {round(pieu.ple_etoile, 3)} MPa                   |
    | Hauteur d'encastrement effective :     | $D_{{ef}}$ =  | {round(pieu.hauteur_encastrement_effective, 3)} m |
    | Facteur de portance pressiométrique :  | $k_{{p}}$ =   | {pieu.kp_util}                                    |
    """
    )

with colC:
    st.subheader('Coefficients partiels')
    st.markdown(
        f"""
    | Tableau F.2.1            |                    |                       |
    |:---                      |---:                |---:                   |
    | Pour la compression :    | $Ɣ_{{Rd1,comp}}$ = | {pieu.gamma_rd1_comp} |
    | Pour la traction :       | $Ɣ_{{Rd1,trac}}$ = | {pieu.gamma_rd1_trac} |
    | Compression & Traction : | $Ɣ_{{Rd2}}$ =      | {pieu.gamma_rd2}      |
    """
    )

st.divider()


###  ----------------- Capacités Résistantes du Pieu  ----------------- ###

st.subheader('Capacité résistante du pieu')

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
    | Résistances en Compression |                  |                                        |
    |:---                        |---:              |---:                                    |
    | ELS Quasi-Permanent :      | $R_{{c;cr;d}}$ = | {1000 * pieu.portance_ELS_QP: .1f} kN  |
    | ELS Caractéristique :      | $R_{{c;cr;d}}$ = | {1000 * pieu.portance_ELS_Car: .1f} kN |
    | ELU Structural :           | $R_{{cd}}$ =     | {1000 * pieu.portance_ELU_Str: .1f} kN |
    | ELU Accidentel :           | $R_{{cd}}$ =     | {1000 * pieu.portance_ELU_Acc: .1f} kN |
    """
    )

with colC:
    st.markdown(
        f"""
    | Résistances en Traction |                  |                                        |
    |:---                     |---:              |---:                                    |
    | ELS Quasi-Permanent :   | $R_{{t;cr;d}}$ = | {1000 * pieu.traction_ELS_QP: .1f} kN  |
    | ELS Caractéristique :   | $R_{{t;cr;d}}$ = | {1000 * pieu.traction_ELS_Car: .1f} kN |
    | ELU Structural :        | $R_{{td}}$ =     | {1000 * pieu.traction_ELU_Str: .1f} kN |
    | ELU Accidentel :        | $R_{{td}}$ =     | {1000 * pieu.traction_ELU_Acc: .1f} kN |
    """
    )

st.divider()

###  ----------------- Courbe de tassement  ----------------- ###

st.subheader("Courbe de tassement du pieu - Méthode de Franck & Zhao - NF P94-262 Annexe L")
tog_tass = st.toggle("Tracer la courbe de tassement", key="tog_tass")

if tog_tass == True:

    tassement = pieu.settlement_curve()
    dz = tassement[0]      # y
    Q  = tassement[1]      # x = Qtete

    # mise à l'échelle (MN->kN)
    pairs = [(1000*q, 1000*d) for q, d in zip(Q, dz)]

    neg = [(q, d) for (q, d) in pairs if q <= 0]
    pos = [(q, d) for (q, d) in pairs if q >= 0]

    # Pour l'affichage : s'assurer que (0,0) est présent dans chaque série
    # (sans le dupliquer si déjà là)
    def ensure_origin(lst):
        if not any(abs(q) < 1e-12 and abs(d) < 1e-12 for (q, d) in lst):
            lst = lst + [(0.0, 0.0)]
        return lst

    neg = ensure_origin(neg)
    pos = ensure_origin(pos)

    # Trier par Qtete
    neg = sorted(neg, key=lambda t: t[0])
    pos = sorted(pos, key=lambda t: t[0])

    x_acc_neg = [round(q, ROUND_FORCE) for (q, d) in neg]
    y_acc_neg = [round(d, ROUND_DEPL) for (q, d) in neg]
    x_acc_pos = [round(q, ROUND_FORCE) for (q, d) in pos]
    y_acc_pos = [round(d, ROUND_DEPL) for (q, d) in pos]

    # Raideur Kz = Q / dz, scindée aussi
    eps = 1e-6  # en mm si tu as mis *1000 ; ajuste si besoin
    x_kz_acc_neg = [q for (q, d) in neg if abs(d) > eps]
    Kz_acc_neg   = [q / d for (q, d) in neg if abs(d) > eps]

    x_kz_acc_pos = [round(q, ROUND_FORCE) for (q, d) in pos if abs(d) > eps]
    Kz_acc_pos   = [round(q / d, ROUND_DEPL) for (q, d) in pos if abs(d) > eps]


    col1, col2 = st.columns(2)
    with col1:
        # st.write('Tassement pieu/sol')
        fig1 = go.Figure()
        fig1.add_trace(
            go.Scatter(
            x=x_acc_neg, 
            y=y_acc_neg,
            line={"color": "teal", "dash":"dash"},
            name="Traction"
            )
        )
        fig1.add_trace(
            go.Scatter(
            x=x_acc_pos,
            y=y_acc_pos,
            line={"color": "teal"},
            name="Compression"
            )
        )
        fig1.layout.title.text = "Courbe de tassement"
        fig1.layout.xaxis.title = "Charge vertical en tête de pieu [kN]"
        fig1.layout.yaxis.title = "Déplacement vertical en tête de pieu [mm]"
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        # st.write('Frottement pieu/sol')
        fig2 = go.Figure()
        fig2.add_trace(
            go.Scatter(
            x=x_kz_acc_neg, 
            y=Kz_acc_neg,
            line={"color": "slateblue", "dash": "dash", 'width': 2},
            name="Kz_neg"
            )
        )
        fig2.add_trace(
            go.Scatter(
            x=x_kz_acc_pos, 
            y=Kz_acc_pos,
            line={"color": "slateblue", 'width': 2},
            name="Kz_pos"
            )
        )

        fig2.layout.title.text = "Courbe de raideur axiale du pieu"
        fig2.layout.xaxis.title = "Charge vertical en tête de pieu [kN]"
        fig2.layout.yaxis.title = "Raideur axiale en tête de pieu [MN/ml]"
        st.plotly_chart(fig2, use_container_width=True)

st.divider()

###  ----------------- Étude de l'équilibre général du pieu  ----------------- ###

st.subheader('Équilibre pour un chargement vertical donné')

tog_equ = st.toggle("Recherche de l'équilibre", key="tog_equ")
if tog_equ == True:
    resistance_mini = math.floor(-1000 * pieu.resistance_skin_friction)
    resistance_maxi = math.floor(1000 * pieu.resistance_totale)
    q_target = st.slider(
        "Charge verticale en tête de pieu [kN] :",
        min_value=resistance_mini,
        max_value=resistance_maxi,
        value=380,
        key="q_target"
    )

    equilibre = pieu.equilibre_top_down_Qtete(q_target / 1000)
    z_acc = []
    Q_acc = []
    Q_sol = []
    dz_acc = []
    dz_sol = []
    qs_acc = []
    qs_lim = []
    qs_max = -math.inf
    for slice in equilibre[2]:
        z_acc.append(slice.z_top)
        Q_acc.append(slice.Q_top * 1000)
        Q_sol.append(q_target - slice.Q_top * 1000)
        dz_acc.append(slice.dz_middle * 1000)
        dz_sol.append(0)
        qs_acc.append(slice.qs * 1000)
        qs_lim.append(slice.qs_lim * 1000)
        qs_max = max(qs_max, slice.qs)

    # cola, colb = st.columns([3, 2])
    # with cola:
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
        st.write('Tassement pieu/sol')
        fig1 = go.Figure()
        fig1.add_trace(
            go.Scatter(
            x=dz_acc, 
            y=z_acc,
            line={"color": "teal", 'width': 2},
            name="δz sol"
            )
        )
        fig1.add_trace(
            go.Scatter(
            x=dz_sol, 
            y=z_acc,
            line={"color": "slateblue", 'width': 1, 'dash':'dash'},
            name="δz sol"
            )
        )
        st.plotly_chart(fig1, use_container_width=True)
        fig1.layout.title.text = "Tassement pieu/sol"
    with col2:
        st.write('Frottement pieu/sol')
        fig2 = go.Figure()
        fig2.add_trace(
            go.Scatter(
            x=qs_acc, 
            y=z_acc,
            line={"color": "teal", 'width': 2},
            name="qs"
            )
        )
        fig2.add_trace(
            go.Scatter(
            x=qs_lim, 
            y=z_acc,
            line={"color": "slateblue", 'width': 1, 'dash':'dash'},
            name="qs_lim"
            )
        )

        st.plotly_chart(fig2, use_container_width=True)
    with col3:
        st.write('Effort dans le pieu')
        fig3 = go.Figure()
        fig3.add_trace(
            go.Scatter(
            x=Q_acc, 
            y=z_acc,
            line={"color": "teal", 'width': 2},
            name="Qpieu(z)"
            )
        )
        fig3.add_trace(
            go.Scatter(
            x=Q_sol, 
            y=z_acc,
            line={"color": "slateblue", 'width': 1, 'dash':'dash'},
            name="Qsol(z)"
            )
        )
        st.plotly_chart(fig3, use_container_width=True)


st.divider()

st.subheader('Comportement transversal de la fondation  ⚠️ En cours !')

# Données complémentaires
with st.expander("Données :"):
    Eb_trans = st.number_input("Module d'Young du pieu [MPa] :", value=20_000, key="trans_Eb")
    largeur = st.number_input("Largeur perpendiculaire au sens de déplacement [m] :", value=0.250, key="trans_largeur")
    inertia = st.number_input("Moment d'inertie du pieu [m4] :", value=0.001, key="trans_inertia")
    force = st.number_input("Force horizontale en tête de pieu [kN] :", value=0.0, key="trans_force")
    bending = st.number_input("Moment fléchissant en tête de pieu [kN.m] :", value=0.0, key="trans_bending")
    comb_situation = st.selectbox("Situation :", ['court terme', 'long terme', 'ELU', 'sismique'], key="trans_situation")

tog_transversal = st.toggle("Lancer le calcul", key="tog_transversal")
if tog_transversal == True:
    situation = str(comb_situation)
    horizontal_force = force / 1000
    bending_moment = bending / 1000
    pile_model = pieu.get_fe_model(horizontal_force, bending_moment, situation)
    pile_model.analyze_linear()

    get_curves = utils.get_model_curves(pile_model, level_top)
    abscisse = get_curves[0]
    moment = [m*1000 for m in get_curves[1]]
    shear = [v*1000 for v in get_curves[2]]
    deflection = [d*1000 for d in get_curves[3]]

    z_top = utils.max_list(abscisse)
    z_bott = utils.min_list(abscisse)

    cola, colb = st.columns([3, 2])
    with cola:
        st.write('Moment fléchissant maximum :')
        st.write('Moment fléchissant minimum :')
        st.write('Effort tranchant maximum :')
        st.write('Effort tranchant minimum :')
        st.write('Déplacement horizontal maximum :')
        st.write('Déplacement horizontal minimum :')
    with colb:
        st.write(f"M_max     = {utils.max_list(moment): .2f} kN.m")
        st.write(f"M_min     = {utils.min_list(moment): .2f} kN.m")
        st.write(f"V_max     = {utils.max_list(shear): .2f} kN")
        st.write(f"V_min     = {utils.min_list(shear): .2f} kN")
        st.write(f"dy_max     = {utils.max_list(deflection): .2f} mm")
        st.write(f"dy_min     = {utils.min_list(deflection): .2f} mm")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.write('Moment flechissant')
        fig1 = go.Figure()
        fig1.add_trace(
            go.Scatter(
            x=moment, 
            y=abscisse,
            line={"color": "teal", 'width': 2},
            name="M [kN.m]"
            )
        )
        fig1.add_trace(
            go.Scatter(
            x=[0, 0], 
            y=[z_bott, z_top],
            line={"color": "slateblue", 'width': 1, 'dash':'dash'},
            name="0"
            )
        )

        st.plotly_chart(fig1, use_container_width=True)
        fig1.layout.title.text = "Moment fléchissant"
    with col2:
        st.write('Effort tranchant')
        fig2 = go.Figure()
        fig2.add_trace(
            go.Scatter(
            x=shear, 
            y=abscisse,
            line={"color": "teal", 'width': 2},
            name="V [kN]"
            )
        )
        fig2.add_trace(
            go.Scatter(
            x=[0, 0], 
            y=[z_bott, z_top],
            line={"color": "slateblue", 'width': 1, 'dash':'dash'},
            name="0"
            )
        )
        st.plotly_chart(fig2, use_container_width=True)
    with col3:
        st.write('Déplacement horizontal')
        fig3 = go.Figure()
        fig3.add_trace(
            go.Scatter(
            x=deflection, 
            y=abscisse,
            line={"color": "teal", 'width': 2},
            name="δy [mm]"
            )
        )
        fig3.add_trace(
            go.Scatter(
            x=[0, 0], 
            y=[z_bott, z_top],
            line={"color": "slateblue", 'width': 1, 'dash':'dash'},
            name="0"
            )
        )
        st.plotly_chart(fig3, use_container_width=True)
