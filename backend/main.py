from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.telegram_notifier import procesar_alerta, telegram_configurado

DB_PATH = Path(__file__).resolve().parent / "aforoai.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS mediciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                fecha TEXT NOT NULL,
                hora TEXT NOT NULL,
                personas INTEGER NOT NULL,
                capacidad INTEGER NOT NULL,
                ocupacion_porcentaje REAL NOT NULL,
                estado TEXT NOT NULL,
                origen TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_mediciones_timestamp ON mediciones(timestamp)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="AforoAI API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "null"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MedicionIn(BaseModel):
    device_id: str = Field(min_length=1, max_length=80)
    timestamp: datetime
    personas: int = Field(ge=0)
    capacidad: int = Field(gt=0)
    origen: Literal["REAL", "SIMULADO"] = "REAL"


def estado_para(porcentaje: float) -> str:
    if porcentaje <= 40:
        return "BAJO"
    if porcentaje <= 70:
        return "NORMAL"
    if porcentaje <= 100:
        return "ALTO"
    return "AFORO_SUPERADO"


def row_to_dict(row):
    return dict(row) if row else None


@app.get("/api/health")
def health():
    return {"status": "ok", "database": "sqlite", "telegram_configurado": telegram_configurado()}


@app.post("/api/mediciones", status_code=201)
def crear_medicion(data: MedicionIn):
    ts = data.timestamp
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    ts = ts.astimezone(timezone.utc)
    porcentaje = round((data.personas / data.capacidad) * 100, 2)
    estado = estado_para(porcentaje)
    values = (
        data.device_id, ts.isoformat(), ts.date().isoformat(), ts.strftime("%H:%M:%S"),
        data.personas, data.capacidad, porcentaje, estado, data.origen,
    )
    with get_connection() as conn:
        cur = conn.execute("""
            INSERT INTO mediciones
            (device_id,timestamp,fecha,hora,personas,capacidad,ocupacion_porcentaje,estado,origen)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, values)
        row = conn.execute("SELECT * FROM mediciones WHERE id=?", (cur.lastrowid,)).fetchone()
        result = row_to_dict(row)
        try:
            alerta = procesar_alerta(conn, result)
        except Exception as exc:
            # Una falla de Telegram nunca debe impedir guardar la medición.
            print(f"[WARN] No se pudo enviar alerta Telegram: {exc}")
            alerta = None
    result["alerta_telegram"] = alerta
    return result


@app.get("/api/mediciones")
def listar_mediciones(limit: int = Query(100, ge=1, le=2000)):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM mediciones ORDER BY timestamp DESC, id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [row_to_dict(r) for r in reversed(rows)]


@app.get("/api/estado-actual")
def estado_actual():
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM mediciones ORDER BY timestamp DESC, id DESC LIMIT 1").fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Aun no existen mediciones")
    return row_to_dict(row)


@app.get("/api/estadisticas")
def estadisticas():
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) n FROM mediciones").fetchone()["n"]
        if not total:
            return {"total_mediciones": 0, "promedio_personas": 0, "max_personas": 0, "aforo_superado": 0, "por_hora": []}
        summary = conn.execute("""
            SELECT ROUND(AVG(personas),2) promedio_personas,
                   MAX(personas) max_personas,
                   SUM(CASE WHEN estado='AFORO_SUPERADO' THEN 1 ELSE 0 END) aforo_superado
            FROM mediciones
        """).fetchone()
        hours = conn.execute("""
            SELECT substr(hora,1,2) hora, ROUND(AVG(personas),2) promedio_personas
            FROM mediciones GROUP BY substr(hora,1,2) ORDER BY hora
        """).fetchall()
    return {
        "total_mediciones": total,
        "promedio_personas": summary["promedio_personas"],
        "max_personas": summary["max_personas"],
        "aforo_superado": summary["aforo_superado"],
        "por_hora": [dict(r) for r in hours],
    }

@app.get("/api/prediccion")
def prediccion():
    """Predice personas dentro de 30 minutos usando el modelo entrenado localmente."""
    import pickle
    model_path = Path(__file__).resolve().parents[1] / "ml" / "models" / "occupancy_model.pkl"
    metrics_path = Path(__file__).resolve().parents[1] / "ml" / "models" / "metrics.json"
    if not model_path.exists():
        raise HTTPException(status_code=503, detail="Modelo no entrenado. Ejecuta: python ml/train.py")
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM mediciones ORDER BY timestamp DESC, id DESC LIMIT 3").fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail="No existen mediciones")
    latest = dict(rows[0])
    chronological = [dict(r) for r in reversed(rows)]
    vals = [r["personas"] for r in chronological]
    while len(vals) < 3:
        vals.insert(0, vals[0])
    ts = datetime.fromisoformat(latest["timestamp"].replace("Z", "+00:00"))
    features = {
        "hora_decimal": ts.hour + ts.minute / 60,
        "dia_semana": ts.weekday(),
        "personas": latest["personas"],
        "ocupacion_porcentaje": latest["ocupacion_porcentaje"],
        "lag_1": vals[-2],
        "lag_2": vals[-3],
        "promedio_3": sum(vals[-3:]) / 3,
    }
    with model_path.open("rb") as f:
        bundle = pickle.load(f)
    X = [[features[name] for name in bundle["features"]]]
    predicted = max(0, int(round(float(bundle["model"].predict(X)[0]))))
    pct = round(predicted / latest["capacidad"] * 100, 2)
    result = {
        "personas_actuales": latest["personas"],
        "capacidad": latest["capacidad"],
        "horizonte_minutos": 30,
        "personas_estimadas": predicted,
        "ocupacion_estimada_porcentaje": pct,
        "estado_estimado": estado_para(pct),
        "modelo": "RandomForestRegressor",
    }
    if metrics_path.exists():
        import json
        result["metricas"] = json.loads(metrics_path.read_text(encoding="utf-8"))
    return result
