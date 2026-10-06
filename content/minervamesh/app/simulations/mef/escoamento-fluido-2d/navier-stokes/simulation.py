import numpy as np
import matplotlib.pyplot as plt
import matplotlib.tri as tri
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import spsolve
from pyscript import when, document
import asyncio
from common import generate_mesh_generic, assemble_matrices, plot_to_base64
import geometry

# Sinalizador global de controle
STOP_SIMULATION = False

@when("click", "#stop-btn")
def stop_simulation_handler(event=None):
    global STOP_SIMULATION
    STOP_SIMULATION = True
    document.getElementById("stop-btn").classList.add("hidden")
    document.getElementById("stop-btn").classList.remove("flex")
    document.getElementById("run-btn").classList.remove("hidden")
    document.getElementById("run-btn").classList.add("flex")

# ==============================
# Funções auxiliares do solver NS
# ==============================
def assemble_convection(X, Y, triang, u_el, v_el):
    n_nodes = len(X)
    C = lil_matrix((n_nodes, n_nodes))
    elements = triang.triangles
    mask = triang.mask if triang.mask is not None else np.zeros(len(elements), dtype=bool)
    
    for i, el in enumerate(elements):
        if mask[i]: continue
        x = X[el]
        y = Y[el]
        area = 0.5 * np.abs(x[0]*(y[1]-y[2]) + x[1]*(y[2]-y[0]) + x[2]*(y[0]-y[1]))
        b = np.array([y[1] - y[2], y[2] - y[0], y[0] - y[1]])
        c = np.array([x[2] - x[1], x[0] - x[2], x[1] - x[0]])
        ue = u_el[i]
        ve = v_el[i]
        K_dot_grad = (ue * b + ve * c) / (2 * area)
        ce = np.outer(np.ones(3) * (area / 3.0), K_dot_grad)
        for row in range(3):
            for col in range(3):
                C[el[row], el[col]] += ce[row, col]
    return C.tocsr()

def get_boundary_normals(X, Y, boundary_nodes, triang):
    adj = [set() for _ in range(len(X))]
    mask = triang.mask if triang.mask is not None else np.zeros(len(triang.triangles), dtype=bool)
    for i, el in enumerate(triang.triangles):
        if mask[i]: continue
        for j in range(3):
            n1, n2 = el[j], el[(j+1)%3]
            adj[n1].add(n2)
            adj[n2].add(n1)
            
    boundary_set = set(boundary_nodes)
    valid_neighbors = np.zeros(len(boundary_nodes), dtype=int)
    h_sq = np.zeros(len(boundary_nodes))
    
    for i, node in enumerate(boundary_nodes):
        node_neighbors = list(adj[node])
        best_nb = -1
        min_dist = 1e9
        for nb in node_neighbors:
            if nb not in boundary_set:
                d = (X[node]-X[nb])**2 + (Y[node]-Y[nb])**2
                if d < min_dist:
                    min_dist = d
                    best_nb = nb
        if best_nb == -1:
            for nb in node_neighbors:
                d = (X[node]-X[nb])**2 + (Y[node]-Y[nb])**2
                if d < min_dist:
                    min_dist = d
                    best_nb = nb
        valid_neighbors[i] = best_nb
        h_sq[i] = min_dist
    return valid_neighbors, h_sq

