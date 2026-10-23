import os
import time
import numpy as np
from collections import deque
from datetime import datetime
from psychopy import core, event, visual

from Unit_.LSL_ import LSL_Recorder
from Unit_.Stimuli_ import Stimuli_SSVEP
from Unit_.CCA_ import cca_ssvep
from Unit_.Get_Frame import Get_Camera, Get_Frame
from Unit_.Put_Command import Put_Command


# ! Realtime state
score = 0
current_pred_dir = "+"


# ! Task-realtime 
def Task_realtime(info_):
    global score, current_pred_dir
    # Select_screen = info_.get("Select_screen")
    Device_name = info_.get("Device_name")
    Task = info_.get("Task")
    best_th = info_.get("Threshold", 0.5)
    folder_path = info_.get("Folder_path")
    if not folder_path:
        print("[Realtime] Select a data folder before starting realtime.")
        return
    realtime_dir = os.path.join(folder_path, "realtime")
    os.makedirs(realtime_dir, exist_ok=True)
    recognition_index = 0

    def save_recognition(direction, eeg):
        nonlocal recognition_index
        while True:
            recognition_index += 1
            filename = f"{datetime.now():%Y%m%d_%H%M%S_%f}_{recognition_index:06d}_{direction}.npy"
            path = os.path.join(realtime_dir, filename)
            try:
                target = open(path, "xb")
            except FileExistsError:
                continue
            with target:
                np.save(target, eeg)
            print(f"[Realtime] Saved {direction}: {path} | shape={eeg.shape}")
            return
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
    
    command_client = None
    command_api = info_.get("Command_API")
    if Task in {"SSVEP", "PD-SSVEP"} and command_api:
        try:
            command_client = Put_Command(command_api)
            command_client.start()
        except (OSError, ValueError) as exc:
            print(f"[Realtime] {exc}")
    if Task == "SSVEP" and command_client is None:
        print("[Realtime] Command_API is not configured; game control is disabled")

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
                            detected_eeg = stim_data[-required_2s_samples:, :].copy()
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
                            detected_eeg = stim_data[-required_3s_samples:, :].copy()
                            detected = True
                    if detected:
                        save_recognition(current_pred_dir, detected_eeg)
                        if command_client is not None:
                            command_client.send_direction(current_pred_dir)
                        data_buffer.clear()
                    last_analysis_time = t
        finally:
            if command_client is not None:
                command_client.stop()
            time.sleep(0.5)
            stimuli.exit()

    # ! PD-SSVEP
    elif Task == "PD-SSVEP":
        try:
            frame_client = (Get_Camera(int(info_.get("Camera_Index", 1)))
                            if info_.get("Use_Camera", False)
                            else Get_Frame(info_.get("Frame_API", "")))
            frame_client.start()
        except (ValueError, RuntimeError) as exc:
            print(f"[PD-SSVEP realtime] {exc}")
            if command_client is not None:
                command_client.stop()
            stimuli.exit()
            return
        score = 0
        current_pred_dir = "-"
        # SSVEP stimuli
        # stimuli = Stimuli_SSVEP(block_size=200)
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
                _frame = frame_client.get_frame()
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
                                detected_eeg = stim_data[-required_2s_samples:, :].copy()
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
                                detected_eeg = stim_data[-required_3s_samples:, :].copy()
                                detected = True
                        if detected:
                            save_recognition(current_pred_dir, detected_eeg)
                            if command_client is not None:
                                command_client.send_direction(current_pred_dir)
                            data_buffer.clear()
                        last_analysis_time = t
                except Exception as e:
                    print(f"[EEG Analysis error] {e}")
        finally:
            frame_client.stop()
            if command_client is not None:
                command_client.stop()
            time.sleep(0.5)
            stimuli.exit()

    elif Task == "MI":
        print("Not this model")

    else:
        print("Not this model")
        
    print("[Realtime End]")


