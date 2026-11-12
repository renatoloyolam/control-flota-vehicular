"""Perfil Conductor: check-in operativo con reporte de novedades y fotos."""
import streamlit as st

from src import db, storage
from src.logica import OPCIONES_NEUMATICOS, evaluar_reporte


def render() -> None:
    st.header("🧰 Check-in operativo del vehículo")
    conductores = db.listar_conductores()
    etiquetas = {f"{c['nombre_completo']} · {c['rut']}": c["rut"] for c in conductores}
    elegido = st.selectbox("Conductor", list(etiquetas))
    rut = etiquetas[elegido]

    patentes = db.patentes_autorizadas(rut)
    if not patentes:
        st.warning("Este conductor no tiene vehículos con autorización vigente.")
        return

    with st.form("form_reporte", clear_on_submit=True):
        patente = st.selectbox("Vehículo", patentes)
        km = st.number_input("Kilometraje actual", min_value=0, step=1)
        combustible = st.slider("Nivel de combustible (%)", 0, 100, 50)
        neumaticos = st.radio("Estado de neumáticos", OPCIONES_NEUMATICOS)
        luces_ok = st.checkbox("Luces operativas", value=True)
        frenos_falla = st.checkbox("⚠️ Falla en sistema de frenos")
        obs = st.text_area("Novedades mecánicas")
        foto = st.file_uploader("Foto del odómetro o novedad", type=["jpg", "jpeg", "png"])
        enviar = st.form_submit_button("Enviar reporte", use_container_width=True)

    if not enviar:
        return
    veh = db.get_vehiculo(patente)
    if km < veh["kilometraje_actual"]:
        st.error(f"El kilometraje no puede ser menor al registrado ({veh['kilometraje_actual']:,} km).")
        return

    ev = evaluar_reporte(frenos_falla, neumaticos, luces_ok, obs)
    try:
        url = None
        if foto:
            ruta = f"{patente}/{storage.ahora().strftime('%Y%m%d_%H%M%S')}.jpg"
            url = storage.subir_foto(storage.BUCKET_VEHICULOS, ruta, foto.getvalue())
        estado = db.guardar_reporte({
            "patente": patente, "rut_conductor": rut, "kilometraje_salida": int(km),
            "nivel_combustible": combustible, "presion_neumaticos": ev["presion_ok"],
            "luces_operativas": luces_ok, "observaciones": ev["observaciones"],
            "foto_evidencia_url": url,
        }, ev["critico"])
    except Exception as e:
        st.error(f"No se pudo guardar el reporte: {e}")
        return

    st.success("Reporte enviado correctamente.")
    if ev["critico"]:
        st.error(f"Falla crítica detectada: el vehículo {patente} quedó en estado **{estado}**.")
