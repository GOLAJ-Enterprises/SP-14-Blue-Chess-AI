# SP-14 Blue Chess AI

A local chess engine that lets you play against a neural network-based AI or another player, using a browser-based interface served locally via Flask and pywebview.

## Features
- AI powered by a TorchScript policy-value neural network
- Monte Carlo Tree Search (MCTS) for move selection
- Modern browser-based UI with drag-and-drop pieces
- No internet required — runs entirely offline
- Launches in a native window using pywebview
- One-click standalone `.exe` build for Windows

## Requirements
- **Python 3.11.x** (must be exact — not 3.10 or 3.12+)
- **Poetry** for dependency management and virtual environment setup
- **Windows** (for building and running the `.exe`)

## Setup

```bash
pip install poetry
poetry config virtualenvs.in-project true
poetry install
.venv\Scripts\activate
```

## Build the Standalone `.exe`

```bash
pyinstaller --noconfirm --onefile --add-data "app/templates;app/templates" --add-data "app/static;app/static" --add-data "app/data;app/data" --add-data "neural_net/model;neural_net/model" run.py
```

## Run

```bash
dist\run.exe
```

This will start a local Flask server and launch the game in a native window via pywebview.

## Clean Build (Optional)

To remove old build files:

```bash
rm -r build/ dist/ run.spec
```

Then re-run the PyInstaller command above.

## Project Structure

```
SP-14-Blue-Chess-AI/
├── app/                  # Flask routes, templates, static files
├── bitboarder/           # Bitboard-based chess engine core
├── neural_net/           # TorchScript model and training code
├── run.py                # App entrypoint (server + pywebview)
├── pyproject.toml        # Poetry project config
├── dist/run.exe          # Final compiled executable (after build)
```

## Notes
- The `.exe` works completely offline — it starts the local server and opens the game in a standalone window.
- You can rename `run.exe` to something like `chess-ai.exe` for distribution.
