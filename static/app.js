(function () {
    "use strict";

    const app          = document.getElementById("app");
    const header       = document.getElementById("header");
    const messagesEl   = document.getElementById("messages");
    const form         = document.getElementById("queryForm");
    const input        = document.getElementById("cedulaInput");
    const submitBtn    = document.getElementById("submitBtn");
    const dashboardBtn = document.getElementById("dashboardBtn");
    const dashboardView= document.getElementById("dashboardView");
    const closeDashBtn = document.getElementById("closeDashboardBtn");
    const dashLoader   = document.getElementById("dashLoader");
    const dashContent  = document.getElementById("dashContent");

    let isAnalyzing = false;
    let chartsBuilt = false;

    // ==========================================
    // DASHBOARD
    // ==========================================

    dashboardBtn.addEventListener("click", () => {
        const isOpen = dashboardView.style.display !== "none";
        if (isOpen) {
            closeDashboard();
        } else {
            openDashboard();
        }
    });

    closeDashBtn.addEventListener("click", closeDashboard);

    function openDashboard() {
        activateChatMode();
        dashboardView.style.display = "block";
        document.getElementById("chatContainer").style.display = "none";
        dashboardBtn.classList.add("active");

        if (!chartsBuilt) {
            loadDashboard();
        }
    }

    function closeDashboard() {
        dashboardView.style.display = "none";
        document.getElementById("chatContainer").style.display = "";
        dashboardBtn.classList.remove("active");
    }

    async function loadDashboard() {
        dashLoader.style.display  = "flex";
        dashContent.style.display = "none";

        try {
            const res  = await fetch("/dashboard-data");
            const data = await res.json();

            if (data.error) {
                dashLoader.innerHTML = `<span style="color:#f87171">Error: ${data.error}</span>`;
                return;
            }

            renderKPIs(data.kpis);
            renderDonut("chartRiesgo",    "legendRiesgo",    data.por_riesgo,
                ["#f87171","#fbbf24","#34d399"], ["ALTO","MEDIO","BAJO"]);
            renderDonut("chartEstrategia","legendEstrategia",data.por_estrategia,
                ["#2563eb","#7c3aed","#f59e0b","#10b981"]);
            renderDonut("chartCanal",     "legendCanal",     data.por_canal,
                ["#3b82f6","#8b5cf6","#06b6d4"]);
            renderBarSaldo(data.saldo_por_riesgo);
            renderTopTable(data.top_clientes);

            chartsBuilt = true;
            dashLoader.style.display  = "none";
            dashContent.style.display = "block";

        } catch (e) {
            dashLoader.innerHTML = `<span style="color:#f87171">No se pudo cargar el dashboard.</span>`;
        }
    }

    function renderKPIs(kpis) {
        const grid = document.getElementById("kpiGrid");
        const items = [
            { label: "Total Clientes",           value: kpis.total_clientes.toLocaleString(),             icon: "👥" },
            { label: "Saldo Total en Mora",       value: "$" + formatMillones(kpis.saldo_total),           icon: "💰" },
            { label: "Prob. Promedio Recuperación",value: kpis.prob_promedio + "%",                        icon: "📈" },
            { label: "Mora Promedio (días)",      value: Math.round(kpis.mora_promedio).toLocaleString(),  icon: "📅" }
        ];
        grid.innerHTML = items.map(i => `
            <div class="kpi-card">
                <span class="kpi-icon">${i.icon}</span>
                <span class="kpi-value">${i.value}</span>
                <span class="kpi-label">${i.label}</span>
            </div>
        `).join("");
    }

    function renderDonut(canvasId, legendId, dataObj, colors, order) {
        const keys   = order || Object.keys(dataObj);
        const values = keys.map(k => dataObj[k] || 0);
        const total  = values.reduce((a, b) => a + b, 0);

        const ctx = document.getElementById(canvasId).getContext("2d");
        new Chart(ctx, {
            type: "doughnut",
            data: {
                labels: keys,
                datasets: [{
                    data: values,
                    backgroundColor: colors.slice(0, keys.length),
                    borderWidth: 2,
                    borderColor: "#0a0f1a"
                }]
            },
            options: {
                cutout: "68%",
                plugins: { legend: { display: false }, tooltip: {
                    callbacks: {
                        label: ctx => ` ${ctx.label}: ${ctx.parsed.toLocaleString()} (${((ctx.parsed/total)*100).toFixed(1)}%)`
                    }
                }},
                animation: { animateRotate: true, duration: 800 }
            }
        });

        const legend = document.getElementById(legendId);
        legend.innerHTML = keys.map((k, i) => `
            <div class="legend-item">
                <span class="legend-dot" style="background:${colors[i]}"></span>
                <span class="legend-label">${k}</span>
                <span class="legend-val">${((values[i]/total)*100).toFixed(1)}%</span>
            </div>
        `).join("");
    }

    function renderBarSaldo(saldoPorRiesgo) {
        const order  = ["ALTO","MEDIO","BAJO"];
        const labels = order.filter(k => saldoPorRiesgo[k] !== undefined);
        const values = labels.map(k => saldoPorRiesgo[k]);
        const colors = { ALTO: "#f87171", MEDIO: "#fbbf24", BAJO: "#34d399" };

        const ctx = document.getElementById("chartSaldo").getContext("2d");
        new Chart(ctx, {
            type: "bar",
            data: {
                labels,
                datasets: [{
                    label: "Saldo en mora",
                    data: values,
                    backgroundColor: labels.map(l => colors[l]),
                    borderRadius: 8,
                    borderSkipped: false
                }]
            },
            options: {
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: ctx => ` $${formatMillones(ctx.parsed.y)}`
                        }
                    }
                },
                scales: {
                    x: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(255,255,255,0.05)" } },
                    y: { ticks: { color: "#94a3b8", callback: v => "$" + formatMillones(v) }, grid: { color: "rgba(255,255,255,0.05)" } }
                },
                animation: { duration: 800 }
            }
        });
    }

    function renderTopTable(clientes) {
        const tbody = document.getElementById("topTableBody");
        tbody.innerHTML = clientes.map((c, i) => `
            <tr>
                <td>${i + 1}</td>
                <td class="cedula-cell">${escapeHtml(String(c.CEDULA))}</td>
                <td>$${Number(c.SALDO).toLocaleString("es-CO")}</td>
                <td>${c.MORA}</td>
                <td>${Math.round(c.PROBABILIDAD * 100)}%</td>
                <td><span class="badge badge--${c.NIVEL_RIESGO.toLowerCase()}">${c.NIVEL_RIESGO}</span></td>
                <td>${escapeHtml(c.ESTRATEGIA)}</td>
            </tr>
        `).join("");
    }

    function formatMillones(n) {
        if (n >= 1e9) return (n / 1e9).toFixed(1) + "B";
        if (n >= 1e6) return (n / 1e6).toFixed(1) + "M";
        if (n >= 1e3) return (n / 1e3).toFixed(0) + "K";
        return n.toString();
    }

    // ==========================================
    // CHAT
    // ==========================================

    function activateChatMode() {
        if (!app.classList.contains("chat-mode")) {
            app.classList.remove("welcome-mode");
            app.classList.add("chat-mode");
            wrapHeaderForChat();
        }
    }

    function wrapHeaderForChat() {
        if (header.querySelector(".header-inner")) return;

        const inner    = document.createElement("div");
        inner.className = "header-inner";

        const logo     = header.querySelector(".logo");
        const title    = header.querySelector(".title");
        const subtitle = header.querySelector(".subtitle");
        const dbBtn    = header.querySelector(".dashboard-btn");

      
        const textBlock = document.createElement("div");
        textBlock.appendChild(title);
        textBlock.appendChild(subtitle);

        inner.appendChild(logo);
        inner.appendChild(textBlock);

        const right = document.createElement("div");
        right.className = "header-right";
        right.appendChild(dbBtn);

        header.innerHTML = "";
        header.appendChild(inner);
        header.appendChild(right);
    }

    function setLoading(loading) {
        isAnalyzing      = loading;
        submitBtn.disabled = loading;
        input.disabled   = loading;
        submitBtn.classList.toggle("loading", loading);
    }

    function scrollToBottom() {
        requestAnimationFrame(() => {
            messagesEl.scrollTop = messagesEl.scrollHeight;
        });
    }

    function createUserMessage(texto) {
        const msg = document.createElement("div");
        msg.className = "message user";
        msg.innerHTML = `<div class="bubble">${escapeHtml(texto)}</div>`;
        return msg;
    }

    function createLoaderMessage() {
        const msg = document.createElement("div");
        msg.className  = "message bot loading";
        msg.id         = "loaderMessage";
        msg.innerHTML  = `
            <div class="avatar" aria-hidden="true">🤖</div>
            <div class="bot-content">
                <div class="bot-label">Recovery AI</div>
                <div class="bot-card">
                    <div class="loader-spinner" aria-hidden="true"></div>
                    <span class="loader-text">Analizando consulta...</span>
                </div>
            </div>
        `;
        return msg;
    }

    function createBotMessage(data) {
        const probPct    = Math.round(parseFloat(data.probabilidad) * 10000) / 100;
        const riesgo     = data.nivel_riesgo    || "—";
        const prioridad  = data.prioridad_gestion || data.prioridad || "—";
        const canal      = data.canal_recomendado || "—";
        const estrategia = data.estrategia       || "—";
        const analisis   = data.respuesta        || buildFallbackAnalysis(data, probPct);

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

    function createGeneralMessage(texto) {
        const msg = document.createElement("div");
        msg.className = "message bot";
        msg.innerHTML = `
            <div class="avatar" aria-hidden="true">🤖</div>
            <div class="bot-content">
                <div class="bot-label">Recovery AI</div>
                <div class="bot-card">
                    <div class="ia-analysis">
                        <div class="analysis-text">${escapeHtml(texto)}</div>
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

    async function sendMessage(texto) {
        activateChatMode();
        closeDashboard();

        messagesEl.appendChild(createUserMessage(texto));
        messagesEl.appendChild(createLoaderMessage());
        scrollToBottom();
        setLoading(true);

        try {
            const response = await fetch("/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ mensaje: texto.trim() })
            });

            const data = await response.json();
            removeLoader();

            if (data.error) {
                messagesEl.appendChild(createErrorMessage(data.error));
            } else if (data.tipo === "analisis") {
                messagesEl.appendChild(createBotMessage(data.datos
                    ? { ...data.datos, respuesta: data.respuesta }
                    : data
                ));
            } else {
                messagesEl.appendChild(createGeneralMessage(data.respuesta || "Sin respuesta del asistente."));
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
        const texto = input.value.trim();
        if (!texto) return;
        sendMessage(texto);
    });

    input.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            form.requestSubmit();
        }
    });

})();
