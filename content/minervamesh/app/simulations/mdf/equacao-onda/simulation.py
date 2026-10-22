#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Equação da Onda 1D (Esquema Leapfrog Explícito)
------------------------------------------------
Modelo: u_tt = c^2 u_xx, 0 < x < L, t > 0
Condições de contorno: u(0,t) = u(L,t) = 0 (fixas)
Condições iniciais: u(x,0) = u0(x), u_t(x,0) = v0(x)

Este script simula a equação da onda 1D usando o esquema leapfrog explícito.
Para a condição "senoide", também plota a solução analítica
u(x,t) = sin(pi x/L) * cos(c pi t/L) para comparação.
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
# 1. Condição inicial u(x,0)
# ==============================
def initial_displacement(x, L, mode):
    """Retorna a condição inicial de deslocamento u(x,0) de acordo com o modo."""
    if mode == "senoide":
        return np.sin(np.pi * x / L)
    if mode == "pulso":
        u0 = np.zeros_like(x)
        mask = (x > 0.4 * L) & (x < 0.6 * L)
        u0[mask] = 0.5 * (1 - np.cos(2 * np.pi * (x[mask] - 0.4 * L) / (0.2 * L)))
        return u0
    return np.zeros_like(x)


# ==============================
# 2. Executar simulação
# ==============================
@when("click", "#runWaveBtn")
async def run_simulation(event=None):
    """Executa a simulação, monta frames e publica um GIF no contêiner HTML."""
    # parâmetros
    L = float(document.getElementById("L").value)
    nx = int(document.getElementById("nx").value)
    c = float(document.getElementById("c").value)
    tmax = float(document.getElementById("tmax").value)
    CFL = float(document.getElementById("cfl").value)
    mode = document.getElementById("mode").value

    dx = L / (nx - 1)
    dt = CFL * dx / c  # condição de estabilidade CFL<=1
    nt = max(1, int(tmax / dt))

    x = np.linspace(0.0, L, nx)
    # grid denso apenas para traçar a solução analítica com suavidade
    x_dense = np.linspace(0.0, L, max(400, min(2000, 5 * nx)))

    # condições iniciais
    u_prev = initial_displacement(x, L, mode)  # u(x,0)
    v0 = np.zeros_like(x)  # u_t(x,0)
    u = u_prev.copy() + dt * v0  # passo inicial

    r = (c * dt / dx) ** 2

    # aplicar CC fixas
    u_prev[0] = 0.0
    u_prev[-1] = 0.0
    u[0] = 0.0
    u[-1] = 0.0

    # abrir modal de execução durante a simulação
    container = document.getElementById("wave-output")
    sim_loading = document.getElementById("sim-loading")
    if sim_loading is not None:
        try:
            sim_loading.showModal()
        except Exception:
            pass
    # pequena espera para o DOM aplicar o modal antes do processamento pesado
    await asyncio.sleep(0.05)

    frames = []
    # ==============================
    # 3. Renderizar frame (matplotlib -> PNG em memória)
    # ==============================
    def odd_periodic_extension(xq, L):
        """Extensão ímpar 2L-periódica de u0(x) para CC de Dirichlet via método das imagens."""
        y = np.mod(xq, 2.0 * L)
        vals = np.empty_like(y)
        left = y <= L
        vals[left] = initial_displacement(y[left], L, "pulso")
        vals[~left] = -initial_displacement(2.0 * L - y[~left], L, "pulso")
        return vals

    def render_frame(u_frame, t):
        """Desenha um frame e retorna a imagem como array para o GIF."""
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(x, u_frame, label="Numérico", color="#3B82F6")
        if mode == "senoide":
            u_ana_dense = np.sin(np.pi * x_dense / L) * np.cos(c * np.pi * t / L)
            ax.plot(x_dense, u_ana_dense, '--', label="Analítico", color="#EF4444")
        elif mode == "pulso":
            # Solução analítica por d'Alembert com extensão ímpar 2L-periódica (u_t(x,0)=0):
            u_ana_dense = 0.5 * (
                odd_periodic_extension(x_dense - c * t, L) +
                odd_periodic_extension(x_dense + c * t, L)
            )
            ax.plot(x_dense, u_ana_dense, '--', label="Analítico (d'Alembert)", color="#EF4444")
        ax.set_ylim(-1.2, 1.2)
        ax.set_xlim(0, L)
        ax.set_xlabel("x")
        ax.set_ylabel("u")
        ax.set_title(f"Equação da Onda 1D - Leapfrog | t = {t:.3f}s")
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.legend()
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close(fig)
        buf.seek(0)
        return imageio.imread(buf)

    frames.append(render_frame(u_prev, 0.0))
    # ==============================
    # 4. Loop temporal (leapfrog)
    # ==============================
    for n in range(1, nt + 1):
        u_new = np.empty_like(u)
        # interior
        u_new[1:-1] = 2 * u[1:-1] - u_prev[1:-1] + r * (u[2:] - 2 * u[1:-1] + u[:-2])
        # CC fixas
        u_new[0] = 0.0
        u_new[-1] = 0.0

        u_prev, u = u, u_new

        if n % max(1, nt // 50) == 0 or n == nt:
            frames.append(render_frame(u, n*dt))

    # ==============================
    # 5. Montar GIF e publicar no DOM
    # ==============================
    gif_buffer = io.BytesIO()
    imageio.mimsave(gif_buffer, frames, format='GIF', duration=0.08, loop=0)
    gif_buffer.seek(0)
    gif_base64 = base64.b64encode(gif_buffer.read()).decode("utf-8")
    container.innerHTML = f"<img src='data:image/gif;base64,{gif_base64}' class='rounded shadow w-full'/>"
    if sim_loading is not None:
        try:
            sim_loading.close()
        except Exception:
            pass


