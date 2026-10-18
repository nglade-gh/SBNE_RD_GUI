# UsageIA — Inventaire des opérations et évaluation du coût en tokens

> **Note méthodologique** : ce document est une **estimation**, pas une mesure exacte.
> Hermes Agent ne expose pas de compteur de tokens par opération. Les chiffres
> ci-dessous sont évalués à partir de la nature de chaque opération (lecture de
> fichiers, écriture de patches, exécutions de tests, réflexion/réponse) et de
> la taille typique des données manipulées. Les ordres de grandeur sont fiables ;
> les valeurs précises sont indicatives.

---

## Résumé

| Phase | Opérations | Coût estimé (tokens) |
|---|---|---|
| SBNE — Refactoring | 8 | ~45 000 |
| SBNE — Parallélisation + lanceur | 6 | ~30 000 |
| SBNE — Documentation + nettoyage | 5 | ~20 000 |
| SBNE_GUI — Interface pygame_gui | 8 | ~40 000 |
| SBNE_GUI — Corrections 1–5.4 | 8 | ~35 000 |
| SBNE_GUI — Bug édition paramètres | 6 | ~25 000 |
| SBNE_GUI — Corrections 4 (threads, layout) | 7 | ~30 000 |
| SBNE_GUI — Stats overlap / 2 onglets droit | 6 | ~25 000 |
| SBNE_RD_GUI — Pivot réaction-diffusion | 12 | ~60 000 |
| SBNE_RD_GUI — Paramètres + menu sauvegarde | 7 | ~30 000 |
| SBNE_RD_GUI — Conditions aux limites | 5 | ~25 000 |
| SBNE_RD_GUI — Corrections 3.1–3.8 | 11 | ~55 000 |
| SBNE_RD_GUI — Corrections supplémentaires (molette, CL, traduction) | 18 | ~75 000 |
| **TOTAL** | **106** | **~510 000** |

---

## Inventaire détaillé

### SBNE — Refactoring (terminé)

| # | Opération | Coût estimé |
|---|---|---|
| 4 | Lecture des 19 fichiers du projet | ~10 000 |
| 5 | Création du venv `.venv` | ~3 000 |
| 6 | Baseline 2000 pas (énergie 155 000.0) | ~5 000 |
| 7 | Refactoring de 7 fichiers | ~15 000 |
| 8 | Vérification équivalence comportementale | ~5 000 |
| 9 | Bugs corrigés (identifiés lors de la vérification) | ~4 000 |
| 10 | Nettoyage final | ~2 000 |
| 11 | Validation finale | ~1 000 |

### SBNE — Parallélisation + lanceur (terminé)

| # | Opération | Coût estimé |
|---|---|---|
| 12 | Profilage des goulots d'étranglement | ~4 000 |
| 13 | Mesures d'échelle (temps/pas vs population) | ~3 000 |
| 14 | Création `launcher.py` (interface web) | ~12 000 |
| 15 | Ajout `MAX_ITERATIONS` | ~2 000 |
| 16 | Fix QUIT headless (handler pygame/SDL) | ~5 000 |
| 17 | Tests du lanceur | ~4 000 |

### SBNE — Documentation + nettoyage (terminé)

| # | Opération | Coût estimé |
|---|---|---|
| 18 | Création `README.md` | ~5 000 |
| 19 | Création `requirements.txt` | ~2 000 |
| 20 | Création `.gitignore` | ~1 000 |
| 21 | Retrait 9 imports inutilisés | ~3 000 |
| 22 | Suppression fichiers morts | ~2 000 |
| 23 | Commit git `6c20782` | ~2 000 |
| 24 | Vérification finale | ~5 000 |

### SBNE_GUI — Interface pygame_gui

| # | Opération | Coût estimé |
|---|---|---|
| 25 | Création du projet SBNE_GUI (copie depuis SBNE) | ~5 000 |
| 26 | Installation pygame_gui 0.6.9 | ~3 000 |
| 27 | Création `GUIInterface.py` (ConsoleLog, TabButton, StatsPanel, LeftPanelTree) | ~15 000 |
| 28 | Réécriture `Environnement.py` (boucle pygame_gui) | ~10 000 |
| 29 | Création `gui_theme.json` | ~2 000 |
| 30 | Création `sync_from_chouette.sh` | ~2 000 |
| 31 | Tests d'affichage | ~5 000 |
| 32 | Intégration tête-à-tête avec l'utilisateur | ~8 000 |

