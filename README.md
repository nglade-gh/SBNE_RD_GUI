# SBNE_RD_GUI — Simulateur d'écosystème évolutionnaire (réaction-diffusion MD1/MD2)

Simulation d'un écosystème de **micro-organismes agentifs** dont le « cerveau » est un
**réseau de neurones booléen signé** (SBN, *signed boolean network*). Les agents se
déplacent, voient, mangent et se reproduisent dans un **environnement torique** (le
monde s'enroule : à droite du monde on ressort à gauche). Chaque cerveau est soumis à
mutation à la reproduction : c'est de là que vient l'évolution. L'historique complet des
cerveaux est enregistré en base SQLite **sous forme de deltas (comme git)**.

**Variante SBNE_RD_GUI** : la nourriture est modélisée par un **système de
réaction-diffusion à 2 matières** (MD1 et MD2) résolu par la méthode **ADI
(Peaceman-Rachford)** d'ordre 2 — voir `ReactionDiffusion.py`.

- Monde : `1280 × 720` px par défaut, torique, rendu pygame + bandeau d'information.
  La fenêtre fait `1920 × 980` : le monde + **panneau gauche** (explorateur :
  paramètres / agents / environnement) + **panneau droit** (onglets cerveau + stats)
  + **barre de contrôle** (haut) + **console de log** (bas).
- Interface : `pygame_gui` 0.6.9 (widgets : boutons, slider) + rendu custom pygame
  (panneaux, graphes SBN, onglets, console). Voir `GUIInterface.py` et `gui_theme.json`.
- Population initiale : 150 agents (paramétrable), chacun avec ~1000 d'énergie.
- L'énergie **globale** du système (agents + MD1 + MD2) est **strictement conservée** à
  chaque pas : c'est l'invariant de contrôle du simulateur.

---

## 1. Comment fonctionne la simulation

### Les agents
Un agent possède : une position `(x, y)`, un angle, une **énergie** (qu'il dépense), et
son **SBN**. Il meurt quand son énergie passe sous **50** (`Agent.DEATH_ENERGY`) ; il se
reproduit quand elle atteint **1200** (`DIVISION_ENERGY`) : l'enfant est placé 15 px
plus loin, dans la zone aveugle du parent, avec l'énergie du parent et un cerveau
**muté**.

### Le cerveau (SBN)
- Réseau de neurones **booléens signés** : états `0/1`, poids **entiers** bornés à
  `VALEUR_MAX_POIDS` (3).
- 6 **organes** = neurones fondamentaux, **non supprimables** (indices fixes) :

  | Index | Organe | Rôle |
  |---|---|---|
  | 0 | Œil (`EYE`) | Entrée : ce que l'agent voit dans son cône de vision |
  | 1 | Bouche agents (`MOUTH`) | Action : manger un autre agent |
  | 2 | Bouche MD1 (`MOUTH_MD1`) | Action : consommer de la matière diffuse 1 |
  | 3 | Bouche MD2 (`MOUTH_MD2`) | Action : consommer de la matière diffuse 2 |
  | 4 | Nageoire F (`MOVE`) | Action : avancer |
  | 5 | Nageoire R (`ROTATE`) | Action : tourner |

- Le réseau démarre avec 10 nœuds ; les autres nœuds et arcs sont libres. À chaque
  naissance, le cerveau de l'enfant subit des mutations : **suppression** de nœud/arc
  (probabilité `PROBA_DELETION`), **insertion** (`PROBA_INSERTION`), **évolution de
  poids** (`PROBA_EVOLUTION`).
- À chaque pas : `état_sortie = (état @ poids > 0)` ; la sortie des organes donne les
  actions (manger un agent, consommer MD1/MD2, avancer, tourner).

### L'énergie et la réaction-diffusion MD1/MD2
- **3 bouches, 3 sources de nourriture** : un agent peut manger un **autre agent** (duel
  : le plus énergique gagne ; à égalité, tirage aléatoire), ou consommer directement
  la **MD1** ou la **MD2** du sol à sa position. Chaque tentative coûte `COST_EAT`
  (identique pour les 3 bouches) et l'énergie consommée devient de l'énergie d'agent.
- **Toute énergie dépensée est relâchée en MD1** : le métabolisme, le coût des neurones
  et le coût des actions (y compris les bouches) sont déposés sous forme de MD1 à la
  position de l'agent. À la mort, toute l'énergie restante est relâchée en MD1.
- **Diffusion** : la MD1 et la MD2 diffusent sur le tore avec des coefficients `D_MD1`
  et `D_MD2` (px²/s). La MD1 se convertit lentement en MD2 avec la constante
  `K_MD1_MD2` (0.01 s⁻¹ ; 1 itération = 1 s).
- **Résolution numérique** : schéma **ADI (Peaceman-Rachford)**, d'ordre 2 en espace et
  en temps (Crank-Nicholson généralisé). Chaque pas est décomposé en deux demi-pas
  implicites 1D (x puis y) sur le tore, résolus par un solveur **Thomas cyclique**
  (correction de rang 2 via Woodbury — `ReactionDiffusion.py`). La matière est stockée
  dans des grilles de pas carré `DX_GRID` (20 px par défaut).
- **Conservation** : la diffusion ne crée ni ne détruit de matière ; la conversion
  MD1→MD2 transfère exactement la matière perdue par MD1 vers MD2. L'énergie globale
  `Σ(énergie agents) + total(MD1) + total(MD2)` est strictement constante.
- Un agent mort laisse son énergie sur le sol (même mécanisme).

### Un pas de simulation
1. Activation des déchets arrivés à échéance.
2. Mélange aléatoire des agents (équité : aucun ordre privilégié).
3. Reconstruction de la **grille spatiale** (recherche de voisins en O(1) au lieu d'O(n²),
   avec enroulement torique).
4. Pour chaque agent : **perception** (voisins dans le cône de vision), **pas du SBN**,
   actions (manger un agent / consommer MD1 / consommer MD2 / avancer / tourner),
   éventuelle **division** (l'enfant agit au pas suivant) + enregistrement du cerveau
   muté en base. Toute énergie dépensée est relâchée en MD1 à la position de l'agent.
5. Résolution duels, nettoyage des morts (mark-and-sweep), puis **diffusion-réaction**
   du champ MD1/MD2 (ADI) : la matière se diffuse et la MD1 se convertit en MD2.

---

## 1. Interface graphique (SBNE_GUI)

La fenêtre `1920 × 980` est organisée en 5 zones :

```
┌──────────────────────────────────────────────────────────────────┐
│ Barre de contrôle : [⏸ Pause][⏹ Stop][↺ Restart][🖼 Graphics]   │
│                   [Refresh: 30 FPS ●──────]  [◀ Préc][Suiv ▶]   │
├──────────┬────────────────────────────────────┬──────────────────┤
│ PANNEAU  │  D bandeau d'info (TEST/STEPS/POP)│  PANNEAU DROIT   │
│ GAUCHE   ├────────────────────────────────────┤  Onglets cerveau  │
│          │                                    │  [61][139][104]  │
│ EXPLOR.  │         MONDE (1280×720)           │  graphe SBN      │
│          │         agents + nourriture        │                  │
│ Params   │                                    │  STATISTIQUES    │
│ Agents   │                                    │  Pop: 150 ...    │
│ Env      │                                    │                  │
├──────────┴────────────────────────────────────┴──────────────────┤
│ CONSOLE (logs colorés : vert=info, jaune=warning, rouge=erreur)  │
└──────────────────────────────────────────────────────────────────┘
```

### Barre de contrôle (haut, sous le bandeau)
| Contrôle | Effet |
|---|---|
| **⏸ Pause** | Bascule pause/reprise (équivalent à `Espace`) |
| **⏹ Stop** | Arrête la simulation et ferme |
| **↺ Restart** | Réinitialise la simulation (nouvelle population, nouveau dossier `simulations/`) |
| **🖼 Graphics: ON/OFF** | Active/désactive le rendu (calcul intensif, équivalent à `G`) |
| **Refresh: N FPS** (slider 1–60) | Fréquence de mise à jour graphique (le tour continue hors rendu) |
| **◀ Précédent / Suivant ▶** | Défile les agents sélectionnés dans les onglets cerveau |

### Panneau gauche — Explorateur
Arborescence à sections dépliables :
- **Paramètres** : liste des clés `PARAMS` et leurs valeurs (référence ; modifier dans `Environnement.py` ou via `--param`).
- **Agents** : liste des agents vivants (`†` = mort). **Clic = sélectionner/désélectionner**
  un agent pour les onglets cerveau (clic dans la zone monde = même effet).
- **Environnement** : *réservé* (emplacement pour futures fonctionnalités).

### Panneau droit
- **CERVEAUX** : rangée d'onglets (1 par agent sélectionné, max `MAX_SELECTED_SBN` = 5).
  Chaque onglet affiche le SBN de l'agent (nœuds organes/internes, arêtes +/− avec poids).
  Sélectionner plus de 5 agents → message rouge en console.
- **STATISTIQUES** : population, énergie moyenne, noeuds moyens, âge max, énergie globale,
  nourriture, pas, agents sélectionnés — mis à jour à chaque image.
- **Affichage matière** : touches `1` (MD1 seule, vert), `2` (MD2 seule, rouge), `3`
  (mélange MD1+MD2 — jaune/orange là où les deux coexistent).

### Console (bas)
Journal des opérations avec **code couleur** :
- 🟢 **vert** : actions communes (démarrage, pause, sélection/désélection, onglets…)
- 🟡 **jaune** : remarques (tous les agents sont morts → arrêt)
- 🔴 **rouge** : erreurs critiques (dépassement de `MAX_SELECTED_SBN`, limites atteintes)

### Raccourcis (mode fenêtre)
| Touche | Action |
|---|---|
| `Espace` | Pause / lecture |
| `G` | Activer / désactiver le rendu |
| `V` | Afficher / masquer les cônes de vision |
| `S` | Fenêtre de résumé des statistiques |
| Clic gauche sur un agent | Sélectionne/désélectionne l'agent (onglet cerveau) |
| Clic gauche sur le vide | Efface la sélection |

---

## 2. Structure du projet

| Fichier | Rôle |
|---|---|
| `Environnement.py` | **Cœur** : classe `Simulation` (boucle principale, orchestration logique/rendu/base, widgets pygame_gui). Point d'entrée. |
| `GUIInterface.py` | Widgets custom pygame : `ConsoleLog`, `TabButton`, `StatsPanel`, `LeftPanelTree` |
| `gui_theme.json` | Thème pygame_gui (couleurs boutons/slider/label) |
| `SbNetwork.py` | Le cerveau : réseau booléen signé, mutations, pas logique. |
| `Agent.py` | L'agent : état, perception, actions, énergie, division. |
| `ReactionDiffusion.py` | Grilles MD1/MD2 + solveur ADI (Thomas cyclique) de la diffusion-réaction. |
| `SpatialGrid.py` | Index spatial torique (recherche de voisins). |
| `Interface.py` | Rendu pygame : bandeau d'information, pause, opacité des cônes. |
| `GraphVisualisation.py` | Graphiques matplotlib (résumé, graphe d'un SBN). |
| `evolution_tracker.py` | **Historique git-like** : snapshots + deltas jsonpatch en SQLite, reconstruction. |
| `ExportData.py` | Export des cerveaux (`save_nodes_influence`) toutes les 50 000 pas, dans `exports/`. |
| `launcher.py` | **Lanceur de campagnes parallèles** avec interface web (voir §7). |
| `Analyse.py` | Pipeline d'analyse des exports (graphiques pandas/seaborn/matplotlib). |
| `analyse_evolution.py` | Exemple : reconstruire le cerveau d'un agent à une itération. |
| `genealogy_viewer.py` / `genealogy_viewerv2.py` | Visualiseurs Tkinter de la généalogie (deux versions, la v2 est plus récente). |
| `get_agent_lineage_with_visualization.py` | Généalogie + visualisation networkx (utilisé par les viewers). |
| `lignéfixv2.py` | Variant de la généalogie (base `evolution.db` dans le dossier courant). |
| `simulations/` | Un sous-dossier par simulation (voir §5) — local, ignoré par git. |

---

## 3. Installation

### Installation complète (nouvelle machine)
```bash
cd SBNE_GUI
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### Vous avez déjà un venv (ex. créé avec seulement 3 paquets)
Rien à recréer — il suffit de compléter les dépendances manquantes :
```bash
.venv/bin/pip install -r requirements.txt
```
C'est le correctif de l'erreur
`ModuleNotFoundError: No module named 'networkx'` : `requirements.txt` fait
autorité, et pip n'installe que ce qui manque.

### Les 8 dépendances (`requirements.txt`)

| Paquet | Utilisé pour |
|---|---|
| `numpy` | Les SBN (opérations matricielles), grille de diffusion, historique des réseaux |
| `pygame` | Fenêtre, boucle de simulation, rendu du monde torique |
| `pygame_gui` | Widgets de l'interface (boutons, slider, labels) — version 0.6.9 |
| `jsonpatch` | L'historique git-like : calcul et rejeu des deltas de cerveaux |
| `seaborn` | Statistiques et graphiques de synthèse |
| `matplotlib` | Résumés, graphes de SBN, généalogies |
| `pandas` | L'analyse post-hoc (`Analyse.py`) |
| `networkx` | L'export des cerveaux (`ExportData.py`), graphes de généalogie |

> ⚠️ `pygame_gui` nécessite `pygame ≥ 2.6.1`. La version 0.6.9 est testée et fonctionnelle ;
> les versions ≥ 0.6.12 nécessitent `pygame ≥ 2.6.2` (pas encore disponible sur cette machine).

Python ≥ 3.10 (testé sur 3.12 et 3.13, avec un **venv propre** sans
`--system-site-packages` : installation + run headless vérifiés).
**Toujours exécuter avec `.venv/bin/python`** (les dépendances ne sont pas dans le
Python système).

> ⚠️ **Le venv n'est pas déplaçable.** Les scripts de `.venv/bin/` ont des shebangs à
> chemin absolu : si vous déplacez ou recopiez le dossier du projet, le venv copie avec
> est cassé (`zsh: .venv/bin/pip: bad interpreter: ... no such file or directory`).
> Pire, `python3 -m venv .venv` sur un venv existant ne régénère pas les scripts.
> Solution : supprimer et recréer sur place —
> `rm -rf .venv && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`.

---

## 4. Lancer une simulation

### Avec fenêtre (défaut)
```bash
.venv/bin/python Environnement.py
```

### Sans fenêtre (calcul seul — pour les campagnes, CI, benchmarks)
```bash
.venv/bin/python Environnement.py --headless --max-steps 2000 --seed 7
```

### Options CLI

| Option | Effet |
|---|---|
| `--headless` | Pas de fenêtre (SDL en mode dummy), calcul seul. |
| `--max-steps N` | Arrêt automatique après N pas. **Prioritaire** sur `PARAMS["MAX_ITERATIONS"]`. |
| `--seed N` | Surcharge `PARAMS["SEED"]` (reproductibilité). |
| `--param CLE=VALEUR` | Surcharge un paramètre `PARAMS` (répétable). Ex. `--param NUM_AGENTS=300 --param PROBA_INSERTION=0.6`. Valeurs converties en int/float/bool/str ; clé inconnue → erreur (pas de faute de frappe silencieuse). |
| `--outdir NOM` | Nom du sous-dossier créé dans `simulations/` (défaut : horodatage). |

> **Temps maximal** : `PARAMS["MAX_ITERATIONS"]` (défaut `0` = illimité) est le
> paramètre de base ; `--max-steps` le surcharge s'il est passé.

> Les raccourcis clavier et souris sont documentés dans la section 1 (interface graphique).

---

## 5. Paramètres de la simulation (`PARAMS` dans `Environnement.py`)

| Clé | Défaut | Signification |
|---|---|---|
| `TEST_NAME` | — | Nom de l'expérience (affiché, tracé dans les exports). |
| `SEED` | `42` | Graine aléatoire (reproductibilité). |
| `NUM_AGENTS` | `150` | Population initiale. |
| `MAX_ITERATIONS` | `0` | **Temps maximal** : nombre max de pas (0 = illimité). |
| `BASE_ENERGY` | `1000` | Énergie initiale des agents. |
| `DIVISION_ENERGY` | `1200` | Seuil de reproduction. |
| `PROBA_DELETION` | `0.4` | Probabilité (à la naissance) de supprimer un nœud/arc. |
| `PROBA_INSERTION` | `0.4` | Probabilité d'insérer un nœud/arc. |
| `PROBA_EVOLUTION` | `0.4` | Probabilité d'évoluer un poids. |
| `VALEUR_MAX_POIDS` | `3` | Amplitude max des poids (entiers). |
| `DISTANCE_VISION` | `70` | Portée de la vision (px). |
| `VISION_ANGLE` | `30` | Demi-angle du cône de vision (degrés). |
| `COST_NEURON` | `0.3` | Coût par nœud, par pas. |
| `COST_MOVE` | `0.02` | Coût d'avancer. |
| `COST_ROTATE` | `0.1` | Coût de tourner. |
| `COST_EAT` | `0.01` | Coût de manger / consommer MD1 / MD2 (identique pour les 3 bouches). |
| `COST_METABOLISM` | `0.1` | Coût de base par pas. |
| `DX_GRID` | `20.0` | Pas de la grille de matière (px). |
| `D_MD1` / `D_MD2` | `0.005` | Coefficients de diffusion MD1/MD2 (px²/s). |
| `K_MD1_MD2` | `0.1` | Vitesse de conversion MD1→MD2 (s⁻¹). |
| `CONSUME_QTY` | `100.0` | Matière (MD1/MD2) prélevée par tentative de bouche. |
| `NUM_MD1_INIT` | `10` | Dépôts initiaux de MD1. |
| `MD1_INIT_QTY` | `500.0` | Quantité d'énergie par dépôt initial de MD1. |
| `MAX_SELECTED_SBN` | `5` | Nombre max d'agents sélectionnés (onglets cerveau). Surcharger la sélection → message rouge en console. |
| `DISPLAY_REFRESH_FPS` | `30` | Fréquence de mise à jour graphique (FPS du rendu ; slider 1–60 dans la barre de contrôle). |
| `WIDTH` / `HEIGHT` | `1280` / `720` | *(options, hors PARAMS)* : taille du monde, lues si présentes dans le dict. |
| `N_ITER` | `1` | *(options, hors PARAMS)* : pas logiques par image (accélère le temps simulé). |

Pour tester une variation de paramètres en une commande :
```bash
.venv/bin/python Environnement.py --headless --seed 3 \
    --param NUM_AGENTS=300 --param PROBA_INSERTION=0.6 --param MAX_ITERATIONS=5000 \
    --outdir essai_insertion_06
```

---

## 6. Contenu d'une simulation (`simulations/<nom>/`)

| Fichier | Contenu |
|---|---|
| `parameters.json` | Paramètres effectivement utilisés (PARAMS + surcharges). |
| `stats.json` | Historique des stats (tous les 100 pas) : population, taille moyenne des réseaux, énergie moyenne, **énergie globale**, + totaux finaux. |
| `evolution.db` | Base SQLite de l'historique des cerveaux (voir §7). |
| `simulation_summary.png` | Résumé graphique en fin de simulation. |
| `exports/` | *(au-delà de 50 000 pas)* exports des cerveaux toutes les 50 000 pas (CSV + graphes) via `ExportData.py` — alimente `Analyse.py`. |
| `campaign.json` | *(lanceur)* provenance : campagne, run, seed, surcharges. |
| `run.log` | *(lanceur)* sortie du processus. |

---

## 7. Historique des cerveaux (base SQLite « git-like »)

**`evolution.db`** contient trois tables :

- `agents` : `id_agent`, `id_parent`, `iteration_creation` — l'arbre généalogique.
- `networks` : `id_agent`, `iteration`, `network_data` (JSON complet : états, poids,
  identifiants des nœuds), `network_hash`, `is_snapshot`.
- `commits` : `id_agent`, `iteration`, `diff_data` (**delta jsonpatch** par rapport au
  cerveau du parent), `id_parent_commit`, `message`.

Écritures :
- **À chaque naissance** : le réseau de l'enfant est enregistré (JSON complet dans
  `networks` + **delta** par rapport au parent dans `commits`) — une mutation = un commit.
- **Toutes les 50 000 pas** : *snapshot* périodique de chaque agent vivant
  (`is_snapshot=TRUE`).

Lecture / reconstruction — depuis n'importe quel script Python :
```python
from evolution_tracker import rebuild_network, close_all_connections

# Cerveau de l'agent 10 tel qu'il existait à l'itération 60 000 :
network = rebuild_network("simulations/<nom>/evolution.db", 10, 60000)
# -> {"states": [...], "weights": [[...]]}  (taille du réseau = len(states))
close_all_connections()
```
`rebuild_network` repart du dernier snapshot ≤ l'itération cible et **rejoue les
deltas** (jsonpatch) — c'est le chemin git. Sans snapshot, il lit directement le réseau
complet. (Exemple complet : `analyse_evolution.py`.)

---

## 8. Lanceur de campagnes parallèles (`launcher.py`)

Le vrai usage recherche = **beaucoup de simulations** (seeds / paramètres différents).
La machine a 32 cœurs : le lanceur en profite.

```bash
.venv/bin/python launcher.py            # panneau web sur http://127.0.0.1:8765
.venv/bin/python launcher.py --port 9000
```

**Interface web** (aucune dépendance externe) :
- Formulaire : étiquette, nb de runs, graine de base (run *i* = base + *i*), pas max
  (`0` = le paramètre `MAX_ITERATIONS` s'applique), parallélisme max (vide = auto),
  surcharges de paramètres (une `CLE=VALEUR` par ligne).
- Suivi en temps réel par campagne / par run : état, durée, nombre de pas, population
  finale, dossier de sortie, courbe de population, fin de log.
- Bouton **Arrêter** : SIGTERM puis **SIGKILL** après 3 s (nécessaire : voir §11),
  les runs non démarrés passent en `skipped`.

**API** (pour scripter) :
```
GET  /api/state                        → tout l'état (campagnes, runs)
POST /api/campaign                     → créer : {label, n_runs, seed_base, max_steps,
                                           max_parallel, params: "CLE=VALEUR\n..."}
POST /api/campaign/<id>/stop           → arrêter une campagne
GET  /api/run/<camp_id>/<run_id>/log   → fin du log (?lines=N)
GET  /api/run/<camp_id>/<run_id>/curve → courbe population {steps:[...], pop:[...]}
```

Chaque run est un **sous-processus indépendant** (`Environnement.py --headless ...`)
dans son propre dossier `simulations/<campagne>_seed<S>_runNN/` — donc aucune
interférence, et les 32 cœurs sont exploités pour les **campagnes** (pas pour une
simulation unique).

---

## 9. Post-analyse

| Outil | Usage |
|---|---|
| `Analyse.py` | Pipeline graphique sur les **exports** (CSV `agents_save_*.csv` produits par `ExportData.py` toutes les 50 000 pas) : `python Analyse.py` — parcourt `simulations/`, génère `1_temporel/`, `2_spatial/`, `3_moyennes_barplot/`. |
| `analyse_evolution.py` | Exemple de reconstruction de cerveau à une itération (adapter `db_path`, `agent_id`, `target_iteration`). |
| `genealogy_viewerv2.py` | Visualiseur Tkinter de la généalogie (v2 recommandée). |
| `lignéfixv2.py` | Généalogie networkx sur `evolution.db` **du dossier courant** (copier la base ou lancer depuis le bon dossier). |

Les scripts « ad hoc » (`analyse_evolution.py`, `lignéfixv2.py`) ont le chemin de la
base **codé en dur en relatif** : les lancer depuis le dossier qui contient la
`evolution.db` visée.

---

## 10. Invariant de contrôle et vérifications

> **L'énergie globale est strictement conservée à chaque pas.**
> `Σ agent.énergie + total(MD1) + total(MD2)` reste constant
> (155 000.0 sur les runs de référence). Toute modification du simulateur qui fait
> dériver cette valeur a créé un fuit/bug d'énergie.

Vérifications à faire **après toute modification** (et avant de dire « c'est bon ») :
1. `py_compile` des fichiers modifiés.
2. Run headless court (`--max-steps 2000 --seed 7`) : pas de crash, stats cohérentes.
3. Comparaison de l'énergie globale début/fin du run (dérive attendue : **0**).
4. Pour les fonctions pures (`SbNetwork`, `DiffusionGrid`, `SpatialGrid`) : comparer
   les sorties avec une seed fixée, avant/après.

---

## 11. Pièges connus

- **Headless : le SIGTERM ne tue pas la simulation.** pygame/SDL installe un handler qui
  transforme le SIGTERM en événement `pygame.QUIT` ; le QUIT est désormais ignoré en
  headless (fix 2026-10-16 — avant, les runs headless mouraient **aléatoirement**,
  parfois après 30 pas, avec des stats tronquées et un exit 0). Conséquence pratique :
  pour tuer un run headless il faut **SIGKILL** — le lanceur l'escadre automatiquement
  après 3 s de SIGTERM. En mode fenêtre, le QUIT (bouton croix) arrête normalement.
- **Reproductibilité** : avec la même `SEED`, un run headless est reproductible ;
  attention, tout changement d'ordre d'itération ou de graine décale la trajectoire.
- **Collisions de dossiers** : le nom de dossier par défaut est l'horodatage à la
  seconde ; deux lancements manuels dans la même seconde écriraient dans le même
  dossier. Le lanceur contourne en passant toujours `--outdir` explicite.
- **Nettoyage 2026-10-16** : les doublons morts (`save_network_state.py`,
  `SpatialGridAgent.py`, `simulation_setup.py`) et les backups `*.copy.py` ont été
  supprimés du dépôt (les originaux restent dans l'historique git). La convention de
  backup local `NOMFICHIER.copy.py` est couverte par le `.gitignore`.
- **Performance** (mesurée, 2026-10-16) : ~8 ms/pas à 150 agents (dont ~7 ms = le
  graphe matplotlib de suivi tous les 100 pas, **même en headless**), ~62 ms/pas à
  500, ~1000 ms/pas à 2000 (croissance super-linéaire : à haute population, ~47 % du
  temps = commits SQLite (un par naissance), ~24 % = perception/voisins). Gagnera le
  plus : désactiver les graphes en headless + écrire la base en asynchrone.

---

## 12. Exemples de sessions

```bash
# Run interactif classique
.venv/bin/python Environnement.py

# Benchmark reproductible
.venv/bin/python Environnement.py --headless --max-steps 2000 --seed 7

# Campagne manuelle : 10 seeds, 3000 pas, 200 agents
for s in $(seq 1 10); do
  .venv/bin/python Environnement.py --headless --seed $s --max-steps 3000 \
      --param NUM_AGENTS=200 --outdir campagneA_seed$s &
done; wait

# Campagne via le panneau web
.venv/bin/python launcher.py
# → http://127.0.0.1:8765
```
