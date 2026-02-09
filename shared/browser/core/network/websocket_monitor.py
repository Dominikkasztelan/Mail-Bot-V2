import asyncio
import json
from typing import Any

from playwright.async_api import Page, WebSocket


class WebSocketMonitor:
    """
    Monitors WebSocket traffic to detect generation events without DOM scraping.
    """

    def __init__(self, page: Page) -> None:
        self.page = page
        self.generation_events: list[dict[str, Any]] = []
        self._listening = False

    async def start_listening(self) -> None:
        """Attaches listener to websocket frames."""
        if self._listening:
            return
        self.page.on("websocket", self._on_websocket)
        self._listening = True

    def _on_websocket(self, ws: WebSocket) -> None:
        ws.on("framereceived", self._on_frame_received)

    def _on_frame_received(self, frame_payload: str | bytes) -> None:
        """
        Parses incoming WS frames to find generation completion events.
        Leonardo.ai typically uses GraphQL over WS or similar real-time protocol.
        """
        try:
            if isinstance(frame_payload, bytes):
                decoded = frame_payload.decode("utf-8")
            else:
                decoded = frame_payload

            # This logic needs to be reverse-engineered from actual traffic.
            # Hypothetical example looking for "generationComplete" or specific GraphQL subscription updates.
            if "generation" in decoded and "complete" in decoded.lower():
                json_payload = json.loads(decoded)
                self.generation_events.append(json_payload)

        except Exception:
            # Ignore parsing errors for non-JSON frames
            pass

    async def wait_for_generation_complete(self, timeout: int = 60) -> dict[str, Any] | None:
        """Waits for a generation event to appear in the log."""
        start_time = asyncio.get_event_loop().time()
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            if self.generation_events:
                return self.generation_events.pop()
            await asyncio.sleep(0.5)
        return None
