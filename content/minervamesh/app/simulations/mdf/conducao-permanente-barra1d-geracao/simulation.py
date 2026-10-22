#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simulação de Condução de Calor em Barra Unidimensional
-----------------------------------------------------
Este script implementa uma solução numérica e analítica para o problema
de condução de calor em uma barra unidimensional com geração de calor constante.
Utiliza o método das diferenças finitas para a solução numérica.

@author: lgsfarias
"""

import numpy as np
import matplotlib.pyplot as plt
from js import document
from pyodide.ffi import create_proxy

# ==============================
# 1. Solução Analítica
# ==============================
def analytical_solution(x, Q, alpha, L):
    """
    Calcula a solução analítica da equação de condução de calor.
    
    Parâmetros:
    -----------
    x : array
        Pontos de discretização
    Q : float
        Geração de calor constante
    alpha : float
        Coeficiente de difusividade térmica
    L : float
        Comprimento da barra
    
    Retorna:
    --------
    array
        Temperatura em cada ponto x
    """
    C1 = 1 / L + (Q / (2 * alpha)) * L
    return - (Q / (2 * alpha)) * x**2 + C1 * x

# ==============================
# 2. Função Principal de Simulação
# ==============================
def runSimulation(event):
    """
    Executa a simulação de condução de calor e plota os resultados.
    """
    # Parâmetros do problema
    L = 1.0  # Comprimento da barra
    nx = int(document.getElementById("nx").value) - 2  # Número de pontos internos
    alpha = float(document.getElementById("alpha").value)  # Coeficiente de difusividade
    Q = float(document.getElementById("Q").value)  # Geração de calor
    dx = L / (nx + 1)  # Passo da discretização

    # ==============================
    # 3. Montagem do Sistema Linear
    # ==============================
    # Inicialização da matriz de rigidez e vetor de fontes
    K = np.zeros((nx, nx))
    F = np.zeros(nx)

    # Preenchimento da matriz de rigidez usando diferenças finitas
    for i in range(nx):
        K[i, i] = 2
        if i > 0:
            K[i, i - 1] = -1
        if i < nx - 1:
            K[i, i + 1] = -1

    # Montagem do vetor de fontes
    F.fill(Q / alpha * dx**2)
    F[-1] -= -1  # Aplicação da condição de contorno em x = L

    # ==============================
    # 4. Solução do Sistema
    # ==============================
    T_internal = np.linalg.solve(K, F)
    T = np.concatenate(([0], T_internal, [1]))  # Adição das condições de contorno

    # ==============================
    # 5. Cálculo da Solução Analítica
    # ==============================
    x_analytical = np.linspace(0, L, 100)
    T_analytical = analytical_solution(x_analytical, Q, alpha, L)

    # ==============================
    # 6. Visualização dos Resultados
    # ==============================
    plt.figure(figsize=(10, 6))
    x = np.linspace(0, L, nx + 2)
    plt.plot(x, T, 'o-', label="Solução Numérica", color='#3B82F6', linewidth=2, markersize=8)
    plt.plot(x_analytical, T_analytical, '--', label="Solução Analítica", color='#EF4444', linewidth=2)
    
    # Adição dos parâmetros na legenda
    param_label = f"Parâmetros:\nNº Nós (nx): {nx} | Alpha: {alpha} | Q: {Q}"
    plt.plot([], [], ' ', label=param_label)
    
    # Configuração do gráfico
    plt.title("Comparação: Solução Numérica vs Analítica", fontsize=14, pad=15)
    plt.xlabel("Posição (x)", fontsize=12)
    plt.ylabel("Temperatura (T)", fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(fontsize=10, framealpha=0.9)
    plt.tight_layout()
    plt.show()

# ==============================
# 7. Configuração do Evento
# ==============================
# Configuração do evento de clique no botão
run_btn = document.getElementById("runBtn")
run_btn.addEventListener("click", create_proxy(runSimulation))

