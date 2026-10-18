"""
GUIInterface — Interface graphique avancée pour SBNE_GUI.

Contient :
- ConsoleLog : console de log avec code couleur (vert/jaune/rouge)
- TabButton : onglet personnalisé (pygame_gui n'a pas de UITabContainer)
- LeftPanelTree : left panel tree (Parameters / Agents / Environment)
- StatsPanel : panneau de statistiques en direct
"""
import pygame
import pygame_gui
from pygame_gui.elements import UIButton, UIHorizontalSlider, UITextEntryLine, UIPanel, UIScrollingContainer

# ============================================================================
# COULEURS
# ============================================================================
COLOR_BG_DARK = (15, 18, 25)
COLOR_BG_PANEL = (25, 30, 40)
COLOR_BG_HEADER = (35, 42, 55)
COLOR_BORDER = (60, 70, 90)
COLOR_TEXT = (220, 225, 235)
COLOR_TEXT_DIM = (150, 160, 175)
COLOR_GREEN = (80, 200, 100)
COLOR_YELLOW = (230, 200, 60)
COLOR_RED = (230, 70, 70)
COLOR_BUTTON_NORMAL = (45, 55, 75)
COLOR_BUTTON_HOVER = (60, 75, 100)
COLOR_BUTTON_ACTIVE = (30, 120, 60)
COLOR_TAB_ACTIVE = (40, 90, 50)
COLOR_TAB_INACTIVE = (35, 42, 55)
COLOR_SLIDER_BG = (40, 45, 55)


# ============================================================================
# CONSOLE DE LOG
# ============================================================================
class ConsoleLog:
    """Console de log en bas de la fenêtre avec code couleur par gravité."""

    def __init__(self, x, y, w, h, font_size=13, max_messages=200):
        self.rect = pygame.Rect(x, y, w, h)
        self.font = pygame.font.SysFont("monospace", font_size)
        self.max_messages = max_messages
        self.messages = []  # (texte, couleur)
        self.padding = 8
        self.line_height = font_size + 4

    def log(self, texte, couleur=COLOR_GREEN):
        """Ajoute un message à la console."""
        self.messages.append((texte, couleur))
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]

    def info(self, texte):
        self.log(texte, COLOR_GREEN)

    def warning(self, texte):
        self.log(texte, COLOR_YELLOW)

    def error(self, texte):
        self.log(texte, COLOR_RED)

    def handle_event(self, event):
        """Gère le scroll de la console (molette souris)."""
        if event.type == pygame.MOUSEWHEEL and self.rect.collidepoint(event.pos):
            return True
        return False

    def draw(self, screen):
        """Dessine la console de log."""
        # Fond
        pygame.draw.rect(screen, COLOR_BG_DARK, self.rect)
        pygame.draw.line(screen, COLOR_BORDER, (self.rect.x, self.rect.y),
                         (self.rect.right, self.rect.y), 2)

        # Titre
        title = self.font.render("CONSOLE", True, COLOR_TEXT_DIM)
        screen.blit(title, (self.rect.x + self.padding, self.rect.y + 4))

        # Messages visibles
        visible_h = self.rect.h - 20
        max_visible = visible_h // self.line_height
        start = max(0, len(self.messages) - max_visible)

        y = self.rect.y + 18
        for texte, couleur in self.messages[start:]:
            if y + self.line_height > self.rect.bottom - 4:
                break
            # Horodatage simplié : juste le texte
            surface = self.font.render(texte, True, couleur)
            screen.blit(surface, (self.rect.x + self.padding, y))
            y += self.line_height

        # Indicateur de scroll si nécessaire
        if len(self.messages) > max_visible:
            indicator = self.font.render(f"↑ {len(self.messages) - max_visible} hidden messages", True, COLOR_TEXT_DIM)
            screen.blit(indicator, (self.rect.right - indicator.get_width() - self.padding, self.rect.y + 4))


# ============================================================================
# ONGLET PERSONNALISÉ
# ============================================================================
class TabButton:
    """Onglet cliquable personnalisé (remplace UITabContainer absent de pygame_gui 0.6.9)."""

    def __init__(self, x, y, w, h, text, font_size=13):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.font = pygame.font.SysFont("Arial", font_size)
        self.active = False
        self.hovered = False

    def handle_event(self, event):
        """Retourne True si l'onglet a été cliqué."""
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    def draw(self, screen):
        """Dessine l'onglet."""
        if self.active:
            color = COLOR_TAB_ACTIVE
            text_color = (255, 255, 255)
        elif self.hovered:
            color = COLOR_BUTTON_HOVER
            text_color = COLOR_TEXT
        else:
            color = COLOR_TAB_INACTIVE
            text_color = COLOR_TEXT_DIM

        pygame.draw.rect(screen, color, self.rect, border_radius=4)
        pygame.draw.rect(screen, COLOR_BORDER, self.rect, 1, border_radius=4)

        surface = self.font.render(self.text, True, text_color)
        tx = self.rect.x + (self.rect.w - surface.get_width()) // 2
        ty = self.rect.y + (self.rect.h - surface.get_height()) // 2
        screen.blit(surface, (tx, ty))


