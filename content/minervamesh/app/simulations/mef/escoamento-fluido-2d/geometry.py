import numpy as np

def get_cylinder(params):
    cx, cy, r = params["cx"], params["cy"], params["r"]
    n_pts = 100
    theta = np.linspace(0, 2*np.pi, n_pts, endpoint=False)
    x_bound = cx + r * np.cos(theta)
    y_bound = cy + r * np.sin(theta)
    boundary_pts = np.column_stack([x_bound, y_bound])
    
    def mask_func(x, y):
        return (x - cx)**2 + (y - cy)**2 > (r * 1.01)**2

    return boundary_pts, mask_func

def get_rectangle(params):
    cx, cy = params["cx"], params["cy"]
    w, h = params["w"], params["h"]
    
    perim = 2 * (w + h)
    n_w = int(100 * (w / perim))
    n_h = int(100 * (h / perim))
    n_w = max(5, n_w)
    n_h = max(5, n_h)
    
    hw = w / 2
    hh = h / 2
    
    x_b = np.linspace(cx - hw, cx + hw, n_w, endpoint=False)
    y_b = np.full_like(x_b, cy - hh)
    
    y_r = np.linspace(cy - hh, cy + hh, n_h, endpoint=False)
    x_r = np.full_like(y_r, cx + hw)
    
    x_t = np.linspace(cx + hw, cx - hw, n_w, endpoint=False)
    y_t = np.full_like(x_t, cy + hh)
    
    y_l = np.linspace(cy + hh, cy - hh, n_h, endpoint=False)
    x_l = np.full_like(y_l, cx - hw)
    
    x_bound = np.concatenate([x_b, x_r, x_t, x_l])
    y_bound = np.concatenate([y_b, y_r, y_t, y_l])
    boundary_pts = np.column_stack([x_bound, y_bound])
    
    def mask_func(x, y):
        buffer = 1.01
        return (np.abs(x - cx) > hw * buffer) | (np.abs(y - cy) > hh * buffer)
        
    return boundary_pts, mask_func

def get_step(params):
    # Degrau de face posterior (backward-facing step)
    # O degrau fica no canto inferior esquerdo.
    # Dimensões: step_h, step_l
    step_h = params["step_h"]
    step_l = params["step_l"]

    # Pontos da fronteira do degrau (formato em L)
    # 1. Topo do degrau (0, step_h) -> (step_l, step_h)
    # 2. Face posterior do degrau (step_l, step_h) -> (step_l, 0)

    n_pts = 50
    x_top = np.linspace(0, step_l, n_pts)
    y_top = np.full_like(x_top, step_h)
    
    y_back = np.linspace(step_h, 0, n_pts)
    x_back = np.full_like(y_back, step_l)

    # Concatena
    x_bound = np.concatenate([x_top, x_back])
    y_bound = np.concatenate([y_top, y_back])
    boundary_pts = np.column_stack([x_bound, y_bound])
    
    def mask_func(x, y):
        # Remove se x < step_l E y < step_h
        # Mantém se x >= step_l OU y >= step_h
        # Pequeno buffer para não remover os nós da fronteira
        # Queremos remover o bloco (0,0) até (step_l, step_h),
        # logo mantemos se NÃO (x < step_l-eps E y < step_h-eps)
        eps = 1e-3
        return ~((x < step_l - eps) & (y < step_h - eps))
        
    return boundary_pts, mask_func



def get_none(params):
    # Sem obstáculo (cavidade ou canal puro)
    return np.empty((0, 2)), lambda x, y: np.ones_like(x, dtype=bool)

def get_geometry(geo_type, params):
    if geo_type == "cylinder":
        return get_cylinder(params)
    elif geo_type == "rectangle":
        return get_rectangle(params)
    elif geo_type == "step":
        return get_step(params)
    else:
        return get_none(params)
