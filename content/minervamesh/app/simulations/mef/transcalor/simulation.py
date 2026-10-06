#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simulação Transiente de Condução de Calor em Placa 2D
@author: lgsfarias
"""

# ==============================
# 0. Importações
# ==============================
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.tri as tri
from scipy.sparse import lil_matrix, csr_matrix
from scipy.sparse.linalg import spsolve
from pyscript import when, document
import imageio.v2 as imageio
import io
import base64
import asyncio

# ==============================
# 1. Geração da Malha
# ==============================
nx, ny = 40, 40
x = np.linspace(0, 1, nx)
y = np.linspace(0, 1, ny)
Xg, Yg = np.meshgrid(x, y)
X = Xg.flatten()
Y = Yg.flatten()
points = np.column_stack((X, Y))
triang = tri.Triangulation(X, Y)
elements = triang.triangles
n_nodes = len(points)

# ==============================
# 2. Matrizes Locais
# ==============================
def element_matrices(coords, k, rho, cv):
    x0, x1, x2 = coords
    area = 0.5 * abs((x1[0] - x0[0]) * (x2[1] - x0[1]) - (x2[0] - x0[0]) * (x1[1] - x0[1]))
    b = np.array([x1[1] - x2[1], x2[1] - x0[1], x0[1] - x1[1]])
    c = np.array([x2[0] - x1[0], x0[0] - x2[0], x1[0] - x0[0]])
    ke = (k / (4 * area)) * (np.outer(b, b) + np.outer(c, c))
    me = (rho * cv * area / 12.0) * (np.ones((3, 3)) + np.eye(3))
    return ke, me

# ==============================
# 3. Gerar imagem do frame
# ==============================
def generate_frame_image(u, step, dt, Tbottom, Ttop):
    fig, ax = plt.subplots(figsize=(6, 5))
    tpc = ax.tricontourf(triang, u, levels=50, cmap='jet', vmin=Tbottom, vmax=Ttop)
    ax.set_title(f"t = {step * dt:.3f} s")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    fig.colorbar(tpc, ax=ax)
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    return imageio.imread(buf)

# ==============================
# 4. Rodar Simulação
# ==============================
@when("click", "#run-btn")
async def run_simulation(event=None):
    # Mostrar spinner de loading dentro do plot-output
    document.getElementById("plot-output").innerHTML = """
      <div class="flex flex-col items-center justify-center py-6">
        <div class="animate-spin h-10 w-10 border-4 border-blue-500 border-t-transparent rounded-full"></div>
        <p class="mt-4 text-blue-700 font-medium">Calculando simulação...</p>
      </div>
    """

    await asyncio.sleep(0.05) # permite que o DOM atualize antes de continuar

    # Parâmetros
    dt = float(document.getElementById("dt").value)
    n_steps = int(document.getElementById("n_steps").value)
    Tbottom = float(document.getElementById("Tbottom").value)
    Ttop = float(document.getElementById("Ttop").value)
    k = float(document.getElementById("k").value)
    rho = float(document.getElementById("rho").value)
    cv = float(document.getElementById("cv").value)

    # Matrizes globais
    M = lil_matrix((n_nodes, n_nodes))
    K = lil_matrix((n_nodes, n_nodes))
    for el in elements:
        coords = points[el]
        ke, me = element_matrices(coords, k, rho, cv)
        for i in range(3):
            for j in range(3):
                K[el[i], el[j]] += ke[i, j]
                M[el[i], el[j]] += me[i, j]
    M = M.tocsr()
    K = K.tocsr()

    # Condições iniciais
    u = np.zeros(n_nodes)
    for i in range(n_nodes):
        xi, yi = X[i], Y[i]
        if np.isclose(xi, 0) or np.isclose(xi, 1):
            u[i] = Tbottom + (Ttop - Tbottom) * yi
        elif np.isclose(yi, 0):
            u[i] = Tbottom
        elif np.isclose(yi, 1):
            u[i] = Ttop

    u_init = u.copy()
    boundary_nodes = [i for i in range(n_nodes) if
                      np.isclose(X[i], 0) or np.isclose(X[i], 1) or
                      np.isclose(Y[i], 0) or np.isclose(Y[i], 1)]

    A = M + dt / 2 * K
    B = M - dt / 2 * K
    A = A.tolil()
    for i in boundary_nodes:
        A[i, :] = 0
        A[i, i] = 1
    A = A.tocsr()

    # Loop de tempo
    frames = []
    for step in range(n_steps):
        b = B @ u
        b[boundary_nodes] = u_init[boundary_nodes]
        u = spsolve(A, b)
        frames.append(generate_frame_image(u, step, dt, Tbottom, Ttop))

    # Salvar GIF
    gif_buffer = io.BytesIO()
    imageio.mimsave(gif_buffer, frames, format='GIF', duration=0.1, loop=0)
    gif_buffer.seek(0)
    gif_base64 = base64.b64encode(gif_buffer.read()).decode("utf-8")

    # Metricas de validacao
    # T no centro vs regime permanente analitico T_ss = Tbottom + (Ttop-Tbottom) y
    # Escala difusiva tau_dif = L^2 * rho * cv / k (dominio unitario: L=1)
    idx_centro = int(np.argmin((X - 0.5) ** 2 + (Y - 0.5) ** 2))
    T_centro_mef = float(u[idx_centro])
    T_centro_ss = float(Tbottom + (Ttop - Tbottom) * Y[idx_centro])
    erro_centro = abs(T_centro_mef - T_centro_ss)
    tau_dif = 1.0 * rho * cv / k if k > 0 else float('inf')
    t_final = n_steps * dt
    frac_tau = t_final / tau_dif if tau_dif > 0 else 0.0

    metrics_html = (
        "<div class=\"bg-blue-50 border-l-4 border-blue-400 p-3 rounded w-full\">"
        "<h4 class=\"font-semibold text-blue-800 mb-1\">Validação</h4>"
        f"<p class=\"text-sm text-gray-700\"><strong>Tempo final:</strong> "
        f"{t_final:.3f} s ({frac_tau*100:.1f}% da escala difusiva "
        f"τ_dif = {tau_dif:.2f} s)</p>"
        f"<p class=\"text-sm text-gray-700\"><strong>T(0,5; 0,5) MEF:</strong> "
        f"{T_centro_mef:.4f} °C</p>"
        f"<p class=\"text-sm text-gray-700\"><strong>T(0,5; 0,5) regime permanente "
        f"(T_bot + (T_top − T_bot)·y):</strong> {T_centro_ss:.4f} °C</p>"
        f"<p class=\"text-sm text-gray-700\"><strong>Desvio do regime permanente:</strong> "
        f"{erro_centro:.4f} °C (aumentar n_steps para convergir)</p>"
        "</div>"
    )

    # Mostrar resultado final
    document.getElementById("plot-output").innerHTML = (
        f"<div class='flex flex-col gap-3 w-full'>"
        f"<img src='data:image/gif;base64,{gif_base64}' class='rounded shadow w-full'/>"
        f"{metrics_html}"
        f"</div>"
    )
