# SP-14 Blue Chess AI

A local chess engine that lets you play against a neural network-based AI or another player, using a browser-based interface served locally via Flask.

## Features
- AI powered by a TorchScript policy-value neural network
- Monte Carlo Tree Search (MCTS) for move selection
- Modern browser-based UI with drag-and-drop pieces
- No internet required — runs entirely offline
- Automatically opens in your default browser (Chrome, Edge, Firefox, etc.)
- Supports Windows, macOS, and Linux
- One-click standalone executable build for Windows

## Requirements
- **Python 3.11.x** (must be exact — not 3.10 or 3.12+)
- **Poetry** (for dependency management and virtual environment setup)
- **Windows, macOS, or Linux**
- **Windows** required if building a `.exe` for distribution

## Setup

Install Poetry if you don't already have it:
```bash
pip install poetry
```

Configure Poetry to create virtual environments inside the project:
```bash
poetry config virtualenvs.in-project true
```

Install project dependencies:
```bash
poetry install
```

Activate the virtual environment:

### Windows
```bash
.venv\Scripts\activate
```

### macOS/Linux
```bash
source .venv/bin/activate
```

## Run Locally (No Build)

You can run the app directly for development without building anything:
```bash
python run.py
```

This will start the local server and open the game in your browser at `http://127.0.0.1:5000`

## Build a Standalone Executable

Use PyInstaller to bundle everything into one file:

### Windows
```bash
pyinstaller --noconfirm --onefile --add-data "app/templates;app/templates" --add-data "app/static;app/static" --add-data "app/data;app/data" --add-data "neural_net/model;neural_net/model" run.py
```

### macOS/Linux
```bash
pyinstaller --noconfirm --onefile --add-data "app/templates:app/templates" --add-data "app/static:app/static" --add-data "app/data:app/data" --add-data "neural_net/model:neural_net/model" run.py
```

This generates a self-contained executable inside the `dist/` folder.

## Run the Executable

### Windows
```bash
dist\run.exe
```

### macOS/Linux
```bash
./dist/run
```

The app will automatically open in your browser when launched.

## Clean Build (Optional)

If you want to wipe the previous builds before rebuilding:

### Windows (PowerShell)
```bash
Remove-Item -Recurse -Force build, dist, run.spec
```

### macOS/Linux
```bash
rm -r build/ dist/ run.spec
```

Then rerun the PyInstaller command above.

## Project Structure

```
SP-14-Blue-Chess-AI/
├── app/                  # Flask routes, templates, static files
├── bitboarder/           # Bitboard-based chess engine core
├── neural_net/           # TorchScript model and training code
├── run.py                # App entrypoint (server + browser launch)
├── pyproject.toml        # Poetry project config
├── dist/                 # Final compiled executable (after build)
```

## Notes
- The executable works fully offline - no internet connection is needed after the initial setup.
- You can rename `run.exe` (or `run`) to something like `chess-ai.exe` for easier distribution.
- Only windows supports `.exe` output - macOS/Linux builds produce a standalone binary (`run`).