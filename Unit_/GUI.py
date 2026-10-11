import os 
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, messagebox, filedialog

from Unit_.LSL_ import LSL_Recorder
from screeninfo import get_monitors


class SSVEP_GUI:
    def __init__(self, root, shared_info, task_queue):
        self.root = root
        self.shared_info = shared_info
        self.task_queue = task_queue
        self._last_analysis_time = ""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self._setup_scale()

        # ! Setup window
        self._setup_window()

        # ! Setup styles and fonts
        self._setup_styles()

        # ! Initialize data
        self.info = {
            "ID": tk.StringVar(value=str(shared_info.get("ID", ""))),
            "Name": tk.StringVar(value=str(shared_info.get("Name", ""))),
            "Age": tk.StringVar(value=str(shared_info.get("Age", ""))),
            "Gender": tk.StringVar(value=str(shared_info.get("Gender", ""))),
            "Folder_path": tk.StringVar(value=str(shared_info.get("Folder_path", ""))),
            "Device_name": tk.StringVar(value=str(shared_info.get("Device_name", ""))),
            "Device_status": tk.StringVar(value=str(shared_info.get("Device_status", "Disconnected"))),
            "Threshold": tk.DoubleVar(value=float(shared_info.get("Threshold", 0.5))),
            "Select_screen": tk.StringVar(value=str(shared_info.get("Select_screen", ""))),
            "Algorithm": tk.StringVar(value=str(shared_info.get("Algorithm", ""))),
            "Win_len": tk.DoubleVar(value=float(shared_info.get("Win_len", 2.0))),
            "Step_len": tk.DoubleVar(value=float(shared_info.get("Step_len", 0.1))),
            "Task": tk.StringVar(value=str(shared_info.get("Task", ""))),
            "Task_Duration": tk.DoubleVar(value=float(shared_info.get("Task_Duration", 10.0))),
            "Rest_Duration": tk.DoubleVar(value=float(shared_info.get("Rest_Duration", 2.0))),
            "Analysis_Results": {
                "ACC": tk.DoubleVar(value=float(shared_info.get("Analysis_Results", {}).get("ACC", 0.0))),
                "Per_Direction_ACC": {
                    "up": tk.DoubleVar(value=float(shared_info.get("Analysis_Results", {}).get("Per_Direction_ACC", {}).get("up", 0.0))),
                    "down": tk.DoubleVar(value=float(shared_info.get("Analysis_Results", {}).get("Per_Direction_ACC", {}).get("down", 0.0))),
                    "left": tk.DoubleVar(value=float(shared_info.get("Analysis_Results", {}).get("Per_Direction_ACC", {}).get("left", 0.0))),
                    "right": tk.DoubleVar(value=float(shared_info.get("Analysis_Results", {}).get("Per_Direction_ACC", {}).get("right", 0.0))),
                },
                "Per_Direction_Details": {
                    "up": {
                        "correct": tk.IntVar(value=int(shared_info.get("Analysis_Results", {}).get("Per_Direction_Details", {}).get("up", {}).get("correct", 0))),
                        "total": tk.IntVar(value=int(shared_info.get("Analysis_Results", {}).get("Per_Direction_Details", {}).get("up", {}).get("total", 0))),
                    },
                    "down": {
                        "correct": tk.IntVar(value=int(shared_info.get("Analysis_Results", {}).get("Per_Direction_Details", {}).get("down", {}).get("correct", 0))),
                        "total": tk.IntVar(value=int(shared_info.get("Analysis_Results", {}).get("Per_Direction_Details", {}).get("down", {}).get("total", 0))),
                    },
                    "left": {
                        "correct": tk.IntVar(value=int(shared_info.get("Analysis_Results", {}).get("Per_Direction_Details", {}).get("left", {}).get("correct", 0))),
                        "total": tk.IntVar(value=int(shared_info.get("Analysis_Results", {}).get("Per_Direction_Details", {}).get("left", {}).get("total", 0))),
                    },
                    "right": {
                        "correct": tk.IntVar(value=int(shared_info.get("Analysis_Results", {}).get("Per_Direction_Details", {}).get("right", {}).get("correct", 0))),
                        "total": tk.IntVar(value=int(shared_info.get("Analysis_Results", {}).get("Per_Direction_Details", {}).get("right", {}).get("total", 0))),
                    },
                },
                "total_correct": tk.IntVar(value=int(shared_info.get("Analysis_Results", {}).get("total_correct", 0))),
                "total_samples": tk.IntVar(value=int(shared_info.get("Analysis_Results", {}).get("total_samples", 0))),
                "sensitivity": tk.DoubleVar(value=float(shared_info.get("Analysis_Results", {}).get("sensitivity", 0.0))),
                "specificity": tk.DoubleVar(value=float(shared_info.get("Analysis_Results", {}).get("specificity", 0.0))),
                "precision": tk.DoubleVar(value=float(shared_info.get("Analysis_Results", {}).get("precision", 0.0))),
                "F1_score": tk.DoubleVar(value=float(shared_info.get("Analysis_Results", {}).get("F1_score", 0.0))),
                "Analysis_Time": tk.StringVar(value=str(shared_info.get("Analysis_Results", {}).get("Analysis_Time", ""))),
            },
        }
        # ! Scan_screen
        self.Scan_screen()
        # ! Build GUI
        self._build_gui()
        # ! Setup status bar
        self._setup_status_bar()
        self._install_resize_scaling()

    # ! Setup
    def _setup_scale(self):
        screen_w, screen_h = 0, 0
        try:
            monitors = get_monitors()
            if monitors:
                primary = next((m for m in monitors if m.is_primary), monitors[0])
                screen_w, screen_h = primary.width, primary.height
        except Exception:
            pass
        try:
            tk_w = self.root.winfo_screenwidth()
            tk_h = self.root.winfo_screenheight()
        except Exception:
            tk_w, tk_h = 0, 0
        screen_w = max(screen_w, tk_w) if screen_w and tk_w else (screen_w or tk_w)
        screen_h = max(screen_h, tk_h) if screen_h and tk_h else (screen_h or tk_h)
        raw = min(screen_w / 1920, screen_h / 1080)
        self.scale_factor = max(0.6, min(2.5, raw))
        print(f"[GUI] Screen: {screen_w}x{screen_h}  →  scale_factor = {self.scale_factor:.2f}")

    def sp(self, value):
        # scale pixel
        return int(value * self.scale_factor)

    def _setup_window(self):
        # Set window icon
        try:
            self.root.iconphoto(True, tk.PhotoImage(file="Viz_/Unit_/BCI.png"))
        except:
            pass
        # Window properties — scaled proportionally
        self.root.title("BCI System")
        w, h = self.sp(1200), self.sp(800)
        self._design_window_width = w
        self._design_window_height = h
        self.root.geometry(f"{w}x{h}+0+0")
        self.root.resizable(True, True)
        self.root.minsize(self.sp(800), self.sp(500))
        self.root.config(bg="#f5f5f5")
    
    def _setup_styles(self):
        # Color palette
        self.colors = {
            'bg': "#f5f5f5",
            'primary': "#2c3e50",
            'accent': "#3498db",
            'success': "#27ae60",
            'error': "#e74c3c",
            'warning': "#f39c12",
            'info': "#3498db",
            'light_bg': "#fef9e7",
            'disabled': "#bdc3c7",
            'white': "white",
            'black': "#2c3e50"
        }
        # Font definitions — sizes scaled by scale_factor
        sf = self.scale_factor
        self.fonts = {
            'title': ("Segoe UI", max(18, int(32 * sf)), "bold"),
            'subtitle': ("Segoe UI", max(11, int(16 * sf)), "bold"),
            'label': ("Segoe UI", max(11, int(16 * sf))),
            'label_small': ("Segoe UI", max(10, int(14 * sf))),
            'entry': ("Segoe UI", max(10, int(15 * sf))),
            'button': ("Segoe UI", max(10, int(15 * sf)), "bold"),
            'button_large': ("Segoe UI", max(10, int(15 * sf)), "bold"),
            'tab': ("Segoe UI", max(10, int(16 * sf)), "bold"),
            'status': ("Segoe UI", max(10, int(14 * sf))),
            'monospace': ("Consolas", max(10, int(14 * sf))),
            'monospace_large': ("Consolas", max(10, int(14 * sf))),
            'result_title': ("Segoe UI", max(11, int(16 * sf)), "bold"),
            'result_text': ("Segoe UI", max(10, int(14 * sf)))
        }
        # Configure ttk style
        style = ttk.Style()
        style.theme_use('clam')
        # Base style
        style.configure(".", 
                       background=self.colors['bg'], 
                       foreground=self.colors['primary'])
        # Notebook (Tabs)
        style.configure("TNotebook", 
                       background=self.colors['bg'], 
                       borderwidth=0)
        style.configure("TNotebook.Tab",
                       font=self.fonts['tab'],
                       padding=[self.sp(12), self.sp(8)],
                       background="#e0e0e0")
        style.map("TNotebook.Tab", 
                 background=[("selected", self.colors['accent'])], 
                 foreground=[("selected", self.colors['white'])])
        # Buttons
        style.configure("TButton",
                       font=self.fonts['button'],
                       padding=self.sp(8),
                       background=self.colors['accent'],
                       foreground=self.colors['white'])
        style.map("TButton", 
                 background=[("active", "#2980b9")])
        
        style.configure("Accent.TButton",
                       font=self.fonts['button_large'],
                       padding=self.sp(8),
                       background=self.colors['success'],
                       foreground=self.colors['white'])
        style.map("Accent.TButton", 
                 background=[("active", "#219a52")])
        # Labels
        style.configure("TLabel", 
                       font=self.fonts['label'], 
                       background=self.colors['bg'])
        # LabelFrames
        style.configure("TLabelframe", 
                       background=self.colors['bg'], 
                       foreground=self.colors['primary'])
        style.configure("TLabelframe.Label", 
                       font=self.fonts['label'], 
                       background=self.colors['bg'], 
                       foreground=self.colors['primary'])
        # Entries
        style.configure("TEntry",
                       font=self.fonts['entry'],
                       padding=self.sp(8),
                       fieldbackground=self.colors['white'])
        # Comboboxes
        style.configure("TCombobox",
                       font=self.fonts['entry'],
                       padding=self.sp(8))
        # Configure dropdown menu font (Combobox dropdown list)
        self.root.option_add('*TCombobox*Listbox.font', ("Segoe UI", self.sp(18)))
    
    def _setup_status_bar(self):
        self.status_bar = tk.Label(
            self.root,
            text="Ready",
            bd=max(1, self.sp(2)),
            relief=tk.SUNKEN,
            anchor=tk.W,
            font=self.fonts['status'],
            bg="#e0e0e0",
            fg=self.colors['primary'],
            padx=self.sp(12),
            pady=self.sp(8)
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    # ! Resize scaling
    @staticmethod
    def _scale_numeric(value, factor):
        # Scale Tk size 
        if isinstance(value, (tuple, list)):
            scaled = [SSVEP_GUI._scale_numeric(item, factor) for item in value]
            return tuple(scaled) if isinstance(value, tuple) else scaled
        try:
            return int(round(float(value) * factor))
        except (TypeError, ValueError):
            return value

    def _scaled_font(self, font, factor):
        # Scale font size.
        if font in (None, ""):
            return font
        try:
            if isinstance(font, (tuple, list)):
                family, size, *styles = font
            else:
                actual = tkfont.Font(root=self.root, font=font).actual()
                family = actual["family"]
                size = actual["size"]
                styles = []
                if actual.get("weight") == "bold":
                    styles.append("bold")
                if actual.get("slant") == "italic":
                    styles.append("italic")
                if actual.get("underline"):
                    styles.append("underline")
                if actual.get("overstrike"):
                    styles.append("overstrike")
            size = int(size)
            scaled_size = max(7, int(round(abs(size) * factor)))
            if size < 0:
                scaled_size = -scaled_size
            return (family, scaled_size, *styles)
        except (tk.TclError, TypeError, ValueError):
            return font

    def _install_resize_scaling(self):
        # Remember the built UI size and rescale it on window resize.
        self._resize_base_scale = self.scale_factor
        self._resize_widgets = []
        dimension_options = {
            "width", "height", "padx", "pady", "bd", "borderwidth",
            "highlightthickness", "wraplength", "insertwidth",
            "selectborderwidth",
        }
        def capture(widget):
            options = {}
            for option in dimension_options | {"font"}:
                try:
                    options[option] = widget.cget(option)
                except tk.TclError:
                    continue
            manager = widget.winfo_manager()
            try:
                if manager == "pack":
                    layout = (manager, widget.pack_info())
                elif manager == "grid":
                    layout = (manager, widget.grid_info())
                elif manager == "place":
                    layout = (manager, widget.place_info())
                else:
                    layout = (manager, {})
            except tk.TclError:
                layout = (manager, {})
            self._resize_widgets.append((widget, options, layout))
            for child in widget.winfo_children():
                capture(child)
        capture(self.root)
        self._resize_after_id = None
        self.root.bind("<Configure>", self._queue_resize_scaling, add="+")

    def _queue_resize_scaling(self, event):
        if event.widget is not self.root:
            return
        if self._resize_after_id is not None:
            self.root.after_cancel(self._resize_after_id)
        self._resize_after_id = self.root.after(100, self._apply_resize_scaling)

    def _apply_resize_scaling(self):
        self._resize_after_id = None
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        if width <= 1 or height <= 1:
            return
        ratio = min(
            width / self._design_window_width,
            height / self._design_window_height,
        )
        ratio = max(0.5, min(2.0, ratio))
        self.scale_factor = self._resize_base_scale * ratio
        for widget, options, (manager, layout) in self._resize_widgets:
            try:
                updates = {}
                for option, original in options.items():
                    if option == "font":
                        if original in (None, ""):
                            continue
                        updates[option] = self._scaled_font(original, ratio)
                    elif option in {"width", "height"} and self._uses_text_units(widget, option):
                        continue
                    else:
                        updates[option] = self._scale_numeric(original, ratio)
                if updates:
                    widget.configure(**updates)
                layout_updates = {}
                for option in ("padx", "pady", "ipadx", "ipady", "x", "y", "width", "height"):
                    if option in layout:
                        layout_updates[option] = self._scale_numeric(layout[option], ratio)
                if layout_updates:
                    if manager == "pack":
                        widget.pack_configure(**layout_updates)
                    elif manager == "grid":
                        widget.grid_configure(**layout_updates)
                    elif manager == "place":
                        widget.place_configure(**layout_updates)
            except (tk.TclError, RuntimeError):
                continue
        self._apply_scaled_styles(ratio)

    @staticmethod
    def _uses_text_units(widget, option):
        widget_class = widget.winfo_class()
        if option == "width":
            return widget_class in {
                "Label", "Button", "Entry", "Listbox", "Text",
                "TLabel", "TButton", "TEntry", "TCombobox",
            }
        if option == "height":
            return widget_class in {
                "Label", "Button", "Listbox", "Text", "TLabel", "TButton",
            }
        return False

    def _apply_scaled_styles(self, ratio):
        base_fonts = getattr(self, "_resize_base_fonts", None)
        if base_fonts is None:
            base_fonts = self.fonts.copy()
            self._resize_base_fonts = base_fonts
        self.fonts = {
            name: self._scaled_font(font, ratio)
            for name, font in base_fonts.items()
        }
        style = ttk.Style(self.root)
        style.configure("TNotebook.Tab", font=self.fonts["tab"],
                        padding=[self.sp(12), self.sp(8)])
        style.configure("TButton", font=self.fonts["button"],
                        padding=self.sp(8))
        style.configure("Accent.TButton", font=self.fonts["button_large"],
                        padding=self.sp(8))
        style.configure("TLabel", font=self.fonts["label"])
        style.configure("TLabelframe.Label", font=self.fonts["label"])
        style.configure("TEntry", font=self.fonts["entry"], padding=self.sp(8))
        style.configure("TCombobox", font=self.fonts["entry"], padding=self.sp(8))
        self.root.option_add("*TCombobox*Listbox.font", self.fonts["entry"])
        if hasattr(self, "results_text"):
            for tag, font_key in (
                ("title", "result_title"),
                ("success", "result_text"),
                ("error", "result_text"),
                ("info", "result_text"),
                ("result_item", "monospace_large"),
                ("separator", "label_small"),
            ):
                self.results_text.tag_configure(tag, font=self.fonts[font_key])
    
    # ! main gui
    def _build_gui(self):
        # Title Frame
        title_frame = tk.Frame(self.root, bg=self.colors['primary'], height=self.sp(100))
        title_frame.pack(fill='x', side='top')
        title_frame.pack_propagate(False)
        title = tk.Label(
            title_frame,
            text="BCI System",
            font=self.fonts['title'],
            bg=self.colors['primary'],
            fg=self.colors['white']
        )
        title.pack(expand=True)
        # Main container with padding
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill='both', expand=True, padx=self.sp(20), pady=self.sp(20))
        # Notebook (Tabs)
        notebook = ttk.Notebook(main_container)
        notebook.pack(fill='both', expand=True)
        # Create tab frames
        info_frame = ttk.Frame(notebook)
        eeg_device_frame = ttk.Frame(notebook)
        collect_frame = ttk.Frame(notebook)
        analysis_frame = ttk.Frame(notebook)
        realtime_frame = ttk.Frame(notebook)
        # Add tabs
        notebook.add(info_frame, text='Personal Info')
        notebook.add(eeg_device_frame, text='EEG Device')
        notebook.add(collect_frame, text='Data Collection')
        notebook.add(analysis_frame, text='Data Analysis')
        notebook.add(realtime_frame, text='Real Time')
        # Build each page
        self.page_info(info_frame)
        self.page_EEG_device(eeg_device_frame)
        self.page_Collect(collect_frame)
        self.page_Analysis(analysis_frame)
        self.page_Realtime(realtime_frame)
    
    # ! global Methods 
    def update_status(self, message, color="black"):
        # updata status
        self.status_bar.config(text=f"  {message}", fg=color)
        self.status_bar.update_idletasks()
    
    def select_folder(self):
        # select path
        folder_path = filedialog.askdirectory(title="Select Data Save Folder")
        if folder_path:
            self.info["Folder_path"].set(folder_path)
            self.update_status(f"Data folder selected: {os.path.basename(folder_path)}", "green")
    
    def Scan_screen(self):
        # scan screen
        try:
            sys_monitors = get_monitors()
            screen_list = []
            for monitor in sys_monitors:
                screen_list.append(f"{monitor.name} ({monitor.width}x{monitor.height})")
            if not screen_list:
                screen_list = []
        except Exception as e:
            print(f"Screen scan error: {e}")
            screen_list = []
        self.screen_list = screen_list
        return screen_list

    def print_info(self):
        # print all info
        if self.info["Name"].get() == "" or self.info["ID"].get() == "":
            messagebox.showwarning("Incomplete Information", "Please fill in all personal information!")
            return
        def extract_values(data):
            if hasattr(data, 'get') and not hasattr(data, 'keys'):
                try:
                    return data.get()
                except:
                    return str(data)
            elif isinstance(data, dict):
                return {k: extract_values(v) for k, v in data.items()}
            else:
                return data
        current_values = extract_values(self.info)
        print(current_values)
        self.update_status(f"Information saved for Subject: {self.info['Name'].get()}", "green")
        messagebox.showinfo("Success", f"Information saved successfully!\nSubject: {self.info['Name'].get()}")
    
    def scan_lsl_devices(self):
        # scan lsl
        try:
            self.update_status("Scanning for LSL devices...", "blue")
            self.device_listbox.delete(0, tk.END)
            self.found_streams = []
            streams = LSL_Recorder.search_streams()
            if not streams:
                self.device_listbox.insert(tk.END, "No LSL devices found on the network.")
                self.lsl_status_label.config(text="❌ Status: Scan complete (No devices)", 
                                            foreground="orange")
                self.update_status("Scan complete: No devices found", "orange")
                return
            for s in streams:
                self.found_streams.append(s)
                display_text = f"{s['name']} | Type: {s['type']} | Ch: {s['channels']} | SR: {s['srate']}"
                self.device_listbox.insert(tk.END, display_text)
            self.lsl_status_label.config(text=f"✅ Status: Found {len(streams)} device(s)", 
                                        foreground="green")
            self.update_status(f"Found {len(streams)} LSL device(s)", "green")
        except Exception as e:
            messagebox.showerror("Scan Error", f"Failed to scan LSL streams:\n{e}")
            self.lsl_status_label.config(text="❌ Status: Scan Failed", foreground="red")
            self.update_status("Scan failed", "red")
    
    def connect_lsl_device(self):
        # connect lsl
        selection = self.device_listbox.curselection()
        if not selection or len(self.found_streams) == 0:
            messagebox.showwarning("Warning", "Please select a device from the list first!")
            return
        selected_index = selection[0]
        selected_stream = self.found_streams[selected_index]
        device_name = selected_stream['name']
        try:
            self.recorder = LSL_Recorder(stream_name=device_name, channels=None)
            messagebox.showinfo("Success", f"Successfully connected to:\n{device_name}")
            self.info["Device_name"].set(device_name)
            self.info["Device_status"].set("Connected")
            self.lsl_status_label.config(text=f"🔗 Status: Connected to {device_name}", 
                                        foreground="blue")
            self.update_status(f"Connected to device: {device_name}", "blue")
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect:\n{e}")
            self.lsl_status_label.config(text="❌ Status: Connect Failed", foreground="red")
            self.update_status("Connection failed", "red")
    
    def save_to_shared(self):
        # save shared info
        self.shared_info["ID"] = self.info["ID"].get()
        self.shared_info["Name"] = self.info["Name"].get()
        self.shared_info["Age"] = self.info["Age"].get()
        self.shared_info["Gender"] = self.info["Gender"].get()
        self.shared_info["Folder_path"] = self.info["Folder_path"].get()
        self.shared_info["Device_name"] = self.info["Device_name"].get()
        self.shared_info["Device_status"] = self.info["Device_status"].get()
        self.shared_info["Select_screen"] = self.info["Select_screen"].get()
        self.shared_info["Win_len"] = float(self.info["Win_len"].get())
        self.shared_info["Step_len"] = float(self.info["Step_len"].get())
        self.shared_info["Algorithm"] = self.info["Algorithm"].get()
        self.shared_info["Threshold"] = float(self.info["Threshold"].get())
        self.shared_info["Task"] = self.info["Task"].get()
        self.shared_info["Task_Duration"] = float(self.info["Task_Duration"].get())
        self.shared_info["Rest_Duration"] = float(self.info["Rest_Duration"].get())
        self.shared_info["Analysis_Results"] = {
            "ACC": float(self.info["Analysis_Results"]["ACC"].get()),
            "Per_Direction_ACC": {
                "up": float(self.info["Analysis_Results"]["Per_Direction_ACC"]["up"].get()),
                "down": float(self.info["Analysis_Results"]["Per_Direction_ACC"]["down"].get()),
                "left": float(self.info["Analysis_Results"]["Per_Direction_ACC"]["left"].get()),
                "right": float(self.info["Analysis_Results"]["Per_Direction_ACC"]["right"].get()),
            },
            "Per_Direction_Details": {
                "up": {
                    "correct": int(self.info["Analysis_Results"]["Per_Direction_Details"]["up"]["correct"].get()),
                    "total": int(self.info["Analysis_Results"]["Per_Direction_Details"]["up"]["total"].get()),
                },
                "down": {
                    "correct": int(self.info["Analysis_Results"]["Per_Direction_Details"]["down"]["correct"].get()),
                    "total": int(self.info["Analysis_Results"]["Per_Direction_Details"]["down"]["total"].get()),
                },
                "left": {
                    "correct": int(self.info["Analysis_Results"]["Per_Direction_Details"]["left"]["correct"].get()),
                    "total": int(self.info["Analysis_Results"]["Per_Direction_Details"]["left"]["total"].get()),
                },
                "right": {
                    "correct": int(self.info["Analysis_Results"]["Per_Direction_Details"]["right"]["correct"].get()),
                    "total": int(self.info["Analysis_Results"]["Per_Direction_Details"]["right"]["total"].get()),
                },
            },
            "total_correct": int(self.info["Analysis_Results"]["total_correct"].get()),
            "total_samples": int(self.info["Analysis_Results"]["total_samples"].get()),
            "sensitivity": float(self.info["Analysis_Results"]["sensitivity"].get()),
            "specificity": float(self.info["Analysis_Results"]["specificity"].get()),
            "precision": float(self.info["Analysis_Results"]["precision"].get()),
            "F1_score": float(self.info["Analysis_Results"]["F1_score"].get()),
            "Analysis_Time": str(self.info["Analysis_Results"]["Analysis_Time"].get()),
        }
        print("[GUI] Data saved to shared Info")

    def load_from_shared(self):
        # load shared info
        self.info["ID"].set(str(self.shared_info.get("ID", "")))
        self.info["Name"].set(str(self.shared_info.get("Name", "")))
        self.info["Age"].set(str(self.shared_info.get("Age", "")))
        self.info["Gender"].set(str(self.shared_info.get("Gender", "")))
        self.info["Folder_path"].set(str(self.shared_info.get("Folder_path", "")))
        self.info["Device_name"].set(str(self.shared_info.get("Device_name", "")))
        self.info["Device_status"].set(str(self.shared_info.get("Device_status", "Disconnected")))
        self.info["Threshold"].set(float(self.shared_info.get("Threshold", 0.5)))
        self.info["Select_screen"].set(str(self.shared_info.get("Select_screen", "")))
        self.info["Algorithm"].set(str(self.shared_info.get("Algorithm", "")))
        self.info["Win_len"].set(float(self.shared_info.get("Win_len", 2.0)))
        self.info["Step_len"].set(float(self.shared_info.get("Step_len", 0.1)))
        self.info["Task"].set(str(self.shared_info.get("Task", "")))
        self.info["Task_Duration"].set(float(self.shared_info.get("Task_Duration", 10.0)))
        self.info["Rest_Duration"].set(float(self.shared_info.get("Rest_Duration", 2.0)))

        results = self.shared_info.get("Analysis_Results", {})
        self.info["Analysis_Results"]["ACC"].set(float(results.get("ACC", 0.0)))
        self.info["Analysis_Results"]["total_correct"].set(int(results.get("total_correct", 0)))
        self.info["Analysis_Results"]["total_samples"].set(int(results.get("total_samples", 0)))
        self.info["Analysis_Results"]["sensitivity"].set(float(results.get("sensitivity", 0.0)))
        self.info["Analysis_Results"]["specificity"].set(float(results.get("specificity", 0.0)))
        self.info["Analysis_Results"]["precision"].set(float(results.get("precision", 0.0)))
        self.info["Analysis_Results"]["F1_score"].set(float(results.get("F1_score", 0.0)))
        self.info["Analysis_Results"]["Analysis_Time"].set(str(results.get("Analysis_Time", "")))

        per_direction_acc = results.get("Per_Direction_ACC", {})
        self.info["Analysis_Results"]["Per_Direction_ACC"]["up"].set(
            float(per_direction_acc.get("up", 0.0)))
        self.info["Analysis_Results"]["Per_Direction_ACC"]["down"].set(
            float(per_direction_acc.get("down", 0.0)))
        self.info["Analysis_Results"]["Per_Direction_ACC"]["left"].set(
            float(per_direction_acc.get("left", 0.0)))
        self.info["Analysis_Results"]["Per_Direction_ACC"]["right"].set(
            float(per_direction_acc.get("right", 0.0)))
        
        per_direction_details = results.get("Per_Direction_Details", {})
        for direction in ["up", "down", "left", "right"]:
            details = per_direction_details.get(direction, {})
            self.info["Analysis_Results"]["Per_Direction_Details"][direction]["correct"].set(
                int(details.get("correct", 0)))
            self.info["Analysis_Results"]["Per_Direction_Details"][direction]["total"].set(
                int(details.get("total", 0)))
        print("[GUI] Variables updated from shared dictionary")
        
    # ! Page 1 (personal info)
    def page_info(self, parent):
        content_frame = ttk.Frame(parent)
        content_frame.pack(expand=True, fill='both')
        # Center the form
        form_frame = ttk.Frame(content_frame)
        form_frame.place(relx=0.5, rely=0.5, anchor='center')
        form_frame.columnconfigure(1, weight=1)
        # Subject ID
        ttk.Label(form_frame, text="Subject ID:", font=self.fonts['subtitle']).grid(
            row=0, column=0, padx=self.sp(12), pady=self.sp(10), sticky='e')
        id_entry = ttk.Entry(form_frame, textvariable=self.info["ID"],
                            width=28, font=self.fonts['entry'])
        id_entry.grid(row=0, column=1, padx=self.sp(12), pady=self.sp(10), sticky='ew')
        # Name
        ttk.Label(form_frame, text="Name:", font=self.fonts['subtitle']).grid(
            row=1, column=0, padx=self.sp(12), pady=self.sp(10), sticky='e')
        name_entry = ttk.Entry(form_frame, textvariable=self.info["Name"],
                              width=28, font=self.fonts['entry'])
        name_entry.grid(row=1, column=1, padx=self.sp(12), pady=self.sp(10), sticky='ew')
        # Age
        ttk.Label(form_frame, text="Age:", font=self.fonts['subtitle']).grid(
            row=2, column=0, padx=self.sp(12), pady=self.sp(10), sticky='e')
        age_entry = ttk.Entry(form_frame, textvariable=self.info["Age"],
                             width=28, font=self.fonts['entry'])
        age_entry.grid(row=2, column=1, padx=self.sp(12), pady=self.sp(10), sticky='ew')
        # Gender
        ttk.Label(form_frame, text="Gender:", font=self.fonts['subtitle']).grid(
            row=3, column=0, padx=self.sp(12), pady=self.sp(10), sticky='e')
        gender_combo = ttk.Combobox(form_frame, textvariable=self.info["Gender"],
                                    values=["", "Male", "Female"], width=25,
                                    font=self.fonts['entry'], state="readonly")
        gender_combo.grid(row=3, column=1, padx=self.sp(12), pady=self.sp(10), sticky='ew')
        gender_combo.current(0)
        # Save button
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=self.sp(24))
        save_btn = ttk.Button(btn_frame, text="💾 Save Information",
                             command=self.print_info, style="Accent.TButton", width=22)
        save_btn.pack()

    # ! Page 2 (lsl device)
    def page_EEG_device(self, parent):
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill='both', expand=True, padx=self.sp(20), pady=self.sp(20))
        # Button panel
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=(0, self.sp(12)))

        scan_btn = ttk.Button(btn_frame, text="🔍 Scan Devices",
                             command=self.scan_lsl_devices, width=20)
        scan_btn.pack(side='left', padx=self.sp(12))

        connect_btn = ttk.Button(btn_frame, text="🔌 Connect",
                                command=self.connect_lsl_device, width=20)
        connect_btn.pack(side='left', padx=self.sp(12))
        # Device list frame
        list_frame = ttk.LabelFrame(main_frame, text="Available LSL Streams", padding=self.sp(12))
        list_frame.pack(fill='both', expand=True, pady=self.sp(12))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        # Create frame for listbox and scrollbar
        list_container = ttk.Frame(list_frame)
        list_container.grid(row=0, column=0, sticky='nsew')
        list_container.columnconfigure(0, weight=1)
        list_container.rowconfigure(0, weight=1)
        self.device_listbox = tk.Listbox(list_container, selectmode=tk.SINGLE,
                                         height=7, font=self.fonts['monospace'],
                                         bg=self.colors['white'], fg=self.colors['primary'],
                                         selectbackground=self.colors['accent'],
                                         selectforeground=self.colors['white'],
                                         relief=tk.FLAT, highlightthickness=self.sp(2),
                                         highlightcolor=self.colors['disabled'])
        scrollbar = ttk.Scrollbar(list_container, orient="vertical",
                                 command=self.device_listbox.yview)
        self.device_listbox.configure(yscrollcommand=scrollbar.set)
        self.device_listbox.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')
        # Status label
        self.lsl_status_label = ttk.Label(main_frame, text="⚠️ Status: Waiting for scan...",
                                          font=self.fonts['label_small'])
        self.lsl_status_label.pack(pady=self.sp(8))
        self.found_streams = []
    
    # ! Page 3 (collect data)
    def page_Collect(self, parent):
        content_frame = ttk.Frame(parent)
        content_frame.pack(expand=True, fill='both')
        main_frame = ttk.Frame(content_frame)
        main_frame.place(relx=0.5, rely=0.5, anchor='center')
        # Row 0: Data Folder
        folder_frame = ttk.Frame(main_frame)
        folder_frame.pack(fill='x', pady=self.sp(10))
        ttk.Label(folder_frame, text="📁 Data Folder:", font=self.fonts['label'],
                 width=18, anchor='e').pack(side='left', padx=(0, self.sp(12)))
        folder_entry = ttk.Entry(folder_frame, textvariable=self.info["Folder_path"],
                                 width=30, state="readonly", font=self.fonts['entry'])
        folder_entry.pack(side='left', padx=(0, self.sp(12)))
        browse_btn = ttk.Button(folder_frame, text="Browse",
                               command=self.select_folder, width=12)
        browse_btn.pack(side='left')
        # Row 1: Screen
        screen_frame = ttk.Frame(main_frame)
        screen_frame.pack(fill='x', pady=self.sp(10))
        self.Scan_screen()
        ttk.Label(screen_frame, text="🖥 Screen:", font=self.fonts['label'],
                 width=18, anchor='e').pack(side='left', padx=(0, self.sp(12)))
        screen_combo = ttk.Combobox(screen_frame, textvariable=self.info["Select_screen"],
                                    values=self.screen_list, width=27,
                                    font=self.fonts['entry'], state="readonly")
        screen_combo.pack(side='left')
        if self.screen_list:
            screen_combo.current(0)
        # Row 2: Task and Preview
        task_frame = ttk.Frame(main_frame)
        task_frame.pack(fill='x', pady=self.sp(10))
        ttk.Label(task_frame, text="🎯 Task:", font=self.fonts['label'],
                 width=18, anchor='e').pack(side='left', padx=(0, self.sp(12)))
        task_combo = ttk.Combobox(task_frame, textvariable=self.info["Task"],
                                  values=["", "SSVEP", "PD-SSVEP", "MI"], width=20,
                                  font=self.fonts['entry'], state="readonly")
        task_combo.pack(side='left', padx=(0, self.sp(12)))
        task_combo.current(0)
        preview_btn = ttk.Button(task_frame, text="👁 Preview",
                                command=self.preview_task, width=10)
        preview_btn.pack(side='left')
        # Row 3: Task Duration and Rest Duration
        duration_frame = ttk.Frame(main_frame)
        duration_frame.pack(fill='x', pady=self.sp(10))
        ttk.Label(duration_frame, text="⏱ Task Duration (s):", font=self.fonts['label'],
                 width=18, anchor='e').pack(side='left', padx=(0, self.sp(12)))
        task_duration_entry = ttk.Entry(duration_frame, textvariable=self.info["Task_Duration"],
                                        width=10, font=self.fonts['entry'])
        task_duration_entry.pack(side='left', padx=(0, self.sp(12)))
        self.info["Task_Duration"].set("10.0")
        ttk.Label(duration_frame, text="Rest Duration (s):", font=self.fonts['label']).pack(
            side='left', padx=(0, self.sp(12)))
        rest_duration_entry = ttk.Entry(duration_frame, textvariable=self.info["Rest_Duration"],
                                        width=10, font=self.fonts['entry'])
        rest_duration_entry.pack(side='left')
        self.info["Rest_Duration"].set("2.0")
        # Row 4: Collect button
        collect_btn = ttk.Button(main_frame, text="⏺ Start Collection",
                                command=self.Collect_task,
                                style="Accent.TButton", width=22)
        collect_btn.pack(pady=self.sp(24))
    
    # ! Page 4 (analysis data)
    def page_Analysis(self, parent):
        content_frame = ttk.Frame(parent)
        content_frame.pack(expand=True, fill='both')
        # Control frame (top part)
        control_frame = ttk.Frame(content_frame)
        control_frame.pack(fill='x', padx=self.sp(20), pady=(self.sp(12), self.sp(8)))
        # Center the form horizontally
        form_frame = ttk.Frame(control_frame)
        form_frame.pack(anchor='center')
        form_frame.columnconfigure(0, weight=0, minsize=self.sp(250))
        form_frame.columnconfigure(1, weight=1)
        # Row 0: Data Folder
        ttk.Label(form_frame, text="📁 Data Folder:", font=self.fonts['label'],
                 anchor='e').grid(row=0, column=0, padx=(0, self.sp(12)), pady=self.sp(10), sticky='e')
        folder_entry = ttk.Entry(form_frame, textvariable=self.info["Folder_path"],
                                 width=30, state="readonly", font=self.fonts['entry'])
        folder_entry.grid(row=0, column=1, padx=(0, self.sp(12)), pady=self.sp(10), sticky='w')
        browse_btn = ttk.Button(form_frame, text="Browse",
                               command=self.select_folder, width=12)
        browse_btn.grid(row=0, column=2, padx=0, pady=self.sp(10), sticky='w')
        # Row 1: Window Length and Window Step
        ttk.Label(form_frame, text="⏱ Window Length (s):", font=self.fonts['label'],
                 anchor='e').grid(row=1, column=0, padx=(0, self.sp(12)), pady=self.sp(10), sticky='e')
        window_container = ttk.Frame(form_frame)
        window_container.grid(row=1, column=1, columnspan=2, sticky='w', pady=self.sp(10))
        win_len_entry = ttk.Entry(window_container, textvariable=self.info["Win_len"],
                                  width=8, font=self.fonts['entry'])
        win_len_entry.pack(side='left', padx=(0, self.sp(12)))
        ttk.Label(window_container, text="Step (s):", font=self.fonts['label_small']).pack(
            side='left', padx=(0, self.sp(8)))
        win_step_entry = ttk.Entry(window_container, textvariable=self.info["Step_len"],
                                   width=8, font=self.fonts['entry'])
        win_step_entry.pack(side='left')
        # Row 2: Algorithm and Analysis button
        ttk.Label(form_frame, text="🧠 Algorithm:", font=self.fonts['label'],
                 anchor='e').grid(row=2, column=0, padx=(0, self.sp(12)), pady=self.sp(10), sticky='e')
        algo_container = ttk.Frame(form_frame)
        algo_container.grid(row=2, column=1, columnspan=2, sticky='w', pady=self.sp(10))
        algo_combo = ttk.Combobox(algo_container, textvariable=self.info["Algorithm"],
                                  values=["", "CCA", "FBCCA"], width=20,
                                  font=self.fonts['entry'], state="readonly")
        algo_combo.pack(side='left', padx=(0, self.sp(12)))
        algo_combo.current(0)
        analysis_btn = ttk.Button(algo_container, text="▶ Start Analysis",
                                  command=self.Analysis_task,
                                  style="Accent.TButton", width=18)
        analysis_btn.pack(side='left')
        # Results display frame (bottom part)
        results_frame = ttk.LabelFrame(content_frame, text="📊 Analysis Results", padding=self.sp(12))
        results_frame.pack(fill='both', expand=True, padx=self.sp(20), pady=(self.sp(8), self.sp(12)))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        # Create a frame with scrollbar for results
        results_container = ttk.Frame(results_frame)
        results_container.grid(row=0, column=0, sticky='nsew')
        results_container.columnconfigure(0, weight=1)
        results_container.rowconfigure(0, weight=1)
        # Text widget for displaying results
        self.results_text = tk.Text(results_container, font=self.fonts['monospace_large'],
                                    bg=self.colors['light_bg'], fg=self.colors['primary'],
                                    wrap=tk.WORD, padx=self.sp(12), pady=self.sp(12),
                                    relief=tk.FLAT, highlightthickness=max(1, self.sp(1)),
                                    highlightcolor=self.colors['disabled'])

        results_scrollbar = ttk.Scrollbar(results_container, orient="vertical",
                                         command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=results_scrollbar.set)
        self.results_text.grid(row=0, column=0, sticky='nsew')
        results_scrollbar.grid(row=0, column=1, sticky='ns')
        # Configure tags for different text styles
        self.results_text.tag_configure("title", font=self.fonts['result_title'],
                                        foreground=self.colors['primary'], spacing3=self.sp(10))
        self.results_text.tag_configure("success", font=self.fonts['result_text'],
                                        foreground=self.colors['success'])
        self.results_text.tag_configure("error", font=self.fonts['result_text'],
                                        foreground=self.colors['error'])
        self.results_text.tag_configure("info", font=self.fonts['result_text'],
                                        foreground=self.colors['info'])
        self.results_text.tag_configure("result_item", font=self.fonts['monospace_large'],
                                        foreground="#8e44ad", spacing1=self.sp(5))
        self.results_text.tag_configure("separator", font=self.fonts['label_small'],
                                        foreground=self.colors['disabled'])
        # Add initial welcome message
        self.results_text.insert(tk.END, "✨ Analysis Results\n", "title")
        self.results_text.insert(tk.END, "─" * 30 + "\n", "separator")
        self.results_text.insert(tk.END, "Select a data folder and algorithm, then click 'Start Analysis' to begin.\n", "info")
        self.results_text.config(state=tk.DISABLED)
        self.display_analysis_results()
    
    def display_analysis_results(self):
        # print analisis result
        results = self.shared_info.get("Analysis_Results", {})
        analysis_time = results.get("Analysis_Time", "")
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)
        if analysis_time == "":
            self.results_text.insert(tk.END, "✨ Analysis Results\n", "title")
            self.results_text.insert(tk.END, "─" * 30 + "\n", "separator")
            self.results_text.insert(tk.END, "No analysis results yet.\n", "info")
            self.results_text.insert(tk.END, "Click 'Start Analysis' to begin.\n", "info")
        else:
            acc = results.get("ACC", 0.0)
            total_correct = results.get("total_correct", 0)
            total_samples = results.get("total_samples", 0)
            self.results_text.insert(tk.END, "✨ Analysis Results\n", "title")
            self.results_text.insert(tk.END, "─" * 30 + "\n", "separator")
            self.results_text.insert(tk.END, f"📅 Time: {analysis_time}\n\n", "info")
            if total_samples > 0:
                self.results_text.insert(tk.END, f"🎯 Overall Accuracy: {acc:.2f}%\n", "success")
                self.results_text.insert(tk.END, f"   Correct: {total_correct} / {total_samples}\n\n", "result_item")
            else:
                self.results_text.insert(tk.END, f"🎯 Overall Accuracy: {acc:.2f}%\n\n", "error")
            self.results_text.insert(tk.END, "📊 Per-Direction Accuracy:\n", "title")
            per_direction_acc = results.get("Per_Direction_ACC", {})
            per_direction_details = results.get("Per_Direction_Details", {})
            direction_emoji = {"up": "⬆️", "down": "⬇️", "left": "⬅️", "right": "➡️"}
            for direction in ["up", "down", "left", "right"]:
                dir_acc = per_direction_acc.get(direction, 0.0)
                details = per_direction_details.get(direction, {})
                correct = details.get("correct", 0)
                total = details.get("total", 0)
                emoji = direction_emoji.get(direction, "❓")
                if total > 0:
                    self.results_text.insert(tk.END, f"  {emoji} {direction.capitalize():6s}: {dir_acc:.2f}%", "success")
                    self.results_text.insert(tk.END, f" ({correct}/{total})\n", "result_item")
                else:
                    self.results_text.insert(tk.END, f"  {emoji} {direction.capitalize():6s}: N/A\n", "error")
            sensitivity = results.get("sensitivity", 0.0)
            specificity = results.get("specificity", 0.0)
            precision = results.get("precision", 0.0)
            F1_score = results.get("F1_score", 0.0)
            threshold = self.shared_info.get("Threshold", 0.0)
            if sensitivity > 0 or specificity > 0:
                self.results_text.insert(tk.END, "\n⚙️ Threshold Metrics:\n", "title")
                self.results_text.insert(tk.END, f"  Threshold: {threshold:.4f}\n", "result_item")
                self.results_text.insert(tk.END, f"  Sensitivity(Recall): {sensitivity:.4f}\n", "result_item")
                self.results_text.insert(tk.END, f"  Specificity: {specificity:.4f}\n", "result_item")
                self.results_text.insert(tk.END, f"  precision: {precision:.4f}\n", "result_item")
                self.results_text.insert(tk.END, f"  F1_score: {F1_score:.4f}\n", "result_item")
            self.results_text.insert(tk.END, "\n" + "─" * 30 + "\n", "separator")
        self.results_text.config(state=tk.DISABLED)
    
    # ! Page 5 (real time)
    def page_Realtime(self, parent):
        content_frame = ttk.Frame(parent)
        content_frame.pack(expand=True, fill='both')
        # Center form
        form_frame = ttk.Frame(content_frame)
        form_frame.place(relx=0.5, rely=0.5, anchor='center')
        form_frame.columnconfigure(1, weight=1)
        # Task selection
        ttk.Label(form_frame, text="🎯 Task:", font=self.fonts['subtitle']).grid(
            row=0, column=0, padx=self.sp(12), pady=self.sp(10), sticky='e')
        task_combo = ttk.Combobox(form_frame, textvariable=self.info["Task"],
                                  values=["", "SSVEP", "PD-SSVEP", "MI"], width=25,
                                  font=self.fonts['entry'], state="readonly")
        task_combo.grid(row=0, column=1, padx=self.sp(12), pady=self.sp(10), sticky='ew')
        task_combo.current(0)
        # Screen selection
        self.Scan_screen()
        ttk.Label(form_frame, text="🖥 Screen:", font=self.fonts['subtitle']).grid(
            row=1, column=0, padx=self.sp(12), pady=self.sp(10), sticky='e')
        screen_combo = ttk.Combobox(form_frame, textvariable=self.info["Select_screen"],
                                    values=self.screen_list, width=25,
                                    font=self.fonts['entry'], state="readonly")
        screen_combo.grid(row=1, column=1, padx=self.sp(12), pady=self.sp(10), sticky='ew')
        if self.screen_list:
            screen_combo.current(0)
        # Algorithm selection
        ttk.Label(form_frame, text="🧠 Algorithm:", font=self.fonts['subtitle']).grid(
            row=2, column=0, padx=self.sp(12), pady=self.sp(10), sticky='e')
        algo_combo = ttk.Combobox(form_frame, textvariable=self.info["Algorithm"],
                                  values=["", "CCA", "FBCCA"], width=25,
                                  font=self.fonts['entry'], state="readonly")
        algo_combo.grid(row=2, column=1, padx=self.sp(12), pady=self.sp(10), sticky='ew')
        algo_combo.current(0)
        # Threshold
        ttk.Label(form_frame, text="⚙ Threshold:", font=self.fonts['subtitle']).grid(
            row=3, column=0, padx=self.sp(12), pady=self.sp(10), sticky='e')
        threshold_entry = ttk.Entry(form_frame, textvariable=self.info["Threshold"],
                                    width=28, font=self.fonts['entry'])
        threshold_entry.grid(row=3, column=1, padx=self.sp(12), pady=self.sp(10), sticky='ew')
        # Realtime button
        realtime_btn = ttk.Button(form_frame, text="▶ Start Realtime",
                                  command=self.Realtime_task,
                                  style="Accent.TButton", width=22)
        realtime_btn.grid(row=4, column=0, columnspan=3, pady=self.sp(24))


    # ! all Task
    def preview_task(self):
        if self.info["Task"].get() == "":    
            messagebox.showwarning("Missing Algorithm", "Please select an Task!")
            return
        else:
            self.save_to_shared()
            self.task_queue.put("preview")
            self.root.destroy()
    
    def Collect_task(self):
        if self.info["Folder_path"].get() == "":
            messagebox.showwarning("Missing Folder", "Please select a data folder!")
            return
        elif self.info["Task"].get() == "":    
            messagebox.showwarning("Missing Algorithm", "Please select an Task!")
            return
        else:
            self.save_to_shared()
            self.task_queue.put("collect")
            self.root.destroy()
    
    def Analysis_task(self):
        if self.info["Folder_path"].get() == "":
            messagebox.showwarning("Missing Folder", "Please select a data folder!")
            return
        elif self.info["Algorithm"].get() == "" or self.info["Algorithm"].get() == "FBCCA":    
            messagebox.showwarning("Missing Algorithm", "Please select an analysis algorithm!")
            return
        else:
            self.save_to_shared()
            self.task_queue.put("analysis")
            self.update_status("Analysis in progress... Please check results after completion.", "blue")
            self._last_analysis_time = self.shared_info.get("Analysis_Results", {}).get("Analysis_Time", "")
            self.root.after(1000, self._check_analysis_complete)
    
    def _check_analysis_complete(self):
        current_time = self.shared_info.get("Analysis_Results", {}).get("Analysis_Time", "")
        if current_time != "" and current_time != self._last_analysis_time:
            self._last_analysis_time = current_time
            self.load_from_shared() 
            self.display_analysis_results()
            self.update_status("Analysis completed!", "green")
            messagebox.showinfo("Success", "Analysis completed successfully!")
        else:
            self.root.after(1000, self._check_analysis_complete)

    def Realtime_task(self):
        if self.info["Task"].get() == "":    
            messagebox.showwarning("Missing Algorithm", "Please select an Task!")
            return
        elif self.info["Algorithm"].get() == "" or self.info["Algorithm"].get() == "FBCCA":    
            messagebox.showwarning("Missing Algorithm", "Please select an analysis algorithm!")
            return
        else:
            self.save_to_shared()
            self.task_queue.put("realtime")
            self.root.destroy()
    
    def on_closing(self):
        print("[GUI] Window closing, sending exit signal...")
        self.task_queue.put("__exit__")
        self.root.destroy()
