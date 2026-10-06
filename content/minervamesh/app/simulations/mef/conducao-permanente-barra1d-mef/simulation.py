#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Condução Permanente 1D (MEF) — Problema 5.2.2
Barra 1D com geração interna Q, T(0)=T0 e T(L)=TL.
Elementos lineares, solução analítica para comparação.
"""

import numpy as np
import matplotlib.pyplot as plt
from js import document
from pyscript import when
import asyncio
import io
import imageio.v2 as imageio
import base64


# ==============================
# 1. Solução analítica
# ==============================
def analytical_solution(x, Q, k, L, T0, TL):
    # Solução da EDO: -k T'' = Q, T(0)=T0, T(L)=TL
    C1 = (TL - T0 + (Q * L * L) / (2 * k)) / L
    C2 = T0
    return - (Q / (2 * k)) * x * x + C1 * x + C2


# ==============================
# 2. Executar simulação MEF 1D
# ==============================
@when("click", "#runMEF1D")
async def run_mef_1d(event=None):
    # Abrir modal de execução
    sim_loading = document.getElementById("sim-loading")
    try:
        sim_loading.showModal()
    except Exception:
        pass
    await asyncio.sleep(0.05)

    # Parâmetros
    L = float(document.getElementById("L").value)
    nel = int(document.getElementById("nel").value)
    T0 = float(document.getElementById("T0").value)
    TL = float(document.getElementById("TL").value)
    k = float(document.getElementById("k").value)
    Q = float(document.getElementById("Q").value)

    # Malha 1D
    nn = nel + 1
    x = np.linspace(0.0, L, nn)
    h = L / nel

    # Matrizes/vetores globais
    K = np.zeros((nn, nn))        # matriz de rigidez (apostila: K)
    b = np.zeros(nn)              # vetor de carregamento (apostila: b)

    # Elemento linear: ke = k/h * [[1,-1],[-1,1]]; be = Q*h/2 * [1,1]
    ke = (k / h) * np.array([[1.0, -1.0], [-1.0, 1.0]])
    be = (Q * h / 2.0) * np.array([1.0, 1.0])

    # Montagem
    for e in range(nel):
        n1, n2 = e, e + 1
        K[n1:n2+1, n1:n2+1] += ke
        b[n1:n2+1] += be

    # Contornos essenciais (Dirichlet)
    # T(0)=T0
    K[0, :] = 0.0
    K[0, 0] = 1.0
    b[0] = T0
    # T(L)=TL
    K[-1, :] = 0.0
    K[-1, -1] = 1.0
    b[-1] = TL

    # Resolver
    T = np.linalg.solve(K, b)

    # Analítico (grade densa para curva lisa)
    x_dense = np.linspace(0.0, L, max(600, min(2400, 8 * nn)))
    T_ana_dense = analytical_solution(x_dense, Q, k, L, T0, TL)

    # Analítico nos nós da malha para métricas de erro
    T_ana_mesh = analytical_solution(x, Q, k, L, T0, TL)
    erro_nodal = np.abs(T - T_ana_mesh)
    e_max = float(np.max(erro_nodal))
    T_max_mef = float(np.max(T))
    x_max_mef = float(x[int(np.argmax(T))])
    T_max_ana = float(np.max(T_ana_dense))
    x_max_ana = float(x_dense[int(np.argmax(T_ana_dense))])

    # Plot
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(x, T, 'o-', label='MEF 1D', color='#3B82F6')
    ax.plot(x_dense, T_ana_dense, '--', label='Analítica', color='#EF4444')
    ax.set_xlabel('x [m]')
    ax.set_ylabel('Temperatura [°C]')
    ax.set_title('Condução Permanente 1D (MEF)')
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend()
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    img = imageio.imread(buf)
    gif_buffer = io.BytesIO()
    imageio.mimsave(gif_buffer, [img], format='GIF', duration=1.0)
    gif_buffer.seek(0)
    gif_base64 = base64.b64encode(gif_buffer.read()).decode('utf-8')

    container = document.getElementById("mef1d-output")
    metrics_html = f"""
    <div class="bg-blue-50 border-l-4 border-blue-400 p-3 rounded w-full">
        <h4 class="font-semibold text-blue-800 mb-1">Validação</h4>
        <p class="text-sm text-gray-700"><strong>Malha:</strong> {nel} elementos lineares, h = {h:.4f} m</p>
        <p class="text-sm text-gray-700"><strong>T_max (MEF):</strong> {T_max_mef:.6f} °C em x = {x_max_mef:.3f} m</p>
        <p class="text-sm text-gray-700"><strong>T_max (analítica):</strong> {T_max_ana:.6f} °C em x = {x_max_ana:.3f} m</p>
        <p class="text-sm text-gray-700"><strong>Erro máximo nodal:</strong> {e_max:.2e} °C</p>
    </div>
    """
    container.innerHTML = (
        f"<div class='flex flex-col gap-3 w-full'>"
        f"<img src='data:image/gif;base64,{gif_base64}' class='rounded shadow w-full'/>"
        f"{metrics_html}"
        f"</div>"
    )

    try:
        sim_loading.close()
    except Exception:
        pass


