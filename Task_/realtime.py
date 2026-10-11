import cv2
import time
import json
import asyncio
import threading
import websockets
import webbrowser
import http.server
import numpy as np
import socketserver
from collections import deque
from psychopy import core, event, visual

from Unit_.LSL_ import LSL_Recorder
from Unit_.Stimuli_ import Stimuli_SSVEP
from Unit_.CCA_ import cca_ssvep


# ! Web Services
# Shared state — used by all tasks
latest_frame = None
clients = set()
score = 0
current_pred_dir = "+"
ws_loop = None
frame_lock = threading.Lock()
_web_services_started = False

# WebSocket handler (receive image + score) 
async def _ws_handler(websocket):
    global latest_frame, score
    clients.add(websocket)
    try:
        async for message in websocket:
            try:
                # receive image (binary)
                if isinstance(message, bytes):
                    np_arr = np.frombuffer(message, np.uint8)
                    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                    if frame is not None:
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        frame = frame.astype(np.float32) / 127.5 - 1.0
                        frame = cv2.flip(frame, 0)   # vertical flip
                        with frame_lock:
                            latest_frame = frame
                # receive JSON message (score)
                elif isinstance(message, str):
                    data = json.loads(message)
                    if data.get("type") == "score":
                        new_score = data.get("score", 0)
                        if new_score != score:
                            now = time.strftime('%H:%M:%S')
                            print(f"[SCORE] {score} → {new_score} | exp_t={core.getTime():.3f}s | {now}")
                        score = new_score
            except Exception as e:
                print(f"[WS handler error] {e}")
    finally:
        clients.remove(websocket)

async def _start_ws():
    global ws_loop
    ws_loop = asyncio.get_running_loop()
    async with websockets.serve(_ws_handler, "localhost", 8765):
        print("WebSocket started: ws://localhost:8765")
        await asyncio.Future()

def _run_ws():
    asyncio.run(_start_ws())

#  HTTP server
def _start_http():
    PORT = 8000
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("HTTP server: http://localhost:8000")
        httpd.serve_forever()


#  Auto-open browser 
def _open_browser():
    time.sleep(1.0)  # wait for servers to start
    webbrowser.open("http://localhost:8000/Viz_/Unit_/game.html")


#  Send control command to WebSocket clients 
async def _send_control(direction):
    if len(clients) == 0:
        return
    msg = json.dumps({
        "type": "control",
        "direction": direction
    })
    await asyncio.gather(*[ws.send(msg) for ws in clients])


# Thread-safe: send control command from the PsychoPy main thread.
def send_control_sync(direction):
    global ws_loop
    if ws_loop is None:
        print("[WARN] ws_loop not ready yet")
        return
    try:
        future = asyncio.run_coroutine_threadsafe(_send_control(direction), ws_loop)
        future.result(timeout=2)
        now = time.strftime('%Y-%m-%d %H:%M:%S')
        print(f"[ACTION] {direction} | exp_t={core.getTime():.3f}s | {now}")
    except Exception as e:
        print(f"[send_control error] {e}")


# Send shutdown message to all WebSocket clients (close game page)
async def _send_shutdown():
    if len(clients) == 0:
        return
    msg = json.dumps({"type": "shutdown"})
    await asyncio.gather(*[ws.send(msg) for ws in clients])


def send_shutdown_sync():
    global ws_loop
    if ws_loop is None:
        print("[WARN] ws_loop not ready, cannot send shutdown")
        return
    try:
        future = asyncio.run_coroutine_threadsafe(_send_shutdown(), ws_loop)
        future.result(timeout=2)
        print("[SHUTDOWN] Game page close command sent")
    except Exception as e:
        print(f"[send_shutdown error] {e}")


# Start HTTP + WebSocket servers + open browser 
def start_web_services():
    global _web_services_started
    if _web_services_started:
        return
    _web_services_started = True
    threading.Thread(target=_run_ws, daemon=True).start()
    threading.Thread(target=_start_http, daemon=True).start()
    threading.Thread(target=_open_browser, daemon=True).start()


