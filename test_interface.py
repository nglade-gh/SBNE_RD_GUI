#!/usr/bin/env python
"""
test_interface.py — Diagnostic des interactions de l'interface SBNE_GUI.

À lancer depuis le dossier SBNE_GUI :
    .venv/bin/python test_interface.py

Affiche OK/ÉCHEC pour chaque interaction. Code de sortie 0 si tout passe.
"""
import os
import sys

os.environ.setdefault("MPLBACKEND", "Agg")
# Pas de display (environnement headless/CI) → driver SDL dummy automatique
if "SDL_VIDEODRIVER" not in os.environ and not os.environ.get("DISPLAY"):
    os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
import pygame_gui  # noqa: F401 — vérifie que pygame_gui est bien installé

from Environnement import Simulation, PARAMS

sim = Simulation(PARAMS, headless=False, max_steps=0, outdir='test_interface')
for _ in range(5):
    sim.step()
sim.render()

results = []


def check(name, cond, detail=""):
    results.append((name, cond))
    print(f"[{'OK  ' if cond else 'ÉCHEC'}] {name} {detail}")


def clic(x, y):
    """Clic complet : down + up, puis 2 frames (press + événement UI pygame_gui)."""
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(x, y)))
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=(x, y)))
    sim.handle_events()
    sim.handle_events()  # 2e frame : l'événement UI_BUTTON_START_PRESS posté par pygame_gui


print("=== 1. Boutons barre de contrôle ===")
# La simulation démarre en pause (nouveau comportement) → on reprend d'abord
check("démarrage en pause", sim.is_paused)
clic(sim.btn_pause.rect.centerx, sim.btn_pause.rect.centery)
check("pause (re clic) → is_paused=False", not sim.is_paused)
clic(sim.btn_pause.rect.centerx, sim.btn_pause.rect.centery)
check("pause → is_paused=True", sim.is_paused)
clic(sim.btn_pause.rect.centerx, sim.btn_pause.rect.centery)
check("pause (re clic) → False", not sim.is_paused)

clic(sim.btn_graphics.rect.centerx, sim.btn_graphics.rect.centery)
check("écran → show_graphics=False", not sim.show_graphics)
clic(sim.btn_graphics.rect.centerx, sim.btn_graphics.rect.centery)
check("écran (re clic) → True", sim.show_graphics)

clic(sim.btn_restart.rect.centerx, sim.btn_restart.rect.centery)
check("restart → steps=0, pop ok", sim.total_steps == 0 and len(sim.agents) == PARAMS["NUM_AGENTS"])

print("=== 2. Panneau gauche : fold ===")
sim.render()
tab = sim.left_panel.tab_rects.get("Agents")
if tab:
    clic(tab.centerx, tab.centery)
    check("clic onglet Agents → active_tab='agents'", sim.left_panel.active_tab == "agents")
    tab_p = sim.left_panel.tab_rects.get("Parameters")
    clic(tab_p.centerx, tab_p.centery)
    check("retour onglet Parameters → active_tab='params'", sim.left_panel.active_tab == "params")
else:
    check("onglet Agents", False, "(onglet Agents non trouvé)")

print("=== 3. Scrollbar panneau gauche ===")
sb = sim.left_panel.scrollbar_rect
if sb:
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=sb.center))
    sim.handle_events()
    pygame.event.post(pygame.event.Event(pygame.MOUSEMOTION, pos=(sb.centerx, sb.centery + 60)))
    sim.handle_events()
    check("drag scrollbar", sim.left_panel.scroll_y > 0, f"(scroll_y={sim.left_panel.scroll_y})")
else:
    check("drag scrollbar", False, "(pas de scrollbar)")

print("=== 4. Édition paramètre ===")
sim.left_panel.scroll_y = 0
sim.render()
r = sim.left_panel.param_value_rects.get("NUM_AGENTS")
if r:
    clic(r.centerx, r.centery)
    for c in "200":
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=0, unicode=c))
        sim.handle_events()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, unicode="\r"))
    sim.handle_events()
    check("édition NUM_AGENTS=200", sim.left_panel.params["NUM_AGENTS"] == 200,
          f"(valeur={sim.left_panel.params['NUM_AGENTS']})")
    sim.left_panel.params["NUM_AGENTS"] = 150  # restaurer
else:
    check("édition paramètre", False, "(rect NUM_AGENTS non trouvé)")

print("=== 5. Navigation cerveau ===")
for a in sim.agents[:3]:
    sim._toggle_agent_selection(a.id)
sim.render()
r1 = sim.brain_nav_rects.get("next1")
if r1:
    avant = sim.selected_agents[sim.active_brain_tab]
    clic(r1.centerx, r1.centery)
    apres = sim.selected_agents[sim.active_brain_tab]
    check("next1 (parmi tous)", apres != avant, f"{avant} → {apres}")
    clic(sim.brain_nav_rects["prev1"].centerx, sim.brain_nav_rects["prev1"].centery)
    check("prev1 (retour)", sim.selected_agents[sim.active_brain_tab] == avant)
else:
    check("next1", False, "(rect next1 non trouvé)")
r2 = sim.brain_nav_rects.get("next2")
if r2:
    avant2 = sim.selected_agents[sim.active_brain_tab]
    clic(r2.centerx, r2.centery)
    apres2 = sim.selected_agents[sim.active_brain_tab]
    check("next2 (parmi sélectionnés)", apres2 != avant2, f"{avant2} → {apres2}")

print("=== 6. Clic monde ===")
candidates = [a for a in sim.agents if a.id not in sim.selected_agents]
a = candidates[0] if candidates else sim.agents[0]
mx = sim.world_rect.x + a.x * sim.world_rect.w / sim.width
my = sim.world_rect.y + a.y * sim.world_rect.h / sim.height
clic(int(mx), int(my))
check("clic monde → sélection", a.id in sim.selected_agents)

print()
n_ok = sum(1 for _, c in results if c)
print(f"RÉSULTAT : {n_ok}/{len(results)} interactions OK")
sys.exit(0 if n_ok == len(results) else 1)