### SBNE_GUI — Corrections 1–5.4

| # | Opération | Coût estimé |
|---|---|---|
| 33 | Clic gauche/droit sélection + aura bleue | ~5 000 |
| 34 | Toolbar repositionnée | ~3 000 |
| 35 | Boutons icônes | ~3 000 |
| 36 | Fold + scrollbar | ~5 000 |
| 37 | Édition paramètres (clic + validation) | ~5 000 |
| 38 | Slider fonctionnel | ~3 000 |
| 39 | Checkbox vert | ~2 000 |
| 40 | Labels réduits | ~2 000 |
| 41 | Redimensionnement panneau gauche | ~3 000 |
| 42 | Onglets cerveaux refondus (prev1/next1 parmi tous, prev2/next2 parmi sélectionnés) | ~8 000 |
| 43 | `set_system_cursor` try/except (dummy driver) | ~2 000 |

### SBNE_GUI — Bug édition paramètres (corrigé)

| # | Opération | Coût estimé |
|---|---|---|
| 44 | Diagnostic : `LeftPanelTree` consomme tous les événements pendant l'édition | ~5 000 |
| 45 | Patch `GUIInterface.py` : clic pendant édition → `_commit_edit()` + `"PROPAGATE"` | ~5 000 |
| 46 | Patch `Environnement.py` : `lp_result == "PROPAGATE"` → `False` | ~3 000 |
| 47 | Fix `K_KPENTER` → `K_KP_ENTER` | ~2 000 |
| 48 | Test propagation (5 interactions) | ~3 000 |
| 49 | Test `test_interface.py` 13/13 OK | ~5 000 |

### SBNE_GUI — Corrections 4 (suppression boutons, layout, threads)

| # | Opération | Coût estimé |
|---|---|---|
| 50 | Suppression boutons prev/next toolbar | ~3 000 |
| 51 | Graphe rescalé (marge) | ~3 000 |
| 52 | Stats repositionnées (y = height-185) | ~2 000 |
| 53 | Threads séparés (sim_lock, sim_thread) | ~8 000 |
| 54 | Fix crash dashboard float (`int(temps_simule_ms)`) | ~2 000 |
| 55 | Test parallélisme (95 pas / 73 frames en 1.5s) | ~5 000 |
| 56 | Test headless 300 pas OK | ~3 000 |
| 57 | Ajustement final layout | ~4 000 |

### SBNE_GUI — Stats overlap / 2 onglets droit

| # | Opération | Coût estimé |
|---|---|---|
| 58 | Réduction fond CERVEAUX → `stats_panel.rect.top - 10` | ~3 000 |
| 59 | USER insiste : "non, le problème n'est pas du tout réglé" | ~2 000 |
| 60 | USER propose 2 onglets sélectionnables | ~2 000 |
| 61 | Implémentation `right_tab` + `_draw_stats_content` | ~8 000 |
| 62 | Tests affichage | ~3 000 |
| 63 | Validation finale | ~7 000 |

### SBNE_RD_GUI — Pivot réaction-diffusion

| # | Opération | Coût estimé |
|---|---|---|
| 64 | USER : "Note que ce que j'appelle Eat c'est en fait Mouth" | ~1 000 |
| 65 | Création `ReactionDiffusion.py` (solveur ADI Peaceman-Rachford) | ~15 000 |
| 66 | Fix `_solve_cyclic` (Sherman-Morrison → Woodbury rang 2) | ~8 000 |
| 67 | Cache des corrections cycliques précalculé | ~3 000 |
| 68 | Patch `Environnement.py` : suppression Food/DiffusionGrid, ajout `field` | ~10 000 |
| 69 | Patch `SpatialGrid.py` : `rebuild(agents)` | ~3 000 |
| 70 | Patch rendu : `field.render_surface()` | ~3 000 |
| 71 | Labels 6 organes (EYE, MOUTH, MOUTH_MD1, MOUTH_MD2, MOVE, ROTATE) | ~3 000 |
| 72 | `collect_stats` avec MD1/MD2 totals | ~3 000 |
| 73 | Cleanup dead code (digestion_calendar, stomach, diffusion_grid, Food.py, DiffusionGrid.py) | ~3 000 |
| 74 | Fix console headless (création dans `__init__`) | ~2 000 |
| 75 | TEST 2000 pas (11.4s, écart 0.000000) | ~5 000 |

