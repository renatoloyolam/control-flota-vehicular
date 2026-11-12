"""Perfil Guardia (móvil): verificar patente + conductor y registrar el acceso."""
import streamlit as st

from src import db, storage
from src.logica import evaluar_acceso, formatear_rut, normalizar_patente

ESTILO = {
    "Autorizado": ("✅ AUTORIZADO", "success"),
    "Denegado": ("⛔ DENEGADO", "error"),
    "Alerta de Estado": ("⚠️ ALERTA DE ESTADO", "warning"),
}


def consultar(patente: str, rut: str) -> tuple[str, str, dict | None]:
    """Consulta cruzada: vehículo + conductor + autorización vigente.

    Son 3 consultas simples a PostgreSQL (vehiculos, conductores,
    autorizaciones con vigente = true). La decisión final se toma en
    `evaluar_acceso`, que cruza los tres resultados a la vez.
    """
    vehiculo = db.get_vehiculo(patente)
    conductor = db.get_conductor(rut)
    autorizado = bool(vehiculo and conductor and db.tiene_autorizacion_vigente(patente, rut))
    resultado, motivo = evaluar_acceso(vehiculo, conductor, autorizado)
    return resultado, motivo, vehiculo


def render() -> None:
    st.header("🛂 Control de acceso vehicular")
    perfil = st.session_state["perfil"]

    with st.form("form_acceso", clear_on_submit=False):
        patente_txt = st.text_input("Patente", placeholder="ABCD-12", max_chars=8)
        rut_txt = st.text_input("RUT del conductor", placeholder="18.234.567-K")
        foto = st.file_uploader("Foto de la patente (opcional)", type=["jpg", "jpeg", "png"])
        enviado = st.form_submit_button("Verificar y registrar", use_container_width=True)

    if not enviado:
        return
    if not patente_txt.strip() or not rut_txt.strip():
        st.error("Ingrese la patente y el RUT del conductor.")
        return

    patente, rut = normalizar_patente(patente_txt), formatear_rut(rut_txt)
    try:
        resultado, motivo, vehiculo = consultar(patente, rut)
        storage.registrar_acceso(patente, rut, resultado, motivo, perfil["nombre"],
                                 foto.getvalue() if foto else None)
    except Exception as e:  # error de red/Supabase: se informa sin romper la app
        st.error(f"No se pudo completar la verificación: {e}")
        return

    titulo, tipo = ESTILO[resultado]
    getattr(st, tipo)(f"## {titulo}\n\n{motivo}")
    if vehiculo:
        c1, c2 = st.columns(2)
        c1.metric("Vehículo", vehiculo["marca_modelo"])
        c2.metric("Estado operativo", vehiculo["estado_operativo"])
    st.caption(f"Patente {patente} · RUT {rut} · acceso registrado.")
