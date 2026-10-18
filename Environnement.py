"""
SBNE_GUI — Simulation d'un écosystème évolutionnaire avec interface pygame_gui.

Lancement :
    python Environnement.py                  # avec fenêtre graphique
    python Environnement.py --headless       # sans fenêtre (calcul seul)
    python Environnement.py --max-steps 5000 # arrêt automatique
    python Environnement.py --seed 7         # surcharge de la graine
"""
import argparse
import json
import math
import os
import random
import sqlite3
import sys
import threading
import time
from datetime import datetime

import numpy as np
import pygame
import pygame_gui
from pygame_gui.elements import UIButton, UIHorizontalSlider, UITextEntryLine, UIPanel

from Agent import Agent
from ReactionDiffusion import ReactionDiffusion
from ExportData import save_nodes_influence
from GraphVisualisation import show_simulation_summary
from Interface import draw_dashboard, graphics_pause, show_graphics_off
from SpatialGrid import SpatialGrid
from evolution_tracker import save_network_state, close_all_connections
from GUIInterface import ConsoleLog, TabButton, LeftPanelTree, MenuOverlay
import pickle

# Paramètres d'origine (référence — sauvegardés dans ~/.sbne_rd/origin_params.json)
_ORIGINAL_PARAMS = {
    "TEST_NAME": "RD_MD1_MD2_reaction_diffusion",
    "SEED": 42,
    "NUM_AGENTS": 150,
    "MAX_ITERATIONS": 0,
    "BASE_ENERGY": 1000,
    "DIVISION_ENERGY": 1200,
    "PROBA_DELETION": 0.4,
    "PROBA_INSERTION": 0.4,
    "PROBA_EVOLUTION": 0.8,
    "VALEUR_MAX_POIDS": 5,
    "DISTANCE_VISION": 70,
    "VISION_ANGLE": 30,
    "COST_NEURON": 0.1,
    "COST_MOVE": 0.3,
    "COST_ROTATE": 0.1,
    "COST_EAT": 0.01,
    "COST_METABOLISM": 0.1,
    "CONSUME_QTY": 100.0,
    "MAX_SELECTED_SBN": 5,
    "DISPLAY_REFRESH_FPS": 30,
    "DX_GRID": 20.0,
    "D_MD1": 0.5,
    "D_MD2": 0.5,
    "K_MD1_MD2": 0.1,
    "NUM_MD1_INIT": 10,
    "MD1_INIT_QTY": 500.0,
    "CL_MD1_LEFT": "TORIC", "CL_MD1_RIGHT": "TORIC", "CL_MD1_TOP": "TORIC", "CL_MD1_BOTTOM": "TORIC",
    "CL_MD2_LEFT": "TORIC", "CL_MD2_RIGHT": "TORIC", "CL_MD2_TOP": "TORIC", "CL_MD2_BOTTOM": "TORIC",
    "CL_AGENTS_LEFT": "TORIC", "CL_AGENTS_RIGHT": "TORIC", "CL_AGENTS_TOP": "TORIC", "CL_AGENTS_BOTTOM": "TORIC",
    "CL_DIRICHLET_VALUE": 0.0,
}

_SBNE_DIR = os.path.expanduser("~/.sbne_rd")

# ============================================================================
# CONSTANTES DE LAYOUT
# ============================================================================
DASHBOARD_SIZE = 50
TOP_BAR_HEIGHT = 60
LEFT_PANEL_WIDTH = 300
RIGHT_PANEL_WIDTH = 340
CONSOLE_HEIGHT = 150

# ============================================================================
# COULEURS GUI
# ============================================================================
COLOR_BG = (10, 14, 22)
COLOR_PANEL_BG = (18, 22, 32)
COLOR_BORDER = (60, 70, 90)
COLOR_TEXT = (220, 225, 235)
COLOR_TEXT_DIM = (150, 160, 175)
COLOR_GREEN = (80, 200, 100)
COLOR_YELLOW = (230, 200, 60)
COLOR_RED = (230, 70, 70)
COLOR_BTN_NORMAL = (45, 55, 75)
COLOR_BTN_HOVER = (60, 75, 100)
COLOR_BTN_ACTIVE = (30, 120, 60)
COLOR_TAB_ACTIVE = (40, 90, 50)
COLOR_TAB_INACTIVE = (35, 42, 55)


# =============================================
# PARAMÈTRES DE LA SIMULATION
# =============================================
PARAMS = {
    "TEST_NAME": "RD_MD1_MD2_reaction_diffusion",
    "SEED": 42,
    "NUM_AGENTS": 150,
    "MAX_ITERATIONS": 0,
    "BASE_ENERGY": 1000,
    "DIVISION_ENERGY": 1200,
    "PROBA_DELETION": 0.4,
    "PROBA_INSERTION": 0.4,
    "PROBA_EVOLUTION": 0.8,
    "VALEUR_MAX_POIDS": 5,
    "DISTANCE_VISION": 70,
    "VISION_ANGLE": 30,
    "COST_NEURON": 0.1,
    "COST_MOVE": 0.3,
    "COST_ROTATE": 0.1,
    "COST_EAT": 0.01,
    "COST_METABOLISM": 0.1,
    "CONSUME_QTY": 100.0,  # matière (MD1/MD2) consommée par tentative de bouche
    "MAX_SELECTED_SBN": 5,
    "DISPLAY_REFRESH_FPS": 30,
    # --- Réaction-diffusion MD1/MD2 ---
    "DX_GRID": 20.0,        # pas de la grille de matière (px)
    "D_MD1": 0.5,           # coefficient de diffusion MD1 (px²/s)
    "D_MD2": 0.5,           # coefficient de diffusion MD2 (px²/s)
    "K_MD1_MD2": 0.1,       # vitesse de conversion MD1→MD2 (s⁻¹)
    "NUM_MD1_INIT": 10,     # dépôts initiaux de MD1
    "MD1_INIT_QTY": 500.0,  # quantité par dépôt initial (px²·énergie)
    # --- Conditions aux limites (TORIC / NEUMANN / DIRICHLET) ---
    # Pour chaque bord : MD1, MD2, agents. Format : "TORIC" | "NEUMANN" | "DIRICHLET"
    "CL_MD1_LEFT": "TORIC",
    "CL_MD1_RIGHT": "TORIC",
    "CL_MD1_TOP": "TORIC",
    "CL_MD1_BOTTOM": "TORIC",
    "CL_MD2_LEFT": "TORIC",
    "CL_MD2_RIGHT": "TORIC",
    "CL_MD2_TOP": "TORIC",
    "CL_MD2_BOTTOM": "TORIC",
    "CL_AGENTS_LEFT": "TORIC",   # TORIC ou NEUMANN (imperméable)
    "CL_AGENTS_RIGHT": "TORIC",
    "CL_AGENTS_TOP": "TORIC",
    "CL_AGENTS_BOTTOM": "TORIC",
    "CL_DIRICHLET_VALUE": 0.0,   # valeur fixe pour les CL Dirichlet
}