# ! Task-realtime 
def Task_realtime(info_):
    global latest_frame, score, current_pred_dir
    # Select_screen = info_.get("Select_screen")
    Device_name = info_.get("Device_name")
    Task = info_.get("Task")
    best_th = info_.get("Threshold", 0.5)
    # Init LSL
    if not Device_name:
        print("[No LSL stream]")
        return
    else:
        recorder = LSL_Recorder(channels=[], stream_name=Device_name)
        print("Waiting EEG Stable...")
    time.sleep(2.0)
    # Init Stimuli
    stimuli = Stimuli_SSVEP(block_size=200)
    freqs_list = stimuli.freqs
    # Init CCA
    Algorithm = info_.get("Algorithm")
    fs = 250
    selected_chs = [6, 7, 8, 9, 13]
    if Algorithm == "CCA":
        Algorithm_ = cca_ssvep(freqs_list, fs=fs, n_harmonics=2)
    if Algorithm == "FBCCA":
        print("Not this model")
        pass
    # Init buffer
    max_samples = int(4 * fs)
    data_buffer = deque(maxlen=max_samples)
    last_analysis_time = core.getTime()
    analysis_interval = 0.5
    # Start web services
    start_web_services()

    # ! SSVEP
    if Task == "SSVEP":
        current_pred_dir = '+'
        stimuli.countdown_text(text='Ready', show_time=True, seconds=3)
        stimuli_dict = stimuli.create_stimuli()
        try:
            recorder.clear_buffer()     # clear old
            print(f"[START] SSVEP | {time.strftime('%Y-%m-%d %H:%M:%S')}")
            while True:
                if event.getKeys(['escape']):
                    break
                t = core.getTime()
                stimuli.update_stimuli(stimuli_dict, t)
                for stim_info in stimuli_dict.values():
                    stim_info['stim'].draw()
                    stim_info['arrow'].draw()
                stimuli.countdown_text(f"{current_pred_dir}")
                stimuli.win.flip()
                # EEG -> CCA
                chunk, _ = recorder.get_new()
                if len(chunk) > 0:
                    data_buffer.extend(chunk)
                if t - last_analysis_time >= analysis_interval:
                    required_2s_samples = int(2 * fs)
                    required_3s_samples = int(3 * fs)
                    detected = False
                    # 2s
                    if len(data_buffer) >= required_2s_samples:
                        stim_data = np.array(data_buffer)
                        eeg_2s = stim_data[-required_2s_samples:, :]
                        eeg_2s = Algorithm_.select_channel(eeg_2s, channel_select=selected_chs)
                        eeg_2s = Algorithm_.bandpass_filter(eeg_2s, lowcut=6, highcut=31, order=4)
                        pred_dir_2s, scores_2s = Algorithm_.classify(eeg_2s)
                        if scores_2s[pred_dir_2s] > best_th:
                            current_pred_dir = pred_dir_2s
                            detected = True
                    # 3s
                    if not detected and len(data_buffer) >= required_3s_samples:
                        stim_data = np.array(data_buffer)
                        eeg_3s = stim_data[-required_3s_samples:, :]
                        eeg_3s = Algorithm_.select_channel(eeg_3s, channel_select=selected_chs)
                        eeg_3s = Algorithm_.bandpass_filter(eeg_3s, lowcut=6, highcut=31, order=4)
                        pred_dir_3s, scores_3s = Algorithm_.classify(eeg_3s)
                        if scores_3s[pred_dir_3s] > best_th:
                            current_pred_dir = pred_dir_3s
                            detected = True
                    if detected:
                        send_control_sync(current_pred_dir)
                        data_buffer.clear()
                    last_analysis_time = t
        finally:
            send_shutdown_sync()
            time.sleep(0.5)
            stimuli.exit()

    # ! PD-SSVEP
    elif Task == "PD-SSVEP":
        # Reset per-run state
        with frame_lock:
            latest_frame = None
        score = 0
        current_pred_dir = "-"
        # SSVEP stimuli
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
        # score display
        score_text = visual.TextStim(
            win=stimuli.win,
            text="Score: 0",
            pos=(0, 230),
            height=30,
            color='yellow'
        )
        predict_text = visual.TextStim(
            win=stimuli.win,
            text="Predict: -",
            pos=(0, -230),
            height=25,
            color='cyan'
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
        recorder.clear_buffer()  
        print(f"[START] PD-SSVEP | {time.strftime('%Y-%m-%d %H:%M:%S')}")
        try:
            while True:
                keys = event.getKeys()
                if keys:
                    if 'escape' in keys:
                        break
                t = core.getTime()
                # stim update
                stimuli.update_stimuli(stimuli_dict, t)
                # plot game
                with frame_lock:
                    _frame = latest_frame
                if _frame is not None:
                    game_stim.image = _frame
                border.draw()
                game_stim.draw()
                score_text.text = f"Score: {score}"
                score_text.draw()
                predict_text.text = f"Predict: {current_pred_dir}"
                predict_text.draw()
                # plot stim
                for stim_info in stimuli_dict.values():
                    stim_info['stim'].draw()
                    stim_info['arrow'].draw()
                stimuli.win.flip()
                # EEG -> CCA
                try:
                    chunk, _ = recorder.get_new()
                    if len(chunk) > 0:
                        data_buffer.extend(chunk)
                    if t - last_analysis_time >= analysis_interval:
                        required_2s_samples = int(2 * fs)
                        required_3s_samples = int(3 * fs)
                        detected = False
                        # 2s
                        if len(data_buffer) >= required_2s_samples:
                            stim_data = np.array(data_buffer)
                            eeg_2s = stim_data[-required_2s_samples:, :]
                            eeg_2s = Algorithm_.select_channel(eeg_2s, selected_chs)
                            eeg_2s = Algorithm_.bandpass_filter(eeg_2s, 6, 31, 4)
                            pred_dir_2s, score_2s = Algorithm_.classify(eeg_2s)
                            if score_2s[pred_dir_2s] > best_th:
                                current_pred_dir = pred_dir_2s
                                detected = True
                        # 3s
                        if not detected and len(data_buffer) >= required_3s_samples:
                            stim_data = np.array(data_buffer)
                            eeg_3s = stim_data[-required_3s_samples:, :]
                            eeg_3s = Algorithm_.select_channel(eeg_3s, selected_chs)
                            eeg_3s = Algorithm_.bandpass_filter(eeg_3s, 6, 31, 4)
                            pred_dir_3s, score_3s = Algorithm_.classify(eeg_3s)
                            if score_3s[pred_dir_3s] > best_th:
                                current_pred_dir = pred_dir_3s
                                detected = True
                        if detected:
                            send_control_sync(current_pred_dir)
                            data_buffer.clear()
                        last_analysis_time = t
                except Exception as e:
                    print(f"[EEG Analysis error] {e}")
        finally:
            send_shutdown_sync()
            time.sleep(0.5)
            stimuli.exit()

    elif Task == "MI":
        print("Not this model")

    else:
        print("Not this model")
        
    print("[Realtime End]")


