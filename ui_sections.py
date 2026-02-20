import streamlit as st


def build_pile_sidebar():
    st.sidebar.title("Définition du pieu")

    level_top = st.sidebar.number_input("Niveau supérieur du pieu [NGF]", key="pile_top")
    level_bot = st.sidebar.number_input("Niveau inférieur du pieu [NGF]", key="pile_bot")
    categorie = int(
        st.sidebar.number_input(
            "Catégorie du pieu au sens du tableau A1:",
            min_value=1,
            step=1,
            key="pile_cat",
        )
    )
    Eb = st.sidebar.number_input("Module de Young du pieu [MPa]", key="pile_Eb")
    pieu_dp = st.sidebar.number_input("Diamètre équivalent du pieu pour l'effort de pointe [mm]", key="pile_dp")
    pieu_ds = st.sidebar.number_input("Diamètre équivalent du pieu pour le frottement [mm]", key="pile_ds")
    interval = st.sidebar.number_input("Discretisation du pieu [mm]", key="pile_int")

    return {
        "level_top": level_top,
        "level_bot": level_bot,
        "categorie": categorie,
        "Eb": Eb,
        "pieu_dp": pieu_dp,
        "pieu_ds": pieu_ds,
        "interval": interval,
    }
