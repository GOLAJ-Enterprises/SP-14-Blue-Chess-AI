# SP-14 Blue Chess AI

A local chess engine that lets you play against a neural network-based AI or another player, using a browser-based interface served locally via Flask.

## Features
- AI powered by a TorchScript policy-value neural network
- Monte Carlo Tree Search (MCTS) for move selection
- Modern browser-based UI with drag-and-drop pieces
- No internet required — runs entirely offline
- One-click standalone `.exe` build for Windows

## Requirements
- **Python 3.11.x** (must be exact — not 3.10 or 3.12+)
- **Poetry** for dependency management and virtual environment setup
- **Windows** (for building and running the `.exe`)

## How to Build the `.exe`

From the project root:

1. **Install Poetry**  
   ```bash
   pip install poetry
   ```

2. **Install dependencies and activate the virtual environment**  
   ```bash
   poetry install
   .venv\Scripts\activate
   ```

3. **Build the standalone `.exe` using PyInstaller**  
   ```bash
   pyinstaller --noconfirm --onefile ^
     --add-data "app/templates;app/templates" ^
     --add-data "app/static;app/static" ^
     --add-data "app/data;app/data" ^
     --add-data "neural_net/model;neural_net/model" ^
     run.py
   ```

4. **Navigate to the `dist/` folder**  
   - Double-click `run.exe` to launch the app  
   - Your browser will open to `http://127.0.0.1:5000/`

## Project Structure

```
SP-14-Blue-Chess-AI/
├── app/                  # Flask routes, templates, static files
├── bitboarder/           # Bitboard-based chess engine core
├── neural_net/           # TorchScript model and training code
├── run.py                # App entrypoint
├── pyproject.toml        # Poetry project config
├── dist/run.exe          # Final compiled executable (after build)
```

## Notes
- The `.exe` works completely offline — it launches the local server and opens the game in your browser.
- You can rename `run.exe` to something like `chess-ai.exe` before distributing.

## Clean Build (Optional)

If you want to clean up old build files before rebuilding:

```bash
rm -r build/ dist/ run.spec
```

Then re-run the PyInstaller command.
