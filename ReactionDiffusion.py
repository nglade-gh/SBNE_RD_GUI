"""
ReactionDiffusion — solveur d'équation de réaction-diffusion sur tore.

Modèle :
    ∂MD1/∂t = D_MD1 ∇²MD1 − k_MD1_MD2 · MD1
    ∂MD2/∂t = D_MD2 ∇²MD2 + k_MD1_MD2 · MD1

avec dt = 1 s (1 itération = 1 s de temps simulé).

Schéma numérique : ADI (Peaceman-Rachford), d'ordre 2 en espace et en temps.
Chaque pas est décomposé en deux demi-pas implicites 1D (x puis y), chacun
résolu par un solveur Thomas adapté aux conditions aux limites périodiques
(tore) via Sherman-Morrison. Le terme de réaction linéaire (−k·MD1) est intégré
dans la matrice implicite ; le couplage MD1→MD2 utilise MD1^{n+1} (connu après
la première résolution) comme source dans l'équation de MD2.

Aucune dépendance externe : numpy seul.
"""

import numpy as np


def _thomas_vectorized(b_diag, a_sub, c_sup, r):
    """Solveur Thomas vectorisé sur m systèmes tridiagonaux indépendants.

    r : (m, n) — m systèmes de taille n, tous avec les mêmes coefficients.
    a_sub, c_sup, b_diag : scalaires (identiques pour tous les systèmes).
    """
    m, n = r.shape
    if n == 1:
        return r / b_diag
    cp = np.zeros((m, n - 1))
    dp = np.zeros((m, n))
    cp[:, 0] = c_sup / b_diag
    dp[:, 0] = r[:, 0] / b_diag
    for i in range(1, n - 1):
        mm = b_diag - a_sub * cp[:, i - 1]
        cp[:, i] = c_sup / mm
        dp[:, i] = (r[:, i] - a_sub * dp[:, i - 1]) / mm
    dp[:, n - 1] = (r[:, n - 1] - a_sub * dp[:, n - 2]) / (b_diag - a_sub * cp[:, n - 2])
    x = np.zeros((m, n))
    x[:, n - 1] = dp[:, n - 1]
    for i in range(n - 2, -1, -1):
        x[:, i] = dp[:, i] - cp[:, i] * x[:, i + 1]
    return x


def _solve_cyclic(b_diag, a_sub, c_sup, coin_top, coin_bottom, r, cache=None):
    """Résout M x = r où M est tridiagonale cyclique (tore).

    M = T + u1·v1ᵀ + u2·v2ᵀ avec :
      u1 = e₀,        v1 = coin_top·e_{n-1}   → coin M[0, n-1]
      u2 = e_{n-1},   v2 = coin_bottom·e₀    → coin M[n-1, 0]
    T est alors exactement tridiagonale (mêmes coefficients que M, coins retirés).

    Correction de rang 2 (Woodbury) :
      x = T⁻¹r − T⁻¹U·(I + VᵀT⁻¹U)⁻¹·VᵀT⁻¹r
    avec U = [u1, u2], V = [v1, v2].

    Z = T⁻¹U et A = (I + VᵀZ)⁻¹ ne dépendent que des coefficients (pas de r) :
    ils sont précalculés une seule fois et mis en cache.
    r : (m, n) — m systèmes indépendants de taille n.
    """
    m, n = r.shape
    if cache is None:
        # Pré-calcul (valable pour tous les systèmes de même taille)
        e0 = np.zeros(n); e0[0] = 1.0
        e1 = np.zeros(n); e1[n - 1] = 1.0
        z1 = _thomas_vectorized(b_diag, a_sub, c_sup, e0[None, :])[0]  # T⁻¹ e₀
        z2 = _thomas_vectorized(b_diag, a_sub, c_sup, e1[None, :])[0]  # T⁻¹ e_{n-1}
        # VᵀZ = [[coin_top·z1[n-1], coin_top·z2[n-1]],
        #         [coin_bottom·z1[0], coin_bottom·z2[0]]]
        A_mat = np.array([
            [1.0 + coin_top * z1[n - 1], coin_top * z2[n - 1]],
            [coin_bottom * z1[0], 1.0 + coin_bottom * z2[0]],
        ])
        Ainv = np.linalg.inv(A_mat)
        cache = (z1, z2, Ainv)

    z1, z2, Ainv = cache
    y = _thomas_vectorized(b_diag, a_sub, c_sup, r)
    w0 = coin_top * y[:, n - 1]      # v1ᵀ y
    w1 = coin_bottom * y[:, 0]       # v2ᵀ y
    c0 = Ainv[0, 0] * w0 + Ainv[0, 1] * w1
    c1 = Ainv[1, 0] * w0 + Ainv[1, 1] * w1
    return y - c0[:, None] * z1[None, :] - c1[:, None] * z2[None, :]