### SBNE_RD_GUI — Paramètres + menu sauvegarde

| # | Opération | Coût estimé |
|---|---|---|
| 76 | D_MD1/D_MD2=0.005, K_MD1_MD2=0.1 | ~2 000 |
| 77 | `is_paused = True` au démarrage | ~2 000 |
| 78 | Extinction → `is_paused = True` (pas running=False) | ~2 000 |
| 79 | `matter_display` ("BOTH"/"MD1"/"MD2") + touches 1/2/3 | ~3 000 |
| 80 | README.md mis à jour (touches 1/2/3, CONSUME_QTY, D_MD1/D_MD2) | ~3 000 |
| 81 | Patch `test_interface.py` (test pause adapté) | ~2 000 |
| 82 | TEST `test_interface.py` 15/15 OK | ~5 000 |
| 83 | Création `MenuOverlay` (pickle, paramètres défaut/origine/fichier) | ~12 000 |
| 84 | Patch `Environnement.py` : imports, `_ORIGINAL_PARAMS`, bouton MENU | ~5 000 |
| 85 | Patch `Environnement.py` : `_execute_menu_action` | ~5 000 |
| 86 | Patch `Environnement.py` : `handle_events` → `_process_event` | ~3 000 |
| 87 | Fix MOUSEWHEEL crash (`hasattr(event, "pos")`) | ~2 000 |

### SBNE_RD_GUI — Conditions aux limites

| # | Opération | Coût estimé |
|---|---|---|
| 88 | USER clarifie structure CL (4 bords × MD1/MD2/Agents, TORIC défaut, Dirichlet paramétrable) | ~3 000 |
| 89 | Patch `ReactionDiffusion.py` : CL TORIC/NEUMANN/DIRICHLET par bord/matière | ~8 000 |
| 90 | Patch `GUIInterface.py` : `_draw_environment` (4 bords × boutons cyclables) | ~8 000 |
| 91 | Patch `Environnement.py` : `_on_cl_change`, synchronisation `_agents_cl` | ~5 000 |
| 92 | TEST CL agents Neumann (agents bloqués aux bords) | ~3 000 |

### SBNE_RD_GUI — Corrections 3.1–3.8

| # | Opération | Coût estimé |
|---|---|---|
| 93 | USER liste 8 corrections demandées | ~2 000 |
| 94 | Patch `Interface.py` : suppression MODE_FOOD + TEST_NAME du dashboard | ~3 000 |
| 95 | Patch `GUIInterface.py` : molette → `agents_explorer` (bug connu) | ~3 000 |
| 96 | Patch `Environnement.py` : nouveaux paramètres CL (DIRICHLET par bord/matière, WALL) | ~5 000 |
| 97 | Patch `Agent.py` : `move()` IMPERMEABLE + ARRET/REBOND | ~8 000 |
| 98 | Patch `Environnement.py` : `_build_matter_cl` → CL_DIRICHLET_{side}_{matter} | ~3 000 |
| 99 | Patch `Environnement.py` : `step()` utilise `_build_matter_cl` | ~2 000 |
| 100 | Patch `GUIInterface.py` : `active_tab = 'params'`, `tab_rects`, `param_groups` | ~5 000 |
| 101 | Patch `GUIInterface.py` : `draw()` réécrit (2 onglets + `_draw_params`) | ~10 000 |
| 102 | Patch `GUIInterface.py` : `_draw_params` (sous-sections + CL matière/agents + Dirichlet) | ~10 000 |
| 103 | Nettoyage code mort dans `_draw_params` | ~3 000 |

### SBNE_RD_GUI — Corrections supplémentaires (session actuelle)

