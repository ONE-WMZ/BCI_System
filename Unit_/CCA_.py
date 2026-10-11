import numpy as np
from scipy.signal import butter, filtfilt
from sklearn.cross_decomposition import CCA


class cca_ssvep:
    def __init__(self, freqs:dict, fs:int=250, n_harmonics:int=2):
        self.fs = fs
        self.freqs = freqs
        self.n_harmonics = n_harmonics

    def bandpass_filter(self, data, lowcut:int=6, highcut:int=31, order:int=4):
        nyq = 0.5 * self.fs
        low = lowcut / nyq
        high = highcut / nyq
        b, a = butter(order, [low, high], btype='band')
        return filtfilt(b, a, data, axis=0)
    
    def sliding_windows(self, data, win_len_s, win_step_s):
        n_samples = data.shape[0]
        win_size = int(win_len_s * self.fs)
        step_size = int(win_step_s * self.fs)
        windows = []
        for start in range(0, n_samples - win_size + 1, step_size):
            end = start + win_size
            windows.append(data[start:end, :])
        return windows
   
    def gen_ref(self, window_len, freq):
        t = np.arange(window_len) / self.fs
        refs = []
        for h in range(1, self.n_harmonics + 1):
            refs.append(np.sin(2 * np.pi * freq * h * t))
            refs.append(np.cos(2 * np.pi * freq * h * t))
        return np.array(refs).T 
    
    def classify(self, data):
        cca = CCA(n_components=1, copy=True)
        scores = {}
        for dir_, freq in self.freqs.items():
            ref = self.gen_ref(len(data), freq)
            cca.fit(data, ref)
            U, V = cca.transform(data, ref)
            corr = np.corrcoef(U.T, V.T)[0, 1]
            scores[dir_] = corr
        pred_dir = max(scores, key=scores.get)
        return pred_dir, scores
    
    def select_channel(self, eeg, channel_select: list = [6, 7, 8, 9, 13]):
        start_idx = max(0, eeg.shape[0] - 11 * 250)
        eeg = eeg[start_idx:, :]
        n_channels = eeg.shape[1]
        valid_chs = [ch for ch in channel_select if ch < n_channels]
        if not valid_chs:
            raise ValueError(f"No valid channels. Requested {channel_select}, but EEG has {n_channels} channels")
        if len(valid_chs) < len(channel_select):
            print(f"Warning: Dropped {len(channel_select)-len(valid_chs)} invalid channels")
        eeg = eeg[:, valid_chs]
        return eeg
        
    def best_threshold(self, rest_pre_s, direction_pre_s):
        rest_scores = np.array([max(item[1].values()) for item in rest_pre_s])
        active_scores = np.array([max(item[1].values()) for item in direction_pre_s])
        if len(rest_scores) == 0 or len(active_scores) == 0:
            return None
        thresholds = np.arange(0.0, 1.0, 0.005)
        best_th = 0.0
        max_j_score = -np.inf
        best_metrics = None
        for th in thresholds:
            tp = np.sum(active_scores > th)
            fp = np.sum(rest_scores > th)
            sensitivity = tp / len(active_scores)
            false_positive_rate = fp / len(rest_scores)
            j_score = sensitivity - false_positive_rate
            if j_score > max_j_score:
                max_j_score = j_score
                best_th = th
                best_metrics = {
                    'threshold': best_th,
                    'j_score': j_score,
                    'sensitivity': sensitivity,
                    'specificity': 1 - false_positive_rate,
                    'tp': tp,
                    'fp': fp,
                    'tn': len(rest_scores) - fp,
                    'fn': len(active_scores) - tp,
                    'total_active': len(active_scores),
                    'total_rest': len(rest_scores)
                }
        return best_metrics



