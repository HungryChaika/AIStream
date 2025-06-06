import tkinter as tk
from tkinter.messagebox import showinfo
import ctypes
from video_capture import VideoCapture

from sys import platform
if platform == "win32":
    ctypes.windll.shcore.SetProcessDpiAwareness(2) # your windows version should >= 8.1,it will raise exception.


class CameraTk(tk.Frame):
    def __init__(self, window, text=None,sources_names=None, stream=None, callbacks = {}, width = 100, height = 100):
        super().__init__(window, padx=5, pady=5, width=width, height=height, highlightbackground="#000000", highlightthickness=2)
        self.window = window
        self.stream = stream
        self.sources_names = sources_names
        self.text = text
        self.callbacks = callbacks
        self.canvas = None
        self.video_capture = None
        # self.width_video = width
        # self.height_video = height
        self.selected_name_cam = tk.StringVar()
        self.selected_name_cam.set("Выбор\nкамеры")
        self.grid_coords = {
            "x": None,
            "y": None
        }
        # self.canvas = tk.Canvas(self, width=int(width * 0.9), height=int(height * 0.9))
        # self.canvas.pack(anchor="center")
        # self.canvas.bind('<Double-1>', lambda event: self.event_camera_to_fullscreen(event))

        # self.button_choice_of_stream = tk.Button(master=self, text="Выбор\nкамеры", command=lambda: self.event_choice_of_stream())
        # self.button_choice_of_stream.place(x=0, y=0, relx=0.5, rely=0.5, anchor="center")
        self.option_menu = tk.OptionMenu(self, self.selected_name_cam, *self.sources_names, command=lambda choice: self.event_choice_of_stream(choice))
        self.option_menu.place(x=0, y=0, relx=0.5, rely=0.5, anchor="center")

    # def event_choice_of_stream(self, event):
    def event_choice_of_stream(self, choice):
        print(choice)
        address = self.callbacks["get_source_address"](choice)
        print(address)
        self.option_menu.place_forget()

    def event_camera_to_fullscreen(self, event):
        self.callbacks["switch_camera_to_fullscreen"](self)
        self.camera_to_fullscreen()
        self.canvas.bind('<Double-1>', lambda event: self.event_camera_to_grid(event))

    def event_camera_to_grid(self, event):
        self.callbacks["swich_camera_to_grid"](self)
        self.camera_to_grid()
        self.canvas.bind('<Double-1>', lambda event: self.event_camera_to_fullscreen(event))

    def camera_to_fullscreen(self):
        width, height = self.callbacks["get_parent_sizes"]()
        self.configure(width=width, height=height)
        self.resize_canvas(width=width, height=height)

    def camera_to_grid(self):
        width, height = self.callbacks["get_camera_sizes"]()
        self.resize_canvas(width=width, height=height)
        self.configure(width=width, height=height)

    def set_grid_coords(self, x, y):
        self.grid_coords["x"] = x
        self.grid_coords["y"] = y

    def resize_canvas(self, width, height):
        if self.canvas:
            self.canvas.configure(width=int(width * 0.9), height=int(height * 0.9))
        

