"""Control de acceso y estado de flota vehicular - punto de entrada.

Ejecutar:  streamlit run app.py
Navegación condicional: cada perfil (rol) ve solo sus vistas.
"""
import streamlit as st

from src import auth
from src.vistas import admin, conductor, guardia

st.set_page_config(page_title="Control de flota", page_icon="🚙", layout="wide")

VISTAS_POR_ROL = {
    "guardia": {"Control de acceso": guardia.render},
    "conductor": {"Check-in operativo": conductor.render},
    "admin": {"Panel BI": admin.render},
}


def main() -> None:
    perfil = auth.perfil_actual()
    if perfil is None:
        auth.pantalla_login()
        return

    vistas = VISTAS_POR_ROL[perfil["rol"]]
    with st.sidebar:
        st.write(f"👤 **{perfil['nombre']}**  \nPerfil: {perfil['rol']}")
        opcion = st.radio("Menú", list(vistas)) if len(vistas) > 1 else list(vistas)[0]
        if st.button("Cerrar sesión"):
            auth.cerrar_sesion()
    vistas[opcion]()


main()