# ============================================================================
# PANNEAU STATS
# ============================================================================
class StatsPanel:
    """Panneau de statistiques en direct dans le panneau droit."""

    def __init__(self, x, y, w, h, font_size=14):
        self.rect = pygame.Rect(x, y, w, h)
        self.font = pygame.font.SysFont("Arial", font_size)
        self.font_title = pygame.font.SysFont("Arial", font_size + 2, bold=True)
        self.stats = {}

    def update(self, stats_dict):
        self.stats = stats_dict

    def draw(self, screen):
        """Dessine le panneau stats."""
        pygame.draw.rect(screen, COLOR_BG_PANEL, self.rect)
        pygame.draw.line(screen, COLOR_BORDER, (self.rect.x, self.rect.y),
                         (self.rect.right, self.rect.y), 2)

        title = self.font_title.render("STATISTIQUES", True, COLOR_TEXT)
        screen.blit(title, (self.rect.x + 10, self.rect.y + 8))

        y = self.rect.y + 32
        for key, value in self.stats.items():
            if y + self.font.get_height() > self.rect.bottom - 8:
                break
            label = self.font.render(f"{key}:", True, COLOR_TEXT_DIM)
            screen.blit(label, (self.rect.x + 10, y))
            val = self.font.render(str(value), True, COLOR_TEXT)
            screen.blit(val, (self.rect.x + 140, y))
            y += self.font.get_height() + 6


# ============================================================================
# MENU SAUVEGARDE / RESTAURATION
# ============================================================================
class MenuOverlay:
    """Menu de sauvegarde/restauration affiché par-dessus la fenêtre."""

    def __init__(self):
        self.visible = False
        self.buttons = []       # (rect, label, action_id)
        self.input_rect = None  # champ de saisie de chemin
        self.input_text = ""
        self.input_active = False
        self.status_msg = ""

    def toggle(self):
        self.visible = not self.visible

    def show(self):
        self.visible = True

    def handle_event(self, event):
        """Retourne True si l'événement a été consommé."""
        if not self.visible:
            return False
        if event.type == pygame.KEYDOWN:
            if self.input_active:
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.input_active = False
                elif event.key == pygame.K_ESCAPE:
                    self.input_active = False
                elif event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                elif event.unicode and event.unicode.isprintable():
                    self.input_text += event.unicode
                return True
            if event.key == pygame.K_ESCAPE:
                self.visible = False
                return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.input_rect and self.input_rect.collidepoint(event.pos):
                self.input_active = True
                return True
            for rect, _label, action in self.buttons:
                if rect.collidepoint(event.pos):
                    return ("menu_action", action)
            # Clic en dehors du menu → fermer
            self.visible = False
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            self.visible = False
            return True
        return True  # consomme tous les événements quand visible

    def draw(self, screen, font, font_small, font_title):
        """Dessine le menu centré. Retourne la liste des actions à exécuter."""
        if not self.visible:
            return []
        w, h = screen.get_size()
        panel_w, panel_h = 460, 420
        px, py = (w - panel_w) // 2, (h - panel_h) // 2
        pygame.draw.rect(screen, (15, 20, 30), (px, py, panel_w, panel_h), border_radius=8)
        pygame.draw.rect(screen, COLOR_BORDER, (px, py, panel_w, panel_h), 2, border_radius=8)
        screen.blit(font_title.render("MENU — Sauvegarde / Restauration", True, COLOR_TEXT),
                    (px + 16, py + 10))

        actions = [
            ("save_sim", "Save simulation (pickle)"),
            ("restore_sim", "Restore simulation"),
            ("save_default", "Save parameters as default"),
            ("save_params", "Save parameters to file"),
            ("restore_default", "Restore default parameters"),
            ("save_origin", "Save original parameters"),
            ("restore_origin", "Restore original parameters"),
            ("load_params", "Load parameters file"),
            ("close", "Close menu"),
        ]
        self.buttons = []
        y = py + 40
        for action_id, label in actions:
            rect = pygame.Rect(px + 16, y, panel_w - 32, 28)
            hover = rect.collidepoint(pygame.mouse.get_pos())
            pygame.draw.rect(screen, (30, 38, 55) if hover else (25, 30, 45), rect, border_radius=3)
            screen.blit(font_small.render(label, True, COLOR_TEXT), (px + 24, y + 4))
            self.buttons.append((rect, label, action_id))
            y += 32

        # Champ de saisie de chemin
        self.input_rect = pygame.Rect(px + 16, y + 8, panel_w - 32, 24)
        pygame.draw.rect(screen, (20, 26, 40) if not self.input_active else (30, 40, 60),
                         self.input_rect, border_radius=3)
        txt = self.input_text + ("|" if self.input_active else "")
        screen.blit(font_small.render(txt, True, COLOR_TEXT), (self.input_rect.x + 6, self.input_rect.y + 3))

        if self.status_msg:
            screen.blit(font_small.render(self.status_msg, True, COLOR_YELLOW), (px + 16, py + 40))
        return []


