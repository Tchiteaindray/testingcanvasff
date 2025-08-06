import os
import sys
import subprocess
import traceback
import shutil
import json
import platform
from pathlib import Path

# ─── CONFIGURATION ───────────────────────────────────────────────────
DESIRED_PY = "3.10"  # Minimum Python version required
VENV_DIR = "venv"
REQUIREMENTS_FILE = Path("requirements/requirement.txt")
# ─────────────────────────────────────────────────────────────────────

def debug(msg):
    print(f"[bootstrap] {msg}")

def is_windows():
    return platform.system() == "Windows"

def is_macos():
    return platform.system() == "Darwin"

def is_linux():
    return platform.system() == "Linux"

def find_python(version: str):
    """Find Python executable across platforms."""
    python_commands = [
        f"python{version}",  # Linux/macOS
        f"python{version.replace('.', '')}",  # Windows (python310)
        "python3",  # Fallback
        "python",   # Final fallback
    ]

    for cmd in python_commands:
        try:
            path = shutil.which(cmd)
            if path:
                # Verify Python version
                result = subprocess.run(
                    [path, "--version"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                if version in result.stdout:
                    return path
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue

    return None

def install_python(version: str):
    """Install Python using OS-specific package managers."""
    debug(f"⚠ Python {version} not found. Attempting to install...")

    if is_windows():
        try:
            debug("✔ Trying winget install...")
            subprocess.run(
                ["winget", "install", f"Python.Python.{version}", "--silent"],
                check=True,
            )
            return True
        except Exception:
            debug("✖ Winget install failed. Try manual install from python.org")

    elif is_macos():
        try:
            debug("✔ Trying Homebrew install...")
            subprocess.run(["brew", "install", f"python@{version}"], check=True)
            return True
        except Exception:
            debug("✖ Homebrew install failed. Try: 'brew install python@3.10'")

    elif is_linux():
        try:
            debug("✔ Trying apt install...")
            subprocess.run(
                ["sudo", "apt", "install", f"python{version}", "-y"],
                check=True,
            )
            return True
        except Exception:
            debug("✖ APT install failed. Try: 'sudo apt install python3.10'")

    return False

def ensure_python(version: str):
    """Ensure Python is available, install if missing."""
    python_path = find_python(version)
    if python_path:
        debug(f"✔ Found Python {version} at {python_path}")
        return python_path

    if install_python(version):
        python_path = find_python(version)
        if python_path:
            return python_path

    sys.exit(f"✖ Python {version} not found. Please install it manually.")

def create_venv(python_exe: str, venv_dir: str):
    """Create a virtual environment."""
    venv_path = Path(venv_dir)
    if venv_path.exists():
        debug("✔ Virtual environment already exists. Skipping creation.")
        return

    debug("✔ Creating virtual environment...")
    try:
        subprocess.run([python_exe, "-m", "venv", venv_dir], check=True)
    except subprocess.CalledProcessError:
        sys.exit("✖ Failed to create virtual environment.")

def get_venv_python(venv_dir: str):
    """Get the correct Python path inside the virtualenv."""
    venv_path = Path(venv_dir)
    if is_windows():
        return venv_path / "Scripts" / "python.exe"
    else:
        return venv_path / "bin" / "python"

def install_requirements(venv_python: str):
    """Install dependencies from requirements.txt."""
    if not REQUIREMENTS_FILE.exists():
        alt_path = Path("requirement.txt")
        if alt_path.exists():
            debug(f"✔ Found requirements at {alt_path}")
            REQUIREMENTS_FILE.parent.mkdir(exist_ok=True)
            shutil.copy(alt_path, REQUIREMENTS_FILE)
        else:
            sys.exit(f"✖ Requirements file not found at {REQUIREMENTS_FILE}")

    debug("✔ Installing dependencies...")
    try:
        subprocess.run(
            [venv_python, "-m", "pip", "install", "--upgrade", "pip", "setuptools"],
            check=True,
        )
        subprocess.run(
            [venv_python, "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)],
            check=True,
        )
    except subprocess.CalledProcessError:
        sys.exit("✖ Failed to install requirements. Check install_error.log")

def run_main(venv_python: str):
    """Run the main application script."""
    main_script = Path(__file__).parent / "pages" / "main.py"
    if not main_script.exists():
        sys.exit(f"✖ Main script not found at {main_script}")

    debug("✔ Starting application...")
    try:
        subprocess.run([venv_python, str(main_script)], check=True)
    except subprocess.CalledProcessError:
        sys.exit("✖ Application failed to start.")

if __name__ == "__main__":
    print("====== Virtual Gesture Air Canvas Setup ======")
    python_exe = ensure_python(DESIRED_PY)
    create_venv(python_exe, VENV_DIR)
    venv_python = get_venv_python(VENV_DIR)
    install_requirements(venv_python)
    run_main(venv_python)