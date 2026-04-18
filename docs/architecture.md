# Architecture

## Overview

The app is split into three layers:

1. launcher / screen composition
2. game-rule engines
3. shared history, save/load, and visualization helpers

## 1. Launcher and screens

### Launcher

- [darts.py](darts.py)

Creates a single Tk root and swaps between:

- `501`
- `Cricket`
- `Cricket 1v1`

Each screen gets an `on_back` callback so it can return to the menu.

### 501 screen

- [501.py](501.py)

Responsibilities:

- build the full 501 UI
- interpret clicks into darts
- update score/infoboard/stats/zoom panels
- save and load JSON histories
- detect end-of-game popup flow

### Cricket screen

- [cricket.py](cricket.py)

Responsibilities:

- build the shared cricket UI
- switch between team and solo mode
- render the scoreboard, infoboard, and stats panel
- save and load JSON histories
- detect end-of-game popup flow

## 2. Game engines

### 501 engine

- [dart_engine/params_501.py](dart_engine/params_501.py)

Encapsulates:

- team/player ordering
- team score
- turn start score
- bust handling
- double-out win detection

### Cricket engine

- [dart_engine/params_cricket.py](dart_engine/params_cricket.py)
- [dart_engine/params_cricket_1x1.py](dart_engine/params_cricket_1x1.py)

Encapsulate:

- cricket closures
- overflow scoring
- team or player turn rotation
- win detection

## 3. Shared helpers

### Save/load and replay

- [dart_engine/ui_common.py](dart_engine/ui_common.py)

Contains shared logic for:

- config load/save
- file dialogs
- history JSON load/save
- replaying dart history into a game engine

### Player display helpers

- [dart_engine/player_ui.py](dart_engine/player_ui.py)

Contains:

- hit label formatting
- profile picture lookup
- recent turn summary builders

### Scoring/stat helpers

- [dart_engine/helpers_501.py](dart_engine/helpers_501.py)
- [dart_engine/cricket_stats.py](dart_engine/cricket_stats.py)

These are used to derive replay-friendly histories and stats from raw dart events.

## Data flow

### 1. User click

The UI records a dart hit as:

- board coordinates
- resolved number
- multiplier
- current player
- current side/team

### 2. History append

Each dart is appended to `self.dart_history`.

### 3. Engine update

The game engine registers the hit and updates:

- active player/team
- score
- current turn state
- winner state

### 4. Cache refresh

The UI rebuilds cached derived state such as:

- score history
- mark history
- stats panel series
- shot map data
- plot data

### 5. Redraw

Panels are redrawn from the engine state and caches.

## Stats panel model

The stats panel supports multiple views:

- `Shot Map`
- `Score Plot`

The raw stats cache in each UI file is built from `dart_history`, then rendered into:

- player stat cards
- team stat cards
- shot-map markers
- matplotlib plot images

## Persistence model

Only throw history is saved to disk.

On load:

1. JSON history is read
2. player order is inferred
3. engine state is reset
4. the history is replayed to rebuild the live game state

This keeps persistence simple and avoids syncing multiple saved state formats.

## Notes for future work

- The UI files are still fairly large and contain both rendering and controller logic.
- `swap_players_history()` and `swap_teams_history()` are still stubbed in [dart_engine/helpers_general.py](dart_engine/helpers_general.py).
- If the project grows, a natural next split would be:
  - `views/`
  - `controllers/`
  - `stats/`
  - `models/`
