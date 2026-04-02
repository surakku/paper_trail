# Modal — Qwen3.5-9B Deployment

Serves `Qwen/Qwen3.5-9B` via vLLM on a single A100 40GB.
Costs ~$3/hr while active, $0 when idle (Modal serverless).

## Prerequisites

```bash
pip install modal
modal setup    # authenticate with your Modal account
```

## Deploy

**Step 1 — Pre-download weights into a persistent volume (one-time, ~5 min)**
```bash
modal run modal/deploy_qwen.py::download_weights
```

**Step 2 — Deploy the endpoint**
```bash
modal deploy modal/deploy_qwen.py
```

Modal will print a URL like:
```
https://<your-workspace>--qwen35-9b-serve.modal.run
```

**Step 3 — Set in `backend/.env`**
```
MODAL_LLM_URL=https://<your-workspace>--qwen35-9b-serve.modal.run/v1
MODAL_LLM_MODEL=Qwen/Qwen3.5-9B
MODAL_LLM_API_KEY=     # leave blank
```

## Thinking mode

Qwen3.5-9B has built-in thinking mode (outputs `<think>…</think>` before answering).
It's enabled by default and great for research reasoning.

To disable it for a specific request, pass:
```python
extra_body={"chat_template_kwargs": {"enable_thinking": False}}
```

The backend's `llm_service.py` uses standard chat completions — thinking mode works transparently.

## Recommended inference params

| Use case | temperature | top_p | presence_penalty |
|---|---|---|---|
| Research Q&A (thinking on) | 1.0 | 0.95 | 1.5 |
| Summarization (thinking off) | 0.6 | 0.95 | 0.0 |