class CamerasFrame(tk.Frame):
    def __init__(self, window, sources, callbacks = {}):
        super().__init__(window)
        self.sources = None
        self.sources_names = None
        if sources:
            self.sources = sources
            self.sources_names = [name for name, _ in self.sources]
        self.callbacks = callbacks
        self.cameras = []
        self.sub_frame = tk.Frame(self)
        self.sub_frame.pack(anchor="center", expand=True)

        self.callbacks_for_cameras = {
            "switch_camera_to_fullscreen": self.switch_camera_to_fullscreen,
            "swich_camera_to_grid": self.swich_camera_to_grid,
            "get_camera_sizes": self.get_camera_sizes,
            "get_parent_sizes": self.get_parent_sizes,
            "get_source_address": self.get_source_address
        }

    def spawn_cameras(self):
        width_cam, height_cam = self.get_camera_sizes()
        width, height = self.winfo_width(), self.winfo_height()
        grid = self.callbacks["get_current_grid"]()
        index_select = 0
        index_delete = len(self.cameras) - 1
        while index_delete >= grid * grid:
            self.cameras[index_delete].grid_forget()
            self.cameras.pop()
            index_delete -= 1
        for i in range(grid):
            for j in range(grid):
                index_select = i * grid + j
                cam = None
                try:
                    cam = self.cameras[index_select]
                except:
                    cam = CameraTk(sources_names=self.sources_names, window=self.sub_frame, callbacks=self.callbacks_for_cameras, width=width_cam, height=height_cam)
                    self.cameras.append(cam)
                cam.grid(row=i, column=j, sticky=tk.NSEW, padx=int(width*0.005), pady=int(height*0.005))
                cam.set_grid_coords(j, i)
                cam.configure(width=width_cam, height=height_cam)
    
    def get_source_address(self, source_name):
        for name, address in self.sources:
            if name == source_name:
                return address

    def all_cameras_resize_canvas(self):
        width, height = self.get_camera_sizes()
        for cam in self.cameras:
            cam.resize_canvas(width, height)

    def switch_camera_to_fullscreen(self, camera_to_increase):
        self.callbacks["toggle_viewing_menu"]()
        self.update()
        for cam in self.cameras:
            cam.grid_remove()
        camera_to_increase.pack()

    def swich_camera_to_grid(self, camera_to_decrease):
        camera_to_decrease.pack_forget()
        self.callbacks["toggle_viewing_menu"]()
        self.update()
        for cam in self.cameras:
            if cam.grid_coords["x"] != None and cam.grid_coords["y"] != None:
                cam.grid()

    def get_camera_sizes(self):
        width = self.winfo_width()
        height = self.winfo_height()
        grid = self.callbacks["get_current_grid"]()
        return int(width / grid - width * 0.01), int(height / grid - height * 0.01)
    
    def get_parent_sizes(self):
        return self.winfo_width(), self.winfo_height()

    def update_scene(self):
        grid = self.callbacks["get_current_grid"]()


class MenuFrame(tk.Frame):
    def __init__(self, window, num_max_grid = 10, callbacks={}):
        super().__init__(window)
        self.num_max_grid = num_max_grid
        self.callbacks = callbacks
        self.grid_options = self.__create_grid_options()   # [1, 2, 3, 4, ...]
        self.create_info_frame()
        self.selected_size_grid = tk.StringVar()
        self.create_func_frame()

    def show_info(self):
        showinfo(title="Управление", message="ESC - закрыть;\nF11 - свернуть")

    def __create_grid_options(self):
        grid_options = []
        for i in range(self.num_max_grid):
            grid_options.append(f" {i + 1} ")
        return grid_options

    def create_info_frame(self):
        frame_left = tk.Frame(self)
        frame_left.pack(side="left", fill="x", expand=True)
        button = tk.Button(frame_left, text="Клавиши\nуправления", command=lambda: self.show_info())
        button.pack(expand=True, anchor="center", padx=5, pady=5)

    def create_func_frame(self):
        frame_right = tk.Frame(self)
        frame_right.pack(side="right", fill="x", expand=True)
        sub_frame_right = tk.Frame(frame_right)
        sub_frame_right.pack(anchor="center")
        grid = self.callbacks["get_current_grid"]()
        tk.Label(sub_frame_right, text="Размер сетки: ").grid(row=0, column=0, ipadx=10, ipady=10)
        self.selected_size_grid.set(str(grid))
        tk.OptionMenu(sub_frame_right, self.selected_size_grid, *self.grid_options, command=lambda choice: self.event_grid_change(choice)).grid(row=0, column=1, ipadx=10, ipady=10)

        #Placement of the func buttons
        # tk.Button(sub_frame_right, text="Добавить все камеры", command=lambda: self.call_all_camera()).grid(row=0, column=2, ipadx=10, ipady=10, rowspan=2)

    def event_grid_change(self, choice):
        self.selected_size_grid.set(choice)
        self.callbacks["set_current_grid"](elem=int(choice))
        self.callbacks["all_cameras_resize_canvas"]()
        self.callbacks["spawn_cameras"]()

    def adding_callback(self, name=None, func=None):
        if name != None and func != None:
            self.callbacks[name] = func

