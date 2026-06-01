from flask import Flask, request, jsonify, send_from_directory
from flask import Flask, request, jsonify, render_template  
import pandas as pd
import joblib
from sklearn.preprocessing import LabelEncoder
from datetime import datetime

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

def generar_respuesta_ia(probabilidad, cliente, riesgo, prioridad_ia, canal_ia, estrategia_ia):

    prob_pct = round(float(probabilidad) * 100, 2)

    return f"""Cliente analizado exitosamente.

• Probabilidad de recuperación: {prob_pct}%
• Nivel de riesgo: {riesgo}
• Prioridad: {prioridad_ia}
• Canal recomendado: {canal_ia}
• Estrategia sugerida: {estrategia_ia}

La estrategia fue calculada con base en las variables históricas del cliente y el modelo predictivo entrenado."""

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

            "respuesta_ia":
            generar_respuesta_ia(
                probabilidad,
                cliente,
                riesgo,
                prioridad_ia,
                canal_ia,
                estrategia_ia
            ),

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
# FUNCIONES INSIGHTS OPERATIVOS
# ==========================================

def _calcular_tasa_efectividad(df_filtrado):
    """Tasa de gestiones efectivas sobre total de contactos."""
    total_contactos = df_filtrado['CONTACTOS'].sum()
    total_gestiones = df_filtrado['GESTIONES_EFECTIVAS'].sum()
    if total_contactos == 0:
        return 0.0
    return round(float(total_gestiones / total_contactos), 4)


def _calcular_tasa_cumplimiento_promesas(df_filtrado):
    """Ratio de compromisos cumplidos sobre promesas hechas."""
    total_promesas = df_filtrado['PROMESAS'].sum()
    total_compromisos = df_filtrado['COMPROMISOS'].sum()
    if total_promesas == 0:
        return 0.0
    return round(float(total_compromisos / total_promesas), 4)


def _distribucion_por_campo(df_filtrado, campo):
    """Distribución porcentual de un campo categórico."""
    if campo not in df_filtrado.columns or len(df_filtrado) == 0:
        return {}
    conteo = df_filtrado[campo].value_counts(normalize=True)
    return {str(k): round(float(v), 4) for k, v in conteo.items()}


def _segmentar_mora(mora_dias):
    """Clasifica días de mora en tramos operativos."""
    if mora_dias <= 30:
        return "0-30 dias"
    elif mora_dias <= 90:
        return "31-90 dias"
    elif mora_dias <= 180:
        return "91-180 dias"
    elif mora_dias <= 360:
        return "181-360 dias"
    else:
        return "mas de 360 dias"


