from flask import Flask, request, jsonify, Response, render_template
import pandas as pd
import joblib
import requests
import json
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
    df[col] = le.fit_transform(df[col].astype(str))
    label_encoders[col] = le

# ==========================================
# FUNCION RESPUESTA JSON LIMPIA
# ==========================================

def responder(datos):
    return Response(
        json.dumps(datos, ensure_ascii=False),
        content_type='application/json; charset=utf-8'
    )

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
# CONFIGURACION OLLAMA
# ==========================================

OLLAMA_URL   = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "mistral"

# ==========================================
# FUNCIONES OLLAMA
# ==========================================

def llamar_ollama(mensajes):
    payload = {
        "model":    OLLAMA_MODEL,
        "messages": mensajes,
        "stream":   False
    }
    resp = requests.post(OLLAMA_URL, json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()["message"]["content"]

# ==========================================

def extraer_cedula_con_ia(texto_usuario):
    mensajes = [
        {
            "role": "system",
            "content": (
                "Eres un extractor de datos. Tu única tarea es identificar si el usuario "
                "menciona un número de cédula o identificación en su mensaje. "
                "Si encuentras un número que parece una cédula (entre 6 y 12 dígitos), "
                "responde ÚNICAMENTE con ese número, sin texto adicional. "
                "Si NO hay cédula en el mensaje, responde exactamente: SIN_CEDULA"
            )
        },
        {
            "role": "user",
            "content": texto_usuario
        }
    ]
    resultado = llamar_ollama(mensajes).strip()
    if resultado.isdigit():
        return resultado
    return None

# ==========================================

def limpiar_texto(texto):
    return texto.replace('\n\n', ' ').replace('\n', ' ').strip()

# ==========================================

def generar_respuesta_ejecutiva(datos_cliente, pregunta_usuario):
    contexto = f"""
    Cédula: {datos_cliente['cedula']}
    Probabilidad de recuperación: {datos_cliente['probabilidad'] * 100:.0f}%
    Nivel de riesgo: {datos_cliente['nivel_riesgo']}
    Días en mora: {datos_cliente['mora']}
    Saldo: ${datos_cliente['saldo']:,.0f}
    Score externo: {datos_cliente['score_externo']}
    Estrategia recomendada: {datos_cliente['estrategia']}
    Prioridad de gestión: {datos_cliente['prioridad_gestion']}
    Canal recomendado: {datos_cliente['canal_recomendado']}
    Pagos realizados: {datos_cliente['pagos']}
    Contactos previos: {datos_cliente['contactos']}
    Gestiones efectivas: {datos_cliente['gestiones_efectivas']}
    Compromisos: {datos_cliente['compromisos']}
    """

    mensajes = [
        {
            "role": "system",
            "content": (
                "Eres un analista experto en recuperación de cartera bancaria. "
                "Hablas de forma ejecutiva, clara y profesional. "
                "Recibes datos de un cliente en mora y respondes la consulta del asesor. "
                "Nunca inventas información. Solo usas los datos que te proporcionan. "
                "Tus respuestas son concisas pero completas. Máximo 5 párrafos cortos. "
                "Siempre terminas con una recomendación de acción concreta."
            )
        },
        {
            "role": "user",
            "content": f"Datos del cliente:\n{contexto}\n\nPregunta del asesor: {pregunta_usuario}"
        }
    ]

    respuesta = llamar_ollama(mensajes)
    return limpiar_texto(respuesta)


# ==========================================
# ENDPOINT PRINCIPAL
# ==========================================

@app.route('/')
def index():
    return render_template('index.html')
# ==========================================
# ENDPOINT ANALIZAR (original)
# ==========================================

@app.route('/analizar', methods=['POST'])
def analizar():

    try:

        data   = request.json
        cedula = str(data["cedula"])

        cliente = df[df["CEDULA"].astype(str) == cedula]

        if cliente.empty:
            return responder({"error": "Cliente no encontrado"})

        cliente = cliente.iloc[0]

        nuevo_cliente = pd.DataFrame([{
            'SALDO':               cliente['SALDO'],
            'MORA':                cliente['MORA'],
            'PAGOS':               cliente['PAGOS'],
            'PROMESAS':            cliente['PROMESAS'],
            'CONTACTOS':           cliente['CONTACTOS'],
            'GESTIONES_EFECTIVAS': cliente['GESTIONES_EFECTIVAS'],
            'COMPROMISOS':         cliente['COMPROMISOS'],
            'SEGMENTO_CLIENTE':    cliente['SEGMENTO_CLIENTE'],
            'CIUDAD':              cliente['CIUDAD'],
            'PRODUCTO':            cliente['PRODUCTO'],
            'SECTOR':              cliente['SECTOR'],
            'TIPO_OBLIGACION':     cliente['TIPO_OBLIGACION'],
            'SALDO_EXTERNO':       cliente['SALDO_EXTERNO'],
            'CUOTA':               cliente['CUOTA'],
            'SCORE_EXTERNO':       cliente['SCORE_EXTERNO']
        }])

        probabilidad = modelo.predict_proba(nuevo_cliente)[0][1]

        riesgo        = calcular_riesgo(probabilidad, cliente["MORA"], cliente["SCORE_EXTERNO"])
        estrategia_ia = estrategia(probabilidad, cliente["MORA"])
        prioridad_ia  = prioridad(probabilidad, cliente["SALDO"])
        canal_ia      = canal(cliente["CONTACTOS"])

        resultado = {
            "cedula":              str(cliente["CEDULA"]),
            "probabilidad":        round(float(probabilidad), 2),
            "nivel_riesgo":        riesgo,
            "prioridad_gestion":   prioridad_ia,
            "canal_recomendado":   canal_ia,
            "estrategia":          estrategia_ia,
            "mora":                int(cliente["MORA"]),
            "saldo":               float(cliente["SALDO"]),
            "score_externo":       float(cliente["SCORE_EXTERNO"]),
            "pagos":               int(cliente["PAGOS"]),
            "contactos":           int(cliente["CONTACTOS"]),
            "gestiones_efectivas": int(cliente["GESTIONES_EFECTIVAS"]),
            "compromisos":         int(cliente["COMPROMISOS"])
        }

        return responder(resultado)

    except Exception as e:
        return responder({"error": str(e)})

# ==========================================
# ENDPOINT CHAT (lenguaje natural)
# ==========================================

@app.route('/chat', methods=['POST'])
def chat():

    try:

        data            = request.json
        mensaje_usuario = str(data.get("mensaje", "")).strip()

        if not mensaje_usuario:
            return responder({"error": "El campo 'mensaje' es requerido"})

        # ======================================
        # PASO 1: EXTRAER CEDULA
        # ======================================

        cedula = extraer_cedula_con_ia(mensaje_usuario)

        if not cedula:

            mensajes = [
                {
                    "role": "system",
                    "content": (
                        "Eres un asistente experto en recuperación de cartera bancaria. "
                        "Si el usuario no menciona una cédula, oriéntalo para que la proporcione "
                        "o responde consultas generales sobre cobranza y recuperación. "
                        "Sé profesional y conciso."
                    )
                },
                {
                    "role": "user",
                    "content": mensaje_usuario
                }
            ]

            respuesta_general = llamar_ollama(mensajes)
            respuesta_general = limpiar_texto(respuesta_general)

            return responder({
                "tipo":      "general",
                "respuesta": respuesta_general
            })

        # ======================================
        # PASO 2: BUSCAR CLIENTE
        # ======================================

        cliente_df = df[df["CEDULA"].astype(str) == cedula]

        if cliente_df.empty:
            return responder({
                "tipo":      "error",
                "respuesta": f"No encontré ningún cliente con la cédula {cedula} en la base de datos."
            })

        cliente = cliente_df.iloc[0]

        # ======================================
        # PASO 3: PREDICCION
        # ======================================

        nuevo_cliente = pd.DataFrame([{
            'SALDO':               cliente['SALDO'],
            'MORA':                cliente['MORA'],
            'PAGOS':               cliente['PAGOS'],
            'PROMESAS':            cliente['PROMESAS'],
            'CONTACTOS':           cliente['CONTACTOS'],
            'GESTIONES_EFECTIVAS': cliente['GESTIONES_EFECTIVAS'],
            'COMPROMISOS':         cliente['COMPROMISOS'],
            'SEGMENTO_CLIENTE':    cliente['SEGMENTO_CLIENTE'],
            'CIUDAD':              cliente['CIUDAD'],
            'PRODUCTO':            cliente['PRODUCTO'],
            'SECTOR':              cliente['SECTOR'],
            'TIPO_OBLIGACION':     cliente['TIPO_OBLIGACION'],
            'SALDO_EXTERNO':       cliente['SALDO_EXTERNO'],
            'CUOTA':               cliente['CUOTA'],
            'SCORE_EXTERNO':       cliente['SCORE_EXTERNO']
        }])

        probabilidad = modelo.predict_proba(nuevo_cliente)[0][1]

        # ======================================
        # PASO 4: ARMAR DATOS CLIENTE
        # ======================================

        datos_cliente = {
            "cedula":              str(cliente["CEDULA"]),
            "probabilidad":        round(float(probabilidad), 2),
            "nivel_riesgo":        calcular_riesgo(probabilidad, cliente["MORA"], cliente["SCORE_EXTERNO"]),
            "prioridad_gestion":   prioridad(probabilidad, cliente["SALDO"]),
            "canal_recomendado":   canal(cliente["CONTACTOS"]),
            "estrategia":          estrategia(probabilidad, cliente["MORA"]),
            "mora":                int(cliente["MORA"]),
            "saldo":               float(cliente["SALDO"]),
            "score_externo":       float(cliente["SCORE_EXTERNO"]),
            "pagos":               int(cliente["PAGOS"]),
            "contactos":           int(cliente["CONTACTOS"]),
            "gestiones_efectivas": int(cliente["GESTIONES_EFECTIVAS"]),
            "compromisos":         int(cliente["COMPROMISOS"])
        }

        # ======================================
        # PASO 5: RESPUESTA CONVERSACIONAL
        # ======================================

        respuesta_ia = generar_respuesta_ejecutiva(datos_cliente, mensaje_usuario)

        return responder({
            "tipo":      "analisis",
            "cedula":    cedula,
            "datos":     datos_cliente,
            "respuesta": respuesta_ia
        })

    except Exception as e:
        return responder({"error": str(e)})

# ==========================================
# ENDPOINT DASHBOARD
# ==========================================

@app.route('/dashboard-data', methods=['GET'])
def dashboard_data():

    try:

        df_dash = pd.read_csv(
            "dataset_limpio.csv",
            dtype={"CEDULA": str},
            low_memory=False
        ).fillna(0)

        df_encoded = df_dash.copy()

        for col in columnas_texto:
            le = label_encoders[col]
            df_encoded[col] = df_encoded[col].astype(str).apply(
                lambda x: le.transform([x])[0] if x in le.classes_ else 0
            )

        X              = df_encoded[features]
        probabilidades = modelo.predict_proba(X)[:, 1]
        df_dash['PROBABILIDAD'] = probabilidades

        df_dash['NIVEL_RIESGO'] = df_dash.apply(
            lambda r: calcular_riesgo(r['PROBABILIDAD'], r['MORA'], r['SCORE_EXTERNO']), axis=1
        )
        df_dash['ESTRATEGIA'] = df_dash.apply(
            lambda r: estrategia(r['PROBABILIDAD'], r['MORA']), axis=1
        )
        df_dash['PRIORIDAD'] = df_dash.apply(
            lambda r: prioridad(r['PROBABILIDAD'], r['SALDO']), axis=1
        )
        df_dash['CANAL'] = df_dash['CONTACTOS'].apply(canal)

        # KPIs
        total_clientes = len(df_dash)
        saldo_total    = float(df_dash['SALDO'].sum())
        prob_promedio  = float(df_dash['PROBABILIDAD'].mean())
        mora_promedio  = float(df_dash['MORA'].mean())

        # Distribuciones
        por_riesgo     = df_dash['NIVEL_RIESGO'].value_counts().to_dict()
        por_estrategia = df_dash['ESTRATEGIA'].value_counts().to_dict()
        por_prioridad  = df_dash['PRIORIDAD'].value_counts().to_dict()
        por_canal      = df_dash['CANAL'].value_counts().to_dict()

        # Saldo por riesgo
        saldo_por_riesgo = df_dash.groupby('NIVEL_RIESGO')['SALDO'].sum().to_dict()
        saldo_por_riesgo = {k: float(v) for k, v in saldo_por_riesgo.items()}

        # Top 10 clientes por saldo
        top_clientes = (
            df_dash[['CEDULA', 'SALDO', 'MORA', 'PROBABILIDAD', 'NIVEL_RIESGO', 'ESTRATEGIA']]
            .sort_values('SALDO', ascending=False)
            .head(10)
        )
        top_clientes = top_clientes.copy()
        top_clientes['PROBABILIDAD'] = top_clientes['PROBABILIDAD'].round(2)
        top_clientes['SALDO']        = top_clientes['SALDO'].round(0)
        top_lista = top_clientes.to_dict(orient='records')

        resultado = {
            "kpis": {
                "total_clientes": total_clientes,
                "saldo_total":    saldo_total,
                "prob_promedio":  round(prob_promedio * 100, 1),
                "mora_promedio":  round(mora_promedio, 0)
            },
            "por_riesgo":        por_riesgo,
            "por_estrategia":    por_estrategia,
            "por_prioridad":     por_prioridad,
            "por_canal":         por_canal,
            "saldo_por_riesgo":  saldo_por_riesgo,
            "top_clientes":      top_lista
        }

        return responder(resultado)

    except Exception as e:
        return responder({"error": str(e)})

# ==========================================
# RUN
# ==========================================

if __name__ == '__main__':
    app.run(
        port=5000,
        debug=False
    )