class App(tk.Tk):
    def __init__(self, sources=None):
        super().__init__()
        self.sources = sources
        self.attributes("-fullscreen", True)
        self.bind("<F11>", lambda event: self.iconify())
        self.bind("<Escape>", lambda event: self.destroy())
        self.current_cameras_grid = 1

        self.callbacks_for_menu = {
            "set_current_grid": self.set_current_grid,
            "get_current_grid": self.get_current_grid
        }
        self.menu_frame = MenuFrame(window=self, callbacks=self.callbacks_for_menu)
        self.menu_frame.pack(fill="x")

        self.callbacks_for_cameras = {
            "toggle_viewing_menu": self.toggle_viewing_menu,
            "get_current_grid": self.get_current_grid
        }
        self.cameras_frame = CamerasFrame(window=self, sources=self.sources, callbacks=self.callbacks_for_cameras)
        self.cameras_frame.pack(expand=True, fill="both")
        self.menu_frame.adding_callback("spawn_cameras", self.cameras_frame.spawn_cameras)
        self.menu_frame.adding_callback("all_cameras_resize_canvas", self.cameras_frame.all_cameras_resize_canvas)
        self.cameras_frame.update()
        self.cameras_frame.spawn_cameras()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.mainloop()

    def set_current_grid(self, elem=1):
        self.current_cameras_grid = elem

    def get_current_grid(self):
        return self.current_cameras_grid

    def toggle_viewing_menu(self):
        self.menu_frame.pack_forget() if self.menu_frame.winfo_viewable() else self.menu_frame.pack(before=self.cameras_frame, fill="x")

    def on_closing(self, event=None):
        print('[Application] stoping threads')
        # for source in self.cameras_frame.cameras:
        #     source.cameras.vid.running = False
        print('[Application] exit')
        self.destroy()

# sources = [
#         ("first",       "#000000"),
#         ("second",      "#FF0000"),
#         ("third",       "#00FF00"),
#         ("fourth",      "#0000FF"),
#         ("fifth",       "#500050"),
#         ("sixth",       "#FFFF00"),
#         ("seventh",     "#00FFFF"),
#         ("eighth",      "#FF00FF"),
#         ("ninth",       "#800080"),
#         ("tenth",       "#008000"),
#         ("eleventh",    "#000080"),
#         ("twelfth",     "#005500"),
#     ]
sources = [
        ('hallway_igz', "rtsp://admin:Qwerty123@192.168.1.72:554/cam/realmonitor?channel=3&subtype=1"),        #192.168.1.34
        ('fire_exit_imitif', "rtsp://admin:Qwerty123@192.168.1.72:554/cam/realmonitor?channel=5&subtype=1"),   #192.168.1.31
        ('angle_imitif', "rtsp://admin:Qwerty123@192.168.1.72:554/cam/realmonitor?channel=1&subtype=1"),       #192.168.1.35
        ('hallway_imitif', "rtsp://admin:Qwerty123@192.168.1.72:554/cam/realmonitor?channel=7&subtype=1"),     #192.168.1.37
        ('hall_imitif', "rtsp://admin:Qwerty123@192.168.1.72:554/cam/realmonitor?channel=8&subtype=1"),        #192.168.1.38
        ('street', "rtsp://admin:Qwerty123@192.168.1.72:554/cam/realmonitor?channel=9&subtype=1"),             #192.168.1.39
        ('hall_igz', "rtsp://admin:Qwerty123@192.168.1.72:554/cam/realmonitor?channel=6&subtype=1"),           #192.168.1.36
        ('angle_igz', "rtsp://admin:Qwerty123@192.168.1.72:554/cam/realmonitor?channel=4&subtype=1"),          #192.168.1.32
        ('fire_exit_igz', "rtsp://admin:Qwerty123@192.168.1.72:554/cam/realmonitor?channel=10&subtype=1"),     #192.168.1.40
        ('301_6k', "rtsp://admin:Qwerty123@192.168.1.72:554/cam/realmonitor?channel=2&subtype=1"),             #192.168.1.33
        ('323_6k_window', "rtsp://admin:Qwerty123@192.168.1.72:554/cam/realmonitor?channel=11&subtype=1"),     #192.168.1.41
        ('323_6k_door', "rtsp://admin:Qwerty123@192.168.1.72:554/cam/realmonitor?channel=12&subtype=1")        #192.168.1.42
    ]

if __name__ == "__main__":
    application = App(sources=sources)