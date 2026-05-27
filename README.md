# Proyecto_Final_IA

🤖 Agente IA de Recuperación de Cartera

Sistema inteligente de recuperación de cartera bancaria construido con:

Python
Flask
Machine Learning
Ollama
Mistral
n8n
Random Forest

El proyecto funciona como un asistente interno para el área de recovery y cobranza, permitiendo analizar clientes en mora y recomendar estrategias de recuperación de cartera.

🚀 Objetivo del Proyecto

Desarrollar un agente conversacional de inteligencia artificial capaz de:

Analizar clientes en mora
Estimar probabilidad de recuperación
Recomendar estrategias de cobranza
Priorizar gestión de cartera
Recomendar canales de contacto
Ayudar a asesores y analistas de recovery
🧠 Arquitectura del Sistema
n8n → Flask API → Modelo ML → Ollama/Mistral → Respuesta IA

Flujo:

El usuario consulta un cliente
n8n envía la solicitud
Flask procesa la información
El modelo ML calcula probabilidad
Ollama genera análisis ejecutivo
Se devuelve respuesta al asesor
📁 Estructura del Proyecto
Proyecto_IA/
│
├── app.py
├── train_model.py
├── dataset_limpio.csv
├── modelo_recovery.pkl
├── requirements.txt
└── README.md
⚙️ Instalación
1. Clonar repositorio
git clone https://github.com/tuusuario/proyecto_ia.git
2. Crear entorno virtual
python -m venv .venv
3. Activar entorno virtual
Windows PowerShell
.venv\Scripts\Activate.ps1
4. Instalar dependencias
pip install -r requirements.txt
🦙 Instalación de Ollama

Descargar Ollama:

👉 https://ollama.com

Descargar modelo Mistral
ollama pull mistral
Ejecutar Ollama
ollama serve
🤖 Entrenamiento del Modelo

Ejecutar:

python train_model.py

El modelo entrenará un Random Forest y generará:

modelo_recovery.pkl
▶️ Ejecutar API Flask
python app.py

La API quedará disponible en:

http://127.0.0.1:5000
📡 Endpoint Principal
POST /analizar
Request
{
  "cedula": "1000270337"
}
Response
{
  "cedula": "1000270337",
  "probabilidad": 0.71,
  "nivel_riesgo": "MEDIO",
  "prioridad": "ALTA",
  "canal_recomendado": "WHATSAPP",
  "estrategia": "ACUERDO DE PAGO",
  "saldo": 3500000,
  "mora": 420,
  "score_externo": 6
}
🧮 Variables Utilizadas

El modelo utiliza las siguientes variables:

SALDO
MORA
PAGOS
PROMESAS
CONTACTOS
GESTIONES_EFECTIVAS
COMPROMISOS
SEGMENTO_CLIENTE
CIUDAD
PRODUCTO
SECTOR
TIPO_OBLIGACION
SALDO_EXTERNO
CUOTA
SCORE_EXTERNO
📊 Modelo Machine Learning

Modelo utilizado:

RandomForestClassifier

Funciones del modelo:

Probabilidad de recuperación
Clasificación de riesgo
Priorización de cartera
Recomendación de estrategia
🔥 Integración con n8n

El sistema se integra con n8n mediante:

Webhooks
HTTP Request
Basic LLM Chain
Ollama Chat Model

Esto permite construir flujos conversacionales automáticos para recovery.

🧠 Prompt Engineering

El agente fue diseñado para:

No inventar información
Hablar como analista de recovery
Utilizar lenguaje ejecutivo
Recomendar estrategias de cobranza
Explicar probabilidad de recuperación
Analizar riesgo de mora
📈 Mejoras Futuras
Dashboard de recuperación
Integración con Snowflake
Modelos XGBoost
Predicción de contacto
Aprendizaje continuo
Integración WhatsApp
Motor de priorización avanzada
Visualización de KPIs
👨‍💻 Tecnologías
Python
Flask
Pandas
Scikit-Learn
Joblib
Ollama
Mistral
n8n
📌 Estado del Proyecto

✅ API Flask funcional

✅ Modelo ML entrenado

✅ Integración con n8n

✅ Integración con Ollama

✅ Agente conversacional funcional

✅ Recomendaciones automáticas

✅ Priorización de cartera

👤 Autor

Sebastián

Proyecto académico de Inteligencia Artificial aplicada a Recovery y Cobranza Bancaria.

Ya te dejé el README completo y profesional para tu proyecto 🚀

Incluye:

descripción del proyecto
arquitectura
instalación
Flask
Ollama
n8n
entrenamiento ML
endpoints
variables
mejoras futuras
tecnologías
estructura del proyecto