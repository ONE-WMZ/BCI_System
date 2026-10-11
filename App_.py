import time
import tkinter as tk
import multiprocessing

from Task_.preview import Task_preview
from Task_.analysis import Task_analysis
from Task_.collect import Task_collect
from Task_.realtime import Task_realtime

import Unit_.Shared as Shared
from Unit_.GUI import SSVEP_GUI
from Unit_.Process_ import Manager_process


# ! GUI
def run_gui(shared_info, task_queue):
    root = tk.Tk()
    app = SSVEP_GUI(root, shared_info, task_queue)
    root.mainloop()


# ! Task
def run_Task(manager, name:str, gui, info):
    TASK_FUNCTIONS = {
        "preview": Task_preview,
        "collect": Task_collect,
        "analysis": Task_analysis,
        "realtime": Task_realtime,
    }
    task_func = TASK_FUNCTIONS.get(name)
    if not task_func:
        print(f"Error: no this task name-{name}")
        return
    if name != "analysis":
        if gui:
            manager.stop_process(gui)
            manager.remove_process(gui)
    psy_task = manager.creat_process(function=task_func, name=name, args=(info,), kwargs={},)
    manager.run_process(psy_task)
    manager.wait_for_process(psy_task)
    manager.remove_process(psy_task)
    if name != "analysis":
        gui_ = manager.creat_process(function=run_gui, name="SSVEP_GUI", args=(Shared.INFO, Shared.TASK_QUEUE), kwargs={},)
        manager.run_process(gui_)


# ! main
def main():
    Shared.init_shared_resources()
    manager = Manager_process()

    try:
        gui_ = manager.creat_process(
                function=run_gui,
                name="BCI_GUI",
                args=(Shared.INFO, Shared.TASK_QUEUE),
                kwargs={},
            )
        manager.run_process(gui_)
        while True:
            while True:
                if not Shared.TASK_QUEUE.empty():
                    task_name = Shared.TASK_QUEUE.get()
                    break
                time.sleep(1) 
            if task_name == "__exit__":
                print("[Main] Exit signal received, shutting down...")
                break

            run_Task(manager, task_name, gui_, Shared.INFO)

    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        manager.stop_all_processes()



# ! App
if __name__ == "__main__":
    multiprocessing.freeze_support() 
    main() 



