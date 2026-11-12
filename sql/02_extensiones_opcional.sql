-- OPCIONAL (requiere acceso al SQL Editor). La app funciona SIN esto:
-- sin acceso, los accesos se guardan como JSON en el bucket evidencias-garita
-- y la regla de mantención se aplica desde Python (src/db.py).
ALTER TABLE reportes_estado ADD COLUMN IF NOT EXISTS frenos_ok BOOLEAN NOT NULL DEFAULT TRUE;

CREATE TABLE IF NOT EXISTS registros_acceso (
    id SERIAL PRIMARY KEY,
    patente VARCHAR(10) NOT NULL REFERENCES vehiculos(patente),
    rut_conductor VARCHAR(12) REFERENCES conductores(rut),
    fecha_hora TIMESTAMPTZ DEFAULT NOW(),
    resultado VARCHAR(20) NOT NULL CHECK (resultado IN ('Autorizado','Denegado','Alerta de Estado')),
    guardia VARCHAR(100),
    foto_patente_url TEXT
);