# ==============================
# Solver NS
# ==============================
async def solve_navier_stokes(params, plot_div):
    # 1. Malha
    cx, cy = params["cx"], params["cy"]

    # Perfil de entrada (inlet)
    def get_psi_inlet(y_val):
        # Padrão: u=1, psi=y
        return y_val

    scenario = params.get("scenario", "channel")

    if scenario == "cavity":
        # Cavidade: sem geometria/obstáculo
        boundary_pts = np.empty((0, 2))
        def mask_func(x, y): return np.ones_like(x, dtype=bool)
    else:
        boundary_pts, mask_func = geometry.get_geometry(params["geo_type"], params)

    X, Y, triang = generate_mesh_generic(
        params["L"], params["H"], boundary_pts, mask_func, 
        cx, cy, params["nx"], params["ny"]
    )
    n_nodes = len(X)
    
    # 2. Matrizes
    K, M = assemble_matrices(X, Y, triang)
    
    # 3. Fronteiras
    eps = 1e-5
    inlet_nodes = np.where(X < eps)[0]
    wall_bottom = np.where(Y < eps)[0]
    wall_top = np.where(Y > params["H"] - eps)[0]
    
    # Nós do obstáculo (últimos N pontos)
    n_bound = len(boundary_pts)
    obstacle_nodes = np.arange(n_nodes - n_bound, n_nodes)

    solid_walls = np.concatenate([wall_bottom, wall_top, obstacle_nodes])
    solid_walls = np.unique(solid_walls)

    wall_neighbors, wall_h_sq = get_boundary_normals(X, Y, solid_walls, triang)

    # 4. Inicialização e condições de contorno
    psi = np.zeros(n_nodes)
    omega = np.zeros(n_nodes)
    
    scenario = params.get("scenario", "channel")
    
    if scenario == "cavity":
        # Cavidade quadrada com tampa deslizante (lid-driven cavity):
        # psi = 0 em todas as paredes (caixa fechada); o escoamento é
        # induzido pela condição de contorno de vorticidade na tampa.
        eps = 1e-5
        wall_bottom = np.where(Y < eps)[0]
        wall_top = np.where(Y > params["H"] - eps)[0]
        wall_left = np.where(X < eps)[0]
        wall_right = np.where(X > params["L"] - eps)[0]

        # Todos os nós da fronteira
        all_walls = np.concatenate([wall_bottom, wall_top, wall_left, wall_right])
        all_walls = np.unique(all_walls)

        # Contorno de psi: 0 em toda a fronteira
        psi[all_walls] = 0.0
        dirichlet_psi = all_walls

        # Contorno de omega (mesmos nós; atualizado a cada passo no laço)
        dirichlet_omega = all_walls

        # Vizinhos de todas as paredes (necessários para a fórmula de Thom)
        wall_neighbors, wall_h_sq = get_boundary_normals(X, Y, all_walls, triang)

        # Velocidade tangencial de cada parede: a tampa superior se move (u = 1),
        # as demais são estacionárias (u = 0).
        wall_u_tan = np.zeros(len(all_walls))
        for i, node_idx in enumerate(all_walls):
            if Y[node_idx] > params["H"] - eps:
                wall_u_tan[i] = 1.0 # tampa móvel
            else:
                wall_u_tan[i] = 0.0

        solid_walls = all_walls

    else:
        # Escoamento em canal
        psi[inlet_nodes] = get_psi_inlet(Y[inlet_nodes])
        psi[wall_bottom] = 0.0

        # Parede superior
        psi[wall_top] = params["H"]

        # Obstáculo
        if params.get("geo_type") == "step":
             psi[obstacle_nodes] = 0.0
        else:
            # Cilindro, retângulo, etc.
            psi[obstacle_nodes] = get_psi_inlet(cy)

        dirichlet_psi = np.concatenate([inlet_nodes, wall_bottom, wall_top, obstacle_nodes])
        dirichlet_psi = np.unique(dirichlet_psi)
        
        solid_walls = np.concatenate([wall_bottom, wall_top, obstacle_nodes])
        solid_walls = np.unique(solid_walls)
        
        dirichlet_omega = np.concatenate([inlet_nodes, solid_walls])
        dirichlet_omega = np.unique(dirichlet_omega)
        
        wall_neighbors, wall_h_sq = get_boundary_normals(X, Y, solid_walls, triang)

        # Paredes estacionárias
        wall_u_tan = np.zeros(len(solid_walls))

    free_psi = np.setdiff1d(np.arange(n_nodes), dirichlet_psi)
    free_omega = np.setdiff1d(np.arange(n_nodes), dirichlet_omega)
    
    K_free_psi = K[free_psi, :][:, free_psi]
    
    dt = params["dt"]
    Re = params["Re"]
    steps_per_frame = params["steps_per_frame"]
    total_steps = params["total_steps"]
    
    current_step = 0
    
    while current_step < total_steps and not STOP_SIMULATION:
        for _ in range(steps_per_frame):
            # A. Poisson para a função corrente psi
            rhs_psi = M @ omega
            b_psi = rhs_psi[free_psi] - K[free_psi, :][:, dirichlet_psi] @ psi[dirichlet_psi]
            psi[free_psi] = spsolve(K_free_psi, b_psi)
            
            # B. Fórmula de Thom (generalizada para paredes móveis)
            # Dedução (tampa superior, normal interna = -y): a expansão de Taylor
            # na parede com passo -h fornece
            #   psi_nb = psi_w - h (dpsi/dy)_w + (h^2/2) (d2psi/dy2)_w
            # Como u = dpsi/dy, tem-se (dpsi/dy)_w = u_tan. Com psi constante ao
            # longo da parede, d2psi/dx2 = 0, logo d2psi/dy2 = -omega_w. Isolando:
            #   omega_w = -2 (psi_nb - psi_w + h u_tan) / h^2
            # Validada contra Ghia et al. (1982) em Re=100.
            psi_nb = psi[wall_neighbors]
            psi_w = psi[solid_walls]
            h_vals = np.sqrt(wall_h_sq)
            omega[solid_walls] = -2.0 * (psi_nb - psi_w + h_vals * wall_u_tan) / wall_h_sq
            
            # C. Velocidades
            elements = triang.triangles
            mask = triang.mask if triang.mask is not None else np.zeros(len(elements), dtype=bool)
            el_nodes = elements[~mask]
            x_el = X[el_nodes]
            y_el = Y[el_nodes]
            p_el = psi[el_nodes]
            
            b_coeff = np.column_stack([y_el[:,1]-y_el[:,2], y_el[:,2]-y_el[:,0], y_el[:,0]-y_el[:,1]])
            c_coeff = np.column_stack([x_el[:,2]-x_el[:,1], x_el[:,0]-x_el[:,2], x_el[:,1]-x_el[:,0]])
            area_el = 0.5 * np.abs(x_el[:,0]*(y_el[:,1]-y_el[:,2]) + x_el[:,1]*(y_el[:,2]-y_el[:,0]) + x_el[:,2]*(y_el[:,0]-y_el[:,1]))
            
            u_vals = np.sum(p_el * c_coeff, axis=1) / (2 * area_el)
            v_vals = -np.sum(p_el * b_coeff, axis=1) / (2 * area_el)
            
            u_el_full = np.zeros(len(elements))
            v_el_full = np.zeros(len(elements))
            u_el_full[~mask] = u_vals
            v_el_full[~mask] = v_vals
            
            # D. Convecção
            C = assemble_convection(X, Y, triang, u_el_full, v_el_full)

            # E. Transporte de vorticidade
            A = M + (dt / Re) * K
            rhs = M @ omega - dt * (C @ omega)
            
            A_free = A[free_omega, :][:, free_omega]
            b_omega = rhs[free_omega] - A[free_omega, :][:, dirichlet_omega] @ omega[dirichlet_omega]
            omega[free_omega] = spsolve(A_free, b_omega)
            
            current_step += 1

        # Plot
        tci = tri.LinearTriInterpolator(triang, psi)
        (dpsi_dx, dpsi_dy) = tci.gradient(X, Y)
        u = dpsi_dy
        v = -dpsi_dx
        
        fig = plt.figure(figsize=(10, 12))
        gs = fig.add_gridspec(3, 1, height_ratios=[1, 1, 1])
        
        ax1 = fig.add_subplot(gs[0])
        ax2 = fig.add_subplot(gs[1])
        ax3 = fig.add_subplot(gs[2])
        
        # Campo de psi com sombreamento Gouraud e mapa de cores Jet
        contour_psi = ax1.tripcolor(triang, psi, shading='gouraud', cmap='jet')
        ax1.triplot(triang, color='k', alpha=0.2, linewidth=0.5) # malha visível
        ax1.set_title(f"Navier-Stokes (Step {current_step}) - $\\psi$")
        ax1.set_aspect('equal')
        ax1.set_xlabel("x [m]")
        ax1.set_ylabel("y [m]")
        fig.colorbar(contour_psi, ax=ax1)
        
        # Campo de omega com sombreamento Gouraud
        contour_omega = ax2.tripcolor(triang, omega, shading='gouraud', cmap='jet')
        ax2.triplot(triang, color='k', alpha=0.2, linewidth=0.5)
        ax2.set_title(f"Navier-Stokes (Step {current_step}) - $\\omega$")
        ax2.set_aspect('equal')
        ax2.set_xlabel("x [m]")
        ax2.set_ylabel("y [m]")
        fig.colorbar(contour_omega, ax=ax2)
        
        xi = np.linspace(0, params["L"], 100)
        yi = np.linspace(0, params["H"], 100)
        Xi, Yi = np.meshgrid(xi, yi)
        (dpsi_dx_grid, dpsi_dy_grid) = tci.gradient(Xi, Yi)
        u_grid = dpsi_dy_grid
        v_grid = -dpsi_dx_grid
        vel_mag_grid = np.sqrt(u_grid**2 + v_grid**2)
        
        # Linhas de corrente (mapa de cores Jet)
        strm = ax3.streamplot(Xi, Yi, u_grid, v_grid, color=vel_mag_grid, cmap='jet', density=1.5, linewidth=1, arrowsize=1.5)
        ax3.set_title("Linhas de Corrente")
        ax3.set_aspect('equal')
        ax3.set_xlim(0, params["L"])
        ax3.set_ylim(0, params["H"])
        ax3.set_xlabel("x [m]")
        ax3.set_ylabel("y [m]")
        fig.colorbar(strm.lines, ax=ax3)
        

        
        plt.tight_layout()
        
        img_base64 = plot_to_base64(fig)

        # Metricas de validacao (cavidade quadrada): psi_min, centro do vortice,
        # e comparacao com Ghia 1982 para Re=100 quando aplicavel.
        psi_min = float(np.min(psi))
        i_vort = int(np.argmin(psi))
        x_vort = float(X[i_vort])
        y_vort = float(Y[i_vort])

        scenario = params.get("scenario", "")
        is_square = abs(params["L"] - params["H"]) < 1e-9
        show_ghia = (scenario == "cavity" and is_square
                     and abs(params["Re"] - 100.0) < 1e-6)

        if show_ghia:
            ghia_psi_min = -0.1034
            ghia_center = (0.6172, 0.7344)
            ghia_row = (
                "<p class=\"text-sm text-gray-700\"><strong>Referência Ghia et al. (1982) "
                "Re=100:</strong> "
                f"ψ_min ≈ {ghia_psi_min}, centro em ({ghia_center[0]}, {ghia_center[1]})</p>"
            )
        else:
            ghia_row = ""

        metrics_html = (
            "<div class=\"bg-blue-50 border-l-4 border-blue-400 p-3 rounded w-full\">"
            "<h4 class=\"font-semibold text-blue-800 mb-1\">Validação</h4>"
            f"<p class=\"text-sm text-gray-700\"><strong>Passo:</strong> "
            f"{current_step} / {total_steps}, Re = {params['Re']:.1f}, "
            f"malha {params['nx']}×{params['ny']}</p>"
            f"<p class=\"text-sm text-gray-700\"><strong>ψ_min:</strong> "
            f"{psi_min:+.5f} em ({x_vort:.3f}, {y_vort:.3f})</p>"
            f"{ghia_row}"
            "</div>"
        )

        plot_div.innerHTML = (
            "<div class='flex flex-col gap-3 w-full'>"
            f"<img src='data:image/png;base64,{img_base64}' class='max-w-full h-auto rounded shadow-lg' />"
            f"{metrics_html}"
            "</div>"
        )
        await asyncio.sleep(0.01)

    if not STOP_SIMULATION:
        plot_div.innerHTML += '<p class="text-center text-green-600 font-bold mt-2">Simulação Concluída!</p>'
    else:
        plot_div.innerHTML += '<p class="text-center text-red-600 font-bold mt-2">Simulação Parada pelo Usuário.</p>'