# ============================================================================
# ARBORESCENCE GAUCHE
# ============================================================================
class LeftPanelTree:
    """Left panel: collapsible tree (Parameters / Agents / Environment),
    vertical scrollbar (click + drag + wheel), click-to-edit parameters
    (Enter = validate, Escape = cancel)."""

    def __init__(self, x, y, w, h, params_dict, font_size=12, on_param_change=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.font = pygame.font.SysFont("Arial", font_size)                  # titres / headers
        self.font_small = pygame.font.SysFont("Arial", max(8, font_size - 3))  # params & agents (half size)
        self.font_title = pygame.font.SysFont("Arial", font_size + 2, bold=True)
        self.params = params_dict
        self.on_param_change = on_param_change  # callback(cle, nouvelle_valeur)
        self.selected_ids = set()  # ids sélectionnés (checkbox verts)

        self.sections = {
            "Parameters": {"expanded": True, "items": []},
            "Agents": {"expanded": False, "items": []},
            "Environment": {"expanded": False, "items": []},
        }

        # Scroll
        self.scroll_y = 0
        self.scroll_max = 0
        self.scrollbar_rect = None
        self.scrollbar_dragging = False
        self._thumb_h = 16

        # Édition de paramètres (champ actif)
        self.editing_key = None
        self.editing_text = ""

        # Zones cliquables (remplies au draw)
        self.section_headers = {}
        self.param_value_rects = {}
        self.agent_checkboxes = []
        self.cl_buttons = {}       # (side, matter) -> rect
        self.wall_buttons = {}     # side -> rect (AGENT_STOP/AGENT_REBOUNCE)
        self._agents_cl = {}       # side -> "TORIC" | "SOLID"
        self.on_cl_change = None    # callback(side, matter, nouvelle_valeur)

        # Onglets du panneau gauche : 'params' (défaut) ou 'agents'
        self.active_tab = 'params'
        self.tab_rects = {}        # 'params'/'agents' -> rect

        # Parameters tab: collapsible sub-sections
        self.param_groups = {
            "Simulation":  ["TEST_NAME", "SEED", "MAX_ITERATIONS", "DISPLAY_REFRESH_FPS", "MAX_SELECTED_SBN"],
            "Agents":      ["NUM_AGENTS", "BASE_ENERGY", "DIVISION_ENERGY", "DISTANCE_VISION", "VISION_ANGLE",
                            "CONSUME_QTY", "VALEUR_MAX_POIDS", "COST_NEURON", "COST_MOVE", "COST_ROTATE",
                            "COST_EAT", "COST_METABOLISM"],
            "Evolution":   ["PROBA_EVOLUTION", "PROBA_INSERTION", "PROBA_DELETION"],
            "Environment": ["DX_GRID", "NUM_MD1_INIT", "MD1_INIT_QTY", "D_MD1", "D_MD2", "K_MD1_MD2"],
        }
        self.param_groups_expanded = {name: True for name in self.param_groups}

    def update_rect(self, x, y, w, h):
        """Repositionne/redimensionne le panneau (redimensionnement utilisateur)."""
        self.rect = pygame.Rect(x, y, w, h)

    # ------------------------------------------------------------------
    # Hauteur de contenu (pour le scrollbar)
    # ------------------------------------------------------------------
    # Nombre max d'agents affichés dans le panneau (évite un contenu trop long)
    _MAX_AGENTS_DISPLAY = 40

    def _content_height(self):
        """Hauteur de contenu selon l'onglet actif."""
        row_h = 20
        if self.active_tab == 'agents':
            n = min(len(self.sections["Agents"]["items"]), self._MAX_AGENTS_DISPLAY)
            h = 18 * max(1, n)
            if len(self.sections["Agents"]["items"]) > self._MAX_AGENTS_DISPLAY:
                h += 18
            return h
        # Parameters tab: collapsible sub-sections
        h = 0
        for group_name, keys in self.param_groups.items():
            h += 22 + 2  # header
            if not self.param_groups_expanded[group_name]:
                continue
            if group_name == "Environment":
                h += row_h * len(keys) + 4
                # Matter BC: 4 sides x (label + 2 MD1/MD2 buttons + optional Dirichlet value)
                # Agent BC: 4 sides x (label + 1 button + optional wall)
                h += 4 * (row_h + 2 * row_h + row_h + 2) + 4 * (row_h + row_h + row_h + 2)
            else:
                h += row_h * len(keys) + 4
        return h

    # ------------------------------------------------------------------
    # Événements
    # ------------------------------------------------------------------
    def handle_event(self, event, ui_manager):
        """Retourne True si l'événement a été consommé par le panneau."""
        # Recalcule scroll_max pour l'onglet actif (un onglet vient peut-être de changer)
        self.scroll_max = max(0, self._content_height() - (self.rect.h - 56))

        # --- Scrollbar : drag du curseur / clic sur la piste ---
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.scrollbar_rect and self.scrollbar_rect.collidepoint(event.pos):
                self.scrollbar_dragging = True
                self._drag_scroll(event.pos[1])
                return True
            track = self._track_rect()
            if track and track.collidepoint(event.pos) and self.scroll_max > 0:
                self._jump_scroll(event.pos[1])
                return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.scrollbar_dragging:
                self.scrollbar_dragging = False
        if event.type == pygame.MOUSEMOTION and self.scrollbar_dragging:
            self._drag_scroll(event.pos[1])
            return True

        # --- Molette dans le panneau ---
        if event.type == pygame.MOUSEWHEEL:
            pos = event.pos if hasattr(event, "pos") else pygame.mouse.get_pos()
            if self.rect.collidepoint(pos):
                self.scroll_y = max(0, min(self.scroll_max, self.scroll_y - event.y * 22))
                return True

        # --- Saisie du champ d'édition actif ---
        if self.editing_key is not None:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):  # Entrée OU pavé numérique
                    self._commit_edit()
                    return True
                if event.key == pygame.K_ESCAPE:
                    self.editing_key = None
                    self.editing_text = ""
                    return True
                if event.key == pygame.K_BACKSPACE:
                    self.editing_text = self.editing_text[:-1]
                    return True
                if event.unicode and event.unicode.isprintable():
                    self.editing_text += event.unicode
                    return True
                return True  # autres touches ignorées pendant l'édition
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Clic pendant l'édition :
                #  - sur la même valeur → on garde l'édition en cours
                #  - sur une autre valeur → valide puis édite celle-là
                #  - ailleurs → valide et PROPAGE l'événement (boutons, monde, fermer…)
                rect = self.param_value_rects.get(self.editing_key)
                if rect and rect.collidepoint(event.pos):
                    return True
                for key, r in self.param_value_rects.items():
                    if r.collidepoint(event.pos):
                        self._commit_edit()
                        self.editing_key = key
                        self.editing_text = ""
                        return True
                self._commit_edit()
                return "PROPAGATE"
            return True  # autres événements ignorés pendant l'édition

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Tabs: Parameters / Agents
            for name, rect in self.tab_rects.items():
                if rect.collidepoint(event.pos):
                    self.active_tab = 'params' if name == 'Parameters' else 'agents'
                    self.scroll_y = 0
                    return True
            # Sous-sections dépliables (group:*) — même si le header est hors de la zone visible,
            # il reste enregistré dans section_headers donc le clic fonctionne toujours
            for key, rect in self.section_headers.items():
                if key.startswith("group:") and rect.collidepoint(event.pos):
                    gname = key.split(":", 1)[1]
                    self.param_groups_expanded[gname] = not self.param_groups_expanded[gname]
                    # Ajuste le scroll pour rendre le contenu visible
                    if self.param_groups_expanded[gname]:
                        contenu = {"Simulation": 20 * max(1, len(self.params)) + 4,
                                   "Agents": 18 * min(len(self.sections["Agents"]["items"]), self._MAX_AGENTS_DISPLAY) + 18,
                                   "Evolution": 20 * len(self.param_groups["Evolution"]) + 4,
                                   "Environment": 24 + 4 * 4 * 22 + 20}[gname]
                        visible_h = self.rect.h - 56
                        cible = rect.y + contenu - visible_h + 54
                        # Recalcule scroll_max en supposant la section dépliée
                        h = 0
                        for nm in ("Simulation", "Agents", "Evolution", "Environment"):
                            h += 22 + 2
                            if not (self.param_groups_expanded[nm] or nm == gname):
                                continue
                            if nm == "Environment":
                                h += 20 * len(self.param_groups["Environment"]) + 4
                                h += 4 * (20 + 2*20 + 20 + 2) + 4 * (20 + 20 + 20 + 2)
                            else:
                                h += 20 * len(self.param_groups[nm]) + 4
                        self.scroll_max = max(0, h - visible_h)
                        self.scroll_y = min(self.scroll_max, max(0, cible))
                    return True
            # CL matière / agents : boutons cyclables
            for (side_key, matter), rect in self.cl_buttons.items():
                if rect.collidepoint(event.pos):
                    self._cycle_cl(side_key, matter)
                    return True
            # Wall agents (AGENT_STOP/AGENT_REBOUNCE)
            for side_key, rect in self.wall_buttons.items():
                if rect.collidepoint(event.pos):
                    wall_key = f"CL_AGENTS_WALL_{side_key}"
                    cur = self.params.get(wall_key, "AGENT_STOP")
                    new = "AGENT_REBOUNCE" if cur == "AGENT_STOP" else "AGENT_STOP"
                    self.params[wall_key] = new
                    if self.on_cl_change:
                        self.on_cl_change(side_key, "Wall", new)
                    return True
            # Valeur de paramètre : commencer une NOUVELLE saisie (champ vide)
            for key, rect in self.param_value_rects.items():
                if rect.collidepoint(event.pos):
                    self.editing_key = key
                    self.editing_text = ""
                    return True
            # Checkbox d'agent : bascule sélection
            for agent_id, rect, _ in self.agent_checkboxes:
                if rect.collidepoint(event.pos):
                    return ("agent_toggle", agent_id)
            # Boundary condition buttons (Environment section)
            for (side_key, matter), rect in self.cl_buttons.items():
                if rect.collidepoint(event.pos):
                    self._cycle_cl(side_key, matter)
                    return True

        return False

    def _track_rect(self):
        return pygame.Rect(self.rect.right - 7, self.rect.y + 54, 5, self.rect.h - 60)

    def _drag_scroll(self, mouse_y):
        track = self._track_rect()
        ratio = (mouse_y - track.y - self._thumb_h / 2) / max(1, track.h - self._thumb_h)
        self.scroll_y = int(max(0, min(1, ratio)) * self.scroll_max)

    def _jump_scroll(self, mouse_y):
        track = self._track_rect()
        ratio = (mouse_y - track.y) / max(1, track.h)
        self.scroll_y = int(max(0, min(1, ratio)) * self.scroll_max)

    def _commit_edit(self):
        """Valide la saisie → convertit → callback vers Simulation.
        Saisie vide = on garde la valeur actuelle."""
        if self.editing_key is None:
            return
        key = self.editing_key
        raw = self.editing_text.strip()
        if raw:  # ne change que si la saisie est non vide
            value = self._coerce(raw)
            if value != self.params.get(key):
                self.params[key] = value
                if self.on_param_change:
                    self.on_param_change(key, value)
        self.editing_key = None
        self.editing_text = ""

    @staticmethod
    def _coerce(value):
        low = str(value).lower()
        if low in ("true", "false"):
            return low == "true"
        try:
            return int(low)
        except ValueError:
            pass
        try:
            return float(low)
        except ValueError:
            pass
        return value

    # ------------------------------------------------------------------
    # Mise à jour
    # ------------------------------------------------------------------
    def update_agents(self, agents_list):
        self.sections["Agents"]["items"] = [(a.id, a.alive) for a in agents_list]

    def update_selected(self, selected_ids):
        """Ids actuellement sélectionnés (cases vertes)."""
        self.selected_ids = set(selected_ids)

    # ------------------------------------------------------------------
    # Rendu
    # ------------------------------------------------------------------
    def draw(self, screen):
        pygame.draw.rect(screen, COLOR_BG_PANEL, self.rect)
        pygame.draw.line(screen, COLOR_BORDER, (self.rect.x, self.rect.y),
                         (self.rect.right, self.rect.y), 2)

        title = self.font_title.render("EXPLORER", True, COLOR_TEXT)
        screen.blit(title, (self.rect.x + 10, self.rect.y + 6))

        # --- Tab bar (Parameters / Agents) ---
        self.tab_rects = {}
        tab_w = (self.rect.w - 20) // 2
        for i, name in enumerate(("Parameters", "Agents")):
            r = pygame.Rect(self.rect.x + 10 + i * (tab_w + 4), self.rect.y + 26, tab_w, 22)
            self.tab_rects[name] = r
            active = (self.active_tab == ('params' if name == 'Parameters' else 'agents'))
            pygame.draw.rect(screen, COLOR_TAB_ACTIVE if active else COLOR_TAB_INACTIVE,
                             r, border_radius=4)
            lbl = self.font.render(name, True, COLOR_TEXT if active else COLOR_TEXT_DIM)
            screen.blit(lbl, (r.x + 8, r.y + 3))

        # Scroll : bornes calculées AVANT le dessin (hauteur de contenu réelle)
        clip_rect = pygame.Rect(self.rect.x, self.rect.y + 52, self.rect.w, self.rect.h - 56)
        content_h = self._content_height()
        visible_h = clip_rect.h
        self.scroll_max = max(0, content_h - visible_h)
        self.scroll_y = min(self.scroll_y, self.scroll_max)
        screen.set_clip(clip_rect)

        y = self.rect.y + 54 - self.scroll_y

        if self.active_tab == 'params':
            y = self._draw_params(screen, y)
        else:
            y = self._draw_agents(screen, y)

        screen.set_clip(None)

        # Scrollbar vertical fonctionnelle
        if self.scroll_max > 0:
            track = self._track_rect()
            pygame.draw.rect(screen, (30, 35, 48), track, border_radius=3)
            ratio_vis = visible_h / max(1, content_h)
            self._thumb_h = max(16, int(track.h * ratio_vis))
            thumb_y = track.y + int((self.scroll_y / self.scroll_max) * (track.h - self._thumb_h))
            self.scrollbar_rect = pygame.Rect(track.x, thumb_y, 5, self._thumb_h)
            color = COLOR_BUTTON_ACTIVE if self.scrollbar_dragging else COLOR_BUTTON_HOVER
            pygame.draw.rect(screen, color, self.scrollbar_rect, border_radius=3)
        else:
            self.scrollbar_rect = None

    def _draw_section_header(self, screen, name, y):
        header_h = 24
        rect = pygame.Rect(self.rect.x + 4, y, self.rect.w - 8, header_h)
        self.section_headers[name] = rect
        if rect.bottom < self.rect.y + 24 or rect.top > self.rect.bottom - 4:
            return y + header_h + 4
        expanded = self.sections[name]["expanded"]
        color = COLOR_BG_HEADER if expanded else (20, 25, 35)
        pygame.draw.rect(screen, color, rect, border_radius=3)
        arrow = "▼" if expanded else "►"
        screen.blit(self.font.render(arrow, True, COLOR_TEXT_DIM), (self.rect.x + 10, y + 4))
        screen.blit(self.font.render(name, True, COLOR_TEXT), (self.rect.x + 28, y + 4))
        return y + header_h + 4

    def _draw_params(self, screen, y):
        """Parameters tab: collapsible sub-sections (Simulation / Agents /
        Evolution / Environment) + matter and agent BC in Environment."""
        self.param_value_rects = {}
        self.cl_buttons = {}
        self.wall_buttons = {}
        row_h = 20
        # Groupes Simulation, Agents, Evolution (paramètres simples)
        for group_name in ("Simulation", "Agents", "Evolution"):
            # Header de sous-section dépliable
            header_h = 22
            rect = pygame.Rect(self.rect.x + 8, y, self.rect.w - 16, header_h)
            self.section_headers[f"group:{group_name}"] = rect
            expanded = self.param_groups_expanded[group_name]
            if not (rect.bottom < self.rect.y + 52 or rect.top > self.rect.bottom - 4):
                color = COLOR_BG_HEADER if expanded else (20, 25, 35)
                pygame.draw.rect(screen, color, rect, border_radius=3)
                arrow = "▼" if expanded else "►"
                screen.blit(self.font.render(arrow, True, COLOR_TEXT_DIM), (self.rect.x + 14, y + 3))
                screen.blit(self.font.render(group_name, True, COLOR_TEXT), (self.rect.x + 30, y + 3))
            y += header_h + 2
            if not expanded:
                continue
            for key in self.param_groups[group_name]:
                value = self.params.get(key)
                if value is None:
                    continue
                if y + row_h < self.rect.y + 54 or y > self.rect.bottom:
                    y += row_h
                    continue
                screen.blit(self.font_small.render(f"{key}:", True, COLOR_TEXT_DIM), (self.rect.x + 18, y + 4))
                val_rect = pygame.Rect(self.rect.x + 100, y, self.rect.w - 120, row_h)
                if self.editing_key == key:
                    pygame.draw.rect(screen, (30, 40, 60), val_rect, border_radius=3)
                    txt = self.editing_text + "|"
                    color = COLOR_GREEN
                else:
                    txt = str(value)
                    color = COLOR_TEXT
                    if val_rect.collidepoint(pygame.mouse.get_pos()):
                        pygame.draw.rect(screen, (30, 38, 55), val_rect, border_radius=3)
                screen.blit(self.font_small.render(txt, True, color), (val_rect.x + 6, y + 4))
                self.param_value_rects[key] = val_rect
                y += row_h
            y += 4

        # Environment sub-section: RD parameters + matter BC + agent BC
        header_h = 22
        rect = pygame.Rect(self.rect.x + 8, y, self.rect.w - 16, header_h)
        self.section_headers["group:Environment"] = rect
        expanded = self.param_groups_expanded["Environment"]
        if not (rect.bottom < self.rect.y + 52 or rect.top > self.rect.bottom - 4):
            color = COLOR_BG_HEADER if expanded else (20, 25, 35)
            pygame.draw.rect(screen, color, rect, border_radius=3)
            arrow = "▼" if expanded else "►"
            screen.blit(self.font.render(arrow, True, COLOR_TEXT_DIM), (self.rect.x + 14, y + 3))
            screen.blit(self.font.render("Environment", True, COLOR_TEXT), (self.rect.x + 30, y + 3))
        y += header_h + 2
        if not expanded:
            return y

        # Environment parameters (DX_GRID, etc.)
        for key in self.param_groups["Environment"]:
            value = self.params.get(key)
            if value is None:
                continue
            if y + row_h < self.rect.y + 54 or y > self.rect.bottom:
                y += row_h
                continue
            screen.blit(self.font_small.render(f"{key}:", True, COLOR_TEXT_DIM), (self.rect.x + 18, y + 4))
            val_rect = pygame.Rect(self.rect.x + 100, y, self.rect.w - 120, row_h)
            if self.editing_key == key:
                pygame.draw.rect(screen, (30, 40, 60), val_rect, border_radius=3)
                txt = self.editing_text + "|"
                color = COLOR_GREEN
            else:
                txt = str(value)
                color = COLOR_TEXT
                if val_rect.collidepoint(pygame.mouse.get_pos()):
                    pygame.draw.rect(screen, (30, 38, 55), val_rect, border_radius=3)
            screen.blit(self.font_small.render(txt, True, color), (val_rect.x + 6, y + 4))
            self.param_value_rects[key] = val_rect
            y += row_h
        y += 4

        # CL matière : 4 bords × (MD1, MD2) avec type + valeur Dirichlet
        sides = [("X - Gauche", "LEFT"), ("X - Droite", "RIGHT"), ("Y - Haut", "TOP"), ("Y - Bas", "BOTTOM")]
        for label, side_key in sides:
            if y + row_h < self.rect.y + 54 or y > self.rect.bottom:
                y += row_h
                continue
            screen.blit(self.font.render(label, True, COLOR_TEXT), (self.rect.x + 18, y + 3))
            y += row_h
            for matter in ("MD1", "MD2"):
                if y + row_h < self.rect.y + 54 or y > self.rect.bottom:
                    y += row_h
                    continue
                cur = self._get_cl(side_key, matter)
                # Bouton de cycle (Torique/Neumann/Dirichlet)
                btn_rect = pygame.Rect(self.rect.x + 18, y, 110, row_h)
                color = COLOR_BUTTON_HOVER if btn_rect.collidepoint(pygame.mouse.get_pos()) else COLOR_BG_HEADER
                pygame.draw.rect(screen, color, btn_rect, border_radius=3)
                screen.blit(self.font_small.render(f"{matter}: {cur}", True, COLOR_TEXT), (btn_rect.x + 4, y + 4))
                self.cl_buttons[(side_key, matter)] = btn_rect
                y += row_h
                # Si Dirichlet : champ de valeur éditable
                if cur == "DIRICHLET":
                    if y + row_h < self.rect.y + 54 or y > self.rect.bottom:
                        y += row_h
                        continue
                    val_key = f"CL_DIRICHLET_{side_key}_{matter}"
                    screen.blit(self.font_small.render(f"val {matter}:", True, COLOR_TEXT_DIM), (self.rect.x + 30, y + 4))
                    val_rect = pygame.Rect(self.rect.x + 100, y, self.rect.w - 120, row_h)
                    if self.editing_key == val_key:
                        pygame.draw.rect(screen, (30, 40, 60), val_rect, border_radius=3)
                        txt = self.editing_text + "|"
                        color = COLOR_GREEN
                    else:
                        txt = str(self.params.get(val_key, 0.0))
                        color = COLOR_TEXT
                        if val_rect.collidepoint(pygame.mouse.get_pos()):
                            pygame.draw.rect(screen, (30, 38, 55), val_rect, border_radius=3)
                    screen.blit(self.font_small.render(txt, True, color), (val_rect.x + 6, y + 4))
                    self.param_value_rects[val_key] = val_rect
                    y += row_h
            y += 2

        # Agent BC: 4 sides x (TORIC/SOLID + AGENT_STOP/AGENT_REBOUNCE)
        for label, side_key in sides:
            if y + row_h < self.rect.y + 54 or y > self.rect.bottom:
                y += row_h
                continue
            screen.blit(self.font.render(label, True, COLOR_TEXT), (self.rect.x + 18, y + 3))
            y += row_h
            cur = self._get_cl(side_key, "Agents")
            btn_rect = pygame.Rect(self.rect.x + 18, y, 130, row_h)
            color = COLOR_BUTTON_HOVER if btn_rect.collidepoint(pygame.mouse.get_pos()) else COLOR_BG_HEADER
            pygame.draw.rect(screen, color, btn_rect, border_radius=3)
            screen.blit(self.font_small.render(f"Agents: {cur}", True, COLOR_TEXT), (btn_rect.x + 4, y + 4))
            self.cl_buttons[(side_key, "Agents")] = btn_rect
            y += row_h
            if cur == "SOLID":
                wall_key = f"CL_AGENTS_WALL_{side_key}"
                wall_val = self.params.get(wall_key, "AGENT_STOP")
                wbtn_rect = pygame.Rect(self.rect.x + 18, y, 130, row_h)
                wcolor = COLOR_BUTTON_HOVER if wbtn_rect.collidepoint(pygame.mouse.get_pos()) else COLOR_BG_HEADER
                pygame.draw.rect(screen, wcolor, wbtn_rect, border_radius=3)
                screen.blit(self.font_small.render(f"paroi: {wall_val}", True, COLOR_TEXT), (wbtn_rect.x + 4, y + 4))
                self.wall_buttons[side_key] = wbtn_rect
                y += row_h
            y += 2
        return y

    def _draw_agents(self, screen, y):
        """Agents : checkbox (VERTE si sélectionné) + nom (limité à _MAX_AGENTS_DISPLAY)."""
        self.agent_checkboxes = []
        row_h = 18
        items = self.sections["Agents"]["items"]
        displayed = items[:self._MAX_AGENTS_DISPLAY]
        for agent_id, alive in displayed:
            if y + row_h < self.rect.y + 26 or y > self.rect.bottom:
                y += row_h
                continue
            selected = agent_id in self.selected_ids
            cb_rect = pygame.Rect(self.rect.x + 16, y + 2, 12, 12)
            fill = COLOR_GREEN if selected else COLOR_BUTTON_NORMAL
            pygame.draw.rect(screen, fill, cb_rect, border_radius=2)
            pygame.draw.rect(screen, COLOR_BORDER, cb_rect, 1, border_radius=2)
            if cb_rect.collidepoint(pygame.mouse.get_pos()):
                pygame.draw.rect(screen, COLOR_BUTTON_HOVER, cb_rect, border_radius=2)
            status = "" if alive else " †"
            color = COLOR_GREEN if alive else (120, 120, 120)
            screen.blit(self.font_small.render(f"Agent {agent_id}{status}", True, color),
                        (self.rect.x + 34, y + 1))
            self.agent_checkboxes.append((agent_id, cb_rect, alive))
            y += row_h
        # Indicateur si plus d'agents
        if len(items) > self._MAX_AGENTS_DISPLAY:
            surf = self.font_small.render(f"… {len(items) - self._MAX_AGENTS_DISPLAY} autres agents", True, COLOR_TEXT_DIM)
            screen.blit(surf, (self.rect.x + 34, y + 1))
        return y

    # ------------------------------------------------------------------
    # Environment section: boundary conditions
    # ------------------------------------------------------------------
    # Per-side choices: MD1 and MD2 → TORIC / NEUMANN / DIRICHLET ; Agents → TORIC / SOLID
    _CL_CHOICES_MATTER = ["TORIC", "NEUMANN", "DIRICHLET"]
    _CL_CHOICES_AGENTS = ["TORIC", "SOLID"]

    def _draw_environment(self, screen, y):
        """Environment section: 4 sides x (MD1, MD2, Agents) with cycling buttons."""
        self.cl_buttons = {}  # (side, matter) -> rect
        row_h = 22
        sides = [
            ("X - Gauche", "LEFT", "X"), ("X - Droite", "RIGHT", "X"),
            ("Y - Haut", "TOP", "Y"), ("Y - Bas", "BOTTOM", "Y"),
        ]
        for label, side_key, _axis in sides:
            if y + row_h < self.rect.y + 26 or y > self.rect.bottom:
                y += row_h
                continue
            screen.blit(self.font.render(label, True, COLOR_TEXT), (self.rect.x + 16, y + 3))
            y += row_h
            for matter, choices in (("MD1", self._CL_CHOICES_MATTER), ("MD2", self._CL_CHOICES_MATTER), ("Agents", self._CL_CHOICES_AGENTS)):
                if y + row_h < self.rect.y + 26 or y > self.rect.bottom:
                    y += row_h
                    continue
                cur = self._get_cl(side_key, matter)
                btn_rect = pygame.Rect(self.rect.x + 16, y, self.rect.w - 32, row_h)
                color = COLOR_BUTTON_HOVER if btn_rect.collidepoint(pygame.mouse.get_pos()) else COLOR_BG_HEADER
                pygame.draw.rect(screen, color, btn_rect, border_radius=3)
                screen.blit(self.font_small.render(f"{matter}: {cur}", True, COLOR_TEXT), (self.rect.x + 22, y + 3))
                self.cl_buttons[(side_key, matter)] = btn_rect
                y += row_h
        # Paramètre lié : valeur Dirichlet éditable
        if y + row_h < self.rect.y + 26 or y > self.rect.bottom:
            y += row_h
        screen.blit(self.font.render("Dirichlet:", True, COLOR_TEXT), (self.rect.x + 16, y + 3))
        val_rect = pygame.Rect(self.rect.x + 100, y, self.rect.w - 120, row_h)
        cur = self.params.get("CL_DIRICHLET_VALUE", 0.0)
        color = COLOR_GREEN if self.editing_key == "CL_DIRICHLET_VALUE" else COLOR_TEXT
        txt = (self.editing_text + "|") if self.editing_key == "CL_DIRICHLET_VALUE" else str(cur)
        pygame.draw.rect(screen, (30, 40, 60) if self.editing_key == "CL_DIRICHLET_VALUE" else COLOR_BG_HEADER,
                         val_rect, border_radius=3)
        screen.blit(self.font_small.render(txt, True, color), (val_rect.x + 6, y + 4))
        self.param_value_rects["CL_DIRICHLET_VALUE"] = val_rect
        y += row_h
        return y

    def _get_cl(self, side_key, matter):
        """Lit la valeur CL courante (self.params = PARAMS pour MD, _agents_cl pour agents)."""
        if matter in ("MD1", "MD2"):
            return self.params.get(f"CL_{matter}_{side_key}", "TORIC")
        return self._agents_cl.get(side_key, "TORIC")

    def _cycle_cl(self, side_key, matter):
        """Clic sur un bouton CL : cycle à travers les choix."""
        choices = self._CL_CHOICES_AGENTS if matter == "Agents" else self._CL_CHOICES_MATTER
        if matter == "Agents":
            cur = self._agents_cl.get(side_key, "TORIC")
            idx = choices.index(cur) if cur in choices else 0
            new = choices[(idx + 1) % len(choices)]
            self._agents_cl[side_key] = new
            # Synchronise PARAMS pour que _build_agents_cl() retourne la bonne valeur
            self.params[f"CL_AGENTS_{side_key}"] = new
            if self.on_cl_change:
                self.on_cl_change(side_key, matter, new)
        else:
            cur = self.params.get(f"CL_{matter}_{side_key}", "TORIC")
            idx = choices.index(cur) if cur in choices else 0
            new = choices[(idx + 1) % len(choices)]
            self.params[f"CL_{matter}_{side_key}"] = new
            if self.on_cl_change:
                self.on_cl_change(side_key, matter, new)

    def _draw_placeholder(self, screen, y, text):
        surf = self.font.render(text, True, COLOR_TEXT_DIM)
        screen.blit(surf, (self.rect.x + 16, y))
        return y + 24
