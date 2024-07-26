import math
import streamlit as st
import plotly.graph_objects as go

from geotech_module.pieu import Pile
from geotech_module.soil import Soil
import geotech_module.utils as utils

# NEW - This is a handy something from the standard library
from string import ascii_uppercase


st.divider()
st.title("Dimensionnement d'une fondation profonde isolée suivant la norme NF P94-262")
st.divider()

# Pieu
st.sidebar.title('Définition du pieu')
level_top = st.sidebar.number_input("Niveau supérieur du pieu [NGF]", value=0.0)
level_bot = st.sidebar.number_input("Niveau inférieur du pieu [NGF]", value=-14.0)
categorie = st.sidebar.number_input("Catégorie du pieu au sens du tableau A1:", value=19)
Eb = st.sidebar.number_input("Module de Young du pieu [MPa]", value=210_000)
pieu_dp = st.sidebar.number_input("Diamètre équivalent du pieu pour l'effort de pointe [mm]", value=46.3)
pieu_ds = st.sidebar.number_input("Diamètre équivalent du pieu pour le frottement [mm]", value=88.9)
interval = st.sidebar.number_input("Discretisation du pieu [mm]", value=200)

st.subheader('Lithologie')
nb_couches = st.number_input("Nombre de couches de sol à considérer pour l'étude du pieu (maxi 4) :", value = 4)
couches_sols = []

for idx in range(nb_couches):
    letter = ascii_uppercase[idx]
    soil_expander = st.expander(f"Couche do sol '{letter}'")
    
    with soil_expander:
        sol_name = st.text_input(f"Sol '{letter}' - Descriptif de la couche de sol :")
        sol_level_sup = st.number_input(f"Sol '{letter}' - Niveau supérieur de la couche de sol :", value=0.0)
        sol_level_inf = st.number_input(f"Sol '{letter}' - Niveau inférieur de la couche de sol :", value=-1.0)
        sol_courbe_frottement = st.selectbox(f"Sol '{letter}' - Courbe de frottement :", ['Q1', 'Q12', 'Q2', 'Q3', 'Q4', 'Q5'])
        sol_pf = st.number_input(f"Sol '{letter}' - Pression de fluage moyenne [MPa] :", value=0.0)
        sol_pl = st.number_input(f"Sol '{letter}' - Pression limite moyenne [MPa] :", value=0.0)
        sol_Em = st.number_input(f"Sol '{letter}' - Module pressiométrique moyen [MPa] :", value=5.0)
        sol_alpha = st.number_input(f"Sol '{letter}' - Coefficient alpha - suivant étude géotechnique :", value=0.67)

        sol= Soil(
            name=sol_name,
            level_sup=sol_level_sup,
            level_inf=sol_level_inf,
            courbe_frottement=sol_courbe_frottement,
            pf=sol_pf,
            pl=sol_pl,
            Em=sol_Em,
            alpha=sol_alpha
        )
    couches_sols.append(sol)

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

st.subheader('Description du pieu')
col1, col2 = st.columns([3, 1])
with col1:
    st.write('Catégorie du pieu au sens du tableau A1 de la NF P94-262 - Annexe A :')
    st.write('Classe du pieu :')
    st.write(pieu.description, ' :')
with col2:
    st.write(str(pieu.category))
    st.write(str(pieu.pile_classe))
    st.write(pieu.abreviation_pieu)
st.divider()


st.subheader('Capacité résistante du pieu')

colA, colB = st.columns(2)
with colA:
    st.subheader('Compression')
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('- ELS QP :')
        st.markdown('- ELS Car :')
        st.markdown('- ELU Str :')
        st.markdown('- ELU Acc :')
    with col2:
        st.write(str(f"{1000 * pieu.portance_ELS_QP: .1f} kN"))
        st.write(str(f"{1000 * pieu.portance_ELS_Car: .1f} kN"))
        st.write(str(f"{1000 * pieu.portance_ELU_Str: .1f} kN"))
        st.write(str(f"{1000 * pieu.portance_ELU_Acc: .1f} kN"))

