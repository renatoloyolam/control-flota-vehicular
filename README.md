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
scripts/                utilidades (explorar esquema de la BD)
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
