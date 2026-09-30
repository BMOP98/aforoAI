"""Entrena el predictor de ocupación +30 min usando el histórico SQLite de AforoAI."""
from pathlib import Path
import json, pickle, sqlite3
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "backend" / "aforoai.db"
MODEL_PATH = Path(__file__).resolve().parent / "models" / "occupancy_model.pkl"
METRICS_PATH = Path(__file__).resolve().parent / "models" / "metrics.json"
FEATURES = ["hora_decimal", "dia_semana", "personas", "ocupacion_porcentaje", "lag_1", "lag_2", "promedio_3"]


def load_data():
    if not DB_PATH.exists():
        raise SystemExit("No existe backend/aforoai.db. Ejecuta primero el backend y el simulador.")
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query("SELECT * FROM mediciones ORDER BY timestamp", conn)
    if len(df) < 30:
        raise SystemExit("Se necesitan al menos 30 mediciones para entrenar.")
    return df


def build_dataset(df):
    df = df.copy()
    df["timestamp"] = pd.to_datetime( df["timestamp"], format="mixed", utc=True )
    # Entrenamos principalmente con la serie simulada regular; si no existe, usamos todo el histórico.
    sim = df[df["origen"] == "SIMULADO"].copy()
    if len(sim) >= 30:
        df = sim
    df = df.sort_values("timestamp").reset_index(drop=True)
    df["hora_decimal"] = df["timestamp"].dt.hour + df["timestamp"].dt.minute / 60
    df["dia_semana"] = df["timestamp"].dt.dayofweek
    df["lag_1"] = df["personas"].shift(1)
    df["lag_2"] = df["personas"].shift(2)
    df["promedio_3"] = df["personas"].rolling(3).mean()
    # El simulador genera intervalos de 30 minutos: el siguiente registro es el objetivo +30 min.
    df["target_30m"] = df["personas"].shift(-1)
    return df.dropna(subset=FEATURES + ["target_30m"]).copy()


def main():
    data = build_dataset(load_data())
    split = max(int(len(data) * 0.8), 1)
    train, test = data.iloc[:split], data.iloc[split:]
    if test.empty:
        raise SystemExit("No hay suficientes datos para separar entrenamiento y prueba.")
    model = RandomForestRegressor(n_estimators=160, max_depth=10, min_samples_leaf=2, random_state=42, n_jobs=-1)
    model.fit(train[FEATURES], train["target_30m"])
    pred = model.predict(test[FEATURES])
    metrics = {
        "modelo": "RandomForestRegressor",
        "objetivo": "personas dentro de 30 minutos",
        "muestras": int(len(data)),
        "entrenamiento": int(len(train)),
        "prueba": int(len(test)),
        "mae": round(float(mean_absolute_error(test["target_30m"], pred)), 3),
        "rmse": round(float(np.sqrt(mean_squared_error(test["target_30m"], pred))), 3),
        "r2": round(float(r2_score(test["target_30m"], pred)), 3),
        "features": FEATURES,
    }
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with MODEL_PATH.open("wb") as f:
        pickle.dump({"model": model, "features": FEATURES}, f)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Modelo entrenado correctamente")
    print(json.dumps(metrics, indent=2, ensure_ascii=False))
    print(f"Modelo: {MODEL_PATH}")

if __name__ == "__main__":
    main()
