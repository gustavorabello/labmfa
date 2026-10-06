import numpy as np
import matplotlib.tri as tri
from scipy.sparse import lil_matrix, csr_matrix
import matplotlib.pyplot as plt
import io
import base64

# ==============================
# 1. Geração da Malha (Genérica)
# ==============================
def generate_mesh_generic(L, H, boundary_points, mask_function, cx, cy, nx, ny):
    """
    Gera malha triangular com um buraco definido por boundary_points.
    boundary_points: array (N, 2) com pontos da fronteira do obstáculo.
    mask_function: função f(x, y) -> bool que retorna True se o ponto deve ser MANTIDO (fora do obstáculo).
    """
    # 1. Grid de fundo
    x = np.linspace(0, L, nx)
    y = np.linspace(0, H, ny)
    dx = x[1] - x[0]
    dy = y[1] - y[0]
    h_mesh = min(dx, dy)
    
    Xg, Yg = np.meshgrid(x, y)
    X_flat = Xg.flatten()
    Y_flat = Yg.flatten()
    
    # 2. Nós da fronteira do obstáculo (passados como argumento)
    x_bound = boundary_points[:, 0]
    y_bound = boundary_points[:, 1]
    
    # 3. Filtrar nós do grid usando a função de máscara
    mask_keep = mask_function(X_flat, Y_flat)
    
    X_grid_valid = X_flat[mask_keep]
    Y_grid_valid = Y_flat[mask_keep]
    
    # 4. Combinar nós
    X = np.concatenate([X_grid_valid, x_bound])
    Y = np.concatenate([Y_grid_valid, y_bound])
    
    # 5. Triangulação
    triang = tri.Triangulation(X, Y)
    
    # 6. Mascarar triângulos espúrios (dentro do obstáculo):
    # remove-se o triângulo cujo centróide não passa na máscara de "manter".
    x_tri = X[triang.triangles].mean(axis=1)
    y_tri = Y[triang.triangles].mean(axis=1)

    triang.set_mask(~mask_function(x_tri, y_tri))
    
    return X, Y, triang

# ==============================
# 2. Matrizes MEF (Triângulo Linear)
# ==============================
def element_matrices(coords):
    x0, x1, x2 = coords
    detJ = (x1[0] - x0[0]) * (x2[1] - x0[1]) - (x2[0] - x0[0]) * (x1[1] - x0[1])
    area = 0.5 * abs(detJ)
    
    b = np.array([x1[1] - x2[1], x2[1] - x0[1], x0[1] - x1[1]])
    c = np.array([x2[0] - x1[0], x0[0] - x2[0], x1[0] - x0[0]])
    
    ke = (1.0 / (4 * area)) * (np.outer(b, b) + np.outer(c, c))
    me = (area / 12.0) * (np.ones((3, 3)) + np.eye(3))
    
    return ke, me, area, b, c

def assemble_matrices(X, Y, triang):
    n_nodes = len(X)
    K = lil_matrix((n_nodes, n_nodes))
    M = lil_matrix((n_nodes, n_nodes))
    
    elements = triang.triangles
    mask = triang.mask if triang.mask is not None else np.zeros(len(elements), dtype=bool)
    
    for i, el in enumerate(elements):
        if mask[i]: continue
        
        coords = np.column_stack((X[el], Y[el]))
        ke, me, area, b, c = element_matrices(coords)
        
        for row in range(3):
            for col in range(3):
                K[el[row], el[col]] += ke[row, col]
                M[el[row], el[col]] += me[row, col]
                
    return K.tocsr(), M.tocsr()

# ==============================
# 3. Helpers de Plotagem
# ==============================
def plot_to_base64(fig):
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")
