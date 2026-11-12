"""Autenticación y perfiles con st.session_state.

Los usuarios y claves de los tres perfiles viven en .streamlit/secrets.toml
(sección [perfiles.*]); nunca en el código ni en el repositorio.
"""
import hmac

import streamlit as st


def intentar_login(usuario: str, clave: str) -> dict | None:
    """Compara contra los perfiles definidos en secrets. Devuelve el perfil o None."""
    for rol, p in st.secrets["perfiles"].items():
        ok_u = hmac.compare_digest(str(p["usuario"]), usuario.strip())
        ok_c = hmac.compare_digest(str(p["clave"]), clave)
        if ok_u and ok_c:
            return {"rol": rol, "nombre": p.get("nombre", usuario)}
    return None


def pantalla_login() -> None:
    st.title("🚙 Control de flota vehicular")
    st.caption("Ingrese con su perfil: Guardia, Conductor o Administrador.")
    with st.form("login"):
        usuario = st.text_input("Usuario")
        clave = st.text_input("Contraseña", type="password")
        if st.form_submit_button("Ingresar", use_container_width=True):
            perfil = intentar_login(usuario, clave)
            if perfil:
                st.session_state["perfil"] = perfil
                st.rerun()
            st.error("Usuario o contraseña incorrectos.")


def perfil_actual() -> dict | None:
    return st.session_state.get("perfil")


def cerrar_sesion() -> None:
    st.session_state.clear()
    st.rerun()
