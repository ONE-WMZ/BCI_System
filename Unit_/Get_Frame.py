import asyncio
import threading

import cv2
import numpy as np
import websockets


class Get_Frame:
    def __init__(self, endpoint):
        self.endpoint = (endpoint or "").strip()
        if not self.endpoint.startswith(("ws://", "wss://")):
            raise ValueError("Frame API must be a WebSocket URL starting with ws:// or wss://")
        self._latest_frame = None
        self._frame_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self._thread.start()

    def get_frame(self):
        with self._frame_lock:
            return self._latest_frame

    def stop(self):
        self._stop_event.set()

    def _run(self):
        asyncio.run(self._receive_frames())

    async def _receive_frames(self):
        while not self._stop_event.is_set():
            try:
                async with websockets.connect(
                    self.endpoint,
                    max_size=2 * 1024 * 1024,
                    ping_interval=20,
                ) as websocket:
                    print(f"[GameFrame] Connected: {self.endpoint}")
                    while not self._stop_event.is_set():
                        try:
                            message = await asyncio.wait_for(websocket.recv(), timeout=0.5)
                        except asyncio.TimeoutError:
                            continue
                        if not isinstance(message, bytes):
                            continue

                        encoded = np.frombuffer(message, dtype=np.uint8)
                        frame = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
                        if frame is None:
                            continue
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        frame = frame.astype(np.float32) / 127.5 - 1.0
                        frame = cv2.flip(frame, 0)
                        with self._frame_lock:
                            self._latest_frame = frame
            except Exception as exc:
                if not self._stop_event.is_set():
                    print(f"[GameFrame] Connection failed: {exc}; retrying in 1 second")
                    await asyncio.sleep(1)


class Get_Camera:
    # get frames from Camera
    def __init__(self, camera_index=1):
        self.camera_index = camera_index
        self._latest_frame = None
        self._frame_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread = None
        self._capture = None

    def start(self):
        self._capture = cv2.VideoCapture(self.camera_index)
        if not self._capture.isOpened():
            self._capture.release()
            self._capture = None
            raise RuntimeError(
                f"Unable to open camera {self.camera_index + 1} (device index {self.camera_index})"
            )
        self._thread = threading.Thread(target=self._read_frames, daemon=True)
        self._thread.start()

    def get_frame(self):
        with self._frame_lock:
            return self._latest_frame

    def stop(self):
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=1)
        if self._capture is not None:
            self._capture.release()
            self._capture = None

    def _read_frames(self):
        try:
            while not self._stop_event.is_set():
                success, frame = self._capture.read()
                if not success:
                    self._stop_event.wait(0.02)
                    continue
                frame = cv2.flip(frame, 0)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = frame.astype(np.float32) / 127.5 - 1.0
                with self._frame_lock:
                    self._latest_frame = frame
        finally:
            if self._capture is not None:
                self._capture.release()
