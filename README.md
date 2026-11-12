# Control de acceso y estado de flota vehicular

Aplicación Streamlit + Supabase (PostgreSQL y Storage) con tres perfiles:
**Guardia** (control de acceso), **Conductor** (check-in operativo) y **Administrador** (panel BI).

## Estructura
```
app.py                  punto de entrada, login y navegación por perfil
src/logica.py           reglas de negocio (acceso, falla crítica, estados)
src/db.py               consultas a Supabase
src/storage.py          fotos (<= 800 KB) y bitácora de accesos
src/auth.py             sesión y perfiles (st.session_state)
src/vistas/             guardia.py, conductor.py, admin.py
sql/                    scripts SQL (base del curso + extensiones opcionales)
scripts/                utilidades (explorar esquema, verificar buckets, exportar tablas)
docs/                   informe técnico (Word)
tests/                  pruebas con Supabase simulado
.streamlit/secrets.toml.example   plantilla de credenciales
```

## Ejecución local (VS Code)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .streamlit\secrets.toml.example .streamlit\secrets.toml   # y complete sus claves
streamlit run app.py
```
`secrets.toml` está en `.gitignore`: **las claves nunca se suben al repositorio.**

## Pruebas
```powershell
pip install pytest
python -m pytest -q tests
```

## Decisiones de arquitectura
- El entorno entrega solo la clave de API (sin acceso al SQL Editor), por lo que no se crean tablas ni triggers nuevos.
- **Accesos de garita:** se guardan como JSON + foto en el bucket `evidencias-garita`. Si se dispone de SQL Editor, `sql/02_extensiones_opcional.sql` crea la tabla `registros_acceso`.
- **Falla crítica** (frenos o neumáticos severamente bajos): `src/db.py` actualiza `vehiculos.estado_operativo` a *Requiere Mantención*; la falla queda etiquetada en `observaciones`.
- Las fotos se comprimen a JPEG < 800 KB antes de subir a `evidencias-vehiculares`.

## Almacenamiento (Supabase Storage)
| Bucket | Uso | Límite |
|---|---|---|
| `evidencias-vehiculares` | foto de odómetro y novedades del conductor | 800 KB |
| `evidencias-garita` | foto de patente y bitácora de accesos (JSON) | la app comprime a ≤ 800 KB |

Comprobación: `python scripts\verificar_requisito_buckets.py`.

## Seguridad
- La clave de Supabase vive en `.streamlit/secrets.toml` (excluido por `.gitignore`); el repositorio solo contiene `secrets.toml.example`.
- Cada perfil ingresa con usuario y contraseña y accede solo a su pantalla.
- Limitación: las políticas RLS de Storage no se configuraron (requieren el panel de Supabase, al que no se tuvo acceso); el control de acceso se aplica en la aplicación.

## Informe técnico
Ver `docs/Informe_tecnico_flota_vehicular.docx` (arquitectura, diagrama de flujo de datos y capturas de validación).