| # | Opération | Coût estimé |
|---|---|---|
| 104 | USER : 5 corrections (molette, crash agents_explorer, CL SOLID, traduction, noms AGENT_*) | ~3 000 |
| 105 | Patch `GUIInterface.py` : suppression `agents_explorer`/`environnement_explorer` | ~2 000 |
| 106 | Patch `Agent.py` : `'IMPERMEABLE'` → `'SOLID'` partout | ~3 000 |
| 107 | Patch `Environnement.py` : `'NEUMANN'` → `'SOLID'` dans `step()` | ~3 000 |
| 108 | Patch `Environnement.py` : `_build_agents_cl` docstring | ~1 000 |
| 109 | Patch `GUIInterface.py` : `_cycle_cl` synchronise `PARAMS` | ~3 000 |
| 110 | Patch `GUIInterface.py` : `handle_event` recalcule `scroll_max` | ~2 000 |
| 111 | Patch `Agent.py` : `'ARRET'`/`'REBOND'` → `'AGENT_STOP'`/`'AGENT_REBOUNCE'` | ~3 000 |
| 112 | Patch `Environnement.py` : PARAMS + `_build_agents_cl` defaults | ~3 000 |
| 113 | Patch `GUIInterface.py` : `_cycle_cl` + `_draw_environment` AGENT_STOP/REBOUNCE | ~3 000 |
| 114 | Patch `GUIInterface.py` : `cur == "IMPERMEABLE"` → `cur == "SOLID"` | ~1 000 |
| 115 | Patch `GUIInterface.py` : molette fallback `pygame.mouse.get_pos()` | ~2 000 |
| 116 | Traduction : commentaires `Environnement.py` (PARAMS, docstrings) | ~5 000 |
| 117 | Traduction : commentaires `GUIInterface.py` | ~3 000 |
| 118 | Traduction : messages console `Environnement.py` | ~8 000 |
| 119 | Traduction : `Interface.py` (GRAPHICS OFF) | ~2 000 |
| 120 | Traduction : `ReactionDiffusion.py` docstrings | ~2 000 |
| 121 | Traduction : labels `Environnement.py` (BRAINS/STATISTICS) | ~3 000 |
| 122 | Traduction : labels stats (Mean energy, Mean nodes, Max age) | ~3 000 |
| 123 | Vérification : `grep` français restants + compilation | ~3 000 |
| 124 | Réécriture `README.md` complet en anglais | ~10 000 |
| 125 | Création `UsageIA.md` (ce document) | ~5 000 |

---

## Méthode d'évaluation

| Type d'opération | Coût typique |
|---|---|
| Lecture d'un fichier (< 500 lignes) | ~1 000–3 000 tokens |
| Lecture d'un fichier (> 500 lignes) | ~3 000–8 000 tokens |
| Patch simple (1–3 lignes) | ~500–1 500 tokens |
| Patch moyen (docstring / petit bloc) | ~1 000–3 000 tokens |
| Patch grand (réécriture méthode / bloc > 20 lignes) | ~3 000–8 000 tokens |
| Création d'un fichier | ~5 000–15 000 tokens |
| Exécution de test court | ~1 000–3 000 tokens |
| Exécution de test long (headless 2000 pas) | ~3 000–8 000 tokens |
| Diagnostic / réflexion | ~2 000–8 000 tokens |
| Réponse finale | ~500–3 000 tokens |
| Itérations USER (demande + diagnostic) | ~1 000–5 000 tokens |

Ces estimations incluent les tokens d'entrée (contexte + fichiers) et de sortie
(patches + réponses). Le total de ~510 000 tokens couvre l'ensemble des
opérations depuis le début du projet SBNE (refactoring) jusqu'à la session
actuelle SBNE_RD_GUI.

---

## Répartition par type

| Type | Nombre | Coût estimé |
|---|---|---|
| Patches / éditions de code | ~48 | ~180 000 |
| Créations de fichiers | ~6 | ~50 000 |
| Exécutions de tests | ~12 | ~40 000 |
| Lectures de fichiers | ~18 | ~50 000 |
| Diagnostics / réflexions | ~12 | ~50 000 |
| Traductions | ~10 | ~35 000 |
| Réponses / itérations USER | — | ~105 000 |
| **TOTAL** | **106 opérations** | **~510 000** |

---

*Dernière mise à jour : session SBNE_RD_GUI — corrections molette, CL SOLID/AGENT_STOP/AGENT_REBOUNCE, traduction anglaise, README réécrit.*
