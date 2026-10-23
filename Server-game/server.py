import asyncio
import json
from pathlib import Path

from aiohttp import WSMsgType, web


HOST = "0.0.0.0"
COMMAND_PORT = 8765
FRAME_PORT = 8766
GAME_FILE = Path(__file__).with_name("game.html")

game_clients = set()
command_clients = set()
frame_sources = set()
frame_viewers = set()
latest_frame = None


async def index(_request):
    return web.FileResponse(GAME_FILE)


async def health(_request):
    return web.json_response({"status": "ok"})


async def _send_command_to_games(message):
    stale = []
    for client in tuple(game_clients):
        try:
            await client.send_str(message)
        except Exception:
            stale.append(client)
    for client in stale:
        game_clients.discard(client)


async def command_socket(request):
    role = request.query.get("role", "controller")
    if role not in {"game", "controller"}:
        raise web.HTTPBadRequest(text="role must be 'game' or 'controller'")

    ws = web.WebSocketResponse(heartbeat=30)
    await ws.prepare(request)
    command_clients.add(ws)
    if role == "game":
        game_clients.add(ws)
        print("[Command] Game connected")
    else:
        print("[Command] Controller connected")

    try:
        async for message in ws:
            if message.type == WSMsgType.TEXT:
                if role == "controller":
                    await _send_command_to_games(message.data)
                else:
                    try:
                        data = json.loads(message.data)
                    except json.JSONDecodeError:
                        print("[Command] Ignored invalid JSON from game")
                        continue
                    if data.get("type") == "score":
                        print(f"[Game score] {data.get('score')} ({data.get('status', '')})")
            elif message.type == WSMsgType.ERROR:
                print(f"[Command] WebSocket error: {ws.exception()}")
    finally:
        command_clients.discard(ws)
        game_clients.discard(ws)
        print(f"[Command] {role} disconnected")

    return ws


async def http_command(request):
    if request.method == "GET":
        return web.json_response({"status": "ok", "endpoint": "command"})

    try:
        data = await request.json()
    except (json.JSONDecodeError, ValueError):
        raise web.HTTPBadRequest(text="Request body must be valid JSON")
    if not isinstance(data, dict):
        raise web.HTTPBadRequest(text="Request body must be a JSON object")

    await _send_command_to_games(json.dumps(data))
    return web.json_response({"ok": True})


async def _broadcast_frame(frame):
    stale = []
    for viewer in tuple(frame_viewers):
        try:
            await viewer.send_bytes(frame)
        except Exception:
            stale.append(viewer)
    for viewer in stale:
        frame_viewers.discard(viewer)


async def frame_socket(request):
    global latest_frame
    role = request.query.get("role", "viewer")
    if role not in {"source", "viewer"}:
        raise web.HTTPBadRequest(text="role must be 'source' or 'viewer'")

    ws = web.WebSocketResponse(heartbeat=30, max_msg_size=2 * 1024 * 1024)
    await ws.prepare(request)

    if role == "source":
        frame_sources.add(ws)
        print("[Frame] Game frame source connected")
    else:
        frame_viewers.add(ws)
        print("[Frame] Viewer connected")
        if latest_frame is not None:
            await ws.send_bytes(latest_frame)

    try:
        async for message in ws:
            if role == "source" and message.type == WSMsgType.BINARY:
                latest_frame = bytes(message.data)
                await _broadcast_frame(latest_frame)
            elif message.type == WSMsgType.ERROR:
                print(f"[Frame] WebSocket error: {ws.exception()}")
    finally:
        frame_sources.discard(ws)
        frame_viewers.discard(ws)
        print(f"[Frame] {role} disconnected")

    return ws


async def run_server():
    command_app = web.Application()
    command_app.router.add_get("/", index)
    command_app.router.add_get("/health", health)
    command_app.router.add_get("/ws/command", command_socket)
    command_app.router.add_route("GET", "/api/command", http_command)
    command_app.router.add_route("POST", "/api/command", http_command)

    frame_app = web.Application()
    frame_app.router.add_get("/health", health)
    frame_app.router.add_get("/ws/frame", frame_socket)

    command_runner = web.AppRunner(command_app)
    frame_runner = web.AppRunner(frame_app)
    await command_runner.setup()
    await frame_runner.setup()

    try:
        await web.TCPSite(command_runner, HOST, COMMAND_PORT).start()
        await web.TCPSite(frame_runner, HOST, FRAME_PORT).start()
        print("\n")
        print("-"*70)
        print(f"Game page:             | http://localhost:{COMMAND_PORT}/")
        print(f"Command socket:        | ws://localhost:{COMMAND_PORT}/ws/command?role=controller")
        print(f"HTTP command API:      | http://localhost:{COMMAND_PORT}/api/command")
        print(f"Frame socket:          | ws://localhost:{FRAME_PORT}/ws/frame?role=viewer")
        print("Press Ctrl+C to stop   | ") 
        print("-"*70)
        print("\n")
        await asyncio.Event().wait()
    finally:
        for ws in tuple(command_clients | frame_sources | frame_viewers):
            await ws.close()
        await command_runner.cleanup()
        await frame_runner.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        print("\nGame server stopped.")
