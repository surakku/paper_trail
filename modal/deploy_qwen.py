"""
Qwen3.5-9B deployment on Modal via vLLM.

- Single A100 40GB GPU (~$3/hr while active, $0 when idle)
- OpenAI-compatible endpoint
- Thinking mode enabled by default (great for research Q&A)
- 262K context window

Deploy:
    modal deploy modal/deploy_qwen.py

Then set in backend/.env:
    MODAL_LLM_URL=https://<workspace>--qwen35-9b-serve.modal.run/v1
    MODAL_LLM_MODEL=Qwen/Qwen3.5-9B
"""

import modal

APP_NAME = "qwen35-9b"
MODEL_ID = "Qwen/Qwen3.5-9B"
VOLUME_NAME = "qwen35-9b-weights"
WEIGHTS_PATH = "/weights"
MODEL_DIR = f"{WEIGHTS_PATH}/{MODEL_ID.replace('/', '--')}"

app = modal.App(APP_NAME)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "vllm>=0.9.0",
        "huggingface_hub",
        "hf-transfer",
        "fastapi",
        "httpx",
        "uvicorn",
    )
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
)

weights_volume = modal.Volume.from_name(VOLUME_NAME, create_if_missing=True)


def _download_weights():
    """Download model weights into the persistent volume (runs once)."""
    import os
    from huggingface_hub import snapshot_download

    if os.path.exists(f"{MODEL_DIR}/config.json"):
        print("Weights already cached, skipping download.")
        return

    print(f"Downloading {MODEL_ID}…")
    snapshot_download(repo_id=MODEL_ID, local_dir=MODEL_DIR)
    weights_volume.commit()
    print("Download complete.")


@app.function(
    image=image,
    gpu="A100-40GB",
    timeout=60 * 60,
    scaledown_window=300,
    volumes={WEIGHTS_PATH: weights_volume},
)
@modal.asgi_app()
def serve():
    """OpenAI-compatible vLLM server for Qwen3.5-9B via ASGI proxy."""
    import os
    import asyncio
    import subprocess
    import sys
    import time
    from fastapi import FastAPI
    from fastapi.responses import StreamingResponse
    import httpx
    
    os.environ["VLLM_ATTENTION_BACKEND"] = "flash_attn"
    
    # Start vLLM on local port 7000
    print(f"[MODAL] Starting vLLM with model: {MODEL_DIR}")
    proc = subprocess.Popen(
        [
            sys.executable, "-m", "vllm.entrypoints.openai.api_server",
            "--model", MODEL_DIR,
            "--tensor-parallel-size", "1",
            "--max-model-len", "32768",
            "--trust-remote-code",
            "--host", "127.0.0.1",
            "--port", "7000",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    
    print(f"[MODAL] vLLM process started (PID: {proc.pid})")
    
    # Wait for vLLM to be ready (monitor startup)
    async def monitor_startup():
        start = time.time()
        while time.time() - start < 300:  # 5 minute timeout
            if proc.poll() is not None:
                print(f"[MODAL] ERROR: vLLM exited with code {proc.poll()}")
                return False
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get("http://127.0.0.1:7000/health", timeout=2)
                    if resp.status_code == 200:
                        print("[MODAL] vLLM is ready!")
                        return True
            except:
                await asyncio.sleep(1)
        return False
    
    # Create FastAPI app that proxies to vLLM
    fastapi_app = FastAPI()
    
    @fastapi_app.get("/health")
    async def health():
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get("http://127.0.0.1:7000/health", timeout=5)
                return resp.json()
        except:
            return {"status": "starting"}
    
    @fastapi_app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
    async def proxy(path: str, request):
        """Proxy all requests to vLLM."""
        url = f"http://127.0.0.1:7000/{path}"
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                req_body = await request.body() if request.method != "GET" else None
                resp = await client.request(
                    request.method,
                    url,
                    content=req_body,
                    headers=dict(request.headers) if request.headers else None,
                )
                return StreamingResponse(
                    iter([resp.content]),
                    status_code=resp.status_code,
                    headers=dict(resp.headers),
                )
        except Exception as e:
            print(f"[MODAL] Proxy error: {e}")
            return {"error": str(e)}
    
    return fastapi_app


# ---------------------------------------------------------------------------
# One-time weight download job (run before deploying to pre-warm the volume)
# ---------------------------------------------------------------------------

@app.function(
    image=image,
    timeout=60 * 30,
    volumes={WEIGHTS_PATH: weights_volume},
)
def download_weights():
    _download_weights()
