import tomllib
from pathlib import Path
import pandas as pd
from supabase import create_client

raiz = Path(__file__).resolve().parent.parent
with open(raiz / ".streamlit" / "secrets.toml", "rb") as f:
    cfg = tomllib.load(f)["supabase"]

supabase = create_client(cfg["url"], cfg["key"])
salida = raiz / "data"
salida.mkdir(exist_ok=True)

tablas = ["conductores", "vehiculos", "autorizaciones", "reportes_estado"]

for tabla in tablas:
    respuesta = supabase.table(tabla).select("*").execute()
    datos = respuesta.data

    if datos:
        df = pd.DataFrame(datos)
        df.to_csv(salida / f"{tabla}.csv", index=False, encoding="utf-8-sig")
        df.to_excel(salida / f"{tabla}.xlsx", index=False)
        print(f"Tabla {tabla} descargada correctamente.")
    else:
        print(f"La tabla {tabla} está vacía.")
