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
    scaledown_window=300,  # spin down after 5 min idle
    volumes={WEIGHTS_PATH: weights_volume},
)
@modal.asgi_app()
def serve():
    """OpenAI-compatible vLLM server for Qwen3.5-9B."""
    from vllm.engine.arg_utils import AsyncEngineArgs
    from vllm.entrypoints.openai.api_server import create_server

    engine_args = AsyncEngineArgs(
        model=MODEL_DIR,
        tensor_parallel_size=1,
        trust_remote_code=True,
        reasoning_parser="qwen3",     # enables <think>…</think> parsing
        max_model_len=32768,           # cap at 32K for practical latency
        mem_fraction_static=0.8,
        enable_auto_tool_choice=True,
    )

    return create_server(engine_args=engine_args)


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
