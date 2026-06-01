from flask import Flask, request, jsonify
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

        return jsonify({
            "error": str(e)
        })

# ==========================================
# ENDPOINT /stats — Dashboard de indicadores
# ==========================================

@app.route('/stats', methods=['GET'])
def stats():
    try:
        df_stats = df.copy()

        probabilidades = modelo.predict_proba(df_stats[features])[:, 1]
        df_stats['PROBABILIDAD'] = probabilidades

        def get_riesgo(row):
            if row['MORA'] >= 720 or row['SCORE_EXTERNO'] <= 3:
                return 'ALTO'
            elif row['MORA'] >= 360 or row['SCORE_EXTERNO'] <= 6:
                return 'MEDIO'
            else:
                return 'BAJO'

        def get_estrategia(row):
            if row['MORA'] < 180:
                return 'SEGUIMIENTO PREVENTIVO'
            if row['PROBABILIDAD'] >= 0.75:
                return 'ACUERDO DE PAGO'
            elif row['PROBABILIDAD'] >= 0.45:
                return 'NEGOCIACION'
            else:
                return 'COBRANZA JURIDICA'

        def get_prioridad(row):
            if row['PROBABILIDAD'] >= 0.70 and row['SALDO'] >= 5000000:
                return 'ALTA'
            elif row['PROBABILIDAD'] >= 0.40:
                return 'MEDIA'
            else:
                return 'BAJA'

        def get_canal(row):
            if row['CONTACTOS'] >= 3:
                return 'LLAMADA'
            elif row['CONTACTOS'] >= 1:
                return 'WHATSAPP'
            else:
                return 'SMS'

        df_stats['NIVEL_RIESGO'] = df_stats.apply(get_riesgo, axis=1)
        df_stats['ESTRATEGIA']   = df_stats.apply(get_estrategia, axis=1)
        df_stats['PRIORIDAD']    = df_stats.apply(get_prioridad, axis=1)
        df_stats['CANAL']        = df_stats.apply(get_canal, axis=1)

        total_clientes       = len(df_stats)
        prob_promedio        = round(float(df_stats['PROBABILIDAD'].mean()), 4)
        saldo_total          = round(float(df_stats['SALDO'].sum()), 2)
        mora_promedio        = round(float(df_stats['MORA'].mean()), 1)
        score_promedio       = round(float(df_stats['SCORE_EXTERNO'].mean()), 2)
        clientes_riesgo_alto = int((df_stats['NIVEL_RIESGO'] == 'ALTO').sum())
        clientes_prioridad_alta = int((df_stats['PRIORIDAD'] == 'ALTA').sum())
        gestiones_efectivas  = int(df_stats['GESTIONES_EFECTIVAS'].sum())
        compromisos_total    = int(df_stats['COMPROMISOS'].sum())
        pagos_total          = int(df_stats['PAGOS'].sum())

        dist_riesgo     = df_stats['NIVEL_RIESGO'].value_counts().to_dict()
        dist_estrategia = df_stats['ESTRATEGIA'].value_counts().to_dict()
        dist_prioridad  = df_stats['PRIORIDAD'].value_counts().to_dict()
        dist_canal      = df_stats['CANAL'].value_counts().to_dict()

        bins = [0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.01]
        labels_hist = ['0-10%','10-20%','20-30%','30-40%','40-50%','50-60%','60-70%','70-80%','80-90%','90-100%']
        hist_counts = []
        for i in range(len(bins)-1):
            count = int(((df_stats['PROBABILIDAD'] >= bins[i]) & (df_stats['PROBABILIDAD'] < bins[i+1])).sum())
            hist_counts.append({'rango': labels_hist[i], 'cantidad': count})

        mora_por_riesgo = df_stats.groupby('NIVEL_RIESGO')['MORA'].mean().round(1).to_dict()

        top_clientes = (
            df_stats[df_stats['PROBABILIDAD'] >= 0.60]
            .sort_values('SALDO', ascending=False)
            .head(10)[['CEDULA','SALDO','MORA','PROBABILIDAD','ESTRATEGIA','CANAL','NIVEL_RIESGO','PRIORIDAD']]
            .copy()
        )
        top_clientes['PROBABILIDAD'] = top_clientes['PROBABILIDAD'].round(2)
        top_clientes['SALDO'] = top_clientes['SALDO'].round(0)
        top_clientes_list = top_clientes.to_dict(orient='records')

        insights = []
        pct_alto  = round((clientes_riesgo_alto / total_clientes) * 100, 1)
        n_acuerdo = dist_estrategia.get('ACUERDO DE PAGO', 0)
        n_sms     = dist_canal.get('SMS', 0)
        canal_dom = max(dist_canal, key=dist_canal.get)

        if pct_alto > 20:
            insights.append({"tipo":"alerta","titulo":"Alta concentración de riesgo","detalle":f"{clientes_riesgo_alto} clientes ({pct_alto}%) tienen riesgo ALTO. Considerar escalamiento jurídico inmediato."})
        if n_acuerdo > total_clientes * 0.3:
            insights.append({"tipo":"oportunidad","titulo":"Gran segmento recuperable","detalle":f"{n_acuerdo} clientes tienen alta probabilidad de pago. Activar campaña de acuerdo de pago esta semana."})
        if n_sms > total_clientes * 0.2:
            insights.append({"tipo":"alerta","titulo":"Baja contactabilidad","detalle":f"{n_sms} clientes solo reciben SMS. Revisar bases de datos de contacto."})
        if mora_promedio > 400:
            insights.append({"tipo":"alerta","titulo":"Mora promedio elevada","detalle":f"La mora promedio de {mora_promedio:.0f} días supera el umbral crítico."})
        if prob_promedio > 0.55:
            insights.append({"tipo":"oportunidad","titulo":"Cartera con buen potencial","detalle":f"Probabilidad promedio de recuperación: {round(prob_promedio*100,1)}%."})
        insights.append({"tipo":"info","titulo":f"Canal dominante: {canal_dom}","detalle":f"{dist_canal[canal_dom]} clientes ({round(dist_canal[canal_dom]/total_clientes*100,1)}%) se gestionan por {canal_dom}."})

        return jsonify({
            "kpis": {
                "total_clientes": total_clientes, "prob_promedio": prob_promedio,
                "saldo_total": saldo_total, "mora_promedio": mora_promedio,
                "score_promedio": score_promedio, "clientes_riesgo_alto": clientes_riesgo_alto,
                "clientes_prioridad_alta": clientes_prioridad_alta,
                "gestiones_efectivas": gestiones_efectivas,
                "compromisos_total": compromisos_total, "pagos_total": pagos_total
            },
            "distribuciones": {
                "riesgo": dist_riesgo, "estrategia": dist_estrategia,
                "prioridad": dist_prioridad, "canal": dist_canal
            },
            "histograma_probabilidad": hist_counts,
            "mora_por_riesgo": mora_por_riesgo,
            "top_clientes": top_clientes_list,
            "insights": insights
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==========================================
# RUN
# ==========================================

if __name__ == '__main__':

    app.run(
        port=5000,
        debug=False
    )