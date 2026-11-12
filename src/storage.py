"""Supabase Storage: fotos (máx. 800 KB) y bitácora de accesos de la garita.

Como no se puede crear una tabla de accesos, cada acceso se guarda como un
archivo JSON (+ foto opcional) dentro del bucket `evidencias-garita`.
"""
import io
import json
from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st
from PIL import Image, ImageOps

from src.db import get_client

BUCKET_VEHICULOS = "evidencias-vehiculares"
BUCKET_GARITA = "evidencias-garita"
CARPETA_ACCESOS = "accesos"
MAX_BYTES = 800 * 1024
TZ = ZoneInfo("America/Santiago")


def ahora() -> datetime:
    return datetime.now(TZ)


def comprimir_imagen(datos: bytes, max_bytes: int = MAX_BYTES) -> bytes:
    """Convierte a JPEG y reduce calidad/tamaño hasta quedar bajo 800 KB."""
    img = ImageOps.exif_transpose(Image.open(io.BytesIO(datos))).convert("RGB")
    img.thumbnail((1600, 1600))
    for _ in range(6):
        for calidad in (85, 70, 55, 40):
            buf = io.BytesIO()
            img.save(buf, "JPEG", quality=calidad, optimize=True)
            if buf.tell() <= max_bytes:
                return buf.getvalue()
        img = img.resize((int(img.width * 0.8), int(img.height * 0.8)))
    return buf.getvalue()


def subir_foto(bucket: str, ruta: str, datos: bytes) -> str:
    """Comprime, sube y devuelve la URL pública de la foto."""
    jpg = comprimir_imagen(datos)
    st_bucket = get_client().storage.from_(bucket)
    st_bucket.upload(ruta, jpg, {"content-type": "image/jpeg", "upsert": "true"})
    return st_bucket.get_public_url(ruta)


def registrar_acceso(patente: str, rut: str, resultado: str, motivo: str,
                     guardia: str, foto: bytes | None = None) -> dict:
    """Guarda un evento de acceso (JSON + foto de la patente) en el bucket de garita."""
    ts = ahora()
    base = f"{CARPETA_ACCESOS}/{ts.strftime('%Y%m%d_%H%M%S_%f')}_{patente}"
    foto_url = subir_foto(BUCKET_GARITA, base + ".jpg", foto) if foto else None
    evento = {
        "fecha_hora": ts.isoformat(timespec="seconds"),
        "patente": patente, "rut_conductor": rut, "resultado": resultado,
        "motivo": motivo, "guardia": guardia, "foto_url": foto_url,
    }
    get_client().storage.from_(BUCKET_GARITA).upload(
        base + ".json", json.dumps(evento, ensure_ascii=False).encode("utf-8"),
        {"content-type": "application/json", "upsert": "true"})
    st.cache_data.clear()
    return evento


@st.cache_data(ttl=3)
def listar_accesos(limite: int = 100) -> list[dict]:
    """Lee los últimos eventos de acceso (más recientes primero)."""
    bucket = get_client().storage.from_(BUCKET_GARITA)
    archivos = bucket.list(CARPETA_ACCESOS, {"limit": 1000,
                           "sortBy": {"column": "name", "order": "desc"}})
    nombres = sorted((a["name"] for a in archivos if a["name"].endswith(".json")),
                     reverse=True)[:limite]
    eventos = []
    for n in nombres:
        try:
            eventos.append(json.loads(bucket.download(f"{CARPETA_ACCESOS}/{n}")))
        except Exception:
            continue  # archivo ilegible: se omite, no rompe el dashboard
    return eventos