class ReactionDiffusion:
    """Grilles MD1/MD2 sur tore avec diffusion-réaction (ADI + Thomas cyclique)."""

    def __init__(self, width_px, height_px, dx, D_MD1=1000.0, D_MD2=1000.0,
                 k_MD1_MD2=0.01, dt=1.0):
        self.dx = float(dx)
        self.dt = float(dt)
        self.cols = max(1, int(np.ceil(width_px / self.dx)))
        self.rows = max(1, int(np.ceil(height_px / self.dx)))
        self.MD1 = np.zeros((self.rows, self.cols), dtype=np.float64)
        self.MD2 = np.zeros((self.rows, self.cols), dtype=np.float64)
        self.D_MD1 = float(D_MD1)
        self.D_MD2 = float(D_MD2)
        self.k = float(k_MD1_MD2)

        # Pré-calcul des coefficients Thomas (identiques sur toutes les lignes/colonnes)
        self._c1 = 0.5 * self.dt * self.D_MD1 / self.dx**2   # diffusion MD1
        self._c2 = 0.5 * self.dt * self.D_MD2 / self.dx**2   # diffusion MD2
        # Réaction MD1→MD2 : appliquée à raison de r_k/2 dans chaque demi-pas ADI
        # (x et y) pour totaliser exactement -k·MD1·dt par pas (sans double comptage).
        self._rk = 0.25 * self.dt * self.k

        # Pas de temps de simulation écoulé (utile pour diagnostics)
        self.sim_time = 0.0
        # Cache des corrections cycliques pour MD1 et MD2 (indépendant de rhs).
        # Deux tailles de systèmes : direction x (cols) et direction y (rows).
        self._cyc_cache1_x = self._build_cyclic_cache(self._c1, self._rk, self.cols)
        self._cyc_cache1_y = self._build_cyclic_cache(self._c1, self._rk, self.rows)
        self._cyc_cache2_x = self._build_cyclic_cache(self._c2, 0.0, self.cols)
        self._cyc_cache2_y = self._build_cyclic_cache(self._c2, 0.0, self.rows)

    # ------------------------------------------------------------------
    # Géométrie
    # ------------------------------------------------------------------
    def cell_of(self, x, y):
        """Position (px) → indices de case bornés à la grille."""
        cx = int(x // self.dx) % self.cols
        cy = int(y // self.dx) % self.rows
        return cx, cy

    # ------------------------------------------------------------------
    # Dépôts / consommation (granulaires, par case)
    # ------------------------------------------------------------------
    def add_deposit(self, x, y, quantity):
        """Dépose de la MD1 à la position (x, y) en px."""
        if quantity <= 0:
            return
        cx, cy = self.cell_of(x, y)
        self.MD1[cy, cx] += quantity

    def consume_md1(self, x, y, quantity):
        """Consomme de la MD1 à (x, y) ; retourne la quantité réellement prise."""
        if quantity <= 0:
            return 0.0
        cx, cy = self.cell_of(x, y)
        taken = max(0.0, min(self.MD1[cy, cx], quantity))
        self.MD1[cy, cx] -= taken
        return taken

    def consume_md2(self, x, y, quantity):
        """Consomme de la MD2 à (x, y) ; retourne la quantité réellement prise."""
        if quantity <= 0:
            return 0.0
        cx, cy = self.cell_of(x, y)
        taken = max(0.0, min(self.MD2[cy, cx], quantity))
        self.MD2[cy, cx] -= taken
        return taken

    def totals(self):
        """(total MD1, total MD2) sur toute la grille."""
        return float(self.MD1.sum()), float(self.MD2.sum())

    # ------------------------------------------------------------------
    # Pas de temps ADI
    # ------------------------------------------------------------------
    def _build_cyclic_cache(self, c_diff, r_k, n):
        """Précalcule les coefficients et les corrections cycliques (z1, z2, Ainv)
        pour une demi-pas ADI donnée, pour des systèmes de taille n.
        Indépendant de rhs — calculé une seule fois."""
        b_imp = 1.0 + 2.0 * c_diff + r_k
        off_imp = -c_diff
        coin = -c_diff
        # Résolution des deux systèmes élémentaires T z1 = e₀, T z2 = e_{n-1}
        e0 = np.zeros(n); e0[0] = 1.0
        e1 = np.zeros(n); e1[n - 1] = 1.0
        z1 = _thomas_vectorized(b_imp, off_imp, off_imp, e0[None, :])[0]
        z2 = _thomas_vectorized(b_imp, off_imp, off_imp, e1[None, :])[0]
        # A = I + Vᵀ Z (2×2)
        A_mat = np.array([
            [1.0 + coin * z1[n - 1], coin * z2[n - 1]],
            [coin * z1[0], 1.0 + coin * z2[0]],
        ])
        Ainv = np.linalg.inv(A_mat)
        return (b_imp, off_imp, coin, z1, z2, Ainv)

    def step(self):
        """Un pas de temps dt : diffusion + réaction MD1→MD2 (ADI Peaceman-Rachford).

        Conservation exacte : la perte totale de MD1 par réaction est mesurée
        et ajoutée intégralement à MD2 (répartie proportionnellement à MD1^{n+1})."""
        # --- MD1 : ∂MD1/∂t = D1∇²MD1 − k·MD1 (réaction incluse dans la matrice implicite) ---
        md1_before = float(self.MD1.sum())
        self._adi_step(self.MD1, self._cyc_cache1_x, self._cyc_cache1_y, source=None)
        md1_loss = md1_before - float(self.MD1.sum())  # perte due à la réaction (la diffusion conserve)

        # --- MD2 : ∂MD2/∂t = D2∇²MD2 + k·MD1 (diffusion seule) ---
        self._adi_step(self.MD2, self._cyc_cache2_x, self._cyc_cache2_y, source=None)

        # --- Couplage exact : la matière perdue par MD1 va intégralement dans MD2 ---
        if md1_loss > 0:
            total = float(self.MD1.sum())
            if total > 0:
                self.MD2 += md1_loss * self.MD1 / total
            else:
                self.MD2 += md1_loss / self.MD2.size
        self.sim_time += self.dt

    def _adi_step(self, u, cache_x, cache_y, source):
        """Un pas ADI complet (2 demi-pas 1D) pour l'équation ∂u/∂t = D∇²u + f(u) + s.

        cache_x/cache_y = (b_imp, off_imp, coin, z1, z2, Ainv) précalculés dans
        _build_cyclic_cache (respectivement systèmes de taille cols et rows).
        source = grille source constante au pas (ou None).
        """
        b_imp, off_imp, coin, z1, z2, Ainv = cache_x
        # Coefficients explicites (CN) déduits des implicites :
        #   b_imp = 1 + 2·c_diff + r_k, off_imp = −c_diff
        #   → b_exp = 1 − 2·c_diff − r_k = 2 − b_imp, off_exp = +c_diff = −off_imp
        b_exp = 2.0 - b_imp
        off_exp = -off_imp

        # --- Demi-pas x (chaque ligne = un système tridiagonal cyclique) ---
        rhs = b_exp * u + off_exp * (np.roll(u, 1, axis=1) + np.roll(u, -1, axis=1))
        # np.roll gère la périodicité ; rien à corriger pour les coins.
        if source is not None:
            rhs += self.dt * source * 0.5  # source répartie sur les 2 demi-pas x et y
        u_star = _solve_cyclic(b_imp, off_imp, off_imp, coin, coin, rhs, (z1, z2, Ainv))

        # --- Demi-pas y (chaque colonne = un système ; on transpose) ---
        b_imp_y, off_imp_y, coin_y, z1_y, z2_y, Ainv_y = cache_y
        b_exp_y = 2.0 - b_imp_y
        off_exp_y = -off_imp_y
        rhs_y = b_exp_y * u_star.T + off_exp_y * (np.roll(u_star.T, 1, axis=1) + np.roll(u_star.T, -1, axis=1))
        if source is not None:
            rhs_y += self.dt * source.T * 0.5
        u_new_T = _solve_cyclic(b_imp_y, off_imp_y, off_imp_y, coin_y, coin_y, rhs_y, (z1_y, z2_y, Ainv_y))
        u[:] = u_new_T.T

    # ------------------------------------------------------------------
    # Rendu
    # ------------------------------------------------------------------
    def render_surface(self, width_px, height_px, mode="BOTH"):
        """Retourne une surface pygame (rows×cols mise à l'échelle) de la matière.

        mode = "MD1"  : seule la MD1 (vert)
        mode = "MD2"  : seule la MD2 (rouge)
        mode = "BOTH" : mélange — MD1 en vert, MD2 en rouge (jaune/orange là où les deux coexistent)
        Intensité = valeur normalisée par le max courant (lissé pour éviter les scintillements).
        """
        # Max glissant pour une normalisation stable
        m1 = float(self.MD1.max()) if self.MD1.size else 0.0
        m2 = float(self.MD2.max()) if self.MD2.size else 0.0
        self._norm1 = max(getattr(self, '_norm1', 0) * 0.995, m1, 1e-9)
        self._norm2 = max(getattr(self, '_norm2', 0) * 0.995, m2, 1e-9)

        n1 = np.clip(self.MD1 / self._norm1, 0.0, 1.0) if mode != "MD2" else np.zeros_like(self.MD1)
        n2 = np.clip(self.MD2 / self._norm2, 0.0, 1.0) if mode != "MD1" else np.zeros_like(self.MD2)

        rgb = np.zeros((self.rows, self.cols, 3), dtype=np.uint8)
        rgb[:, :, 0] = (n2 * 255).astype(np.uint8)   # R = MD2
        rgb[:, :, 1] = (n1 * 255).astype(np.uint8)   # G = MD1

        # Conversion numpy → surface pygame (transposée : numpy est [row, col])
        import pygame
        surf = pygame.surfarray.make_surface(np.transpose(rgb, (1, 0, 2)))
        return pygame.transform.scale(surf, (width_px, height_px))