def _alertas_operativas(df_filtrado, probabilidades_lista):
    """
    Genera alertas basadas en umbrales críticos del portafolio.
    Retorna lista de alertas con nivel (CRITICA, ADVERTENCIA, INFO).
    """
    alertas = []
    total = len(df_filtrado)
    if total == 0:
        return alertas

    # Alerta: clientes en mora extrema sin ningún contacto
    mora_extrema_sin_contacto = df_filtrado[
        (df_filtrado['MORA'] >= 720) & (df_filtrado['CONTACTOS'] == 0)
    ]
    if len(mora_extrema_sin_contacto) > 0:
        alertas.append({
            "nivel": "CRITICA",
            "codigo": "MORA_720_SIN_CONTACTO",
            "descripcion": "Clientes con mora >= 720 dias sin ningun contacto registrado",
            "cantidad_afectados": int(len(mora_extrema_sin_contacto)),
            "porcentaje_portafolio": round(len(mora_extrema_sin_contacto) / total, 4),
            "accion_sugerida": "Derivar inmediatamente a cobranza juridica o castigar cartera"
        })

    # Alerta: alta concentración de saldo en pocos clientes
    saldo_total = df_filtrado['SALDO'].sum()
    top_10_saldo = df_filtrado.nlargest(max(1, int(total * 0.10)), 'SALDO')['SALDO'].sum()
    concentracion_top10 = top_10_saldo / saldo_total if saldo_total > 0 else 0
    if concentracion_top10 >= 0.60:
        alertas.append({
            "nivel": "ADVERTENCIA",
            "codigo": "CONCENTRACION_SALDO",
            "descripcion": "El 10% de clientes concentra el 60% o mas del saldo total",
            "porcentaje_concentracion": round(float(concentracion_top10), 4),
            "accion_sugerida": "Priorizar gestion personalizada sobre esos clientes de alto impacto"
        })

    # Alerta: baja tasa de efectividad de gestión
    tasa_ef = _calcular_tasa_efectividad(df_filtrado)
    if tasa_ef < 0.20:
        alertas.append({
            "nivel": "ADVERTENCIA",
            "codigo": "BAJA_EFECTIVIDAD_GESTION",
            "descripcion": "Menos del 20% de los contactos resultan en gestiones efectivas",
            "tasa_efectividad": tasa_ef,
            "accion_sugerida": "Revisar guiones de negociacion y canales utilizados"
        })

    # Alerta: clientes con promesas sin compromisos
    promesas_sin_compromiso = df_filtrado[
        (df_filtrado['PROMESAS'] > 0) & (df_filtrado['COMPROMISOS'] == 0)
    ]
    if len(promesas_sin_compromiso) > 0:
        pct = len(promesas_sin_compromiso) / total
        nivel = "ADVERTENCIA" if pct >= 0.15 else "INFO"
        alertas.append({
            "nivel": nivel,
            "codigo": "PROMESAS_SIN_COMPROMISO",
            "descripcion": "Clientes con promesas registradas pero sin compromisos formalizados",
            "cantidad_afectados": int(len(promesas_sin_compromiso)),
            "porcentaje_portafolio": round(pct, 4),
            "accion_sugerida": "Hacer seguimiento y formalizar acuerdos de pago pendientes"
        })

    # Alerta: clientes recuperables desatendidos (alta probabilidad, cero contactos)
    if probabilidades_lista:
        prob_series = pd.Series(probabilidades_lista, index=df_filtrado.index[:len(probabilidades_lista)])
        recuperables_sin_contacto = df_filtrado.loc[
            prob_series[prob_series >= 0.70].index
        ]
        recuperables_sin_contacto = recuperables_sin_contacto[
            recuperables_sin_contacto['CONTACTOS'] == 0
        ]
        if len(recuperables_sin_contacto) > 0:
            alertas.append({
                "nivel": "CRITICA",
                "codigo": "RECUPERABLES_SIN_GESTION",
                "descripcion": "Clientes con alta probabilidad de pago (>=70%) sin ningun contacto realizado",
                "cantidad_afectados": int(len(recuperables_sin_contacto)),
                "accion_sugerida": "Asignar de inmediato a gestores internos o campana activa"
            })

    return alertas


