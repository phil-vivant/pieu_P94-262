import streamlit as st
from geotech_module.pieu import Pile
from ui_sections import (
    build_pile_sidebar_inputs,
    lithology_ui,
    render_settlement_section,
    render_equilibrium_section,
    render_transverse_section,
    render_pile_summary,
    render_resistance_section,
    render_header,
)
from persistence import persistence_ui, DEFAULTS, run_pending_import_if_any


st.set_page_config(
    page_title="Appli Pieu",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialisation des clés "simples"
for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)

run_pending_import_if_any()

# Messages post-import
if st.session_state.pop("_import_ok", False):
    st.toast("Paramètres chargés ✅")

if "_import_error" in st.session_state:
    st.error(f"Fichier invalide : {st.session_state.pop('_import_error')}")



render_header()
couches_sols, z1_sup = lithology_ui()

persistence_ui()

pile_inputs = build_pile_sidebar_inputs()
pieu = Pile(
    category=pile_inputs["categorie"],
    level_top=pile_inputs["level_top"],
    level_bott=pile_inputs["level_bot"],
    Eb=pile_inputs["Eb"],
    Dp=pile_inputs["pieu_dp"] / 1000,
    Ds=pile_inputs["pieu_ds"] / 1000,
    lithology=couches_sols,
    thickness=pile_inputs["interval"] / 1000,
)

render_pile_summary(pieu)
render_resistance_section(pieu)
render_settlement_section(pieu)
render_equilibrium_section(pieu)
render_transverse_section(pieu, pile_inputs["level_top"])
