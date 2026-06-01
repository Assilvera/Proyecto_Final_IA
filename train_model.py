import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.preprocessing import LabelEncoder
import joblib

# =========================
# CARGAR DATASET
# =========================

df = pd.read_csv("dataset_limpio.csv", low_memory=False)

# =========================
# LIMPIEZA
# =========================

df = df.dropna()

# =========================
# VARIABLES
# =========================

features = [
    'SALDO',
    'MORA',
    'PAGOS',
    'PROMESAS',
    'CONTACTOS',
    'GESTIONES_EFECTIVAS',
    'COMPROMISOS',
    'SEGMENTO_CLIENTE',
    'CIUDAD',
    'PRODUCTO',
    'SECTOR',
    'TIPO_OBLIGACION',
    'SALDO_EXTERNO',
    'CUOTA',
    'SCORE_EXTERNO'
]

target = 'TARGET'

# =========================
# ENCODE VARIABLES TEXTO
# =========================


label_encoders = {}

for col in features:
    # Forzar conversión a texto y aplicar LabelEncoder a todas las columnas
    le = LabelEncoder()
    df[col] = le.fit_transform(df[col].astype(str))
    label_encoders[col] = le

# =========================
# X Y y
# =========================

X = df[features]
y = df[target]

# =========================
# SPLIT
# =========================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

# =========================
# MODELO
# =========================

model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)

model.fit(X_train, y_train)

# =========================
# EVALUACIÓN
# =========================

predictions = model.predict(X_test)

print(classification_report(y_test, predictions))

# =========================
# GUARDAR MODELO
# =========================

joblib.dump(model, "modelo_recovery.pkl")

print("Modelo guardado correctamente")


# =========================
# IMPORTANCIA VARIABLES
# =========================

importancias = pd.DataFrame({
    'Variable': features,
    'Importancia': model.feature_importances_
})

importancias = importancias.sort_values(
    by='Importancia',
    ascending=False
)

print("\nIMPORTANCIA VARIABLES\n")
print(importancias)
