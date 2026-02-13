# diploma-backend

## Development setup

**MediaPipe** (used by the face analyzer) supports **Python 3.9–3.12 only**. Use a venv with Python 3.12:

### 1. Install Python 3.12 (if needed)

- **Arch / CachyOS:** `sudo pacman -S python312`
- **Fedora:** `sudo dnf install python3.12`
- **Ubuntu/Debian:** `sudo apt install python3.12 python3.12-venv`

### 2. Create venv with Python 3.12

```bash
# From project root
cd /path/to/diploma-backend

# Remove old venv if you have one (optional)
rm -rf .venv

# Create new venv with Python 3.12
python3.12 -m venv .venv

# Activate (Linux/macOS)
source .venv/bin/activate

# Install dependencies (mediapipe will install correctly on 3.12)
pip install -r requirements.txt
```

### 3. Use the venv

- **Cursor/VS Code:** Choose interpreter `.venv/bin/python` (Ctrl+Shift+P → “Python: Select Interpreter”).
- **Terminal:** run `source .venv/bin/activate` before `uvicorn`, `alembic`, etc.
