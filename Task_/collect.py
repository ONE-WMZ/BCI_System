import os
import csv
import time
import json
import traceback
import numpy as np
from datetime import datetime
from psychopy import core, event, visual

from Unit_.LSL_ import LSL_Recorder
from Unit_.Stimuli_ import Stimuli_SSVEP
from Unit_.Get_Frame import Get_Camera, Get_Frame


def Task_collect(info_):    
    Device_name = info_.get("Device_name")
    # ! Init LSL
    if not Device_name:
        print("[No LSL stream]")
        return  
    else:
        recorder = LSL_Recorder(channels=None, stream_name=Device_name)
        print("Waiting EEG Stable...")
    time.sleep(2)

    Folder_path = info_.get("Folder_path")
    if not Folder_path:
        print("[Error] Folder_path is empty, cannot save data.")
        return
    Task = info_.get("Task")
    Task_Duration = info_.get("Task_Duration")
    Rest_Duration = info_.get("Rest_Duration")
    T_rest = Rest_Duration
    T_stim = Task_Duration
    save_dir = Folder_path
    os.makedirs(save_dir, exist_ok=True)

    events = []
    freqs_list = None

    # ! save person info
    def _save_person_info():
        experiment_info = {
            "ID": info_.get("ID"),
            "Name": info_.get("Name"),
            "Age": info_.get("Age"),
            "Gender": info_.get("Gender"),
            "task": info_.get("Task"),
            "freqs_list": freqs_list,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        with open(os.path.join(save_dir, "person_info.json"), "w", encoding="utf-8") as f:
            json.dump(experiment_info, f, indent=4, ensure_ascii=False)
        print("[Collect] person_info.json saved")

    # ! save events
    def _save_events_csv():
        if not events:
            print("[Collect] Warning: No events to save")
            return
        try:
            with open(os.path.join(save_dir, "events.csv"), "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=events[0].keys())
                writer.writeheader()
                writer.writerows(events)
            print("[Collect] events.csv saved successfully")
        except Exception as e:
            print(f"[Collect] Warning: Failed to save events.csv — {e}")

    # ! SSVEP
    if Task == "SSVEP":
        try:
            # Init Stimuli
            stimuli = Stimuli_SSVEP(block_size=200)
            freqs_list = stimuli.freqs
            stimuli_dict = stimuli.create_stimuli()

            # Save person_info.json 
            _save_person_info()

            events = []
            directions = ['up', 'down', 'left', 'right', '+']
            for act in directions:
                # Rest
                stimuli.countdown_text("Rest", True, int(T_rest))
                # prompt
                stimuli.countdown_text(f'Act: {act}', True, 2)
                # Stimuli
                stim_chunks = []
                stim_clock = core.Clock()
                fixation = visual.TextStim(stimuli.win, text='+', color='white', height=50)
                recorder.clear_buffer()  # clear old
                while stim_clock.getTime() < T_stim:
                    t = stim_clock.getTime()
                    stimuli.update_stimuli(stimuli_dict, t)
                    for stim_info in stimuli_dict.values():
                        stim_info['stim'].draw()
                        stim_info['arrow'].draw()
                    fixation.draw()
                    stimuli.win.flip()
                    chunk, ts = recorder.get_new()
                    if len(chunk) > 0:
                        stim_chunks.append(chunk)
                    if event.getKeys(['escape']):
                        break 
                if stim_chunks:
                    stim_data = np.vstack(stim_chunks)
                    np.save(os.path.join(save_dir, f"{act}.npy"), stim_data)
                    data_shape = stim_data.shape
                else:
                    print("[collect data is None]")
                    data_shape = None
                events.append({
                    "direction": act,
                    "duration_sec": T_stim,
                    "data_shape": data_shape,
                })
        except KeyboardInterrupt:
            print("[Escape key]")
        except Exception as e:
            print(f"[ERROR] Exception during SSVEP collection: {e}")
            traceback.print_exc()
        finally:
            _save_events_csv()
            try:
                stimuli.exit()
            except BaseException:
                pass  

    # ! PD-SSVEP
    elif Task == "PD-SSVEP":
        frame_client = None
        try:
            frame_client = (Get_Camera(int(info_.get("Camera_Index", 1)))
                            if info_.get("Use_Camera", False)
                            else Get_Frame(info_.get("Frame_API", "")))
            frame_client.start()
            # SSVEP
            stimuli = Stimuli_SSVEP(block_size=200)
            freqs_list = stimuli.freqs
            stimuli_dict = stimuli.create_stimuli()

            # Save person_info.json
            _save_person_info()

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
            events = []
            directions = ['up', 'down', 'left', 'right', '+']
            for act in directions:
                # Rest
                stimuli.countdown_text("Rest", True, int(T_rest))
                # prompt
                stimuli.countdown_text(f'Act: {act}', True, 2)
                # ! Stimuli
                stim_chunks = []
                stim_clock = core.Clock()
                recorder.clear_buffer()  # clear old
                while stim_clock.getTime() < T_stim:
                    t = stim_clock.getTime()
                    stimuli.update_stimuli(stimuli_dict, t)
                    # game
                    latest_frame = frame_client.get_frame()
                    if latest_frame is not None:
                        game_stim.image = latest_frame
                    border.draw()
                    game_stim.draw()
                    # stim
                    for stim_info in stimuli_dict.values():
                        stim_info['stim'].draw()
                        stim_info['arrow'].draw()
                    stimuli.win.flip()
                    chunk, ts = recorder.get_new()
                    if len(chunk) > 0:
                        stim_chunks.append(chunk)
                    if event.getKeys(['escape']):
                        break  
                if stim_chunks:
                    stim_data = np.vstack(stim_chunks)
                    np.save(os.path.join(save_dir, f"{act}.npy"), stim_data)
                    data_shape = stim_data.shape
                else:
                    print("[collect data is None]")
                    data_shape = None
                events.append({
                    "direction": act,
                    "duration_sec": T_stim,
                    "data_shape": data_shape,
                })
            
        except KeyboardInterrupt:
            print("[Escape key]")
        except Exception as e:
            print(f"[ERROR] Exception during PD-SSVEP collection: {e}")
            traceback.print_exc()
        finally:
            _save_events_csv()
            if frame_client is not None:
                frame_client.stop()
            try:
                stimuli.exit()
            except BaseException:
                pass

    elif Task == "MI":
        print(f"[No this{Task}]")
        pass
    
    _save_events_csv()
    print("[Collect End]")
