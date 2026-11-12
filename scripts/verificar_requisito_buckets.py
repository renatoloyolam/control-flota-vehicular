"""Comprueba el requisito: buckets en Supabase Storage para evidencias (patentes y odometros)."""
import tomllib
from pathlib import Path

import httpx

ruta = Path(__file__).resolve().parent.parent / ".streamlit" / "secrets.toml"
s = tomllib.loads(ruta.read_text(encoding="utf-8"))["supabase"]
h = {"apikey": s["key"], "Authorization": "Bearer " + s["key"]}
base = s["url"].rstrip("/") + "/storage/v1"

buckets = httpx.get(base + "/bucket", headers=h, timeout=30).json()
print("BUCKETS EXISTENTES")
for b in buckets:
    print(f"- {b['name']}: publico={b.get('public')}, limite={b.get('file_size_limit')} bytes, tipos={b.get('allowed_mime_types')}")

print("\nCONTENIDO (evidencia real subida por la app)")
for b in buckets:
    for carpeta in ("", "accesos"):
        r = httpx.post(f"{base}/object/list/{b['name']}", headers=h,
                       json={"prefix": carpeta, "limit": 100}, timeout=30)
        items = r.json() if r.status_code == 200 else []
        print(f"- {b['name']}/{carpeta}: {len(items)} objetos")
