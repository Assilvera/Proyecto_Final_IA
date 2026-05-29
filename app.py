from flask import Flask, request, jsonify
import numpy as np
import pandas as pd
import joblib
from sklearn.preprocessing import LabelEncoder

# ==========================================
# APP
# ==========================================

app = Flask(__name__)

# ==========================================
# CARGAR DATASET
# ==========================================

df = pd.read_csv(
    "dataset_limpio.csv",
    dtype={"CEDULA": str},
    low_memory=False
)

df = df.fillna(0)

# ==========================================
# FEATURES EXACTAS DEL MODELO
# ==========================================

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

# ==========================================
# CARGAR MODELO
# ==========================================

modelo = joblib.load("modelo_recovery.pkl")

# ==========================================
# LABEL ENCODERS
# ==========================================

label_encoders = {}

columnas_texto = [
    'SEGMENTO_CLIENTE',
    'CIUDAD',
    'PRODUCTO',
    'SECTOR',
    'TIPO_OBLIGACION'
]

for col in columnas_texto:

    le = LabelEncoder()

    df[col] = le.fit_transform(
        df[col].astype(str)
    )

    label_encoders[col] = le

# ==========================================
# FUNCIONES IA
# ==========================================

def calcular_riesgo(probabilidad, mora, score):

    if mora >= 720 or score <= 3:
        return "ALTO"

    elif mora >= 360 or score <= 6:
        return "MEDIO"

    else:
        return "BAJO"

# ==========================================

def estrategia(probabilidad, mora):

    if mora < 180:
        return "SEGUIMIENTO PREVENTIVO"

    if probabilidad >= 0.75:
        return "ACUERDO DE PAGO"

    elif probabilidad >= 0.45:
        return "NEGOCIACION"

    else:
        return "COBRANZA JURIDICA"

# ==========================================

def prioridad(probabilidad, saldo):

    if probabilidad >= 0.70 and saldo >= 5000000:
        return "ALTA"

    elif probabilidad >= 0.40:
        return "MEDIA"

    else:
        return "BAJA"

# ==========================================

def canal(contactos):

    if contactos >= 3:
        return "LLAMADA"

    elif contactos >= 1:
        return "WHATSAPP"

    else:
        return "SMS"

# ==========================================
# ENDPOINT
# ==========================================

@app.route('/analizar', methods=['POST'])

def analizar():

    try:

        data = request.json

        cedula = str(data["cedula"])

        # ======================================
        # BUSCAR CLIENTE
        # ======================================

        cliente = df[
            df["CEDULA"].astype(str) == cedula
        ]

        if cliente.empty:

            return jsonify({
                "error": "Cliente no encontrado"
            })

        cliente = cliente.iloc[0]

        # ======================================
        # DATAFRAME EXACTO DEL MODELO
        # ======================================

        nuevo_cliente = pd.DataFrame([{

            'SALDO':
            cliente['SALDO'],

            'MORA':
            cliente['MORA'],

            'PAGOS':
            cliente['PAGOS'],

            'PROMESAS':
            cliente['PROMESAS'],

            'CONTACTOS':
            cliente['CONTACTOS'],

            'GESTIONES_EFECTIVAS':
            cliente['GESTIONES_EFECTIVAS'],

            'COMPROMISOS':
            cliente['COMPROMISOS'],

            'SEGMENTO_CLIENTE':
            cliente['SEGMENTO_CLIENTE'],

            'CIUDAD':
            cliente['CIUDAD'],

            'PRODUCTO':
            cliente['PRODUCTO'],

            'SECTOR':
            cliente['SECTOR'],

            'TIPO_OBLIGACION':
            cliente['TIPO_OBLIGACION'],

            'SALDO_EXTERNO':
            cliente['SALDO_EXTERNO'],

            'CUOTA':
            cliente['CUOTA'],

            'SCORE_EXTERNO':
            cliente['SCORE_EXTERNO']

        }])

        # ======================================
        # PREDICCION
        # ======================================

        probabilidad = modelo.predict_proba(
            nuevo_cliente
        )[0][1]

        # ======================================
        # VARIABLES IA
        # ======================================

        riesgo = calcular_riesgo(
            probabilidad,
            cliente["MORA"],
            cliente["SCORE_EXTERNO"]
        )

        estrategia_ia = estrategia(
            probabilidad,
            cliente["MORA"]
        )

        prioridad_ia = prioridad(
            probabilidad,
            cliente["SALDO"]
        )

        canal_ia = canal(
            cliente["CONTACTOS"]
        )

        # ======================================
        # RESPUESTA FINAL
        # ======================================

        respuesta = {

            "cedula":
            str(cliente["CEDULA"]),

            "probabilidad":
            round(float(probabilidad), 2),

            "nivel_riesgo":
            riesgo,

            "prioridad_gestion":
            prioridad_ia,

            "canal_recomendado":
            canal_ia,

            "estrategia":
            estrategia_ia,

            "mora":
            int(cliente["MORA"]),

            "saldo":
            float(cliente["SALDO"]),

            "score_externo":
            float(cliente["SCORE_EXTERNO"]),

            "pagos":
            int(cliente["PAGOS"]),

            "contactos":
            int(cliente["CONTACTOS"]),

            "gestiones_efectivas":
            int(cliente["GESTIONES_EFECTIVAS"]),

            "compromisos":
            int(cliente["COMPROMISOS"])

        }

        return jsonify(respuesta)

    except Exception as e:
        return jsonify({"error": str(e)})


def _normalize(value, maximum):
    try:
        maximum = float(maximum)
        return float(value) / maximum if maximum > 0 else 0.0
    except Exception:
        return 0.0


