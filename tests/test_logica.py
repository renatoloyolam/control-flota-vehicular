from src.logica import *

def test_normalizar():
    assert normalizar_patente("abcd 12") == "ABCD-12"
    assert normalizar_patente("abcd12") == "ABCD-12"
    assert formatear_rut("18234567k") == "18.234.567-K"
    assert formatear_rut("18.234.567-K") == "18.234.567-K"

def test_acceso():
    v = {"estado_operativo": "Operativo"}; c = {"estado": "Activo"}
    assert evaluar_acceso(v, c, True)[0] == "Autorizado"
    assert evaluar_acceso(None, c, False)[0] == "Denegado"
    assert evaluar_acceso(v, None, False)[0] == "Denegado"
    assert evaluar_acceso(v, {"estado": "Suspendido"}, True)[0] == "Denegado"
    assert evaluar_acceso(v, c, False)[0] == "Denegado"
    assert evaluar_acceso({"estado_operativo": "Requiere Mantención"}, c, True)[0] == "Alerta de Estado"
    assert evaluar_acceso({"estado_operativo": "Crítico"}, c, True)[0] == "Denegado"

def test_reporte():
    e = evaluar_reporte(True, "Normal", True, "ruido")
    assert e["critico"] and TAG_FRENOS in e["observaciones"] and e["presion_ok"]
    e = evaluar_reporte(False, "Presión severamente baja", True)
    assert e["critico"] and not e["presion_ok"]
    e = evaluar_reporte(False, "Baja presión leve", False)
    assert not e["critico"] and TAG_LUCES in e["observaciones"]
    assert nuevo_estado_vehiculo("Operativo", True) == "Requiere Mantención"
    assert nuevo_estado_vehiculo("Crítico", True) == "Crítico"
    assert nuevo_estado_vehiculo("Operativo", False) == "Operativo"