with colB:
    st.subheader('Traction')
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('- ELS QP :')
        st.markdown('- ELS Car :')
        st.markdown('- ELU Str :')
        st.markdown('- ELU Acc :')
    with col2:
        st.write(str(f"{1000 * pieu.traction_ELS_QP: .1f} kN"))
        st.write(str(f"{1000 * pieu.traction_ELS_Car: .1f} kN"))
        st.write(str(f"{1000 * pieu.traction_ELU_Str: .1f} kN"))
        st.write(str(f"{1000 * pieu.traction_ELU_Acc: .1f} kN"))

st.divider()

st.subheader('Courbe de tassement du pieu')
tog_tass = st.toggle("tracer la courbe de tassement")

if tog_tass == True:
    tassement = pieu.settlement_curve()
    x_acc = []
    y_acc = []
    for x in tassement[1]:
        x_acc.append(1000 * x)
    for y in tassement[0]:
        y_acc.append(1000 * y)

    fig = go.Figure()

    # Plot lines
    fig.add_trace(
        go.Scatter(
        x=x_acc, 
        y=y_acc,
        line={"color": "teal"},
        name="Column B"
        )
    )
    fig.layout.title.text = "Courbe déterminée suivant l'annexe L de la NF P94-262"
    fig.layout.xaxis.title = "Charge vertical en tête de pieu [kN]"
    fig.layout.yaxis.title = "Déplacement vertical en tête de pieu [mm]"

    st.plotly_chart(fig)

st.divider()

st.subheader('Equilibre pour un chargement vertical donné')

tog_equ = st.toggle("Recherche de l'équilibre")
if tog_equ == True:
    resistance_maxi = math.floor(1000 * pieu.resistance_totale)
    q_target = st.slider("Charge verticale en tête de pieu [kN] :", min_value=0, max_value=resistance_maxi, value=380)

    equilibre = pieu.equilibre_Q_top(q_target / 1000)
    z_acc = []
    Q_acc = []
    Q_sol = []
    dz_acc = []
    dz_sol = []
    qs_acc = []
    qs_lim = []
    qs_max = -math.inf
    for slice in equilibre[3]:
        z_acc.append(slice.z_top)
        Q_acc.append(slice.Q_top * 1000)
        Q_sol.append(q_target - slice.Q_top * 1000)
        dz_acc.append(slice.dz_middle * 1000)
        dz_sol.append(0)
        qs_acc.append(slice.qs * 1000)
        qs_lim.append(slice.qs_lim * 1000)
        qs_max = max(qs_max, slice.qs)

    cola, colb = st.columns([3, 2])
    with cola:
        st.write('Effort vertical en tête de pieu :')
        st.write('Effort de pointe :')
        st.write('Déplacement vertical en tête de pieu :')
        st.write('Déplacement vertical au niveau de la pointe du pieu :')
        st.write('Frottement maximum sur la hauteur du pieu :')
    with colb:
        st.write(f"Q_top     = {1000 * equilibre[3][0].Q_top: .2f} kN")
        st.write(f"Q_bot     = {1000 * equilibre[3][-1].Q_bott: .2f} kN")
        st.write(f"dz_top    = {1000 * equilibre[3][0].dz_top: .2f} mm")
        st.write(f"dz_bot    = {1000 * equilibre[3][-1].dz_bott: .2f} mm")
        st.write(f"qs_max    = {1000 * qs_max: .2f} kPa")

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

st.subheader('Comportement transversal de la fondation')

# Données complémentaires
with st.expander("Données :"):
    Eb = st.number_input("Module d'Young du pieu [MPa] :", value=20_000)
    largeur = st.number_input("Largeur perpendiculaire au sens de déplacement [m] :", value=0.250)
    inertia = st.number_input("Moment d'inertie du pieu [m4] :", value=0.001)
    force = st.number_input("Force horizontale en tête de pieu [kN] :", value=0.0)
    bending = st.number_input("Moment fléchissant en tête de pieu [kN.m] :", value=0.0)
    comb_situation = st.selectbox("Situation :", ['court terme', 'long terme', 'ELU', 'sismique'])

tog_transversal = st.toggle("Lancer le calcul")
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
