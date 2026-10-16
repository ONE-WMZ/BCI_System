from psychopy import visual, core, event 
from Unit_.Stimuli_ import Stimuli_SSVEP
from Unit_.Get_Frame import Get_Camera, Get_Frame

# ! 
def Task_preview(info_):
    task = info_.get("Task")
    # Select_screen = info_.get("Select_screen")
    preview_time = info_.get("Task_Duration")

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
            print("[Escape key]")
        finally:
            stimuli.exit()
            
    elif task == "PD-SSVEP":
        frame_api = info_.get("Frame_API", "")
        try:
            frame_client = (Get_Camera(int(info_.get("Camera_Index", 1)))
                            if info_.get("Use_Camera", False)
                            else Get_Frame(frame_api))
            frame_client.start()
        except (ValueError, RuntimeError) as exc:
            print(f"[PD-SSVEP preview] {exc}")
            return

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
        waiting_text = visual.TextStim(
            win=stimuli.win,
            text="Waiting for frame",
            color="white",
            height=24,
        )
        # main()
        try:
            clock = core.Clock()
            while clock.getTime() < preview_time:
                t = clock.getTime()
                # updata SSVEP 
                stimuli.update_stimuli(stimuli_dict, t)
                # game 
                latest_frame = frame_client.get_frame()
                if latest_frame is not None:
                    game_stim.image = latest_frame
                else:
                    waiting_text.draw()
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
            frame_client.stop()
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
            print("[Escape key]")
        finally:
            stimuli.exit()
    else :
        print("[Not this model]")

    print("[Preview finished]")

