import time
import multiprocessing as mp
from typing import Callable, Optional, List, Dict


class Manager_process:
    def __init__(self):
        self.process_info = {
            "process_name": None,
            "process_status": None,
            "process_obj": None,
            "process_pid": None,
        }
        self.multi_process: List[Dict] = []  
    
    def creat_process(self, function: Callable, name: str = None, args: tuple = (), kwargs: dict = None) -> Dict:
        if kwargs is None:
            kwargs = {}
        if name is None:
            name = f"Process_{len(self.multi_process) + 1}"
        process_obj = mp.Process(target=function, args=args, kwargs=kwargs, name=name)
        process_info = {
            "process_name": name,
            "process_status": "created",
            "process_obj": process_obj,
            "process_pid": None,
            "function": function,
            "args": args,
            "kwargs": kwargs,
            "created_time": time.time()
        }
        self.multi_process.append(process_info)
        print(f"[Manager] Creat: {name}")
        return process_info
    
    def run_process(self, process: Dict) -> bool:
        if process not in self.multi_process:
            print(f"[Manager] Error: NO exist")
            return False
        process_obj = process["process_obj"]
        if process_obj.is_alive():
            print(f"[Manager] '{process['process_name']}' Already running")
            return False
        try:
            process_obj.start()
            process["process_status"] = "running"
            process["process_pid"] = process_obj.pid
            print(f"[Manager] Start: {process['process_name']}, PID: {process_obj.pid}")
            return True
        except Exception as e:
            print(f"[Manager] Start Error: {e}")
            process["process_status"] = "error"
            return False
    
    def stop_process(self, process: Dict, timeout: float = 3.0) -> bool:
        if process not in self.multi_process:
            print(f"[Manager] Error: NO exist")
            return False
        process_obj = process["process_obj"]
        if not process_obj.is_alive():
            process["process_status"] = "stopped"
            return True
        try:
            print(f"[Manager] Stop: {process['process_name']}")
            process_obj.terminate()
            process_obj.join(timeout=timeout)
            if process_obj.is_alive():
                print(f"[Manager] Power Stop: {process['process_name']}")
                process_obj.kill()
                process_obj.join()
            process["process_status"] = "stopped"
            process["process_pid"] = None
            return True
        except Exception as e:
            print(f"[Manager] Stop Error: {e}")
            process["process_status"] = "error"
            return False
    
    def get_process_by_name(self, name: str) -> Optional[Dict]:
        for process in self.multi_process:
            if process["process_name"] == name:
                return process
        return None
    
    def get_process_by_pid(self, pid: int) -> Optional[Dict]:
        for process in self.multi_process:
            if process["process_pid"] == pid:
                return process
        return None
    
    def get_running_processes(self) -> List[Dict]:
        return [p for p in self.multi_process if p["process_obj"].is_alive()]
    
    def stop_all_processes(self):
        print(f"[Manager] Stop all process...")
        for process in self.multi_process:
            self.stop_process(process)
    
    def remove_process(self, process: Dict) -> bool:
        if process in self.multi_process:
            self.stop_process(process)
            self.multi_process.remove(process)
            print(f"[Manager] Remove: {process['process_name']}")
            return True
        return False
    
    def get_process_status(self, process: Dict) -> str:
        if process["process_obj"].is_alive():
            return "running"
        return process["process_status"]
    
    def wait_for_process(self, process: Dict, timeout: float = None) -> bool:
        process_obj = process["process_obj"]
        process_obj.join(timeout=timeout)
        return not process_obj.is_alive()
    
    def print_all_processes(self):
        print("\n" + "="*50)
        print("Process List:")
        print("-"*30)
        for process in self.multi_process:
            status = "🟢 Runing" if process["process_obj"].is_alive() else "🔴 Stop"
            print(f"  Name: {process['process_name']}")
            print(f"  Status: {status}")
            print(f"  PID: {process['process_pid']}")
            print(f"  Time: {time.strftime('%H:%M:%S', time.localtime(process['created_time']))}")
            print("-"*30)
        print("="*50 + "\n")
    


