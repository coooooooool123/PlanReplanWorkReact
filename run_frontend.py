import sys
from pathlib import Path
import os

os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

BASE_DIR = Path(__file__).parent
frontend_path = BASE_DIR / "frontend.py"

if __name__ == "__main__":
    import subprocess
    
    env = os.environ.copy()
    env['PYTHONUTF8'] = '1'
    env['PYTHONIOENCODING'] = 'utf-8'
    
    print("启动Streamlit前端...")
    print(f"前端地址: http://localhost:8501")
    
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        str(frontend_path),
        "--server.port=8501",
        "--server.address=localhost"
    ], env=env)