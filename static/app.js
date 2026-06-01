(function () {
    "use strict";

    const app = document.getElementById("app");
    const header = document.getElementById("header");
    const messagesEl = document.getElementById("messages");
    const form = document.getElementById("queryForm");
    const input = document.getElementById("cedulaInput");
    const submitBtn = document.getElementById("submitBtn");

    let isAnalyzing = false;

    function activateChatMode() {
        if (!app.classList.contains("chat-mode")) {
            app.classList.remove("welcome-mode");
            app.classList.add("chat-mode");
            wrapHeaderForChat();
        }
    }

    function wrapHeaderForChat() {
        if (header.querySelector(".header-inner")) return;

        const inner = document.createElement("div");
        inner.className = "header-inner";

        const logo = header.querySelector(".logo");
        const title = header.querySelector(".title");
        const subtitle = header.querySelector(".subtitle");

        const textBlock = document.createElement("div");
        textBlock.appendChild(title);
        textBlock.appendChild(subtitle);

        inner.appendChild(logo);
        inner.appendChild(textBlock);

        header.innerHTML = "";
        header.appendChild(inner);
    }

    function setLoading(loading) {
        isAnalyzing = loading;
        submitBtn.disabled = loading;
        input.disabled = loading;
        submitBtn.classList.toggle("loading", loading);
    }

    function scrollToBottom() {
        requestAnimationFrame(() => {
            messagesEl.scrollTop = messagesEl.scrollHeight;
        });
    }

    function createUserMessage(cedula) {
        const msg = document.createElement("div");
        msg.className = "message user";
        msg.innerHTML = `<div class="bubble">Analizar cliente ${escapeHtml(cedula)}</div>`;
        return msg;
    }

    function createLoaderMessage() {
        const msg = document.createElement("div");
        msg.className = "message bot loading";
        msg.id = "loaderMessage";
        msg.innerHTML = `
            <div class="avatar" aria-hidden="true">🤖</div>
            <div class="bot-content">
                <div class="bot-label">Recovery AI</div>
                <div class="bot-card">
                    <div class="loader-spinner" aria-hidden="true"></div>
                    <span class="loader-text">Analizando cliente...</span>
                </div>
            </div>
        `;
        return msg;
    }

    function createBotMessage(data) {
        const probPct = Math.round(parseFloat(data.probabilidad) * 10000) / 100;
        const riesgo = data.nivel_riesgo || "—";
        const prioridad = data.prioridad_gestion || data.prioridad || "—";
        const canal = data.canal_recomendado || "—";
        const estrategia = data.estrategia || "—";
        const analisis = data.respuesta_ia || buildFallbackAnalysis(data, probPct);

        const msg = document.createElement("div");
        msg.className = "message bot";
        msg.innerHTML = `
            <div class="avatar" aria-hidden="true">🤖</div>
            <div class="bot-content">
                <div class="bot-label">Recovery AI</div>
                <div class="bot-card">
                    <div class="metric-grid">
                        <div class="metric-card">
                            <span class="label">Probabilidad</span>
                            <span class="value">${probPct}%</span>
                        </div>
                        <div class="metric-card">
                            <span class="label">Riesgo</span>
                            <span class="value ${riskClass(riesgo)}">${escapeHtml(riesgo)}</span>
                        </div>
                        <div class="metric-card">
                            <span class="label">Prioridad</span>
                            <span class="value ${priorityClass(prioridad)}">${escapeHtml(prioridad)}</span>
                        </div>
                    </div>
                    <div class="info-grid">
                        <div class="info-card">
                            <span class="label">Canal recomendado</span>
                            <span class="value">${escapeHtml(canal)}</span>
                        </div>
                        <div class="info-card">
                            <span class="label">Estrategia</span>
                            <span class="value">${escapeHtml(estrategia)}</span>
                        </div>
                    </div>
                    <div class="ia-analysis">
                        <div class="analysis-title">Análisis predictivo</div>
                        <div class="analysis-text">${escapeHtml(analisis)}</div>
                    </div>
                </div>
            </div>
        `;
        return msg;
    }

    function createErrorMessage(text) {
        const msg = document.createElement("div");
        msg.className = "message bot error";
        msg.innerHTML = `
            <div class="avatar" aria-hidden="true">🤖</div>
            <div class="bot-content">
                <div class="bot-label">Recovery AI</div>
                <div class="bot-card">
                    <p class="error-text">${escapeHtml(text)}</p>
                </div>
            </div>
        `;
        return msg;
    }

    function riskClass(level) {
        const map = { ALTO: "risk-alto", MEDIO: "risk-medio", BAJO: "risk-bajo" };
        return map[level] || "";
    }

    function priorityClass(level) {
        const map = { ALTA: "priority-alta", MEDIA: "priority-media", BAJA: "priority-baja" };
        return map[level] || "";
    }

    function buildFallbackAnalysis(data, probPct) {
        return [
            "Cliente analizado exitosamente.",
            "",
            `• Probabilidad de recuperación: ${probPct}%`,
            `• Nivel de riesgo: ${data.nivel_riesgo}`,
            `• Prioridad: ${data.prioridad_gestion || data.prioridad}`,
            `• Canal recomendado: ${data.canal_recomendado}`,
            `• Estrategia sugerida: ${data.estrategia}`,
            "",
            "La estrategia fue calculada con base en las variables históricas del cliente y el modelo predictivo entrenado."
        ].join("\n");
    }

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = String(str);
        return div.innerHTML;
    }

    function removeLoader() {
        const loader = document.getElementById("loaderMessage");
        if (loader) loader.remove();
    }

    async function analyzeClient(cedula) {
        activateChatMode();

        messagesEl.appendChild(createUserMessage(cedula));
        messagesEl.appendChild(createLoaderMessage());
        scrollToBottom();

        setLoading(true);

        try {
            const response = await fetch("/analizar", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ cedula: cedula.trim() })
            });

            const data = await response.json();
            removeLoader();

            if (data.error) {
                messagesEl.appendChild(createErrorMessage(data.error));
            } else {
                messagesEl.appendChild(createBotMessage(data));
            }
        } catch (err) {
            removeLoader();
            messagesEl.appendChild(
                createErrorMessage("No se pudo conectar con el servidor. Intenta de nuevo.")
            );
        } finally {
            setLoading(false);
            input.value = "";
            input.focus();
            scrollToBottom();
        }
    }

    form.addEventListener("submit", (e) => {
        e.preventDefault();
        if (isAnalyzing) return;

        const cedula = input.value.trim();
        if (!cedula) return;

        analyzeClient(cedula);
    });

    input.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            form.requestSubmit();
        }
    });
})();
