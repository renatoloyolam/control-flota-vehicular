"""Reglas de negocio puras (sin Streamlit ni Supabase), fáciles de probar.

Decisiones de arquitectura:
- No se pudieron crear tablas/triggers nuevos (el entorno entrega solo la clave
  de API), por lo que la lógica de negocio vive en la capa de aplicación.
- Las fallas críticas del conductor se guardan como etiquetas en `observaciones`
  porque la tabla `reportes_estado` no tiene columnas para frenos/severidad.
"""
import re

ESTADO_OPERATIVO = "Operativo"
ESTADO_MANTENCION = "Requiere Mantención"
ESTADO_CRITICO = "Crítico"

TAG_FRENOS = "[CRÍTICO:FRENOS]"
TAG_NEUMATICOS = "[CRÍTICO:NEUMÁTICOS]"
TAG_LUCES = "[FALLA:LUCES]"

OPCIONES_NEUMATICOS = ["Normal", "Baja presión leve", "Presión severamente baja"]


def normalizar_patente(texto: str) -> str:
    """'abcd 12' / 'abcd12' -> 'ABCD-12' (formato guardado en la BD)."""
    limpio = re.sub(r"[^0-9A-Za-z]", "", texto or "").upper()
    if len(limpio) == 6:
        return f"{limpio[:4]}-{limpio[4:]}"
    return limpio


def formatear_rut(texto: str) -> str:
    """'18234567k' -> '18.234.567-K' (formato guardado en la BD)."""
    limpio = re.sub(r"[^0-9kK]", "", texto or "").upper()
    if len(limpio) < 2 or not limpio[:-1].isdigit():
        return (texto or "").strip().upper()
    cuerpo, dv = limpio[:-1], limpio[-1]
    return f"{int(cuerpo):,}".replace(",", ".") + f"-{dv}"


def evaluar_acceso(vehiculo, conductor, autorizado: bool) -> tuple[str, str]:
    """Resuelve el control de garita: Autorizado / Denegado / Alerta de Estado."""
    if vehiculo is None:
        return "Denegado", "Patente no registrada en el catálogo de vehículos."
    if conductor is None:
        return "Denegado", "RUT no registrado en el catálogo de conductores."
    if conductor.get("estado") != "Activo":
        return "Denegado", f"Conductor con estado '{conductor.get('estado')}'."
    if not autorizado:
        return "Denegado", "El conductor no tiene autorización vigente para este vehículo."
    estado = vehiculo.get("estado_operativo")
    if estado == ESTADO_CRITICO:
        return "Denegado", "Vehículo en estado Crítico: no puede ingresar a operar."
    if estado == ESTADO_MANTENCION:
        return "Alerta de Estado", "Autorizado, pero el vehículo Requiere Mantención."
    return "Autorizado", "Conductor y vehículo con autorización vigente."


def evaluar_reporte(frenos_falla: bool, neumaticos: str, luces_ok: bool,
                    observaciones: str = "") -> dict:
    """Devuelve las observaciones etiquetadas y si hay falla crítica.

    Falla crítica = falla de frenos o presión de neumáticos severamente baja.
    """
    etiquetas = []
    if frenos_falla:
        etiquetas.append(TAG_FRENOS)
    if neumaticos == "Presión severamente baja":
        etiquetas.append(TAG_NEUMATICOS)
    if not luces_ok:
        etiquetas.append(TAG_LUCES)
    texto = " ".join(etiquetas + [(observaciones or "").strip()]).strip()
    return {
        "observaciones": texto,
        "critico": frenos_falla or neumaticos == "Presión severamente baja",
        "presion_ok": neumaticos == "Normal",
    }


def nuevo_estado_vehiculo(estado_actual: str, critico: bool) -> str:
    """Un reporte crítico lleva un vehículo Operativo a 'Requiere Mantención'.

    Nunca mejora un estado: un vehículo 'Crítico' sigue 'Crítico'.
    """
    if critico and estado_actual == ESTADO_OPERATIVO:
        return ESTADO_MANTENCION
    return estado_actual


def tiene_falla_critica(observaciones: str) -> bool:
    obs = observaciones or ""
    return TAG_FRENOS in obs or TAG_NEUMATICOS in obs
