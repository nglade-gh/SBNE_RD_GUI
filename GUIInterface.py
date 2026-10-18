"""
GUIInterface — Interface graphique avancée pour SBNE_GUI.

Contient :
- ConsoleLog : console de log avec code couleur (vert/jaune/rouge)
- TabButton : onglet personnalisé (pygame_gui n'a pas de UITabContainer)
- LeftPanelTree : arborescence gauche (Paramètres / Agents / Environnement)
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
            indicator = self.font.render(f"↑ {len(self.messages) - max_visible} messages masqués", True, COLOR_TEXT_DIM)
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
# ARBORESCENCE GAUCHE
# ============================================================================
class LeftPanelTree:
    """Panneau gauche : arborescence repliable (Paramètres / Agents /
    Environnement), scrollbar vertical fonctionnelle (clic + drag + molette),
    et paramètres éditables par clic (Entrée = valider, Échap = annuler)."""

    def __init__(self, x, y, w, h, params_dict, font_size=12, on_param_change=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.font = pygame.font.SysFont("Arial", font_size)                  # titres / headers
        self.font_small = pygame.font.SysFont("Arial", max(8, font_size - 3))  # params & agents (moitié)
        self.font_title = pygame.font.SysFont("Arial", font_size + 2, bold=True)
        self.params = params_dict
        self.on_param_change = on_param_change  # callback(cle, nouvelle_valeur)
        self.selected_ids = set()  # ids sélectionnés (checkbox verts)

        self.sections = {
            "Paramètres": {"expanded": True, "items": []},
            "Agents": {"expanded": True, "items": []},
            "Environnement": {"expanded": False, "items": []},
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

    def update_rect(self, x, y, w, h):
        """Repositionne/redimensionne le panneau (redimensionnement utilisateur)."""
        self.rect = pygame.Rect(x, y, w, h)

    # ------------------------------------------------------------------
    # Hauteur de contenu (pour le scrollbar)
    # ------------------------------------------------------------------
    def _content_height(self):
        h = 0
        for name in ("Paramètres", "Agents", "Environnement"):
            h += 28  # header (24) + gap (4)
            if not self.sections[name]["expanded"]:
                continue
            if name == "Paramètres":
                h += 20 * max(1, len(self.params))
            elif name == "Agents":
                h += 18 * max(1, len(self.sections["Agents"]["items"]))
            else:
                h += 24
        return h

    # ------------------------------------------------------------------
    # Événements
    # ------------------------------------------------------------------
    def handle_event(self, event, ui_manager):
        """Retourne True si l'événement a été consommé par le panneau."""
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
        if event.type == pygame.MOUSEWHEEL and self.rect.collidepoint(event.pos):
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
            # Header de section : replier/déplier
            for name, rect in self.section_headers.items():
                if rect.collidepoint(event.pos):
                    self.sections[name]["expanded"] = not self.sections[name]["expanded"]
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

        return False

    def _track_rect(self):
        return pygame.Rect(self.rect.right - 7, self.rect.y + 28, 5, self.rect.h - 34)

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

        title = self.font_title.render("EXPLORATEUR", True, COLOR_TEXT)
        screen.blit(title, (self.rect.x + 10, self.rect.y + 6))

        # Scroll : bornes calculées AVANT le dessin (hauteur de contenu réelle)
        clip_rect = pygame.Rect(self.rect.x, self.rect.y + 26, self.rect.w, self.rect.h - 30)
        content_h = self._content_height()
        visible_h = clip_rect.h
        self.scroll_max = max(0, content_h - visible_h)
        self.scroll_y = min(self.scroll_y, self.scroll_max)
        screen.set_clip(clip_rect)

        y = self.rect.y + 28 - self.scroll_y

        if "Paramètres" in self.sections:
            y = self._draw_section_header(screen, "Paramètres", y)
            if self.sections["Paramètres"]["expanded"]:
                y = self._draw_params(screen, y)

        if "Agents" in self.sections:
            y = self._draw_section_header(screen, "Agents", y)
            if self.sections["Agents"]["expanded"]:
                y = self._draw_agents(screen, y)

        if "Environnement" in self.sections:
            y = self._draw_section_header(screen, "Environnement", y)
            if self.sections["Environnement"]["expanded"]:
                y = self._draw_placeholder(screen, y, "Réservé pour futures fonctionnalités.")

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
        """Paramètres : label (petit) + valeur sur la même ligne, sans recouvrement."""
        self.param_value_rects = {}
        row_h = 20
        for key, value in self.params.items():
            if y + row_h < self.rect.y + 26 or y > self.rect.bottom:
                y += row_h
                continue
            # Label petit, à gauche — ne chevauche jamais la valeur
            screen.blit(self.font_small.render(f"{key}:", True, COLOR_TEXT_DIM), (self.rect.x + 14, y + 4))
            # Valeur cliquable à droite
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
        return y

    def _draw_agents(self, screen, y):
        """Agents : checkbox (VERTE si sélectionné) + nom."""
        self.agent_checkboxes = []
        row_h = 18
        for agent_id, alive in self.sections["Agents"]["items"]:
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
        return y

    def _draw_placeholder(self, screen, y, text):
        surf = self.font.render(text, True, COLOR_TEXT_DIM)
        screen.blit(surf, (self.rect.x + 16, y))
        return y + 24
