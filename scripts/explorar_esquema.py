import tomllib
from pathlib import Path
import httpx
from supabase import create_client

raiz = Path(__file__).resolve().parent.parent
with open(raiz / ".streamlit" / "secrets.toml", "rb") as f:
    cfg = tomllib.load(f)["supabase"]
url, key = cfg["url"].rstrip("/"), cfg["key"]
sb = create_client(url, key)

print("=== TABLAS Y COLUMNAS ===")
try:
    r = httpx.get(f"{url}/rest/v1/",
                  headers={"apikey": key, "Authorization": f"Bearer {key}"},
                  timeout=20)
    r.raise_for_status()
    tablas = r.json().get("definitions", {})
    for nombre, d in tablas.items():
        cols = list(d.get("properties", {}).keys())
        try:
            n = sb.table(nombre).select("*", count="exact").limit(1).execute().count
        except Exception:
            n = "?"
        print(f"\n{nombre}  ({n} filas)\n   columnas: {cols}")
except Exception as e:
    print("No se pudo leer el esquema:", e)

print("\n=== BUCKETS ===")
try:
    for b in sb.storage.list_buckets():
        print("-", b.name, "| público:", b.public)
except Exception as e:
    print("Error al listar buckets:", e)