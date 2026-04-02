from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()

PIPELINES_DIR = Path(__file__).parent

# Pipeline file names
PIPELINE_QA = "qa.pipe"
PIPELINE_SUMMARIZE = "summarize.pipe"
PIPELINE_DISCOVERY = "discovery.pipe"
PIPELINE_WEB_SEARCH = "web_search.pipe"
PIPELINE_INGESTION = "ingestion.pipe"


class RocketRideClient:
    """
    Wrapper around the RocketRide Python SDK.

    Pipelines are built visually in the RocketRide VSCode extension and saved as
    .pipe JSON files in this directory. This client loads them and sends inputs
    to the running RocketRide engine.

    Usage:
        async with RocketRideClient() as client:
            result = await client.run(PIPELINE_QA, {"question": "...", "context": "..."})
    """

    def __init__(self) -> None:
        self._uri = os.environ.get("ROCKETRIDE_URI", "ws://localhost:8765")
        self._client = None

    async def __aenter__(self) -> "RocketRideClient":
        try:
            from rocketride import RocketRideClient as _SDK
            self._client = _SDK(uri=self._uri)
            await self._client.__aenter__()
        except Exception:
            # RocketRide engine not running — fallback to direct mode
            self._client = None
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._client:
            await self._client.__aexit__(*args)

    async def run(self, pipeline_file: str, input_data: dict[str, Any]) -> dict[str, Any]:
        pipe_path = PIPELINES_DIR / pipeline_file
        if self._client is None or not pipe_path.exists():
            # Engine not available — return passthrough so the route can handle it directly
            return {"status": "passthrough", "input": input_data}

        await self._client.load_pipeline(str(pipe_path))
        await self._client.send(str(input_data))
        status = await self._client.get_status()
        return {"status": status, "pipeline": pipeline_file}
