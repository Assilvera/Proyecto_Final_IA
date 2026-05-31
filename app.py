from flask import Flask, request, jsonify, render_template  
import pandas as pd
import joblib
from sklearn.preprocessing import LabelEncoder

# ==========================================
# APP
# ==========================================

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

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

        return jsonify({
            "error": str(e)
        })

# ==========================================
# RUN
# ==========================================

@app.route("/consultar", methods=["POST"])
def consultar():

    try:

        cedula = request.form["cedula"]

        cliente = df[
            df["CEDULA"].astype(str) == cedula
        ]

        if cliente.empty:

            return render_template(
                "index.html",
                resultado={
                    "error": "Cliente no encontrado"
                }
            )

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

        probabilidad = modelo.predict_proba(
            nuevo_cliente
        )[0][1]

        resultado = {

    "cedula": str(cliente["CEDULA"]),

    "probabilidad": f"{round(float(probabilidad)*100,2)}%",

    "nivel_riesgo": calcular_riesgo(
        probabilidad,
        cliente["MORA"],
        cliente["SCORE_EXTERNO"]
    ),

    "prioridad": prioridad(
        probabilidad,
        cliente["SALDO"]
    ),

    "canal_recomendado": canal(
        cliente["CONTACTOS"]
    ),

    "estrategia": estrategia(
        probabilidad,
        cliente["MORA"]
    ),

    "respuesta_ia": f"""
Cliente analizado exitosamente.

• Probabilidad de recuperación: {round(float(probabilidad)*100,2)}%
• Nivel de riesgo: {calcular_riesgo(probabilidad, cliente["MORA"], cliente["SCORE_EXTERNO"])}
• Prioridad: {prioridad(probabilidad, cliente["SALDO"])}
• Canal recomendado: {canal(cliente["CONTACTOS"])}
• Estrategia sugerida: {estrategia(probabilidad, cliente["MORA"])}

La estrategia fue calculada con base en las variables históricas del cliente y el modelo predictivo entrenado.
"""
}

        return render_template(
            "index.html",
            resultado=resultado
        )

    except Exception as e:

        return render_template(
            "index.html",
            resultado={
                "error": str(e)
            }
        )

if __name__ == '__main__':

    app.run(
        port=5000,
        debug=False
    )