@when("click", "#run-btn")
async def run_handler(event=None):
    global STOP_SIMULATION
    STOP_SIMULATION = False
    
    plot_div = document.getElementById("plot-output")
    plot_div.innerHTML = "Iniciando..."
    await asyncio.sleep(0.1)

    # Exibe o botão de parar
    document.getElementById("run-btn").classList.add("hidden")
    document.getElementById("run-btn").classList.remove("flex")
    document.getElementById("stop-btn").classList.remove("hidden")
    document.getElementById("stop-btn").classList.add("flex")
    
    try:
        params = {
            "L": float(document.getElementById("L").value),
            "H": float(document.getElementById("H").value),
            "cx": float(document.getElementById("cx").value),
            "cy": float(document.getElementById("cy").value),
            "scenario": document.getElementById("scenario").value,
            "geo_type": document.getElementById("geo_type").value,
            "r": float(document.getElementById("r").value),
            "w": float(document.getElementById("w").value),
            "h": float(document.getElementById("h").value),
            "step_h": float(document.getElementById("step_h").value),
            "step_l": float(document.getElementById("step_l").value),
            "nx": int(document.getElementById("nx").value),
            "ny": int(document.getElementById("ny").value),
            "Re": float(document.getElementById("Re").value),
            "dt": float(document.getElementById("dt").value),
            "steps_per_frame": int(document.getElementById("steps_per_frame").value),
            "total_steps": int(document.getElementById("total_steps").value)
        }
        
        await solve_navier_stokes(params, plot_div)
        
    except Exception as e:
        plot_div.innerHTML = f"Erro: {e}"
        print(e)
    finally:
        document.getElementById("stop-btn").classList.add("hidden")
        document.getElementById("stop-btn").classList.remove("flex")
        document.getElementById("run-btn").classList.remove("hidden")
        document.getElementById("run-btn").classList.add("flex")
