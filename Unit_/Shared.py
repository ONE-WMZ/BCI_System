from multiprocessing import Manager


_manager = None
TASK_QUEUE = None
INFO = None

def init_shared_resources():
    global _manager, TASK_QUEUE, INFO
    
    if _manager is None:
        _manager = Manager()
        TASK_QUEUE = _manager.Queue()
        INFO = _manager.dict({
            "ID": "",
            "Name": "",
            "Age": "",
            "Gender": "",

            "Folder_path": "",
            "Device_name": "",
            "Device_status": "Disconnected",
            "Select_screen": "",

            "Win_len": 2.0,
            "Step_len": 0.1,
            "Algorithm": "",
            "Threshold": 0.0,  

            "Task": "",
            "Task_Duration": 10.0,
            "Rest_Duration": 2.0,

            "Analysis_Results": {
                "ACC": 0.0,       
                "Per_Direction_ACC": {      
                    "up": 0.0,   
                    "down": 0.0, 
                    "left": 0.0,  
                    "right": 0.0, 
                    "+": 0.0,
                },
                "Per_Direction_Details": {
                    "up": {"correct": 0, "total": 0},  
                    "down": {"correct": 0, "total": 0},  
                    "left": {"correct": 0, "total": 0},  
                    "right": {"correct": 0, "total": 0},
                    "+": {"correct": 0, "total": 0},
                },
                "total_correct": 0,  
                "total_samples": 0,   
                "sensitivity": 0.0,   
                "specificity": 0.0,  
                "precision": 0.0,
                "F1_score": 0.0,
                "Analysis_Time": "",
            },
        })
        print("[Shared] Successfully init shared resources!")
        return True
    return False

def get_shared_resources():
    return TASK_QUEUE, INFO