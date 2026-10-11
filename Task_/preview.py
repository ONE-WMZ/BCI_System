import cv2
import time
import asyncio
import threading
import webbrowser
import websockets
import numpy as np
import http.server
import socketserver


from psychopy import visual, core, event 
from Unit_.Stimuli_ import Stimuli_SSVEP

# ! 
def Task_preview(info_):
    task = info_.get("Task")
    # Select_screen = info_.get("Select_screen")
    preview_time = 5

    if task == "SSVEP":
        stimuli = Stimuli_SSVEP(block_size=200)
        stimuli.countdown_text(text='preview', show_time=True, seconds=2)
        stimuli_dict = stimuli.create_stimuli()
        fixation = visual.TextStim(stimuli.win, text='+', color='white', height=50)
        try:
            clock = core.Clock()
            while clock.getTime() < preview_time:
                t = clock.getTime()
                stimuli.update_stimuli(stimuli_dict, t)
                for stim_info in stimuli_dict.values():
                    stim_info['stim'].draw()
                    stim_info['arrow'].draw()
                fixation.draw()
                stimuli.win.flip()
                if event.getKeys(['escape']):
                    break
        except KeyboardInterrupt:
            print("[Keyboard Interrupt]")
        finally:
            stimuli.exit()
            
    elif task == "PD-SSVEP":
        global latest_frame, clients
        latest_frame = None
        clients = set()
        ws_loop = None
        # WebSocket (get image + send control)
        async def handler(websocket):
            global latest_frame, clients
            clients.add(websocket)
            try:
                async for message in websocket:
                    try:
                        #  get image (bit-2)
                        if isinstance(message, bytes):
                            np_arr = np.frombuffer(message, np.uint8)
                            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                            if frame is not None:
                                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                frame = frame.astype(np.float32) / 127.5 - 1.0
                                frame = cv2.flip(frame, 0)   # Vertical flip
                                latest_frame = frame
                    except:
                        pass
            finally:
                clients.remove(websocket)

        async def start_ws():
            nonlocal ws_loop
            ws_loop = asyncio.get_running_loop()
            async with websockets.serve(handler, "localhost", 8765):
                print("WebSocket started: ws://localhost:8765")
                await asyncio.Future()
        threading.Thread(
            target=lambda: asyncio.run(start_ws()),
            daemon=True
        ).start()
        # Send shutdown message to game page
        async def _send_shutdown():
            if len(clients) == 0:
                return
            import json
            msg = json.dumps({"type": "shutdown"})
            await asyncio.gather(*[ws.send(msg) for ws in clients])
        def send_shutdown_sync():
            if ws_loop is None:
                return
            try:
                future = asyncio.run_coroutine_threadsafe(_send_shutdown(), ws_loop)
                future.result(timeout=2)
                print("[SHUTDOWN] Game page close command sent")
            except Exception as e:
                print(f"[send_shutdown error] {e}")
        # HTTP (load HTML)
        def start_http():
            PORT = 8000
            Handler = http.server.SimpleHTTPRequestHandler
            with socketserver.TCPServer(("", PORT), Handler) as httpd:
                print("HTTP server: http://localhost:8000")
                httpd.serve_forever()
        threading.Thread(target=start_http, daemon=True).start()
        # auto open html
        def open_browser():
            time.sleep(1.0) # wait for svevr start 
            # webbrowser.open(html_url)
            webbrowser.open("http://localhost:8000/Viz_/Unit_/game.html")

        threading.Thread(target=open_browser, daemon=True).start()

        # SSVEP
        stimuli = Stimuli_SSVEP(block_size=200)
        stimuli.countdown_text(text='Ready', show_time=True, seconds=3)
        stimuli_dict = stimuli.create_stimuli()
        # game block
        game_stim = visual.ImageStim(
            win=stimuli.win,
            image=None,
            size=(400, 400),
            pos=(0, 0),
            units='pix'
        )
        # border
        border = visual.Rect(
            win=stimuli.win,
            width=405,
            height=405,
            pos=(0, 0),
            lineColor='white',
            lineWidth=3,
            fillColor=None
        )
        # main()
        try:
            clock = core.Clock()
            while clock.getTime() < preview_time:
                t = clock.getTime()
                # updata SSVEP 
                stimuli.update_stimuli(stimuli_dict, t)
                # game 
                if latest_frame is not None:
                    game_stim.image = latest_frame
                border.draw()
                game_stim.draw()
                # stimuli 
                for stim_info in stimuli_dict.values():
                    stim_info['stim'].draw()
                    stim_info['arrow'].draw()
                stimuli.win.flip()
                if event.getKeys(['escape']):
                    break
        finally:
            send_shutdown_sync()
            time.sleep(0.5)
            stimuli.exit()

    elif task == "MI":
        stimuli = Stimuli_SSVEP(block_size=200)
        stimuli.countdown_text(text='preview', show_time=True, seconds=2)
        mi_text = visual.TextStim(
            stimuli.win,
            text='Imagine movement: Left hand',  
            pos=(0,0),
            height=50,
            color='white'
        )
        try:
            clock = core.Clock()
            while clock.getTime() < preview_time:
                t = clock.getTime()
                mi_text.draw()
                stimuli.win.flip()
                if event.getKeys(['escape']):
                    break
        except KeyboardInterrupt:
            print("[Keyboard Interrupt]")
        finally:
            stimuli.exit()
    else :
        print("[Not this model]")

    print("[Preview finished]")

