"""Acceso a datos: todas las consultas a Supabase (PostgreSQL) en un solo módulo."""
import streamlit as st
from supabase import Client, create_client

from src.logica import nuevo_estado_vehiculo


@st.cache_resource
def get_client() -> Client:
    """Cliente único. Las credenciales salen de .streamlit/secrets.toml."""
    cfg = st.secrets["supabase"]
    return create_client(cfg["url"], cfg["key"])


# ---------- lecturas (cache corto para mantener datos casi en tiempo real) ----------
@st.cache_data(ttl=3)
def listar_vehiculos() -> list[dict]:
    return get_client().table("vehiculos").select("*").order("patente").execute().data


@st.cache_data(ttl=30)
def listar_conductores() -> list[dict]:
    return get_client().table("conductores").select("*").order("nombre_completo").execute().data


@st.cache_data(ttl=3)
def listar_reportes(patente: str | None = None, limite: int = 200) -> list[dict]:
    q = get_client().table("reportes_estado").select("*")
    if patente:
        q = q.eq("patente", patente)
    return q.order("fecha_reporte", desc=True).limit(limite).execute().data


def get_vehiculo(patente: str) -> dict | None:
    r = get_client().table("vehiculos").select("*").eq("patente", patente).limit(1).execute()
    return r.data[0] if r.data else None


def get_conductor(rut: str) -> dict | None:
    r = get_client().table("conductores").select("*").eq("rut", rut).limit(1).execute()
    return r.data[0] if r.data else None


def tiene_autorizacion_vigente(patente: str, rut: str) -> bool:
    r = (get_client().table("autorizaciones").select("id")
         .eq("patente", patente).eq("rut_conductor", rut).eq("vigente", True)
         .limit(1).execute())
    return bool(r.data)


def patentes_autorizadas(rut: str) -> list[str]:
    r = (get_client().table("autorizaciones").select("patente")
         .eq("rut_conductor", rut).eq("vigente", True).execute())
    return sorted({f["patente"] for f in r.data})


# ---------- escrituras ----------
def guardar_reporte(reporte: dict, critico: bool) -> str:
    """Inserta el reporte, actualiza km y, si es crítico, el estado del vehículo.

    Devuelve el estado final del vehículo. (Hace en Python lo que un trigger
    haría en la base de datos; ver src/logica.py.)
    """
    sb = get_client()
    sb.table("reportes_estado").insert(reporte).execute()

    veh = get_vehiculo(reporte["patente"])
    estado = nuevo_estado_vehiculo(veh["estado_operativo"], critico)
    cambios = {"kilometraje_actual": max(veh["kilometraje_actual"], reporte["kilometraje_salida"])}
    if estado != veh["estado_operativo"]:
        cambios["estado_operativo"] = estado
    sb.table("vehiculos").update(cambios).eq("patente", reporte["patente"]).execute()
    st.cache_data.clear()
    return estado
