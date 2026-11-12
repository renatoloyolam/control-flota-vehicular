import tomllib
from pathlib import Path
from supabase import create_client

raiz = Path(__file__).resolve().parent.parent
with open(raiz / ".streamlit" / "secrets.toml", "rb") as f:
    cfg = tomllib.load(f)["supabase"]
sb = create_client(cfg["url"], cfg["key"])

for nombre in ["evidencias-vehiculares", "evidencias-garita"]:
    b = sb.storage.get_bucket(nombre)
    print(nombre, "| límite:", getattr(b, "file_size_limit", None),
          "| público:", getattr(b, "public", None))
