import sys
from pathlib import Path

# Add backend directory to Python path
ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from data.seed_db import seed_database
from app.main import app as fastapi_app
import gradio as gr

# 1. Seed demo database on startup
seed_database()

# 2. Define minimal Gradio interface for HF Spaces status probe
with gr.Blocks(title="MediBot Healthcare API") as demo:
    gr.Markdown("# ?? MediBot Enterprise Healthcare API")
    gr.Markdown("The backend is active and serving requests.")

# 3. Mount Gradio onto FastAPI
app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
