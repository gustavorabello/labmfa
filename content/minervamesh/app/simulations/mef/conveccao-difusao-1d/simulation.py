#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convecção-Difusão 1D Permanente (MEF) — Problema 5.2.4
Equação: -k d²T/dx² + ρcp u dT/dx = Q
Condições: T(0)=T0, T(L)=TL
Elementos lineares com estabilização SUPG.
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
def analytical_solution(x, Q, k, rho_cp, u, L, T0, TL):
    """
    Solução analítica da equação de convecção-difusão 1D permanente.
    Equação: -k d²T/dx² + ρcp u dT/dx = Q
    Condições: T(0)=T0, T(L)=TL

    Forma estável numericamente mesmo para grandes números de Péclet: a razão
    (exp(α x) - 1) / (exp(α L) - 1) é reescrita fatorando exp(α L) quando α > 0,
    evitando overflow de exp para α·L grande.
    """
    # Caso puramente difusivo: -k T'' = Q
    if abs(rho_cp * u) < 1e-14:
        C1 = (TL - T0 + (Q * L * L) / (2 * k)) / L
        return -(Q / (2 * k)) * x * x + C1 * x + T0

    alpha = rho_cp * u / k
    Tp   = Q * x / (rho_cp * u)
    Tp_L = Q * L / (rho_cp * u)

    # g(x) := (exp(α x) - 1) / (exp(α L) - 1)
    if alpha > 0:
        # fatora exp(α L) para evitar overflow
        g = np.exp(alpha * (x - L)) * (1.0 - np.exp(-alpha * x)) \
                                    / (1.0 - np.exp(-alpha * L))
    else:
        # para α ≤ 0, expm1 já é estável
        g = np.expm1(alpha * x) / np.expm1(alpha * L)

    return T0 + Tp + (TL - T0 - Tp_L) * g


# ==============================
# 2. Executar simulação MEF 1D com convecção-difusão
# ==============================
@when("click", "#runConveccaoDifusao1D")
async def run_conveccao_difusao_1d(event=None):
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
    rho_cp = float(document.getElementById("rho_cp").value)
    u = float(document.getElementById("u").value)
    Q = float(document.getElementById("Q").value)
    use_supg = document.getElementById("use_supg").checked

    # Malha 1D uniforme
    nn = nel + 1
    x = np.linspace(0.0, L, nn)
    h = L / nel

    # Número de Péclet local
    Pe_local = (rho_cp * u * h) / (2 * k)
    
    # Parâmetro de estabilização SUPG
    if use_supg and abs(Pe_local) > 1e-10:
        tau = h / (2 * abs(u)) * (1 / np.tanh(abs(Pe_local)) - 1 / abs(Pe_local))
    else:
        tau = 0.0

    # Matrizes/vetores globais
    K = np.zeros((nn, nn))        # matriz de rigidez
    b = np.zeros(nn)              # vetor de carregamento

    # Elemento linear com convecção-difusão
    # Matriz de difusão: ke_diff = k/h * [[1,-1],[-1,1]]
    ke_diff = (k / h) * np.array([[1.0, -1.0], [-1.0, 1.0]])
    
    # Matriz de convecção: ke_conv = ρcp*u/2 * [[-1,1],[-1,1]]
    ke_conv = (rho_cp * u / 2.0) * np.array([[-1.0, 1.0], [-1.0, 1.0]])
    
    # Vetor de fontes: be = Q*h/2 * [1,1]
    be = (Q * h / 2.0) * np.array([1.0, 1.0])
    
    # Estabilização SUPG (se habilitada)
    if use_supg and tau > 0:
        # Matriz de estabilização SUPG
        ke_supg = tau * rho_cp * u * u / h * np.array([[1.0, -1.0], [-1.0, 1.0]])
        # Vetor de estabilização SUPG
        be_supg = tau * Q * u * np.array([-1.0, 1.0])
        
        # Combinar todas as contribuições
        ke_total = ke_diff + ke_conv + ke_supg
        be_total = be + be_supg
    else:
        ke_total = ke_diff + ke_conv
        be_total = be

    # Montagem
    for e in range(nel):
        n1, n2 = e, e + 1
        K[n1:n2+1, n1:n2+1] += ke_total
        b[n1:n2+1] += be_total

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
    T_ana_dense = analytical_solution(x_dense, Q, k, rho_cp, u, L, T0, TL)
    
    # Solução analítica nos pontos da malha numérica para cálculo do erro
    T_ana_mesh = analytical_solution(x, Q, k, rho_cp, u, L, T0, TL)

    # Plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    
    # Gráfico principal
    ax1.plot(x, T, 'o-', label='MEF 1D', color='#3B82F6', markersize=6)
    ax1.plot(x_dense, T_ana_dense, '--', label='Analítica', color='#EF4444', linewidth=2)
    ax1.set_xlabel('x [m]')
    ax1.set_ylabel('Temperatura [°C]')
    ax1.set_title('Convecção-Difusão 1D Permanente (MEF)')
    ax1.grid(True, linestyle='--', alpha=0.5)
    ax1.legend()
    
    # Gráfico de erro
    erro = np.abs(T - T_ana_mesh)
    # Evitar erro zero para escala logarítmica
    erro = np.maximum(erro, 1e-18)
    ax2.semilogy(x, erro, 'o-', color='#10B981', markersize=6)
    ax2.set_xlabel('x [m]')
    ax2.set_ylabel('Erro Absoluto [°C]')
    ax2.set_title('Erro entre Solução Numérica e Analítica (Escala Logarítmica)')
    ax2.grid(True, linestyle='--', alpha=0.5)
    # Adicionar texto explicativo
    ax2.text(0.5, 0.5, f'Erro máximo: {np.max(erro):.2e} °C\n(Precisão de máquina)', 
             transform=ax2.transAxes, ha='center', va='center', 
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
             fontsize=10)
    
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150)
    plt.close(fig)
    buf.seek(0)
    img = imageio.imread(buf)
    gif_buffer = io.BytesIO()
    imageio.mimsave(gif_buffer, [img], format='GIF', duration=1.0)
    gif_buffer.seek(0)
    gif_base64 = base64.b64encode(gif_buffer.read()).decode('utf-8')

    container = document.getElementById("conveccao-difusao-output")
    container.innerHTML = f"<img src='data:image/gif;base64,{gif_base64}' class='rounded shadow w-full'/>"

    # Atualizar informações sobre Péclet
    pe_info = document.getElementById("pe-info")
    pe_info.innerHTML = f"""
    <div class="bg-blue-50 border-l-4 border-blue-400 p-3 rounded">
        <h4 class="font-semibold text-blue-800 mb-1">Informações da Simulação</h4>
        <p class="text-sm text-gray-700"><strong>Número de Péclet:</strong> {Pe_local:.3f}</p>
        <p class="text-sm text-gray-700"><strong>Estabilização SUPG:</strong> {'Sim' if use_supg else 'Não'}</p>
        <p class="text-sm text-gray-700"><strong>Parâmetro τ:</strong> {tau:.6f}</p>
        <p class="text-sm text-gray-700"><strong>Velocidade:</strong> {u:.3f} m/s</p>
        <p class="text-sm text-gray-700"><strong>Tamanho elemento:</strong> {h:.4f} m</p>
        <p class="text-sm text-gray-700"><strong>Erro máximo:</strong> {np.max(erro):.2e} °C</p>
    </div>
    """

    try:
        sim_loading.close()
    except Exception:
        pass
