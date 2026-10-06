#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Problema Térmico Transiente 1D (MEF)
------------------------------------------------------------------
Modelo: ρc ∂T/∂t = ∂/∂x(k(x) ∂T/∂x), 0 < x < L, t > 0
Condições de contorno: T(0,t) = 0, T(L,t) = 1 (fixas)
Condutividade térmica descontínua em x=L/2, com valores k1 (primeira metade)
e k2 (segunda metade) configuráveis via interface.

Este script simula a condução transiente de calor 1D usando Método dos Elementos Finitos
com condutividade térmica variável e número de elementos configurável.
Gera um GIF com os frames e embute no DOM via PyScript.
"""

import numpy as np
import matplotlib.pyplot as plt
from js import document
from pyscript import when
import asyncio
import imageio.v2 as imageio
import io
import base64


# ==============================
# 1. Função de condutividade térmica k(x)
# ==============================
def thermal_conductivity(x, L, k1=5.0, k2=1.0):
    """
    Retorna a condutividade térmica k(x).
    Condutividade abrupta (não suavizada).
    """
    return np.where(x < L/2, k1, k2)


# ==============================
# 2. Solução analítica de regime permanente para k(x) descontínuo
# ==============================
def analytical_steady_state(x, L, k1, k2):
    """
    Solução analítica de regime permanente para k(x) descontínuo em x=L/2
    com T(0)=0 e T(L)=1.

    Em permanente, o fluxo q = -k·dT/dx é constante. Integrando em cada região
    e impondo continuidade de T em L/2 e T(L)=1:
        C      = 2·k1·k2 / (L·(k1+k2))
        T(x)   = (C/k1)·x                             para x < L/2
        T(x)   = (C·L/(2·k1)) + (C/k2)·(x - L/2)      para x >= L/2
    """
    C = 2.0 * k1 * k2 / (L * (k1 + k2))
    T = np.zeros_like(x, dtype=float)
    mask_left = x < L / 2
    T[mask_left] = (C / k1) * x[mask_left]
    T_half = (C / k1) * (L / 2)
    T[~mask_left] = T_half + (C / k2) * (x[~mask_left] - L / 2)
    return T


# ==============================
# 2. Matrizes de elemento para MEF 1D
# ==============================
def element_matrices_1d(x1, x2, k_avg, rho_cp):
    """Calcula as matrizes de elemento para condução 1D."""
    h = x2 - x1  # comprimento do elemento

    # Matriz de rigidez do elemento
    ke = (k_avg / h) * np.array([[1, -1], [-1, 1]])

    # Matriz de massa do elemento (capacidade térmica)
    me = (rho_cp * h / 6) * np.array([[2, 1], [1, 2]])

    return ke, me


# ==============================
# 3. Montar sistema global
# ==============================
def assemble_system(n_elements, L, rho_cp=1.0, k1=5.0, k2=1.0):
    """Monta as matrizes globais K e M do sistema MEF."""
    n_nodes = n_elements + 1

    x_nodes = np.zeros(n_nodes)

    # Primeira metade (x < L/2) - pontos uniformes
    n_left = n_elements // 2
    x_nodes[:n_left+1] = np.linspace(0, L/2, n_left+1)

    # Segunda metade (x >= L/2) - pontos uniformes
    n_right = n_elements - n_left
    x_nodes[n_left:] = np.linspace(L/2, L, n_right+1)

    # Inicializar matrizes globais
    K = np.zeros((n_nodes, n_nodes))
    M = np.zeros((n_nodes, n_nodes))

    # Montar sistema elemento por elemento
    for i in range(n_elements):
        x1, x2 = x_nodes[i], x_nodes[i+1]

        # Calcular condutividade média do elemento
        # Para elementos que cruzam a fronteira x=L/2, usar média ponderada
        if x1 < L/2 and x2 > L/2:
            # Elemento cruza a fronteira - calcular média ponderada
            frac_left = (L/2 - x1) / (x2 - x1)  # fração à esquerda da fronteira
            frac_right = (x2 - L/2) / (x2 - x1)  # fração à direita da fronteira
            k_avg = frac_left * k1 + frac_right * k2
        else:
            # Elemento inteiramente em uma região
            x_center = (x1 + x2) / 2
            k_avg = thermal_conductivity(x_center, L, k1, k2)

        ke, me = element_matrices_1d(x1, x2, k_avg, rho_cp)

        # Montar matrizes globais
        K[i:i+2, i:i+2] += ke
        M[i:i+2, i:i+2] += me

    return K, M, x_nodes


# ==============================
# 4. Renderizar frame
# ==============================
def render_frame(T, x_nodes, t, n_elements, k1=1.0, k2=5.0):
    """Desenha um frame e retorna a imagem como array para o GIF."""
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plotar temperatura numérica
    ax.plot(x_nodes, T, 'o-', label="MEF", color="#3B82F6", linewidth=2, markersize=4)

    # Plotar solução analítica de regime permanente (referência)
    x_dense = np.linspace(0, x_nodes[-1], 200)
    T_analytical = analytical_steady_state(x_dense, x_nodes[-1], k1, k2)
    ax.plot(x_dense, T_analytical, '--', label="Regime permanente (analítico)", color="#EF4444", linewidth=2)

    # Plotar condutividade térmica como fundo
    k_values = thermal_conductivity(x_dense, x_nodes[-1], k1, k2)

    # Criar segundo eixo para k(x)
    ax2 = ax.twinx()
    ax2.plot(x_dense, k_values, ':', color='green', alpha=0.7, linewidth=1)
    ax2.set_ylabel('Condutividade k(x)', color='green', fontsize=12)
    ax2.tick_params(axis='y', labelcolor='green')
    ax2.set_ylim(0, max(k1, k2) + 1)

    ax.set_ylim(-0.1, 1.1)
    ax.set_xlim(0, x_nodes[-1])
    ax.set_xlabel("Posição x", fontsize=12)
    ax.set_ylabel("Temperatura T", fontsize=12)
    ax.set_title(f"Condução Transiente 1D - MEF (n={n_elements}) | t = {t:.3f}s", fontsize=14)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(fontsize=12)

    # Adicionar linha vertical no meio para mostrar mudança de k
    # Linha vertical no meio
    ax.axvline(x=x_nodes[-1]/2, color='red', linestyle=':', alpha=0.5)

    # Rótulos em y = k1 e y = k2 no eixo de k(x)
    eps = 0.02 * x_nodes[-1]  # pequeno deslocamento horizontal para não colidir com a linha
    ax2.text(x_nodes[-1]/2 - eps, k1, f'k={k1:g}', ha='right', va='center',
            color='red', fontsize=10)
    ax2.text(x_nodes[-1]/2 + eps, k2, f'k={k2:g}', ha='left', va='center',
            color='red', fontsize=10)

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    plt.close(fig)
    buf.seek(0)
    return imageio.imread(buf)


# ==============================
# 5. Executar simulação
# ==============================
@when("click", "#runHeatBtn")
async def run_simulation(event=None):
    """Executa a simulação MEF, monta frames e publica um GIF no contêiner HTML."""
    # parâmetros
    L = float(document.getElementById("L").value)
    n_elements = int(document.getElementById("n_elements").value)
    k1 = float(document.getElementById("k1").value)
    k2 = float(document.getElementById("k2").value)
    rho_cp = float(document.getElementById("rho_cp").value)
    dt = float(document.getElementById("dt").value)
    theta = float(document.getElementById("theta").value)
    tmax = float(document.getElementById("tmax").value)

    # Montar sistema MEF
    K, M, x_nodes = assemble_system(n_elements, L, rho_cp, k1, k2)
    n_nodes = len(x_nodes)

    # Condições iniciais (temperatura zero em todo domínio, exceto bordas)
    T = np.zeros(n_nodes)

    # Aplicar condições de contorno
    T[0] = 0.0    # T(0,t) = 0
    T[-1] = 1.0   # T(L,t) = 1

    # Identificar nós de contorno
    boundary_nodes = [0, n_nodes-1]
    interior_nodes = list(range(1, n_nodes-1))

    # Preparar sistema para integração temporal conforme equação da apostila
    # ((M/Δt) + θK) T^(n+1) = [(M/Δt) - (1-θ)K] T^n
    A = M/dt + theta * K
    B = M/dt - (1 - theta) * K

    # Aplicar condições de contorno no sistema
    for i in boundary_nodes:
        A[i, :] = 0
        A[i, i] = 1
        B[i, :] = 0
        B[i, i] = 1

    # abrir modal de execução durante a simulação
    container = document.getElementById("heat-output")
    sim_loading = document.getElementById("sim-loading")
    if sim_loading is not None:
        try:
            sim_loading.showModal()
        except Exception:
            pass
    await asyncio.sleep(0.05)

    frames = []
    nt = max(1, int(tmax / dt))

    # Frame inicial
    frames.append(render_frame(T, x_nodes, 0.0, n_elements, k1, k2))

    # ==============================
    # 6. Loop temporal (Crank-Nicolson com suavização suave)
    # ==============================
    T_prev = T.copy()  # Para suavização temporal

    for n in range(1, nt + 1):
        # Resolver sistema: A * T^(n+1) = B * T^n + f
        b = B @ T

        # Aplicar condições de contorno no vetor b
        b[0] = 0.0    # T(0,t) = 0
        b[-1] = 1.0    # T(L,t) = 1

        # Resolver sistema linear
        T_new = np.linalg.solve(A, b)

        # Atualizar temperatura
        T = T_new

        # Garantir condições de contorno exatas
        T[0] = 0.0
        T[-1] = 1.0

        if n % max(1, nt // 50) == 0 or n == nt:
            frames.append(render_frame(T, x_nodes, n*dt, n_elements, k1, k2))

    # ==============================
    # 7. Montar GIF e publicar no DOM
    # ==============================
    gif_buffer = io.BytesIO()
    imageio.mimsave(gif_buffer, frames, format='GIF', duration=0.1, loop=0)
    gif_buffer.seek(0)
    gif_base64 = base64.b64encode(gif_buffer.read()).decode("utf-8")

    # Metricas de validacao: T(L/2) vs analitica de regime permanente
    # Analitica (fluxo continuo em x=L/2): T(L/2) = k2 / (k1 + k2) quando
    # T(0)=0 e T(L)=1. Para k1=5, k2=1 -> T(L/2) = 1/6 aprox 0,1667.
    idx_meio = int(np.argmin(np.abs(x_nodes - L / 2.0)))
    T_meio_mef = float(T[idx_meio])
    T_meio_ana = float(k2 / (k1 + k2))
    erro_meio = abs(T_meio_mef - T_meio_ana)
    tau_dif = L * L * rho_cp / max(k1, k2)
    t_final = nt * dt
    frac_tau = t_final / tau_dif if tau_dif > 0 else 0.0

    metrics_html = f"""
    <div class="bg-blue-50 border-l-4 border-blue-400 p-3 rounded w-full">
        <h4 class="font-semibold text-blue-800 mb-1">Validação</h4>
        <p class="text-sm text-gray-700"><strong>Tempo final:</strong> {t_final:.3f} s ({frac_tau*100:.1f}% de τ_dif = {tau_dif:.2f} s)</p>
        <p class="text-sm text-gray-700"><strong>T(L/2) MEF:</strong> {T_meio_mef:.6f} °C</p>
        <p class="text-sm text-gray-700"><strong>T(L/2) analítica (regime permanente, k2/(k1+k2)):</strong> {T_meio_ana:.6f} °C</p>
        <p class="text-sm text-gray-700"><strong>Desvio em x = L/2:</strong> {erro_meio:.2e} °C</p>
    </div>
    """
    container.innerHTML = (
        f"<div class='flex flex-col gap-3 w-full'>"
        f"<img src='data:image/gif;base64,{gif_base64}' class='rounded shadow w-full'/>"
        f"{metrics_html}"
        f"</div>"
    )

    if sim_loading is not None:
        try:
            sim_loading.close()
        except Exception:
            pass