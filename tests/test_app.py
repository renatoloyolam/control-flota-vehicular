"""Prueba de la interfaz completa con AppTest y Supabase simulado."""
import io
from PIL import Image
from streamlit.testing.v1 import AppTest
from tests.fake_supabase import FakeClient
import src.db, src.storage

fake = FakeClient()
src.db.get_client = lambda: fake
src.storage.get_client = lambda: fake
SECRETS = {"supabase": {"url": "x", "key": "y"},
           "perfiles": {"guardia": {"usuario": "g", "clave": "1", "nombre": "G"},
                        "conductor": {"usuario": "c", "clave": "2", "nombre": "C"},
                        "admin": {"usuario": "a", "clave": "3", "nombre": "A"}}}

def nuevo():
    at = AppTest.from_file(str(__import__("pathlib").Path(__file__).resolve().parent.parent / "app.py"), default_timeout=30)
    at.secrets.update(SECRETS)
    return at.run()

def login(at, u, c):
    at.text_input[0].set_value(u); at.text_input[1].set_value(c)
    at.button[0].click(); return at.run()

def test_login_malo():
    at = login(nuevo(), "g", "mala")
    assert at.error and not at.exception

def test_guardia():
    at = login(nuevo(), "g", "1")
    assert not at.exception, at.exception
    for pat, rut, esperado in [("abcd12", "18234567k", "AUTORIZADO"), ("stuv90", "18234567k", "ALERTA"),
                               ("ddee33", "18234567k", "DENEGADO"), ("zzzz99", "18234567k", "DENEGADO"),
                               ("abcd12", "17987654-3", "DENEGADO")]:
        at.text_input[0].set_value(pat); at.text_input[1].set_value(rut)
        at.button[0].click(); at.run()
        assert not at.exception, at.exception
        txt = " ".join(e.value for e in list(at.success) + list(at.error) + list(at.warning))
        assert esperado in txt, (pat, esperado, txt)
    assert len([k for k in fake.archivos if k[1].endswith(".json")]) == 5

def test_conductor_critico():
    at = login(nuevo(), "c", "2")
    assert not at.exception, at.exception
    at.selectbox[0].select("Carlos Soto · 18.234.567-K")
    at.run()
    at.selectbox[1].select("ABCD-12")
    at.number_input[0].set_value(46000)
    at.checkbox[1].check()  # falla de frenos
    at.button[0].click(); at.run()
    assert not at.exception, at.exception
    assert fake.tablas["vehiculos"][0]["estado_operativo"] == "Requiere Mantención"
    assert fake.tablas["vehiculos"][0]["kilometraje_actual"] == 46000
    assert "[CRÍTICO:FRENOS]" in fake.tablas["reportes_estado"][-1]["observaciones"]

def test_conductor_km_menor():
    at = login(nuevo(), "c", "2")
    at.selectbox[0].select("Carlos Soto · 18.234.567-K"); at.run()
    at.selectbox[1].select("STUV-90"); at.number_input[0].set_value(10)
    at.button[0].click(); at.run()
    assert at.error

def test_admin():
    at = login(nuevo(), "a", "3")
    assert not at.exception, at.exception
    assert len(at.metric) == 4
    assert fake.tablas["vehiculos"][0]["patente"] == "ABCD-12"

def test_compresion():
    from src.storage import comprimir_imagen, MAX_BYTES
    import os
    img = Image.frombytes("RGB", (3000, 3000), os.urandom(3000 * 3000 * 3))
    b = io.BytesIO(); img.save(b, "PNG")
    assert len(comprimir_imagen(b.getvalue())) <= MAX_BYTES
