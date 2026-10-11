import cv2
import numpy as np
from psychopy import visual, core, logging as psycho_logging
from screeninfo import get_monitors


class Stimuli_SSVEP:
    def __init__(self, block_size: int, mode: str = 'cosine_phase',):
        psycho_logging.console.setLevel(psycho_logging.ERROR)
        # screen: use primary monitor
        sys_monitors = get_monitors()
        primary = next((m for m in sys_monitors if m.is_primary), sys_monitors[0])
        primary_index = next((i for i, m in enumerate(sys_monitors) if m.is_primary), 0)
        self.width = int(primary.width)
        self.height = int(primary.height)
        self.win = visual.Window(fullscr=True,
                                size=[self.width, self.height],
                                screen=primary_index,
                                units='pix',
                                color='black',
                                allowGUI=False,
                                winType='pyglet',
                                )
        core.wait(0.5)
        # Measure refresh rate
        self.refresh_rate = self.win.getActualFrameRate(nIdentical=55)
        # block size
        self.block_size = block_size
        # block pos
        self.block_pos_0 = {'up': (0, int(self.height/2 - self.block_size/2)),
                            'down': (0, -int(self.height/2 - self.block_size/2)),
                            'left': (-int(self.width/2 - self.block_size/2), 0),
                            'right': (int(self.width/2 - self.block_size/2), 0)}
        self.block_pos_1 = {'up': (-int(self.width/2 - self.block_size/2), int(self.height/2 - self.block_size/2)),
                            'down': (-int(self.width/2 - self.block_size/2), -int(self.height/2 - self.block_size/2)),
                            'left': (int(self.width/2 - self.block_size/2), int(self.height/2 - self.block_size/2)),
                            'right': (int(self.width/2 - self.block_size/2), -int(self.height/2 - self.block_size/2))}
        self.arrows = {'up': '↑', 'down': '↓', 'left': '←', 'right': '→'}
        # update mode
        self.mode = mode 
        # Auto select freq based on refresh rate
        if abs(int(self.refresh_rate) - 60) <= 5:
            self.freqs = {'up': 6, 'down': 7.5, 'left': 10, 'right': 15}
        elif abs(int(self.refresh_rate) - 120) <= 5:
            self.freqs = {'up': 8, 'down': 10, 'left': 12, 'right': 15}
        elif abs(int(self.refresh_rate) - 144) <= 5:
            self.freqs = {'up': 8, 'down': 9.6, 'left': 14.4, 'right': 18} 
        else:
            print(f"[Warning]: Refresh rate {self.refresh_rate} Hz not in set(60|120|144)")
        
        print(f"[Screen refresh rate] {self.refresh_rate}")
        print(f"[freqs] {self.freqs}")

    # ! stimuli
    def create_stimuli(self):
        stimuli = {}
        positions = self.block_pos_0
        for d, pos in positions.items():
            stim = visual.Rect(self.win, width=self.block_size, height=self.block_size, pos=pos, fillColor='white', lineColor=None)
            arrow = visual.TextStim(self.win, text=self.arrows[d], pos=pos, color='black', height=self.block_size / 1.5, bold=True)
            stimuli[d] = {'stim': stim, 'arrow': arrow, 'freq': self.freqs[d]}
        return stimuli
    
    # ! stimuli update mode
    def update_stimuli(self, stimuli, t):
        if self.mode == 'square':
            for s in stimuli.values():
                phase = (t * s['freq']) % 1.0
                s['stim'].fillColor = 'white' if phase < 0.5 else 'black'
        elif self.mode == 'cosine':
            for s in stimuli.values():
                phase = 2 * np.pi * (t * s['freq'])
                luminance = np.cos(phase)
                s['stim'].fillColor = luminance
        elif self.mode == 'cosine_phase':
            phase_offsets = [0, np.pi / 2, np.pi, 3 * np.pi / 2]
            for i, s in enumerate(stimuli.values()):
                phase_offset = phase_offsets[i % len(phase_offsets)]
                phase = 2 * np.pi * (t * s['freq']) + phase_offset
                luminance = np.cos(phase)
                s['stim'].fillColor = luminance
        else:
            raise ValueError(f"[Not this mode: {self.mode}]")
        
    # ! web-Cam    
    def create_webcam(self, cam_IP:str, size: int=300, pos=(0, 0)):
        try:
            stream_url = f"http://{cam_IP}/stream"
            cap = cv2.VideoCapture(stream_url, cv2.CAP_ANY)
            # cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not cap.isOpened():
                print(f"Unable to connect to CAM at {stream_url}")
                return None
            webcam_stim = visual.ImageStim(
                self.win,
                size=[size, size],
                pos=pos,
                units='pix',
                name='webcam',
            )
            return cap, webcam_stim
        except Exception as e:
            print(f"[Error: {e}]")
            return None
    
    # ! Countdown
    def countdown_text(self, text:str, show_time:bool=False, seconds:int=0,):
        if seconds == 0 or seconds<0:
            msg = visual.TextStim(self.win, text=f"{text}", color='white', height=50)
            msg.draw()
        else:
            for sec in reversed(range(1, seconds + 1)):
                if show_time:
                    msg = visual.TextStim(self.win, text=f"{text} {sec}", color='white', height=50)
                else:
                    msg = visual.TextStim(self.win, text=f"{text}", color='white', height=50)
                msg.draw()
                self.win.flip()
                core.wait(1.0)

    def exit(self):
        self.win.close()
        core.quit()


# ! ----------------------------------------------------------------------------
# ! Cam_block
# webcam_data = my_stimuli.create_webcam(size=500, pos=(0, 0))
# if webcam_data:
#     cap, webcam_stim = webcam_data # 解包元组
#     ret, frame = cap.read()
#     if ret:
#         frame_rotated = cv2.rotate(frame, cv2.ROTATE_180)
#         frame_rgb = cv2.cvtColor(frame_rotated, cv2.COLOR_BGR2RGB)
#         frame_normalized = frame_rgb.astype(np.float32) / 255.0
#         webcam_stim.setImage(frame_normalized)
#         webcam_stim.draw()
# ! ----------------------------------------------------------------------------
