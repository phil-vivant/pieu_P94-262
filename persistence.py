from datetime import datetime
import streamlit as st
import pandas as pd
import json
import hashlib


APP_STATE_KEYS = [
    # Sol
    "z1_sup",

    # Pieu
    "pile_top", "pile_bot", "pile_cat", "pile_Eb", "pile_dp",
    "pile_ds", "pile_int",

    # Toggles / actions
    "tog_tass",
    "tog_equ", "q_target",

    # Transversal
    "trans_Eb", "trans_largeur", "trans_inertia", "trans_force",
    "trans_bending", "trans_situation",
    "tog_transversal",
]

DEFAULTS = {
    # Sol
    "z1_sup": 0.0,
    # Pieu
    "pile_top": 0.0,
    "pile_bot": -10.0,
    "pile_cat": 3,
    "pile_Eb": 10_000,
    "pile_dp": 800,
    "pile_ds": 800,
    "pile_int": 50,

    # Toggles / actions
    "tog_tass": False,
    "tog_equ": False,
    "q_target": 1500.0,

    # Transversal
    "trans_Eb": 10_000,
    "trans_largeur": 1.0,
    "trans_inertia": 1.0,
    "trans_force": 100.0,
    "trans_bending": 100.0,
    "trans_situation": "court terme",
    "tog_transversal": False,

    # (optionnel) UI
    "case_name": "NDC_Pieu",
}
APP_SIMPLE_KEYS = list(DEFAULTS.keys())


def export_state():
    state = {}

    # 1) Variables simples
    for k in APP_SIMPLE_KEYS:
        state[k] = st.session_state.get(k, DEFAULTS.get(k))

    # 2) Lithologie (version appliquée)
    df = st.session_state.get("soil_df", pd.DataFrame())
    state["soils"] = df.to_dict(orient="records")

    state["_schema"] = "pieu_app_state_v2"
    return state


def import_state(payload):
    if "soils" not in payload or not isinstance(payload["soils"], list):
        raise ValueError("Champ 'soils' manquant ou invalide (attendu: liste).")

    # Variables simples
    for k in APP_SIMPLE_KEYS:
        if k in payload:
            # petits casts utiles
            if k in {"pile_cat", "pile_int"}:
                st.session_state[k] = int(payload[k])
            elif isinstance(DEFAULTS.get(k), bool):
                st.session_state[k] = bool(payload[k])
            elif isinstance(DEFAULTS.get(k), int):
                st.session_state[k] = int(payload[k])
            elif isinstance(DEFAULTS.get(k), float):
                st.session_state[k] = float(payload[k])
            else:
                st.session_state[k] = payload[k]
        else:
            st.session_state.setdefault(k, DEFAULTS.get(k))

    # Lithologie
    st.session_state["soil_df"] = pd.DataFrame(payload["soils"])


def run_pending_import_if_any():
    """
    Applique un import JSON différé avant la création des widgets Streamlit.

    Pourquoi :
    - Streamlit interdit de modifier st.session_state["..."] d'un widget
      après instanciation du widget.
    - On stocke donc le payload JSON dans _pending_import_payload, puis
      on l'applique au run suivant, tout en haut du script.
    """
    if "_pending_import_payload" not in st.session_state:
        return

    try:
        payload = st.session_state.pop("_pending_import_payload")
        import_state(payload)
        st.session_state["_import_ok"] = True

    except Exception as e:
        st.session_state["_import_error"] = str(e)


def persistence_ui(simple_keys=APP_SIMPLE_KEYS):
    with st.sidebar.expander("💾 Sauvegarde / Chargement", expanded=False):
        name = st.text_input("Nom du cas", key="case_name")

        data = export_state()
        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        st.download_button(
            "⬇️ Sauver (.json)",
            data=json.dumps(data, ensure_ascii=False, indent=2),
            file_name=f"{name}_{stamp}.json",
            mime="application/json",
            width="stretch",
        )

        # reset uploader au run suivant
        if st.session_state.get("_clear_state_file", False):
            st.session_state.pop("state_file", None)
            st.session_state["_clear_state_file"] = False

        up = st.file_uploader("⬆️ Charger (.json)", type=["json"], key="state_file")

        if up is not None:
            if st.button("✅ Appliquer le fichier", width="stretch", key="apply_state"):
                try:
                    file_bytes = up.getvalue()
                    file_hash = hashlib.sha256(file_bytes).hexdigest()
                    payload = json.loads(file_bytes.decode("utf-8"))

                    # ✅ IMPORT DIFFÉRÉ (et non import_state direct)
                    st.session_state["_pending_import_payload"] = payload
                    st.session_state["_last_loaded_hash"] = file_hash
                    st.session_state["_clear_state_file"] = True

                    st.rerun()

                except Exception as e:
                    st.error(f"Fichier invalide : {e}")
