import os
import time
import json
import numpy as np
from Unit_.CCA_ import cca_ssvep


# ! V3
def Task_analysis(info_):

    Folder_path = info_.get("Folder_path")
    Algorithm = info_.get("Algorithm")
    Win_len = info_.get("Win_len")
    Step_len = info_.get("Step_len")

    # freqs_list
    person_info_path = os.path.join(Folder_path, "person_info.json")
    if not os.path.exists(person_info_path):
        # Fallback: search for person_info.json in subdirectories
        print(f"[Warning] person_info.json not found at: {person_info_path}")
        print(f"[Info] Searching for person_info.json in subdirectories of: {Folder_path}")
        found = False
        if os.path.isdir(Folder_path):
            for root, _, files in os.walk(Folder_path):
                if "person_info.json" in files:
                    person_info_path = os.path.join(root, "person_info.json")
                    print(f"[Info] Found person_info.json at: {person_info_path}")
                    found = True
                    break
        if not found:
            print(f"[Error] read json: person_info.json not found in {Folder_path} or its subdirectories")
            return

    with open(person_info_path, "r", encoding="utf-8") as f:
        existing_info = json.load(f)
    freqs_list = existing_info.get("freqs_list")
    if freqs_list is None:
        print(f"[Error] 'freqs_list' key missing in: {person_info_path}")
        return
    
    if not Folder_path or not Algorithm:
        print("Error: Missing Folder path or Algorithm selection.")
        return
    if not os.path.isdir(Folder_path):
        print(f"Error: Path is not a directory: {Folder_path}")
        return
    if not os.listdir(Folder_path):
        print(f"Error: Folder is empty: {Folder_path}")
        return
    
    results = {
        "ACC": 0.0,        
        "Per_Direction_ACC": {"up": 0.0, "down": 0.0, "left": 0.0, "right": 0.0},
        "Per_Direction_Details": {
            "up": {"correct": 0, "total": 0},
            "down": {"correct": 0, "total": 0},
            "left": {"correct": 0, "total": 0},
            "right": {"correct": 0, "total": 0}
        },
        "total_correct": 0,          
        "total_samples": 0,          
        "sensitivity": 0.0,          # Recall
        "specificity": 0.0,
        "precision": 0.0, 
        "F1_score": 0.0, 
        "Analysis_Time": time.strftime('%Y-%m-%d %H:%M:%S'),
    }
    
    try:
        if Algorithm == "CCA":
            cca_analyzer = cca_ssvep(freqs_list, fs=250, n_harmonics=2)
            directions = ['up', 'down', 'left', 'right']
            rest_pre_s = []             # Store as [pred_dir, scores_dict]
            direction_pre_s = []        # Store as [pred_dir, scores_dict]
            total_correct = 0
            total_samples = 0
            
            # rest
            rest_file = os.path.join(Folder_path, "+.npy")
            if os.path.exists(rest_file):
                rest = np.load(rest_file)
                rest = cca_analyzer.select_channel(rest)
                rest = cca_analyzer.bandpass_filter(rest, lowcut=6, highcut=31, order=4)
                windows_rest = cca_analyzer.sliding_windows(rest, Win_len, Step_len)
                for win_data in windows_rest:
                    pred_dir, scores = cca_analyzer.classify(win_data)
                    rest_pre_s.append([pred_dir, scores])   # Keep original format
            else:
                print("Warning: Rest file (+.npy) not found. Skipping rest analysis.")
            
            # directions
            for direction in directions:
                stim_file = os.path.join(Folder_path, f"{direction}.npy")
                if not os.path.exists(stim_file):
                    print(f"Warning: File for direction '{direction}' not found. Skipping.")
                    continue
                eeg = np.load(stim_file)
                eeg = cca_analyzer.select_channel(eeg)
                eeg = cca_analyzer.bandpass_filter(eeg, lowcut=6, highcut=31, order=4)
                windows_eeg = cca_analyzer.sliding_windows(eeg, Win_len, Step_len)
                dire_correct = 0
                for win_data in windows_eeg:
                    pred_dir, scores = cca_analyzer.classify(win_data)
                    direction_pre_s.append([pred_dir, scores])  # Keep original format
                    if pred_dir == direction:
                        dire_correct += 1
                if len(windows_eeg) > 0:
                    acc = (dire_correct / len(windows_eeg)) * 100
                    results["Per_Direction_ACC"][direction] = acc
                    results["Per_Direction_Details"][direction] = {
                        "correct": dire_correct, 
                        "total": len(windows_eeg)
                    }
                    total_correct += dire_correct
                    total_samples += len(windows_eeg)
        
            if total_samples > 0:
                results["ACC"] = (total_correct / total_samples) * 100
                results["total_correct"] = total_correct
                results["total_samples"] = total_samples
            
            if len(rest_pre_s) > 0 and len(direction_pre_s) > 0:
                threshold_metrics = cca_analyzer.best_threshold(rest_pre_s, direction_pre_s)
                if threshold_metrics is not None:
                    info_["Threshold"] = threshold_metrics['threshold']
                    results["sensitivity"] = threshold_metrics['sensitivity'] * 100  
                    results["specificity"] = threshold_metrics['specificity'] * 100  
                    
                    # Get confusion matrix values
                    tp = threshold_metrics.get('tp', 0)
                    fp = threshold_metrics.get('fp', 0)
                    tn = threshold_metrics.get('tn', 0)
                    fn = threshold_metrics.get('fn', 0)
                    
                    # Precision = TP / (TP + FP)
                    if (tp + fp) > 0:
                        results["precision"] = (tp / (tp + fp)) * 100
                    else:
                        results["precision"] = 0.0
                    
                    # Recall (same as sensitivity)
                    results["recall"] = results["sensitivity"]
                    
                    # F1 Score = 2 * (Precision * Recall) / (Precision + Recall)
                    if (results["precision"] + results["recall"]) > 0:
                        results["F1_score"] = 2 * (results["precision"] * results["recall"]) / \
                                              (results["precision"] + results["recall"])
                    else:
                        results["F1_score"] = 0.0
                    
                    # Print detailed metrics
                    print(f"\n[Threshold Metrics]")
                    print(f"  Threshold: {threshold_metrics['threshold']:.4f}")
                    # print(f"  Youden's J Score: {threshold_metrics['j_score']:.4f}")
                    print(f"  Confusion Matrix: TP={tp}, FN={fn}, TN={tn}, FP={fp}")
                    print(f"  Sensitivity (Recall): {results['sensitivity']:.2f}%")
                    print(f"  Specificity: {results['specificity']:.2f}%")
                    print(f"  Precision: {results['precision']:.2f}%")
                    print(f"  F1 Score: {results['F1_score']:.2f}%")
            else:
                print("Warning: Cannot calculate threshold metrics (missing rest or stimulus data)")
            
            info_["Analysis_Results"] = results
            info_["_last_analysis_update"] = time.time()
            print("\n [Analysis] Completed Successfully.")
            print(f"  Overall Accuracy: {results['ACC']:.2f}%")
            print(f"  Total Samples: {total_samples}")
            print(f"  Correct Predictions: {total_correct}\n")
            
        elif Algorithm == "FBCCA":
            print("Error: FBCCA module not implemented yet.")       
        
        else:
            print(f"Error: Unknown Algorithm '{Algorithm}'")
            
    except ImportError as e:
        print(f"Import Error: {e}")
    except Exception as e:
        print(f"Analysis Failed: {e}")
        import traceback
        traceback.print_exc()