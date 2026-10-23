import asyncio
import json
import queue
import threading
from urllib.parse import urlsplit

import aiohttp
import websockets

from Unit_.Command_API import load_commands, send_command


class Put_Command:
    def __init__(self, endpoint):
        self.endpoint = (endpoint or "").strip()
        scheme = urlsplit(self.endpoint).scheme.lower()
        self.commands = None
        if scheme not in {"ws", "wss", "http", "https"}:
            self.commands = load_commands(self.endpoint)
        self._is_http = scheme in {"http", "https"}
        self._queue = queue.Queue()
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self._thread.start()

    def send_direction(self, direction):
        if not self._stop_event.is_set():
            if self.commands is not None:
                normalized = direction.strip().casefold()
                name = next((name for name in self.commands
                             if name.strip().casefold() == normalized), None)
                if name is None:
                    print(f"[GameCommand] No command configured for direction: {direction}", flush=True)
                    return
                self._queue.put(name)
                print(f"[GameCommand] Queued direction {direction} -> {name}", flush=True)
            else:
                self._queue.put(json.dumps({"type": "control", "direction": direction}))

    def stop(self):
        self._stop_event.set()

    def _run(self):
        asyncio.run(self._send_loop())

    async def _send_loop(self):
        if self.commands is not None:
            await self._send_commands_loop()
            return
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

    async def _send_commands_loop(self):
        while not self._stop_event.is_set():
            try:
                name = await asyncio.to_thread(self._queue.get, True, 0.5)
            except queue.Empty:
                continue
            try:
                status = await asyncio.to_thread(send_command, self.commands[name])
                print(f"[GameCommand] {name}: HTTP {status}")
            except Exception as exc:
                print(f"[GameCommand] {name} failed: {exc}")

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