def _recomendaciones_portafolio(metricas, alertas):
    """
    Genera recomendaciones estratégicas accionables basadas en métricas y alertas.
    """
    recomendaciones = []

    tasa_ef = metricas.get("tasa_efectividad_gestion", 0)
    tasa_cumplimiento = metricas.get("tasa_cumplimiento_promesas", 0)
    pct_riesgo_alto = metricas.get("distribucion_riesgo", {}).get("ALTO", 0)
    pct_juridica = metricas.get("distribucion_estrategia", {}).get("COBRANZA JURIDICA", 0)

    if tasa_ef < 0.30:
        recomendaciones.append({
            "area": "OPERACIONES",
            "recomendacion": "Aumentar capacitacion en tecnicas de negociacion",
            "impacto_esperado": "Mejorar tasa de contacto efectivo al menos 10 puntos porcentuales",
            "urgencia": "ALTA"
        })

    if tasa_cumplimiento < 0.50:
        recomendaciones.append({
            "area": "SEGUIMIENTO",
            "recomendacion": "Implementar sistema de recordatorios automaticos de compromisos",
            "impacto_esperado": "Reducir incumplimiento de promesas y mejorar flujo de recuperacion",
            "urgencia": "MEDIA"
        })

    if pct_riesgo_alto >= 0.40:
        recomendaciones.append({
            "area": "RIESGO",
            "recomendacion": "Escalar el 40% de cartera de riesgo alto a gestores especializados",
            "impacto_esperado": "Contener deterioro adicional y activar recuperacion temprana",
            "urgencia": "ALTA"
        })

    if pct_juridica >= 0.30:
        recomendaciones.append({
            "area": "LEGAL",
            "recomendacion": "Revisar estrategia juridica: alto volumen puede saturar el canal",
            "impacto_esperado": "Priorizar casos con mayor saldo para maximizar recuperacion juridica",
            "urgencia": "MEDIA"
        })

    codigos_alertas = [a["codigo"] for a in alertas]
    if "MORA_720_SIN_CONTACTO" in codigos_alertas:
        recomendaciones.append({
            "area": "CASTIGO_CARTERA",
            "recomendacion": "Evaluar castigo contable de cartera con mora >= 720 dias sin gestion",
            "impacto_esperado": "Liberar provisiones y depurar portafolio activo",
            "urgencia": "ALTA"
        })

    return recomendaciones


# ==========================================
# ENDPOINT INSIGHTS OPERATIVOS
# ==========================================