def calcular_probabilidad_contacto(cliente_row, df):

    # Obtener valores del cliente
    contactos = float(cliente_row.get('CONTACTOS', 0))
    gestiones = float(cliente_row.get('GESTIONES_EFECTIVAS', 0))
    pagos = float(cliente_row.get('PAGOS', 0))
    mora = float(cliente_row.get('MORA', 0))
    score = float(cliente_row.get('SCORE_EXTERNO', 0))

    # Máximos del dataset 
    max_contactos = df['CONTACTOS'].max() if 'CONTACTOS' in df else 1
    max_gestiones = df['GESTIONES_EFECTIVAS'].max() if 'GESTIONES_EFECTIVAS' in df else 1
    max_pagos = df['PAGOS'].max() if 'PAGOS' in df else 1
    max_mora = df['MORA'].max() if 'MORA' in df else 1
    max_score = df['SCORE_EXTERNO'].max() if 'SCORE_EXTERNO' in df else 1

    # Normalizar los valores
    n_contactos = _normalize(contactos, max_contactos)
    n_gestiones = _normalize(gestiones, max_gestiones)
    n_pagos = _normalize(pagos, max_pagos)
    n_mora = _normalize(mora, max_mora)
    n_score = _normalize(score, max_score)

    # Heuristica combinada (se pueden ajustar los pesos según la importancia relativa la cual no se)
    score_contacto = (
        0.25 * n_contactos +
        0.25 * n_gestiones +
        0.20 * n_pagos +
        0.15 * (1 - n_mora) +
        0.15 * (1 - n_score)
    )

    score_contacto = max(0.0, min(1.0, score_contacto))

    return round(float(score_contacto), 2)


@app.route('/probabilidad_contacto', methods=['POST'])
def probabilidad_contacto():
    try:
        data = request.json
        cedula = str(data["cedula"])

        cliente = df[ df["CEDULA"].astype(str) == cedula ]

        if cliente.empty:
            return jsonify({"error": "Cliente no encontrado"})

        cliente = cliente.iloc[0]

        nuevo_cliente = pd.DataFrame([{
            'SALDO': cliente['SALDO'],
            'MORA': cliente['MORA'],
            'PAGOS': cliente['PAGOS'],
            'PROMESAS': cliente['PROMESAS'],
            'CONTACTOS': cliente['CONTACTOS'],
            'GESTIONES_EFECTIVAS': cliente['GESTIONES_EFECTIVAS'],
            'COMPROMISOS': cliente['COMPROMISOS'],
            'SEGMENTO_CLIENTE': cliente['SEGMENTO_CLIENTE'],
            'CIUDAD': cliente['CIUDAD'],
            'PRODUCTO': cliente['PRODUCTO'],
            'SECTOR': cliente['SECTOR'],
            'TIPO_OBLIGACION': cliente['TIPO_OBLIGACION'],
            'SALDO_EXTERNO': cliente['SALDO_EXTERNO'],
            'CUOTA': cliente['CUOTA'],
            'SCORE_EXTERNO': cliente['SCORE_EXTERNO']
        }])

        probabilidad = modelo.predict_proba(nuevo_cliente)[0][1]

        # Calcular probabilidad de contacto 
        prob_contacto = calcular_probabilidad_contacto(cliente, df)

        # Recomendación de asignación basada en probabilidades y riesgo
        asignacion = "EXTERNA"
        razon = "Reglas heurísticas básicas"

        if probabilidad >= 0.75 and prob_contacto >= 0.5:
            asignacion = "INTERNA"
            razon = "Alta probabilidad de recuperación y contacto viable"
        elif probabilidad < 0.40 and prob_contacto < 0.30:
            asignacion = "JURIDICA"
            razon = "Baja probabilidad y bajo contacto: derivar a jurídica"
        elif 0.40 <= probabilidad < 0.75 and prob_contacto >= 0.40:
            asignacion = "CAMPAÑA"
            razon = "Probabilidad media y contactabilidad aceptable: incluir en campaña"
        else:
            asignacion = "EXTERNA"
            razon = "Condiciones mixtas - asignación a externo recomendada"

        riesgo = calcular_riesgo(probabilidad, cliente["MORA"], cliente["SCORE_EXTERNO"])
        estrategia_ia = estrategia(probabilidad, cliente["MORA"])
        prioridad_ia = prioridad(probabilidad, cliente["SALDO"])
        canal_ia = canal(cliente["CONTACTOS"])

        respuesta = {
            "cedula": str(cliente["CEDULA"]),
            "probabilidad": round(float(probabilidad), 2),
            "nivel_riesgo": riesgo,
            "prioridad_gestion": prioridad_ia,
            "canal_recomendado": canal_ia,
            "estrategia": estrategia_ia,
            "mora": int(cliente["MORA"]),
            "saldo": float(cliente["SALDO"]),
            "score_externo": float(cliente["SCORE_EXTERNO"]),
            "pagos": int(cliente["PAGOS"]),
            "contactos": int(cliente["CONTACTOS"]),
            "gestiones_efectivas": int(cliente["GESTIONES_EFECTIVAS"]),
            "compromisos": int(cliente["COMPROMISOS"]),
            # Campos nuevos
            "probabilidad_contacto": prob_contacto,
            "recomendacion_asignacion": asignacion,
            "asignacion_razon": razon
        }

        return jsonify(respuesta)

    except Exception as e:
        return jsonify({"error": str(e)})

# ==========================================
# RUN
# ==========================================

if __name__ == '__main__':

    app.run(
        port=5000,
        debug=False
    )