"""Perfil Administrador (Puesto de Mando): panel BI de la flota."""
import pandas as pd
import streamlit as st

from src import db, storage
from src.logica import (ESTADO_CRITICO, ESTADO_MANTENCION, ESTADO_OPERATIVO,
                        tiene_falla_critica)

COLORES = {ESTADO_OPERATIVO: ("#2e7d32", "white"),
           ESTADO_MANTENCION: ("#f9a825", "black"),
           ESTADO_CRITICO: ("#c62828", "white")}


def _kpis(veh: pd.DataFrame, rep: pd.DataFrame) -> None:
    total = len(veh)
    operativos = int((veh["estado_operativo"] == ESTADO_OPERATIVO).sum())
    inmov = total - operativos
    fallas = int(rep["observaciones"].fillna("").map(tiene_falla_critica).sum()) if len(rep) else 0
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Disponibilidad de la flota", f"{operativos / total * 100:.0f}%" if total else "—")
    c2.metric("Inmovilizadas / en mantención", inmov)
    c3.metric("Vehículos totales", total)
    c4.metric("Alertas por fallas críticas", fallas)


def _matriz(veh: pd.DataFrame) -> None:
    st.subheader("Estado por vehículo")
    cols = st.columns(5)
    for i, v in veh.reset_index(drop=True).iterrows():
        fondo, texto = COLORES.get(v["estado_operativo"], ("#757575", "white"))
        cols[i % 5].markdown(
            f"<div style='background:{fondo};color:{texto};padding:10px;border-radius:10px;"
            f"text-align:center;margin-bottom:8px'><b>{v['patente']}</b><br>"
            f"<small>{v['marca_modelo']}</small><br><small>{v['estado_operativo']}</small></div>",
            unsafe_allow_html=True)


def _analitica(veh: pd.DataFrame, accesos: pd.DataFrame) -> None:
    st.subheader("Uso y consumo")
    c1, c2 = st.columns(2)
    c1.caption("Kilometraje acumulado por vehículo")
    c1.bar_chart(veh.set_index("patente")["kilometraje_actual"])
    c2.caption("Kilometraje promedio por tipo de vehículo")
    c2.bar_chart(veh.groupby("tipo_vehiculo")["kilometraje_actual"].mean())
    if accesos.empty:
        st.info("Aún no hay accesos registrados.")
        return
    c3, c4 = st.columns(2)
    c3.caption("Accesos por patente")
    c3.bar_chart(accesos["patente"].value_counts())
    unido = accesos.merge(veh[["patente", "tipo_vehiculo"]], on="patente", how="left")
    c4.caption("Accesos por tipo de vehículo")
    c4.bar_chart(unido["tipo_vehiculo"].fillna("No registrado").value_counts())


def _feed(accesos: pd.DataFrame) -> None:
    st.subheader("Feed cronológico de accesos")
    if accesos.empty:
        return
    iconos = {"Autorizado": "✅", "Denegado": "⛔", "Alerta de Estado": "⚠️"}
    for _, a in accesos.head(10).iterrows():
        col_t, col_f = st.columns([4, 1])
        col_t.markdown(f"{iconos.get(a['resultado'], '')} **{a['patente']}** · {a['rut_conductor']} · "
                       f"{a['resultado']}  \n{a['fecha_hora']} · {a['motivo']} · guardia: {a['guardia']}")
        if isinstance(a.get("foto_url"), str) and a["foto_url"]:
            col_f.image(a["foto_url"], width=90)


def _auditoria(veh: pd.DataFrame) -> None:
    st.subheader("Auditoría de incidencias")
    patente = st.selectbox("Seleccione una patente", veh["patente"].tolist())
    reportes = db.listar_reportes(patente)
    if not reportes:
        st.info("Sin reportes de conductores para esta patente.")
        return
    for r in reportes:
        critico = tiene_falla_critica(r.get("observaciones"))
        with st.expander(f"{'🔴' if critico else '🟢'} {r['fecha_reporte'][:16]} · {r['kilometraje_salida']:,} km"):
            st.write(f"Combustible: {r['nivel_combustible']}% · Neumáticos: "
                     f"{'OK' if r['presion_neumaticos'] else 'Baja presión'} · "
                     f"Luces: {'OK' if r['luces_operativas'] else 'Falla'}")
            st.write(r.get("observaciones") or "_Sin observaciones_")
            st.caption(f"Conductor: {r['rut_conductor']}")
            if r.get("foto_evidencia_url"):
                st.image(r["foto_evidencia_url"], width=320)


def _cuerpo() -> None:
    veh = pd.DataFrame(db.listar_vehiculos())
    rep = pd.DataFrame(db.listar_reportes())
    if rep.empty:
        rep = pd.DataFrame(columns=["observaciones"])
    accesos = pd.DataFrame(storage.listar_accesos())
    _kpis(veh, rep)
    _matriz(veh)
    _analitica(veh, accesos)
    _feed(accesos)


def render() -> None:
    st.header("📊 Puesto de Mando · Panel BI")
    auto = st.sidebar.toggle("Actualización automática (10 s)", value=True)
    if st.sidebar.button("Actualizar ahora"):
        st.cache_data.clear()
    # st.fragment re-ejecuta solo el panel cada 10 s => sincronización casi en tiempo real
    st.fragment(run_every=10 if auto else None)(_cuerpo)()
    st.divider()
    _auditoria(pd.DataFrame(db.listar_vehiculos()))
