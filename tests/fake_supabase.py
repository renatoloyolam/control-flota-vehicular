"""Cliente Supabase falso en memoria, solo para pruebas."""
import json


class Resp:
    def __init__(self, data, count=None):
        self.data, self.count = data, count


class Query:
    def __init__(self, db, tabla):
        self.db, self.tabla, self.f, self.op, self.payload = db, tabla, [], "select", None
        self.lim, self.ord = None, None

    def select(self, *a, **k): self.op = "select"; return self
    def insert(self, p): self.op, self.payload = "insert", p; return self
    def update(self, p): self.op, self.payload = "update", p; return self
    def eq(self, c, v): self.f.append((c, v)); return self
    def limit(self, n): self.lim = n; return self
    def order(self, c, desc=False): self.ord = (c, desc); return self

    def execute(self):
        filas = self.db.tablas[self.tabla]
        if self.op == "insert":
            nuevo = dict(self.payload, id=len(filas) + 1, fecha_reporte="2026-11-12T09:00:00+00:00")
            filas.append(nuevo); return Resp([nuevo])
        sel = [r for r in filas if all(r.get(c) == v for c, v in self.f)]
        if self.op == "update":
            for r in sel: r.update(self.payload)
            return Resp(sel)
        if self.ord: sel = sorted(sel, key=lambda r: r[self.ord[0]], reverse=self.ord[1])
        return Resp(sel[: self.lim] if self.lim else sel, len(sel))


class Bucket:
    def __init__(self, db, nombre): self.db, self.n = db, nombre
    def upload(self, ruta, datos, opts=None): self.db.archivos[(self.n, ruta)] = datos
    def get_public_url(self, ruta): return f"https://fake/{self.n}/{ruta}"
    def list(self, carpeta, opts=None):
        return [{"name": r.split("/", 1)[1]} for (b, r) in self.db.archivos if b == self.n and r.startswith(carpeta + "/")]
    def download(self, ruta): return self.db.archivos[(self.n, ruta)]


class Storage:
    def __init__(self, db): self.db = db
    def from_(self, n): return Bucket(self.db, n)


class FakeClient:
    def __init__(self):
        self.tablas = {
            "conductores": [
                {"id": 1, "rut": "18.234.567-K", "nombre_completo": "Carlos Soto", "grado_o_cargo": "Capitán", "unidad_destino": "BL1", "estado": "Activo"},
                {"id": 2, "rut": "17.987.654-3", "nombre_completo": "Ale Morales", "grado_o_cargo": "Teniente", "unidad_destino": "TEL", "estado": "Suspendido"}],
            "vehiculos": [
                {"id": 1, "patente": "ABCD-12", "tipo_vehiculo": "Táctico", "marca_modelo": "Piranha", "anio": 2018, "kilometraje_actual": 45200, "estado_operativo": "Operativo"},
                {"id": 2, "patente": "STUV-90", "tipo_vehiculo": "Camioneta", "marca_modelo": "Navara", "anio": 2021, "kilometraje_actual": 54000, "estado_operativo": "Requiere Mantención"},
                {"id": 3, "patente": "DDEE-33", "tipo_vehiculo": "Camión", "marca_modelo": "Freightliner", "anio": 2017, "kilometraje_actual": 76000, "estado_operativo": "Crítico"}],
            "autorizaciones": [
                {"id": 1, "patente": "ABCD-12", "rut_conductor": "18.234.567-K", "vigente": True},
                {"id": 2, "patente": "STUV-90", "rut_conductor": "18.234.567-K", "vigente": True},
                {"id": 3, "patente": "DDEE-33", "rut_conductor": "18.234.567-K", "vigente": True}],
            "reportes_estado": [],
        }
        self.archivos = {}
        self.storage = Storage(self)

    def table(self, t): return Query(self, t)
