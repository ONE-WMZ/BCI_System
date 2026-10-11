import numpy as np
from pylsl import StreamInlet, resolve_streams


# !  LSL-EEG
class LSL_Recorder:
    def __init__(self, stream_name:str, channels:list, dtype=np.float32):
        print("【Resolving LSL streams...】")
        streams = resolve_streams()
        try:
            stream = next(s for s in streams if s.name() == stream_name)
        except StopIteration:
            raise RuntimeError(f"【No find LSL streams: {stream_name}】")
        self.inlet = StreamInlet(stream)
        # Save metadata and config
        self.info = stream
        self.channels = channels
        self.dtype = dtype
        print(f"Connected LSL streams: {stream.name()}")
        print(f"\t Channel num: {stream.channel_count()}")
        print(f"\t Sampling rate: {stream.nominal_srate()} Hz")

    def get_new(self, timeout=0.001):
        # get new data from the LSL stream
        chunk, ts = self.inlet.pull_chunk(timeout=timeout)
        if not chunk:
            return np.empty((0, self.info.channel_count())), np.empty((0,))
        chunk = np.asarray(chunk, dtype=self.dtype)
        ts = np.asarray(ts, dtype=self.dtype)
        if self.channels:
            chunk = chunk[:, self.channels]
        return chunk, ts 
    
    @staticmethod
    def search_streams():
        # Search LSL stream
        streams = resolve_streams()
        print("Find stream num:", len(streams))
        stream_info_list = []
        for s in streams:
            info = {
                'name': s.name(),
                'type': s.type(),
                'channels': s.channel_count(),
                'srate': s.nominal_srate()
            }
            stream_info_list.append(info)
        return stream_info_list

    def clear_buffer(self):
        # Clear LSL's cache
        while True:
            chunk, timestamps = self.inlet.pull_chunk(timeout=0.0)
            if len(chunk) == 0:
                break

# ! ----------------------------------------------------------------------------

