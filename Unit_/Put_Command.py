import asyncio
import json
import queue
import threading
from urllib.parse import urlsplit

import aiohttp
import websockets


class Put_Command:
    def __init__(self, endpoint):
        self.endpoint = (endpoint or "").strip()
        scheme = urlsplit(self.endpoint).scheme.lower()
        if scheme not in {"ws", "wss", "http", "https"}:
            raise ValueError("Control API must start with ws://, wss://, http://, or https://")
        self._is_http = scheme in {"http", "https"}
        self._queue = queue.Queue()
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self._thread.start()

    def send_direction(self, direction):
        if not self._stop_event.is_set():
            self._queue.put(json.dumps({"type": "control", "direction": direction}))

    def stop(self):
        self._stop_event.set()

    def _run(self):
        asyncio.run(self._send_loop())

    async def _send_loop(self):
        if self._is_http:
            await self._send_http_loop()
            return

        pending_message = None
        while not self._stop_event.is_set():
            try:
                async with websockets.connect(
                    self.endpoint,
                    open_timeout=3,
                    close_timeout=1,
                    max_size=1024 * 1024,
                    ping_interval=20,
                ) as websocket:
                    print(f"[GameCommand] Connected: {self.endpoint}")
                    while not self._stop_event.is_set():
                        if pending_message is None:
                            try:
                                pending_message = await asyncio.to_thread(
                                    self._queue.get, True, 0.5
                                )
                            except queue.Empty:
                                continue
                        await websocket.send(pending_message)
                        print(f"[GameCommand] Sent: {pending_message}")
                        pending_message = None
            except Exception as exc:
                if pending_message is not None:
                    self._queue.put(pending_message)
                    pending_message = None
                if not self._stop_event.is_set():
                    print(f"[GameCommand] Connection failed: {exc}; retrying in 1 second")
                    await asyncio.sleep(1)

    async def _send_http_loop(self):
        pending_message = None
        timeout = aiohttp.ClientTimeout(total=3)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            while not self._stop_event.is_set():
                if pending_message is None:
                    try:
                        pending_message = await asyncio.to_thread(
                            self._queue.get, True, 0.5
                        )
                    except queue.Empty:
                        continue
                try:
                    async with session.post(
                        self.endpoint,
                        data=pending_message,
                        headers={"Content-Type": "application/json"},
                    ) as response:
                        response.raise_for_status()
                        await response.read()
                    print(f"[GameCommand] HTTP sent: {pending_message}")
                    pending_message = None
                except Exception as exc:
                    if pending_message is not None:
                        self._queue.put(pending_message)
                        pending_message = None
                    if not self._stop_event.is_set():
                        print(f"[GameCommand] HTTP request failed: {exc}; retrying in 1 second")
                        await asyncio.sleep(1)