@app.route('/insights', methods=['POST'])
def insights_operativos():
    """
    Endpoint de insights operativos del portafolio.

    Body JSON (todos opcionales):
    {
        "cedula":        str   — análisis de un cliente específico
        "ciudad":        str   — filtrar por ciudad
        "sector":        str   — filtrar por sector
        "producto":      str   — filtrar por producto
        "tipo_obligacion": str — filtrar por tipo de obligación
        "mora_min":      int   — filtro mínimo de días mora
        "mora_max":      int   — filtro máximo de días mora
        "top_n":         int   — top N clientes prioritarios a retornar (default 10)
    }

    Si se envía "cedula", devuelve insights del cliente + su posición relativa.
    Sin filtros, analiza todo el portafolio.
    """
    try:
        data = request.json or {}

        df_trabajo = df.copy()
        filtros_aplicados = {}

        # ---- Filtros opcionales ----
        cedula = str(data.get("cedula", "")).strip()
        ciudad = str(data.get("ciudad", "")).strip()
        sector = str(data.get("sector", "")).strip()
        producto = str(data.get("producto", "")).strip()
        tipo_obl = str(data.get("tipo_obligacion", "")).strip()
        mora_min = data.get("mora_min", None)
        mora_max = data.get("mora_max", None)
        top_n = int(data.get("top_n", 10))

        if ciudad:
            df_trabajo = df_trabajo[df_trabajo["CIUDAD"].astype(str) == ciudad]
            filtros_aplicados["ciudad"] = ciudad
        if sector:
            df_trabajo = df_trabajo[df_trabajo["SECTOR"].astype(str) == sector]
            filtros_aplicados["sector"] = sector
        if producto:
            df_trabajo = df_trabajo[df_trabajo["PRODUCTO"].astype(str) == producto]
            filtros_aplicados["producto"] = producto
        if tipo_obl:
            df_trabajo = df_trabajo[df_trabajo["TIPO_OBLIGACION"].astype(str) == tipo_obl]
            filtros_aplicados["tipo_obligacion"] = tipo_obl
        if mora_min is not None:
            df_trabajo = df_trabajo[df_trabajo["MORA"] >= int(mora_min)]
            filtros_aplicados["mora_min"] = mora_min
        if mora_max is not None:
            df_trabajo = df_trabajo[df_trabajo["MORA"] <= int(mora_max)]
            filtros_aplicados["mora_max"] = mora_max

        if df_trabajo.empty:
            return jsonify({
                "error": "No se encontraron clientes con los filtros indicados",
                "filtros_aplicados": filtros_aplicados
            })

        total_clientes = len(df_trabajo)

        # ---- Métricas base del portafolio ----
        saldo_total = float(df_trabajo["SALDO"].sum())
        saldo_promedio = float(df_trabajo["SALDO"].mean())
        mora_promedio = float(df_trabajo["MORA"].mean())
        score_promedio = float(df_trabajo["SCORE_EXTERNO"].mean())

        tasa_ef = _calcular_tasa_efectividad(df_trabajo)
        tasa_cumplimiento = _calcular_tasa_cumplimiento_promesas(df_trabajo)

        # Distribución de mora por tramos
        df_trabajo["TRAMO_MORA"] = df_trabajo["MORA"].apply(_segmentar_mora)
        dist_mora = _distribucion_por_campo(df_trabajo, "TRAMO_MORA")

        # Clientes sin ningún contacto
        sin_contacto = int((df_trabajo["CONTACTOS"] == 0).sum())
        pct_sin_contacto = round(sin_contacto / total_clientes, 4)

        # Clientes con al menos un pago
        con_pagos = int((df_trabajo["PAGOS"] > 0).sum())
        pct_con_pagos = round(con_pagos / total_clientes, 4)

        # ---- Riesgo y estrategia con el modelo ----
        riesgos = []
        estrategias = []
        prioridades = []
        canales = []
        probabilidades = []

        for _, row in df_trabajo.iterrows():
            try:
                nuevo = pd.DataFrame([{col: row[col] for col in features}])
                prob = float(modelo.predict_proba(nuevo)[0][1])
            except Exception:
                prob = 0.0

            probabilidades.append(prob)
            riesgos.append(calcular_riesgo(prob, row["MORA"], row["SCORE_EXTERNO"]))
            estrategias.append(estrategia(prob, row["MORA"]))
            prioridades.append(prioridad(prob, row["SALDO"]))
            canales.append(canal(row["CONTACTOS"]))

        prob_promedio = round(float(np.mean(probabilidades)), 4)
        prob_mediana = round(float(np.median(probabilidades)), 4)

        # Distribuciones
        dist_riesgo = {
            r: round(riesgos.count(r) / total_clientes, 4)
            for r in ["ALTO", "MEDIO", "BAJO"]
        }
        dist_estrategia = {}
        for e in estrategias:
            dist_estrategia[e] = dist_estrategia.get(e, 0) + 1
        dist_estrategia = {k: round(v / total_clientes, 4) for k, v in dist_estrategia.items()}

        dist_prioridad = {
            p: round(prioridades.count(p) / total_clientes, 4)
            for p in ["ALTA", "MEDIA", "BAJA"]
        }
        dist_canal = {}
        for c in canales:
            dist_canal[c] = dist_canal.get(c, 0) + 1
        dist_canal = {k: round(v / total_clientes, 4) for k, v in dist_canal.items()}

        metricas = {
            "total_clientes": total_clientes,
            "saldo_total_portafolio": round(saldo_total, 2),
            "saldo_promedio_cliente": round(saldo_promedio, 2),
            "mora_promedio_dias": round(mora_promedio, 1),
            "score_externo_promedio": round(score_promedio, 2),
            "probabilidad_recuperacion_promedio": prob_promedio,
            "probabilidad_recuperacion_mediana": prob_mediana,
            "tasa_efectividad_gestion": tasa_ef,
            "tasa_cumplimiento_promesas": tasa_cumplimiento,
            "clientes_sin_contacto": sin_contacto,
            "pct_sin_contacto": pct_sin_contacto,
            "clientes_con_pagos": con_pagos,
            "pct_con_pagos": pct_con_pagos,
            "distribucion_tramos_mora": dist_mora,
            "distribucion_riesgo": dist_riesgo,
            "distribucion_estrategia": dist_estrategia,
            "distribucion_prioridad": dist_prioridad,
            "distribucion_canal_recomendado": dist_canal
        }

        # ---- Alertas ----
        alertas = _alertas_operativas(df_trabajo, probabilidades)

        # ---- Recomendaciones ----
        recomendaciones = _recomendaciones_portafolio(metricas, alertas)

        # ---- Top N clientes prioritarios ----
        df_trabajo = df_trabajo.copy()
        df_trabajo["_prob"] = probabilidades
        df_top = df_trabajo.sort_values(
            by=["_prob", "SALDO"], ascending=False
        ).head(top_n)

        top_clientes = []
        for _, row in df_top.iterrows():
            prob = float(row["_prob"])
            top_clientes.append({
                "cedula": str(row["CEDULA"]),
                "saldo": round(float(row["SALDO"]), 2),
                "mora_dias": int(row["MORA"]),
                "probabilidad_recuperacion": round(prob, 4),
                "nivel_riesgo": calcular_riesgo(prob, row["MORA"], row["SCORE_EXTERNO"]),
                "estrategia": estrategia(prob, row["MORA"]),
                "prioridad": prioridad(prob, row["SALDO"]),
                "canal_recomendado": canal(row["CONTACTOS"])
            })

        # ---- Insights de cliente específico (si se envió cédula) ----
        insight_cliente = None
        if cedula:
            cliente_row = df_trabajo[df_trabajo["CEDULA"].astype(str) == cedula]
            if not cliente_row.empty:
                idx = cliente_row.index[0]
                pos_idx = list(df_trabajo.index).index(idx)
                prob_cliente = probabilidades[pos_idx] if pos_idx < len(probabilidades) else 0.0
                cr = cliente_row.iloc[0]

                # Posición relativa en el portafolio filtrado
                rank_prob = sorted(probabilidades, reverse=True)
                percentil = round(
                    (rank_prob.index(prob_cliente) / total_clientes) * 100, 1
                ) if prob_cliente in rank_prob else None

                insight_cliente = {
                    "cedula": cedula,
                    "probabilidad_recuperacion": round(prob_cliente, 4),
                    "percentil_en_portafolio": percentil,
                    "nivel_riesgo": calcular_riesgo(prob_cliente, cr["MORA"], cr["SCORE_EXTERNO"]),
                    "estrategia": estrategia(prob_cliente, cr["MORA"]),
                    "prioridad": prioridad(prob_cliente, cr["SALDO"]),
                    "canal_recomendado": canal(cr["CONTACTOS"]),
                    "tramo_mora": _segmentar_mora(cr["MORA"]),
                    "esta_en_top_n": cedula in [c["cedula"] for c in top_clientes]
                }
            else:
                insight_cliente = {"error": "Cedula no encontrada en el portafolio filtrado"}

        # ---- Respuesta final ----
        respuesta = {
            "generado_en": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "filtros_aplicados": filtros_aplicados,
            "metricas_portafolio": metricas,
            "alertas_operativas": alertas,
            "recomendaciones_estrategicas": recomendaciones,
            f"top_{top_n}_clientes_prioritarios": top_clientes
        }

        if insight_cliente:
            respuesta["insight_cliente_consultado"] = insight_cliente

        return jsonify(respuesta)

    except Exception as e:
        return jsonify({"error": str(e)})


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

@app.route('/dashboard')
def dashboard():
    return send_from_directory('.', 'dashboard.html')
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

        riesgo = calcular_riesgo(
            probabilidad,
            cliente["MORA"],
            cliente["SCORE_EXTERNO"]
        )

        prioridad_ia = prioridad(
            probabilidad,
            cliente["SALDO"]
        )

        canal_ia = canal(cliente["CONTACTOS"])

        estrategia_ia = estrategia(
            probabilidad,
            cliente["MORA"]
        )

        resultado = {

            "cedula": str(cliente["CEDULA"]),

            "probabilidad": f"{round(float(probabilidad)*100,2)}%",

            "nivel_riesgo": riesgo,

            "prioridad": prioridad_ia,

            "canal_recomendado": canal_ia,

            "estrategia": estrategia_ia,

            "respuesta_ia": generar_respuesta_ia(
                probabilidad,
                cliente,
                riesgo,
                prioridad_ia,
                canal_ia,
                estrategia_ia
            )
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