def init_database(db_path):
    """Crée les tables (et index) de la base SQLite si elles n'existent pas."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            id_agent TEXT PRIMARY KEY,
            id_parent TEXT,
            iteration_creation INTEGER,
            FOREIGN KEY (id_parent) REFERENCES agents(id_agent)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS networks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_agent TEXT,
            iteration INTEGER,
            network_data TEXT,
            network_hash TEXT,
            is_snapshot BOOLEAN,
            FOREIGN KEY (id_agent) REFERENCES agents(id_agent)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS commits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_agent TEXT,
            id_parent_commit INTEGER,
            iteration INTEGER,
            diff_data TEXT,
            message TEXT,
            FOREIGN KEY (id_agent) REFERENCES agents(id_agent)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_networks_agent_iter ON networks(id_agent, iteration)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_commits_agent_iter ON commits(id_agent, iteration)")
    conn.commit()
    conn.close()


class Simulation:
    """Contient tout l'état d'une simulation et orchestre logique / rendu / base de données."""

    def __init__(self, params, headless=False, max_steps=0, outdir=None):
        # --- PARAMÈTRES GÉNÉRAUX ---
        self.test_name = str(params.get("TEST_NAME", "Extinction_Initiale"))
        seed = params.get("SEED", 42)

        # --- MOTEUR ET AFFICHAGE ---
        self.width = int(params.get("WIDTH", 1280))
        self.height = int(params.get("HEIGHT", 720))
        self.n_iter = int(params.get("N_ITER", 1))
        self.fps = int(params.get("FPS", 60))
        self.display_fps = params.get("DISPLAY_FPS", 0)

        # --- PHYSIQUE ET CAPACITÉS DES AGENTS ---
        self.taille_agent = int(params.get("TAILLE_AGENT", 5))
        self.rotate_deg = params.get("ROTATE_DEG", 10)
        self.vision_angle = params.get("VISION_ANGLE", 45)
        self.distance_manger = int(params.get("DISTANCE_MANGER", self.taille_agent * 2))
        self.distance_vision = int(params.get("DISTANCE_VISION", self.distance_manger))

        # --- DYNAMIQUE DE POPULATION ET ÉNERGIE ---
        self.num_agents = int(params.get("NUM_AGENTS", 1000))
        self.base_energy = params.get("BASE_ENERGY", 100)
        self.division_energy = params.get("DIVISION_ENERGY", 600)
        self.cost_move = params.get("COST_MOVE", 1)
        self.cost_rotate = params.get("COST_ROTATE", 1)
        self.cost_eat = params.get("COST_EAT", 1)
        self.cost_neuron = params.get("COST_NEURON", 1)
        self.cost_metabolism = params.get("COST_METABOLISM", 0.05)
        # Quantité de matière (MD1/MD2) consommée par tentative de bouche
        self.consume_qty = float(params.get("CONSUME_QTY", 100.0))

        # --- RÉACTION-DIFFUSION MD1/MD2 ---
        dx_grid = float(params.get("DX_GRID", 20.0))
        D_MD1 = float(params.get("D_MD1", 0.5))
        D_MD2 = float(params.get("D_MD2", 0.5))
        k_md1_md2 = float(params.get("K_MD1_MD2", 0.1))
        self.field = ReactionDiffusion(self.width, self.height, dx_grid,
                                       D_MD1=D_MD1, D_MD2=D_MD2, k_MD1_MD2=k_md1_md2, dt=1.0)

        # --- Conditions aux limites (TORIC / NEUMANN / DIRICHLET) ---
        self.cl_dirichlet_value = float(params.get("CL_DIRICHLET_VALUE", 0.0))
        self.cl_agents_x_left = params.get("CL_AGENTS_LEFT", "TORIC")
        self.cl_agents_x_right = params.get("CL_AGENTS_RIGHT", "TORIC")
        self.cl_agents_y_top = params.get("CL_AGENTS_TOP", "TORIC")
        self.cl_agents_y_bottom = params.get("CL_AGENTS_BOTTOM", "TORIC")

        # --- MUTATIONS DU CERVEAU ---
        self.proba_deletion = params.get("PROBA_DELETION", 0.01)
        self.proba_insertion = params.get("PROBA_INSERTION", 0.02)
        self.proba_evolution = params.get("PROBA_EVOLUTION", 0.02)
        self.valeur_max_poids = params.get("VALEUR_MAX_POIDS", 3)

        # --- STATISTIQUE ET VISUALISATION ---
        self.tracking_id = params.get("TRACKING_ID", None)
        self.cell_size = self.distance_vision * 1.2

        # --- PARAMÈTRES GUI ---
        self.max_selected_sbn = int(params.get("MAX_SELECTED_SBN", 5))
        self.display_refresh_fps = int(params.get("DISPLAY_REFRESH_FPS", 30))
        self._render_frame_counter = 0

        random.seed(seed)
        np.random.seed(seed)

        # --- CHEMINS ---
        folder_name = outdir if outdir else datetime.now().strftime("%Y%m%d_%H%M%S")
        self.simulation_folder = os.path.join("simulations", folder_name)
        os.makedirs(self.simulation_folder, exist_ok=True)
        self.db_path = os.path.join(self.simulation_folder, "evolution.db")
        init_database(self.db_path)

        chemin_json = os.path.join(self.simulation_folder, "parameters.json")
        with open(chemin_json, "w", encoding="utf-8") as f:
            json.dump(params, f, indent=4)
        print(f"✅ Paramètres sauvegardés dans : {chemin_json}")

        # --- INITIALISATION PYGAME ---
        self.headless = headless
        self.max_steps = max_steps
        # Fenêtre étendue
        self.win_width = LEFT_PANEL_WIDTH + self.width + RIGHT_PANEL_WIDTH
        self.win_height = TOP_BAR_HEIGHT + DASHBOARD_SIZE + self.height + CONSOLE_HEIGHT
        pygame.init()
        self.screen = pygame.display.set_mode((int(self.win_width), int(self.win_height)))
        self.overlay = pygame.Surface((int(self.width), int(self.height + DASHBOARD_SIZE)), pygame.SRCALPHA)
        pygame.display.set_caption("Simulation SBN Evolution — SBNE_GUI")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 18)
        self.font_title = pygame.font.SysFont("Arial", 16, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 12)
        self.font_tiny = pygame.font.SysFont("Arial", 10)
        self.tracked_agent = None
        self.selected_agents = []  # [agent_id, ...]
        self.active_brain_tab = 0
        # Redimensionnement du panneau gauche
        self.left_panel_width = LEFT_PANEL_WIDTH
        self.world_rect = pygame.Rect(LEFT_PANEL_WIDTH, TOP_BAR_HEIGHT + DASHBOARD_SIZE,
                                     self.win_width - LEFT_PANEL_WIDTH - RIGHT_PANEL_WIDTH, self.height)
        self.resizing = False
        self.brain_nav_rects = {}
        # Onglets du panneau droit : "cerveaux" ou "stats" (clic pour changer)
        self.right_tab = "cerveaux"
        self.right_tab_rects = {}
        # Grille affichée : "MD1", "MD2" ou "BOTH" (touches 1/2/3)
        self.matter_display = "BOTH"

        # Threads séparés : simulation (thread dédié) + rendu/événements (thread principal)
        self.sim_lock = threading.Lock()  # protège agents/foods/stats pendant step() vs render()
        self.sim_running = False
        self.sim_thread = None

        # Console de log (toujours créé : _layout() le repositionne, et step()
        # l'avertit quand tous les agents meurent — même en headless)
        self.console = ConsoleLog(0, TOP_BAR_HEIGHT + DASHBOARD_SIZE + self.height,
                                  self.win_width, CONSOLE_HEIGHT, font_size=13)
        # Menu sauvegarde/restauration (créé toujours ; visible seulement en mode interactif)
        self.menu = MenuOverlay()

        # GUI
        self.ui_manager = None
        if not headless:
            self._setup_gui()

        # --- POPULATION INITIALE ---
        self._init_population()

        # --- CHAMP DE MATIÈRE INITIAL (dépôts MD1) ---
        for _ in range(int(params.get("NUM_MD1_INIT", 10))):
            x, y = random.randint(0, self.width), random.randint(0, self.height)
            self.field.add_deposit(x, y, float(params.get("MD1_INIT_QTY", 500.0)))

        # --- ÉTAT DE LA SIMULATION ---
        self.running = True
        self.show_graphics = not headless
        self.total_steps = 0
        self.new_id = self.num_agents
        # En mode interactif, la simulation démarre en pause ; en headless
        # (lanceur, tests), elle démarre immédiatement.
        self.is_paused = not headless
        self.temps_simule_ms = 0.0
        self.vision_cone = True
        self._stop_requested = False

        self.spatial_grid = SpatialGrid(self.width, self.height, self.cell_size)
        self.dist_manger_sq = self.distance_manger * self.distance_manger
        self.distance_vision_sq = self.distance_vision ** 2

        self.stats_steps = []
        self.stats_pop = []
        self.stats_size = []
        self.stats_energy = []
        self.stats_node_activated = []
        self.stats_global_energy = []

        if not headless:
            self.console.info(f"Simulation démarrée — {self.num_agents} agents, seed={seed}")

    # ========================================================================
    # INITIALISATION GUI
    # ========================================================================
    def _setup_gui(self):
        """Initialise pygame_gui et tous les widgets de contrôle."""
        theme = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gui_theme.json')
        self.ui_manager = pygame_gui.UIManager((int(self.win_width), int(self.win_height)), theme)

        # Zone du monde (offset x pour le panneau gauche)
        self.world_offset_x = LEFT_PANEL_WIDTH
        self.world_offset_y = TOP_BAR_HEIGHT + DASHBOARD_SIZE

        # --- Barre de contrôle : sous le dashboard (zone 50..110) ---
        btn_h = 36
        btn_y = TOP_BAR_HEIGHT + 8  # 68 : sous le dashboard (50) et au-dessus du monde (110)
        # Boutons icônes (40px) ; le texte est dessiné par-dessus dans render()
        self.btn_pause = UIButton(pygame.Rect((10, btn_y, 40, btn_h)), "", self.ui_manager)
        self.btn_restart = UIButton(pygame.Rect((60, btn_y, 40, btn_h)), "", self.ui_manager)
        self.btn_graphics = UIButton(pygame.Rect((110, btn_y, 40, btn_h)), "", self.ui_manager)
        # Bouton quitter : icône croix rouge, TOUT À DROITE de la barre (évite les clics erronés)
        self.btn_stop = UIButton(pygame.Rect((self.win_width - RIGHT_PANEL_WIDTH - 50, btn_y, 40, btn_h)),
                                  "", self.ui_manager)
        # Bouton MENU (sauvegarde / restauration)
        self.btn_menu = UIButton(pygame.Rect((self.win_width - RIGHT_PANEL_WIDTH - 100, btn_y, 40, btn_h)),
                                  "", self.ui_manager)

        # Slider pour la fréquence de mise à jour graphique
        self.slider_refresh = UIHorizontalSlider(
            pygame.Rect((170, btn_y, 140, btn_h)),
            self.display_refresh_fps, (1, 60), self.ui_manager)
        self.label_refresh = pygame_gui.elements.UILabel(
            pygame.Rect((320, btn_y, 130, btn_h)),
            f"Refresh: {self.display_refresh_fps} FPS",
            self.ui_manager)

        # --- Panneau gauche : arborescence (aligné sur le monde, PAS de débordement
        #     sur la toolbar qui occupe y = TOP_BAR_HEIGHT .. TOP_BAR_HEIGHT+btn_h+8) ---
        self.left_panel = LeftPanelTree(
            0, TOP_BAR_HEIGHT + DASHBOARD_SIZE, LEFT_PANEL_WIDTH,
            self.height,
            PARAMS, font_size=12,
            on_param_change=self._on_param_change)
        # Callback pour les changements de conditions aux limites
        self.left_panel.on_cl_change = self._on_cl_change
        # Synchronise les CL agents depuis PARAMS
        for side in ("LEFT", "RIGHT", "TOP", "BOTTOM"):
            self.left_panel._agents_cl[side] = PARAMS.get(f"CL_AGENTS_{side}", "TORIC")

        # --- Console en bas ---
        # (créée dans __init__ — repositionnée ici)

        # Positionne/redimensionne tous les éléments selon left_panel_width
        self._layout()

    # ------------------------------------------------------------------
    # Layout : repositionne tout selon la largeur courante du panneau gauche
    # ------------------------------------------------------------------
    def _layout(self):
        lw = self.left_panel_width
        self.world_offset_x = lw
        self.world_rect = pygame.Rect(lw, TOP_BAR_HEIGHT + DASHBOARD_SIZE,
                                     max(200, self.win_width - lw - RIGHT_PANEL_WIDTH), self.height)
        # Panneau gauche
        self.left_panel.update_rect(0, TOP_BAR_HEIGHT + DASHBOARD_SIZE, lw, self.height)
        # Barre de contrôle
        btn_h = 36
        btn_y = TOP_BAR_HEIGHT + 8
        self.btn_pause.set_position((10, btn_y))
        self.btn_restart.set_position((60, btn_y))
        self.btn_graphics.set_position((110, btn_y))
        self.btn_stop.set_position((self.win_width - RIGHT_PANEL_WIDTH - 50, btn_y))
        self.slider_refresh.set_position((170, btn_y))
        self.label_refresh.set_position((320, btn_y))
        # Panneau droit : les 2 onglets (CERVEAUX / STATISTIQUES) occupent toute
        # la hauteur du panneau droit (plus de stats_panel séparé).
        self.right_tab_rects = {}  # repositionné à chaque rendu
        # Console
        self.console.rect.update(0, TOP_BAR_HEIGHT + DASHBOARD_SIZE + self.height,
                                self.win_width, CONSOLE_HEIGHT)

    def _init_population(self):
        """Initialise la population d'agents."""
        self.agents = []
        for i in range(self.num_agents):
            agent = Agent(
                i,
                random.randint(0, self.width),
                random.randint(0, self.height),
                self.base_energy,
                self.rotate_deg,
                self.width,
                self.height,
                self.cost_rotate,
                self.cost_move,
                self.cost_eat,
                self.cost_neuron,
                self.cost_metabolism,
                self.consume_qty
            )
            self.agents.append(agent)
            save_network_state(
                db_path=self.db_path,
                agent_id=agent.id,
                parent_agent_id=None,
                sb_network=agent.sbn,
                iteration=0,
                is_snapshot=True,
                message="Agent initial"
            )

    # ========================================================================
    # GESTION DES ÉVÉNEMENTS
    # ========================================================================
    def handle_events(self):
        """Traite les événements pygame et pygame_gui (mode interactif uniquement)."""
        if self.headless:
            return  # pas de boucle d'événements en headless

        # Le menu consomme tous les événements quand il est visible
        for event in pygame.event.get():
            menu_result = self.menu.handle_event(event)
            if menu_result:
                if isinstance(menu_result, tuple) and menu_result[0] == "menu_action":
                    self._execute_menu_action(menu_result[1])
                return
            self._process_event(event)

        if self.ui_manager:
            self.ui_manager.update(1.0 / self.fps)

    def _process_event(self, event):
        """Traite un événement pygame pygame_gui."""
        mx, my = event.pos if hasattr(event, "pos") else (0, 0)

        # --- Redimensionnement du panneau gauche (bordure verticale) ---
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if (abs(mx - self.left_panel_width) <= 4 and
                    self.world_offset_y <= my < self.world_offset_y + self.height):
                self.resizing = True
        elif event.type == pygame.MOUSEMOTION:
            if self.resizing:
                self.left_panel_width = max(180, min(mx, self.win_width - RIGHT_PANEL_WIDTH - 400))
                self._layout()
            else:
                near = (abs(mx - self.left_panel_width) <= 4 and
                        self.world_offset_y <= my < self.world_offset_y + self.height)
                new_cursor = "size" if near else "arrow"
                if new_cursor != getattr(self, "_cursor_state", None):
                    try:
                        pygame.mouse.set_system_cursor(
                            pygame.SYSTEM_CURSOR_SIZEWE if near else pygame.SYSTEM_CURSOR_ARROW)
                        self._cursor_state = new_cursor
                    except Exception:
                        pass  # Wayland/dummy : curseurs système indisponibles
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.resizing = False

        # Le panneau gauche consomme ses propres clics (fold, scroll, édition…)
        lp_result = self.left_panel.handle_event(event, self.ui_manager)
        if lp_result == "PROPAGATE":
            lp_result = False  # clic validé pendant l'édition : on laisse passer l'événement
        if lp_result:
            if isinstance(lp_result, tuple) and lp_result[0] == "agent_toggle":
                self._toggle_agent_selection(lp_result[1])
            return

        # Onglets du panneau droit (CERVEAUX / STATISTIQUES) : clic = changer d'onglet
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for name, rect in self.right_tab_rects.items():
                if rect.collidepoint(event.pos):
                    self.right_tab = name.lower()
                    return

        # Icônes de navigation du panneau cerveau (rendu custom, pas pygame_gui)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for action, rect in self.brain_nav_rects.items():
                if rect.collidepoint(event.pos):
                    self._brain_nav(action)
                    break

        # Événements UI personnalisés pygame_gui (boutons, slider…)
        if self.ui_manager:
            self.ui_manager.process_events(event)

        if event.type == pygame.QUIT:
            if self.headless:
                return
            self.running = False

        elif event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.btn_pause:
                self.is_paused = not self.is_paused
                if self.is_paused:
                    self.console.info("Simulation mise en pause")
                else:
                    self.console.info("Simulation reprise")
            elif event.ui_element == self.btn_stop:
                self.console.info("Simulation arrêtée par l'utilisateur")
                self.running = False
            elif event.ui_element == self.btn_restart:
                self.console.info("Simulation réinitialisée")
                self._reset_simulation()
            elif event.ui_element == self.btn_graphics:
                self.show_graphics = not self.show_graphics
                self.console.info(f"Rendu graphique {'activé' if self.show_graphics else 'désactivé'}")
            elif event.ui_element == self.btn_menu:
                self.menu.toggle()

        elif event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
            if event.ui_element == self.slider_refresh:
                self.display_refresh_fps = int(event.value)
                self.label_refresh.set_text(f"Refresh: {self.display_refresh_fps} FPS")

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.is_paused = not self.is_paused
                if self.is_paused:
                    self.console.info("Simulation mise en pause")
                else:
                    self.console.info("Simulation reprise")
            elif event.key == pygame.K_g:
                self.show_graphics = not self.show_graphics
                if not self.show_graphics:
                    show_graphics_off(self.screen, self.font, self.width, self.height, self.is_paused, DASHBOARD_SIZE)
            elif event.key == pygame.K_v:
                self.vision_cone = not self.vision_cone
            elif event.key == pygame.K_1:
                self.matter_display = "MD1"
                self.console.info("Affichage matière : MD1 seule")
            elif event.key == pygame.K_2:
                self.matter_display = "MD2"
                self.console.info("Affichage matière : MD2 seule")
            elif event.key == pygame.K_3:
                self.matter_display = "BOTH"
                self.console.info("Affichage matière : MD1 + MD2 (mélange)")

        # Clic gauche : sélectionner un agent / Clic droit : désélectionner
        # (mapping window → coords monde, le monde est mis à l'échelle si panneau redimensionné)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3):
            if self.world_rect.collidepoint(mx, my):
                wx = (mx - self.world_rect.x) * self.width / self.world_rect.w
                wy = (my - self.world_rect.y) * self.height / self.world_rect.h
                self._handle_world_click(wx, wy, button=event.button)

    # ========================================================================
    # SAUVEGARDE / RESTAURATION (menu)
    # ========================================================================
    def _execute_menu_action(self, action):
        """Exécute une action du menu."""
        os.makedirs(_SBNE_DIR, exist_ok=True)
        try:
            if action == "save_sim":
                self._save_simulation(os.path.join(_SBNE_DIR, "simulation_save.pkl"))
            elif action == "restore_sim":
                self._restore_simulation(os.path.join(_SBNE_DIR, "simulation_save.pkl"))
            elif action == "save_default":
                self._save_params_json(PARAMS, os.path.join(_SBNE_DIR, "default_params.json"))
            elif action == "save_params":
                path = self.menu.input_text.strip() or os.path.join(_SBNE_DIR, "params_custom.json")
                self._save_params_json(PARAMS, path)
            elif action == "restore_default":
                self._load_params_json(os.path.join(_SBNE_DIR, "default_params.json"))
            elif action == "save_origin":
                self._save_params_json(_ORIGINAL_PARAMS, os.path.join(_SBNE_DIR, "origin_params.json"))
            elif action == "restore_origin":
                self._load_params_json(os.path.join(_SBNE_DIR, "origin_params.json"))
            elif action == "load_params":
                path = self.menu.input_text.strip()
                if path:
                    self._load_params_json(path)
                else:
                    self.menu.status_msg = "Chemin vide — tapez un chemin dans le champ."
            elif action == "close":
                self.menu.visible = False
        except Exception as e:
            self.console.error(f"Menu: {e}")
            self.menu.status_msg = f"Erreur: {e}"

    def _save_simulation(self, path):
        """Sauvegarde l'état complet (pickle) : agents, champ, stats, RNG."""
        state = {
            'agents': self.agents,
            'md1': self.field.MD1.copy(),
            'md2': self.field.MD2.copy(),
            'total_steps': self.total_steps,
            'new_id': self.new_id,
            'selected_agents': list(self.selected_agents),
            'active_brain_tab': self.active_brain_tab,
            'temps_simule_ms': self.temps_simule_ms,
            'stats_steps': self.stats_steps, 'stats_pop': self.stats_pop,
            'stats_size': self.stats_size, 'stats_energy': self.stats_energy,
            'stats_node_activated': self.stats_node_activated,
            'stats_global_energy': self.stats_global_energy,
            'random_state': random.getstate(),
            'np_state': np.random.get_state(),
        }
        with open(path, 'wb') as f:
            pickle.dump(state, f)
        self.console.info(f"Simulation sauvegardée → {path}")
        self.menu.status_msg = f"Sauvegardé: {os.path.basename(path)}"

    def _restore_simulation(self, path):
        """Restaure l'état complet depuis un pickle."""
        if not os.path.exists(path):
            self.menu.status_msg = f"Fichier introuvable: {path}"
            return
        with open(path, 'rb') as f:
            state = pickle.load(f)
        with self.sim_lock:
            self.agents = state['agents']
            self.field.MD1[:] = state['md1']
            self.field.MD2[:] = state['md2']
            self.total_steps = state['total_steps']
            self.new_id = state['new_id']
            self.selected_agents = state['selected_agents']
            self.active_brain_tab = state['active_brain_tab']
            self.temps_simule_ms = state['temps_simule_ms']
            self.stats_steps = state['stats_steps']
            self.stats_pop = state['stats_pop']
            self.stats_size = state['stats_size']
            self.stats_energy = state['stats_energy']
            self.stats_node_activated = state['stats_node_activated']
            self.stats_global_energy = state['stats_global_energy']
            random.setstate(state['random_state'])
            np.random.set_state(state['np_state'])
        self.console.info(f"Simulation restaurée ← {path}")
        self.menu.status_msg = f"Restauré: {os.path.basename(path)}"

    def _save_params_json(self, params_dict, path):
        """Sauvegarde des paramètres en JSON."""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(params_dict, f, indent=4)
        self.console.info(f"Paramètres sauvegardés → {path}")
        self.menu.status_msg = f"Sauvegardé: {os.path.basename(path)}"

    def _load_params_json(self, path):
        """Charge des paramètres depuis un JSON et met à jour PARAMS."""
        if not os.path.exists(path):
            self.menu.status_msg = f"Fichier introuvable: {path}"
            return
        with open(path, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        for k, v in loaded.items():
            PARAMS[k] = v
        # Synchronise les attributs calculés
        if "CL_DIRICHLET_VALUE" in loaded:
            self.cl_dirichlet_value = float(loaded["CL_DIRICHLET_VALUE"])
        # Met à jour le champ si les paramètres RD ont changé
        self.field = ReactionDiffusion(self.width, self.height,
                                       float(PARAMS.get("DX_GRID", 20.0)),
                                       D_MD1=float(PARAMS.get("D_MD1", 0.5)),
                                       D_MD2=float(PARAMS.get("D_MD2", 0.5)),
                                       k_MD1_MD2=float(PARAMS.get("K_MD1_MD2", 0.1)), dt=1.0)
        # Synchronise le panneau gauche (agents CL) — seulement en mode interactif
        if hasattr(self, 'left_panel'):
            for side in ("LEFT", "RIGHT", "TOP", "BOTTOM"):
                self.left_panel._agents_cl[side] = PARAMS.get(f"CL_AGENTS_{side}", "TORIC")
                setattr(self, f"cl_agents_{side.lower()}", PARAMS.get(f"CL_AGENTS_{side}", "TORIC"))
        self.console.info(f"Paramètres chargés ← {path}")
        self.menu.status_msg = f"Chargé: {os.path.basename(path)}"

    def _on_param_change(self, key, value):
        """Callback : un paramètre a été édité dans le panneau gauche.
        left_panel.params est PARAMS (même référence), donc la valeur y est déjà.
        Synchronise les attributs calculés (CL Dirichlet)."""
        self.console.info(f"Paramètre modifié : {key} = {value}")
        if key == "CL_DIRICHLET_VALUE":
            self.cl_dirichlet_value = float(value)

    def _on_cl_change(self, side, matter, value):
        """Callback : une condition aux limites a été changée dans l'explorateur."""
        if matter == "Agents":
            setattr(self, f"cl_agents_{side.lower()}", value)
        self.console.info(f"CL {side} {matter} → {value}")

    def _toggle_agent_selection(self, agent_id):
        """Bascule la sélection d'un agent (checkbox du panneau ou clic monde)."""
        if agent_id in self.selected_agents:
            self.selected_agents.remove(agent_id)
            self.console.info(f"Agent {agent_id} désélectionné")
        else:
            if len(self.selected_agents) >= self.max_selected_sbn:
                self.console.error(
                    "Il n'est pas possible de sélectionner davantage d'agents ; "
                    "modifiez la valeur du paramètre MAX_SELECTED_SBN")
                return
            self.selected_agents.append(agent_id)
            self.console.info(f"Agent {agent_id} sélectionné (onglet {len(self.selected_agents)})")

    def _handle_world_click(self, wx, wy, button=1):
        """Clic gauche (1) = sélectionner ; clic droit (3) = désélectionner."""
        rayon_sq = self.taille_agent * self.taille_agent
        clicked = None
        for agent in self.agents:
            if not agent.alive:
                continue
            dx = wx - agent.x
            dy = wy - agent.y
            if (dx * dx + dy * dy) <= rayon_sq:
                clicked = agent
                break

        if clicked is None:
            return

        if button == 3:  # Clic droit : désélectionner l'agent pointé
            if clicked.id in self.selected_agents:
                self.selected_agents.remove(clicked.id)
                self.console.info(f"Agent {clicked.id} désélectionné (clic droit)")
            else:
                self.console.info(f"Agent {clicked.id} n'est pas sélectionné")
        else:  # Clic gauche : toggle sélection (limité à MAX_SELECTED_SBN)
            if clicked.id in self.selected_agents:
                self.selected_agents.remove(clicked.id)
                self.console.info(f"Agent {clicked.id} désélectionné")
            else:
                if len(self.selected_agents) >= self.max_selected_sbn:
                    self.console.error(
                        "Il n'est pas possible de sélectionner davantage d'agents ; "
                        "modifiez la valeur du paramètre MAX_SELECTED_SBN")
                    return
                self.selected_agents.append(clicked.id)
                self.console.info(f"Agent {clicked.id} sélectionné (onglet {len(self.selected_agents)})")

    # ========================================================================
    # RÉINITIALISATION (bouton Restart)
    # ========================================================================
    def _reset_simulation(self):
        """Réinitialise l'état de la simulation sans toucher aux widgets GUI.
        Prend le lock : le thread sim peut être en train de muter les données."""
        self.sim_lock.acquire(timeout=3)
        try:
            close_all_connections()

            folder_name = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.simulation_folder = os.path.join("simulations", folder_name)
            os.makedirs(self.simulation_folder, exist_ok=True)
            self.db_path = os.path.join(self.simulation_folder, "evolution.db")
            init_database(self.db_path)

            chemin_json = os.path.join(self.simulation_folder, "parameters.json")
            params = {k: v for k, v in PARAMS.items()}
            with open(chemin_json, "w", encoding="utf-8") as f:
                json.dump(params, f, indent=4)

            self._init_population()
            # Réinitialise le champ de matière MD1/MD2 (dépôts initiaux)
            self.field = ReactionDiffusion(self.width, self.height,
                                           float(params.get("DX_GRID", 20.0)),
                                           D_MD1=float(params.get("D_MD1", 500.0)),
                                           D_MD2=float(params.get("D_MD2", 500.0)),
                                           k_MD1_MD2=float(params.get("K_MD1_MD2", 0.01)),
                                           dt=1.0)
            for _ in range(int(params.get("NUM_MD1_INIT", 10))):
                x, y = random.randint(0, self.width), random.randint(0, self.height)
                self.field.add_deposit(x, y, float(params.get("MD1_INIT_QTY", 500.0)))

            self.running = True
            self.total_steps = 0
            self.new_id = self.num_agents
            self.is_paused = False
            self.temps_simule_ms = 0.0
            self._stop_requested = False
            self.selected_agents.clear()
            self.active_brain_tab = 0
            self.stats_steps.clear()
            self.stats_pop.clear()
            self.stats_size.clear()
            self.stats_energy.clear()
            self.stats_node_activated.clear()
            self.stats_global_energy.clear()
            self.spatial_grid = SpatialGrid(self.width, self.height, self.cell_size)

            self.console.info(f"Simulation réinitialisée — {self.num_agents} agents, seed={PARAMS.get('SEED', 42)}")
        finally:
            self.sim_lock.release()

    # ========================================================================
    # LOGIQUE : UN PAS DE SIMULATION
    # ========================================================================
    def step(self):
        self.total_steps += 1
        new_enfants = []

        if self.total_steps % 50000 == 0:
            save_nodes_influence(self.agents, self.total_steps, self.simulation_folder)
            for agent in self.agents:
                save_network_state(
                    db_path=self.db_path,
                    agent_id=agent.id,
                    parent_agent_id=agent.parent.id if agent.parent else None,
                    sb_network=agent.sbn,
                    iteration=self.total_steps,
                    is_snapshot=True,
                    message="Snapshot périodique"
                )

        random.shuffle(self.agents)
        eat_intentions = {}
        self.spatial_grid.rebuild(self.agents)
        agents_cl = self._build_agents_cl()
        for agent in self.agents:
            agent.env_cl = agents_cl

        for agent in self.agents:
            if not agent.alive:
                continue
            neighbors = self.spatial_grid.neighbors(agent)
            agent.sense(neighbors, self.distance_vision_sq, self.dist_manger_sq, self.vision_angle)
            actions = agent.update(self.field, agent.vision_input, self.proba_evolution, self.valeur_max_poids)
            if actions is None:
                continue
            action_eat, action_eat_md1, action_eat_md2 = actions

            # Bouche agents : proie potentielle vue et mangeable
            if action_eat and (agent.proie_potentielle is not None):
                victim = agent.proie_potentielle
                if victim.alive and isinstance(victim, Agent):
                    eat_intentions[agent] = victim

            # Bouches MD1/MD2 : consommation directe de la matière
            if action_eat_md1:
                agent.eat_md1(self.field)
            if action_eat_md2:
                agent.eat_md2(self.field)

            if agent.energy >= self.division_energy:
                enfant = agent.division(self.new_id, self.vision_angle, self.proba_deletion, self.proba_insertion,
                                        self.valeur_max_poids, self.total_steps)
                self.new_id += 1
                new_enfants.append(enfant)
                save_network_state(
                    db_path=self.db_path,
                    agent_id=enfant.id,
                    parent_agent_id=agent.id,
                    sb_network=enfant.sbn,
                    iteration=self.total_steps,
                    is_snapshot=False,
                    message="Mutation à la naissance"
                )

        # Résolution des conflits de prédation (deux agents qui se mangent mutuellement)
        for agent, victim in eat_intentions.items():
            if not agent.alive or not victim.alive:
                continue
            if eat_intentions.get(victim) == agent:
                if agent.energy > victim.energy:
                    agent.eat(victim)
                elif agent.energy == victim.energy:
                    if random.random() > 0.5:
                        agent.eat(victim)
                    else:
                        victim.eat(agent)
                else:
                    victim.eat(agent)
            else:
                agent.eat(victim)

        # Diffusion-réaction de la matière MD1/MD2 (+ clamp des artefacts numériques négatifs)
        cl_md1 = self._build_cl('CL_MD1')
        cl_md2 = self._build_cl('CL_MD2')
        self.field.step(cl_md1=cl_md1, cl_md2=cl_md2)
        np.maximum(self.field.MD1, 0.0, out=self.field.MD1)
        np.maximum(self.field.MD2, 0.0, out=self.field.MD2)

        # CL agents : bloquer aux bords imperméables
        if self.cl_agents_x_left == "NEUMANN" or self.cl_agents_x_right == "NEUMANN" or \
           self.cl_agents_y_top == "NEUMANN" or self.cl_agents_y_bottom == "NEUMANN":
            for agent in self.agents:
                if self.cl_agents_x_left == "NEUMANN":
                    agent.x = max(agent.x, 1.0)
                if self.cl_agents_x_right == "NEUMANN":
                    agent.x = min(agent.x, self.width - 1.0)
                if self.cl_agents_y_top == "NEUMANN":
                    agent.y = max(agent.y, 1.0)
                if self.cl_agents_y_bottom == "NEUMANN":
                    agent.y = min(agent.y, self.height - 1.0)

        self.agents = [a for a in self.agents if a.alive]
        self.agents.extend(new_enfants)

    def _build_cl(self, prefix):
        """Construit le dict de conditions aux limites pour MD1 ou MD2."""
        v = self.cl_dirichlet_value
        def cl(side):
            val = PARAMS.get(f"{prefix}_{side}", "TORIC")
            if val == "DIRICHLET":
                return ("DIRICHLET", v)
            return val  # "TORIC" ou "NEUMANN"
        return {
            'x_left': cl('LEFT'), 'x_right': cl('RIGHT'),
            'y_top': cl('TOP'), 'y_bottom': cl('BOTTOM'),
        }

    def _build_agents_cl(self):
        """Construit le dict des CL agents ('x_left','x_right','y_top','y_bottom')."""
        return {
            'x_left': PARAMS.get('CL_AGENTS_LEFT', 'TORIC'),
            'x_right': PARAMS.get('CL_AGENTS_RIGHT', 'TORIC'),
            'y_top': PARAMS.get('CL_AGENTS_TOP', 'TORIC'),
            'y_bottom': PARAMS.get('CL_AGENTS_BOTTOM', 'TORIC'),
        }

        # Vérifier extinction → pause (pas d'arrêt : l'utilisateur peut
        # modifier les paramètres et relancer avec le bouton Restart)
        if len(self.agents) == 0:
            self.console.warning("Tous les agents sont morts — simulation en pause")
            self.is_paused = True

    # ========================================================================
    # RENDU
    # ========================================================================
    def render(self):
        """Rendu complet de la fenêtre (thread principal). Le lock protège la
        lecture des données pendant que le thread sim les met à jour."""
        with self.sim_lock:
            self._render_locked()

    def _render_locked(self):
        self.screen.fill(COLOR_BG)

        # --- Zone du monde (surface native 1280×720, mise à l'échelle en rendu) ---
        world_surface = pygame.Surface((self.width, self.height))
        world_surface.fill((0, 0, 0))
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 0))

        # --- Champ de matière (MD1 / MD2 / les deux), sous les agents ---
        matter_surf = self.field.render_surface(self.width, self.height, mode=self.matter_display)
        world_surface.blit(matter_surf, (0, 0))

        # Agents
        for agent in self.agents:
            is_tracked = agent.id in self.selected_agents
            if is_tracked:
                pos = (int(agent.x), int(agent.y))
                # Aura bleue autour des agents sélectionnés
                pygame.draw.circle(world_surface, (80, 160, 255), pos, self.taille_agent + 12, 2)
                pygame.draw.circle(world_surface, (80, 160, 255, 50), pos, self.taille_agent + 12, 6)
            if self.distance_vision > 20:
                agent.draw(world_surface, overlay, self.taille_agent, self.distance_vision, self.vision_angle,
                           self.base_energy, 0,
                           vision_cone=self.vision_cone, tracking=is_tracked)
            else:
                agent.draw(world_surface, world_surface, self.taille_agent, self.distance_vision, self.vision_angle,
                           self.base_energy, 0,
                           vision_cone=self.vision_cone, tracking=is_tracked)

        world_surface.blit(overlay, (0, 0))
        # Monde mis à l'échelle pour remplir la zone dispo (redimensionnement panneau gauche)
        world_scaled = pygame.transform.smoothscale(world_surface, self.world_rect.size)
        self.screen.blit(world_scaled, self.world_rect.topleft)

        # Cases vertes du panneau gauche = agents actuellement sélectionnés
        self.left_panel.update_selected(self.selected_agents)

        # --- Barre de contrôle pygame_gui (AVANT le dashboard pour éviter le chevauchement) ---
        if self.ui_manager:
            self.ui_manager.update(1.0 / self.fps)
            self.ui_manager.draw_ui(self.screen)
            self._draw_toolbar_icones()

        # --- Dashboard (par-dessus les boutons pour masquer le fond) ---
        pop = len(self.agents)
        mean_nodes = sum(a.sbn.num_nodes for a in self.agents) / max(1, pop)
        draw_dashboard(self.screen, self.clock, pop, self.total_steps, mean_nodes, PARAMS, self.width,
                       DASHBOARD_SIZE, self.font, self.temps_simule_ms)

        # --- Panneau gauche ---
        self.left_panel.update_agents(self.agents)
        self.left_panel.draw(self.screen)

        # --- Panneau droit : 2 onglets (CERVEAUX / STATISTIQUES) ---
        self._draw_right_panel()

        # --- Console ---
        self.console.draw(self.screen)

        # --- Menu (par-dessus tout) ---
        self.menu.draw(self.screen, self.font, self.font_small, self.font_title)

        pygame.display.flip()

    # ------------------------------------------------------------------
    # Icônes des boutons de la barre de contrôle
    # ------------------------------------------------------------------
    def _draw_toolbar_icones(self):
        """Dessine les icônes au centre des boutons (UIButton au texte vide)."""
        for rect, draw_fn in [
            (self.btn_pause.rect, self._icon_run_pause),
            (self.btn_restart.rect, self._icon_restart),
            (self.btn_graphics.rect, lambda s, cx, cy, p: self._icon_screen(s, cx, cy, enabled=self.show_graphics)),
            (self.btn_stop.rect, self._icon_stop),
            (self.btn_menu.rect, self._icon_menu),
        ]:
            draw_fn(self.screen, rect.centerx, rect.centery, self.is_paused)

    @staticmethod
    def _icon_run_pause(screen, cx, cy, is_paused):
        """Triangle vert (lecture) ou 2 barres jaunes verticales (pause)."""
        if not is_paused:
            # Lecture : triangle vert
            points = [(cx - 5, cy - 8), (cx - 5, cy + 8), (cx + 8, cy)]
            pygame.draw.polygon(screen, (60, 200, 80), points)
        else:
            # Pause : 2 barres jaunes
            pygame.draw.rect(screen, (230, 200, 60), (cx - 7, cy - 8, 5, 16))
            pygame.draw.rect(screen, (230, 200, 60), (cx + 2, cy - 8, 5, 16))

    @staticmethod
    def _icon_restart(screen, cx, cy, is_paused=False):
        """Flèche verte circulaire (retour sur elle-même)."""
        pygame.draw.arc(screen, (60, 200, 80), (cx - 8, cy - 8, 16, 16), 0.6, 5.2, 3)
        pygame.draw.polygon(screen, (60, 200, 80), [(cx + 7, cy - 7), (cx + 2, cy - 1), (cx + 11, cy - 1)])

    @staticmethod
    def _icon_screen(screen, cx, cy, is_paused=False, enabled=True):
        """Écran/monitor gris clair ; BARRÉ (croix rouge) quand rendu désactivé."""
        pygame.draw.rect(screen, (180, 190, 205), (cx - 9, cy - 7, 18, 12), 2)
        pygame.draw.line(screen, (180, 190, 205), (cx - 3, cy + 7), (cx + 3, cy + 7), 2)
        pygame.draw.line(screen, (180, 190, 205), (cx, cy + 5), (cx, cy + 8), 2)
        if not enabled:
            col = (230, 60, 60)
            pygame.draw.line(screen, col, (cx - 8, cy - 6), (cx + 8, cy + 6), 3)
            pygame.draw.line(screen, col, (cx + 8, cy - 6), (cx - 8, cy + 6), 3)

    @staticmethod
    def _icon_menu(screen, cx, cy, is_paused=False):
        """Menu : 3 barres horizontales (hamburger)."""
        col = (200, 210, 220)
        for i, dy in enumerate((-5, 0, 5)):
            pygame.draw.line(screen, col, (cx - 7, cy + dy), (cx + 7, cy + dy), 3)

    @staticmethod
    def _icon_stop(screen, cx, cy, is_paused=False):
        """Croix rouge (quitter)."""
        col = (230, 60, 60)
        t = 3
        pygame.draw.line(screen, col, (cx - 7, cy - 7), (cx + 7, cy + 7), t)
        pygame.draw.line(screen, col, (cx + 7, cy - 7), (cx - 7, cy + 7), t)

    def _draw_right_panel(self):
        """Panneau droit à 2 onglets sélectionnables : CERVEAUX et STATISTIQUES.
        Un clic sur un onglet affiche son contenu (jamais les deux en même temps)."""
        panel_x = self.win_width - RIGHT_PANEL_WIDTH
        panel_y = TOP_BAR_HEIGHT
        panel_h = TOP_BAR_HEIGHT + DASHBOARD_SIZE + self.height - panel_y
        content_top = panel_y + 30  # sous la barre d'onglets
        content_h = panel_y + panel_h - content_top

        pygame.draw.rect(self.screen, COLOR_PANEL_BG, (panel_x, panel_y, RIGHT_PANEL_WIDTH, panel_h))
        self.brain_nav_rects = {}

        # --- Barre d'onglets (2 boutons en haut du panneau droit) ---
        tab_w = (RIGHT_PANEL_WIDTH - 20) // 2
        for i, name in enumerate(("CERVEAUX", "STATS")):
            r = pygame.Rect(panel_x + 10 + i * (tab_w + 4), panel_y + 5, tab_w, 20)
            self.right_tab_rects[name] = r
            active = (self.right_tab == name.lower())
            pygame.draw.rect(self.screen, COLOR_TAB_ACTIVE if active else COLOR_TAB_INACTIVE,
                             r, border_radius=4)
            lbl = self.font.render(name, True, COLOR_TEXT if active else COLOR_TEXT_DIM)
            self.screen.blit(lbl, (r.x + 8, r.y + 3))

        # --- Contenu selon l'onglet actif ---
        if self.right_tab in ("cerveaux", "cerveau", "brains"):
            self._draw_brains_content(panel_x, content_top, content_h)
        else:
            self._draw_stats_content(panel_x, content_top, content_h)

    def _draw_brains_content(self, panel_x, top, h):
        """Contenu onglet CERVEAUX : liste sélectionnés, navigation, graphe SBN."""
        prev2 = pygame.Rect(panel_x + 8, top + 4, 16, 14)
        next2 = pygame.Rect(panel_x + RIGHT_PANEL_WIDTH - 24, top + 4, 16, 14)
        self._draw_triangle(self.screen, prev2.centerx, prev2.centery, "left", (170, 178, 190))
        self._draw_triangle(self.screen, next2.centerx, next2.centery, "right", (170, 178, 190))
        self.brain_nav_rects["prev2"] = prev2
        self.brain_nav_rects["next2"] = next2

        # Liste des agents sélectionnés (numéros ; l'affiché en ROUGE)
        ids = [str(i) for i in self.selected_agents]
        font_id = pygame.font.SysFont("Arial", 13)
        widths = [font_id.size(t)[0] for t in ids] or [0]
        gap = 10
        total_w = sum(widths) + gap * max(0, len(ids) - 1)
        x = panel_x + max(4, (RIGHT_PANEL_WIDTH - total_w) // 2)
        for i, t in enumerate(ids):
            color = COLOR_RED if i == self.active_brain_tab else COLOR_TEXT
            self.screen.blit(font_id.render(t, True, color), (x, top + 6))
            x += widths[i] + gap

        # Agent affiché : grand numéro + prev1/next1 gris de part et d'autre
        displayed = self.selected_agents[self.active_brain_tab] if self.selected_agents else None
        num_txt = str(displayed) if displayed is not None else "-"
        font_big = pygame.font.SysFont("Arial", 20, bold=True)
        tw = font_big.size(num_txt)[0]
        nx = panel_x + (RIGHT_PANEL_WIDTH - tw) // 2
        ny = top + 28
        prev1 = pygame.Rect(nx - 24, ny, 16, 16)
        next1 = pygame.Rect(nx + tw + 8, ny, 16, 16)
        self._draw_triangle(self.screen, prev1.centerx, prev1.centery, "left", (150, 158, 170))
        self._draw_triangle(self.screen, next1.centerx, next1.centery, "right", (150, 158, 170))
        self.brain_nav_rects["prev1"] = prev1
        self.brain_nav_rects["next1"] = next1
        color_big = COLOR_YELLOW if displayed is not None else COLOR_TEXT_DIM
        self.screen.blit(font_big.render(num_txt, True, color_big), (nx, ny))

        # Graphe SBN de l'agent affiché
        graph_top = ny + 30
        if displayed is not None:
            agent = next((a for a in self.agents if a.id == displayed), None)
            if agent:
                self._draw_sbn_graph(panel_x + 8, graph_top, RIGHT_PANEL_WIDTH - 16,
                                     self.win_height - CONSOLE_HEIGHT - 8 - graph_top, agent)
            else:
                surf = self.font_small.render("Agent mort", True, COLOR_YELLOW)
                self.screen.blit(surf, (panel_x + 10, graph_top + 4))
        else:
            surf = self.font_small.render("Aucun agent sélectionné", True, COLOR_TEXT_DIM)
            self.screen.blit(surf, (panel_x + 10, graph_top + 4))

    def _draw_stats_content(self, panel_x, top, h):
        """Contenu onglet STATISTIQUES : les stats dans la zone disponible."""
        pop = len(self.agents)
        md1_tot, md2_tot = self.field.totals()
        if pop > 0:
            mean_energy = sum(a.energy for a in self.agents) / pop
            mean_nodes = sum(a.sbn.num_nodes for a in self.agents) / pop
            max_age = max(a.step for a in self.agents)
            energy_agent = sum(a.energy for a in self.agents)
            global_e = energy_agent + md1_tot + md2_tot
        else:
            mean_energy = mean_nodes = max_age = global_e = energy_agent = 0
        stats = {
            "Population": pop,
            "Énergie moy.": f"{mean_energy:.0f}",
            "Noeuds moy.": f"{mean_nodes:.1f}",
            "Âge max": max_age,
            "Énergie agents": f"{energy_agent:.0f}",
            "MD1 tot.": f"{md1_tot:.0f}",
            "MD2 tot.": f"{md2_tot:.0f}",
            "Énergie globale": f"{global_e:.0f}",
            "Pas": self.total_steps,
            "Sélectionnés": len(self.selected_agents),
        }
        y = top + 6
        for key, value in stats.items():
            if y + 18 > top + h - 8:
                break
            lbl = self.font_small.render(f"{key}:", True, COLOR_TEXT_DIM)
            self.screen.blit(lbl, (panel_x + 10, y))
            val = self.font_small.render(str(value), True, COLOR_TEXT)
            self.screen.blit(val, (panel_x + 130, y))
            y += 20

    @staticmethod
    def _draw_triangle(screen, cx, cy, direction, color):
        """Triangle gris cliquable (left/right)."""
        s = 7
        if direction == "left":
            pts = [(cx + s, cy - s), (cx + s, cy + s), (cx - s, cy)]
        else:
            pts = [(cx - s, cy - s), (cx - s, cy + s), (cx + s, cy)]
        pygame.draw.polygon(screen, color, pts)

    def _brain_nav(self, action):
        """Navigation cerveau :
        - prev1/next1 : défiler la sélection parmi TOUS les agents vivants
          (depuis l'affiché), wrap ; le nouvel agent prend la place de l'affiché.
        - prev2/next2 : changer l'agent affiché parmi les sélectionnés."""
        if action in ("prev1", "next1"):
            alive_ids = sorted(a.id for a in self.agents)
            if not alive_ids:
                self.console.info("Aucun agent vivant")
                return
            if not self.selected_agents:
                self.console.info("Aucun agent sélectionné — cliquez d'abord sur un agent")
                return
            displayed = self.selected_agents[self.active_brain_tab]
            if displayed in alive_ids:
                idx = alive_ids.index(displayed)
            else:
                idx = 0 if action == "next1" else len(alive_ids) - 1
            step = 1 if action == "next1" else -1
            new_id = alive_ids[(idx + step) % len(alive_ids)]  # wrap aux frontières
            self.selected_agents[self.active_brain_tab] = new_id  # prend sa place
            self.console.info(f"Agent {new_id} sélectionné (remplace {displayed})")
        else:
            n = len(self.selected_agents)
            if n == 0:
                self.console.info("Aucun agent sélectionné")
                return
            step = 1 if action == "next2" else -1
            self.active_brain_tab = (self.active_brain_tab + step) % n
            self.console.info(f"Agent affiché : {self.selected_agents[self.active_brain_tab]}")

    def _draw_sbn_graph(self, x, y, w, h, agent):
        """Dessine le graphe SBN d'un agent dans le rectangle donné.
        Rayon et centre calculés pour que TOUT le graphe (nœuds, étiquettes,
        boucles sur l'arête du bas) soit visible sans débordement."""
        sbn = agent.sbn
        n = sbn.num_nodes

        if n == 0:
            surf = self.font_small.render("Aucun nœud", True, COLOR_TEXT_DIM)
            self.screen.blit(surf, (x + 5, y + 5))
            return

        # Fond délimitant la zone du graphe
        pygame.draw.rect(self.screen, (18, 24, 34), (x, y, w, h), border_radius=6)

        node_r = max(6, min(12, int(80 / n)))
        label_h = 14          # étiquettes au-dessus des nœuds
        loop_pad = node_r + 10  # boucles sous les nœuds
        margin_top = node_r + label_h + 4
        margin_bot = loop_pad + 4
        avail_w = w - 8
        avail_h = max(10, h - margin_top - margin_bot)
        radius = max(14, min(avail_w, avail_h) // 2 - 2)
        cx = x + w / 2
        cy = y + margin_top + avail_h / 2  # centre décalé : plus de place en bas (boucles)

        pos = []
        for i in range(n):
            ang = -math.pi / 2 + 2 * math.pi * i / n
            pos.append((cx + radius * math.cos(ang), cy + radius * math.sin(ang)))

        NAMES = {0: "E", 1: "M", 2: "M1", 3: "M2", 4: "F", 5: "R", 6: "R1", 7: "R2", 8: "R3", 9: "R4"}
        labels = [NAMES.get(sbn.true_ids[i], f"N{sbn.true_ids[i]}") for i in range(n)]
        is_organ = [sbn.true_ids[i] < 6 for i in range(n)]

        # Arêtes
        for i in range(n):
            for j in range(n):
                wgt = int(sbn.weights[i, j])
                if wgt == 0:
                    continue
                color = (80, 200, 90) if wgt > 0 else (225, 75, 75)
                e_width = min(1 + abs(wgt), 4)
                if i == j:
                    nx_, ny_ = pos[i]
                    pygame.draw.circle(self.screen, color, (int(nx_), int(ny_ + node_r + 8)), 4, e_width)
                else:
                    x1, y1 = pos[i]
                    x2, y2 = pos[j]
                    dx, dy = x2 - x1, y2 - y1
                    dist = math.hypot(dx, dy)
                    if dist < node_r * 2 + 4:
                        continue
                    ux, uy = dx / dist, dy / dist
                    sx = x1 + ux * (node_r + 2)
                    sy = y1 + uy * (node_r + 2)
                    ex = x2 - ux * (node_r + 6)
                    ey = y2 - uy * (node_r + 6)
                    pygame.draw.line(self.screen, color, (sx, sy), (ex, ey), e_width)

        # Nœuds
        for i in range(n):
            x_, y_ = pos[i]
            active = int(sbn.states[i]) == 1
            if is_organ[i]:
                base = (150, 200, 255) if active else (65, 105, 175)
            else:
                base = (250, 205, 70) if active else (95, 100, 118)
            pygame.draw.circle(self.screen, base, (int(x_), int(y_)), node_r)
            if active:
                pygame.draw.circle(self.screen, (255, 255, 255), (int(x_), int(y_)), node_r, 1)
            lbl = self.font_tiny.render(labels[i], True,
                                        (235, 240, 250) if is_organ[i] else (185, 195, 215))
            self.screen.blit(lbl, (int(x_ - lbl.get_width() // 2), int(y_ - node_r - 14)))

    # ========================================================================
    # STATISTIQUES
    # ========================================================================
    def collect_stats(self):
        if self.total_steps % 100 == 0 and len(self.agents) > 0:
            self.stats_steps.append(self.total_steps)
            self.stats_pop.append(len(self.agents))
            age_max = max(a.step for a in self.agents)
            energy_agent = sum(a.energy for a in self.agents)
            md1_tot, md2_tot = self.field.totals()
            energy_total = energy_agent + md1_tot + md2_tot
            moyenne_noeuds = sum(a.sbn.num_nodes for a in self.agents) / len(self.agents)
            moyenne_energie = sum(a.energy for a in self.agents) / len(self.agents)
            moyenne_noeuds_actif = sum(float(np.sum(a.sbn.states)) for a in self.agents) / len(self.agents)
            self.stats_size.append(moyenne_noeuds)
            self.stats_energy.append(moyenne_energie)
            self.stats_node_activated.append(moyenne_noeuds_actif)
            self.stats_global_energy.append(energy_total)

            if not self.show_graphics:
                secondes = int(self.temps_simule_ms) // 1000
                print(f"[{secondes}s] Step: {self.total_steps} | Pop: {len(self.agents)} | "
                      f"Énergie Moy: {moyenne_energie:.0f} | Noeuds Moy: {moyenne_noeuds:.1f} | Âge Max: {age_max} | "
                      f"MD1: {md1_tot:.0f} | MD2: {md2_tot:.0f}")

    # ========================================================================
    # BOUCLE PRINCIPALE
    # ========================================================================
    # ========================================================================
    # THREADS SÉPARÉS : simulation (thread dédié) + rendu (thread principal)
    # ========================================================================
    def _sim_loop(self):
        """Thread séparé : logique de simulation uniquement (AUCUNE opération
        SDL/rendu). Publie les données sous self.sim_lock pour le thread principal."""
        while self.sim_running:
            if not self.is_paused:
                with self.sim_lock:
                    for _ in range(self.n_iter):
                        t0 = time.perf_counter()
                        self.step()
                        self.collect_stats()
                        self.temps_simule_ms += (time.perf_counter() - t0) * 1000
                        if self.max_steps and self.total_steps >= self.max_steps:
                            self.sim_running = False
                            self.running = False  # arrête aussi la boucle principale
                            break
            # Laisse de la place au thread principal (rendu) entre les lots de pas
            time.sleep(0.001)

    def run(self):
        """Boucle principale (thread principal) : événements + rendu.
        La simulation tourne en parallèle dans self._sim_loop (thread dédié)."""
        # Démarre le thread de simulation
        self.sim_running = True
        self.sim_thread = threading.Thread(target=self._sim_loop, daemon=True, name="SBNE-sim")
        self.sim_thread.start()

        while self.running:
            self.handle_events()

            if self.show_graphics and not self.headless:
                # Throttle le rendu selon display_refresh_fps
                self._render_frame_counter += 1
                interval = max(1, int(self.fps / self.display_refresh_fps))
                if self._render_frame_counter % interval == 0:
                    self.render()

            self.clock.tick(self.fps)

        # Arrête proprement le thread de simulation
        self.sim_running = False
        if self.sim_thread is not None and self.sim_thread.is_alive():
            self.sim_thread.join(timeout=3)
        self.close()

    def close(self):
        """Sauvegarde des statistiques, ferme la base et pygame."""
        stats_path = os.path.join(self.simulation_folder, "stats.json")
        with open(stats_path, "w", encoding="utf-8") as f:
            json.dump({
                "total_steps": self.total_steps,
                "final_pop": len(self.agents),
                "final_md1": self.field.totals()[0],
                "final_md2": self.field.totals()[1],
                "stats_steps": self.stats_steps,
                "stats_pop": self.stats_pop,
                "stats_size": self.stats_size,
                "stats_energy": self.stats_energy,
                "stats_node_activated": self.stats_node_activated,
                "stats_global_energy": self.stats_global_energy
            }, f)
        print(f"✅ Statistiques sauvegardées dans : {stats_path}")

        close_all_connections()
        pygame.quit()

        summary_save_folder = os.path.join(self.simulation_folder, "simulation_summary.png")
        show_simulation_summary(self.stats_steps, self.stats_pop, self.stats_size, self.stats_energy,
                                self.stats_node_activated, self.stats_global_energy, summary_save_folder)


def _coerce_param(value):
    v = value.strip()
    low = v.lower()
    if low in ("true", "false"):
        return low == "true"
    try:
        return int(v)
    except ValueError:
        pass
    try:
        return float(v)
    except ValueError:
        pass
    return v


def parse_args():
    parser = argparse.ArgumentParser(description="Simulation SBN — écosystème évolutionnaire (SBNE_GUI)")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--param", action="append", default=[], metavar="CLE=VALEUR")
    parser.add_argument("--outdir", default=None)
    return parser.parse_args()


def main():
    args = parse_args()
    if args.seed is not None:
        PARAMS["SEED"] = args.seed
    for spec in args.param:
        if "=" not in spec:
            sys.exit(f"Format --param invalide : {spec!r} (attendu CLE=VALEUR)")
        key, _, value = spec.partition("=")
        key = key.strip()
        if key not in PARAMS:
            sys.exit(f"Paramètre inconnu : {key!r} (clés disponibles : {', '.join(sorted(PARAMS))})")
        PARAMS[key] = _coerce_param(value)
    if args.max_steps is not None:
        max_steps = args.max_steps
    else:
        max_steps = int(PARAMS.get("MAX_ITERATIONS", 0))
    if args.headless:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
    simulation = Simulation(PARAMS, headless=args.headless, max_steps=max_steps, outdir=args.outdir)
    simulation.run()


if __name__ == "__main__":
    main()
