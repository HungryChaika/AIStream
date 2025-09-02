import tkinter as tk
from tkinter import filedialog
import json
import uuid
from pprint import pformat
from os import path
from math import atan2, degrees, sqrt, ceil


def points(el):
    if "points" in el["XY"][0]:
        return [(xy["x"], xy["y"]) for xy in el["XY"][0]["points"]]
    else:
        return el["XY"][0][:-1]

class SchemeCam():
    def __init__(self):
        self.j = self.__open_json("6k3f")
        self.j_cam = self.__open_json("cams_position")
        self.scale = 18
        self.canvas_floor = []  # пары этаж-canvas
        self.canvas_cams = []   # пары canvas-камеры
        self.tops_list = []     # список окон
        self.min_x, self.min_y, self.max_x, self.max_y = self.__calc_max_min()
        self.offset_x, self.offset_y = -self.min_x, -self.min_y

    def __open_json(self, name):
        ''' Открытие json, имеющиего информацию наблюдаемой территории '''
        filename = rf"{path.dirname(__file__)}/res/{name}.json"
        filename.replace("\\", "/")
        try:
            with open(filename) as f:
                j = json.load(f)
        except:
            filename = filedialog.askopenfilename(filetypes=(("BIM JSON", "*.json"),))
            if not filename:
                exit()
            with open(filename) as f:
                j = json.load(f)
        return j

    def __calc_max_min(self):
        ''' Расчёт минимальных и максимальных значений координат всей территории '''
        min_x, min_y, max_x, max_y = 0, 0, 0, 0
        for lvl in self.j['Level']:
            for elem in lvl['BuildElement']:
                for x, y in points(elem):
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)
        return min_x, min_y, max_x, max_y
    
    def __crd(self, x, y):
        ''' Перевод из координат здания в координаты canvas '''
        return (self.offset_x + x) * self.scale, (self.offset_y - y) * self.scale 
    
    def __crd_revers(self, x, y):
        ''' Перевод из координат canvas в координаты здания '''
        return (x / self.scale - self.offset_x), (-y / self.scale + self.offset_y)
    
    def __create_camera(self, canvas, name_level, floor_level):
        camera = CameraCanvas(canvas.create_oval(0, 0, 0, 0, fill = "#FF0000", outline = "#000000"), 
                              camera_radius = min(self.max_x * 0.05 * self.scale / 2, self.max_y * 0.05 * self.scale / 2),
                              floor_level=floor_level, name_level=name_level)
        canvas.bind("<Motion>", lambda event: self.__event_move_cam(event, camera, canvas))
        canvas.bind("<Button-1>", lambda event: self.__event_place_cam(event, camera, canvas))
        canvas.bind("<Tab>", lambda event: self.__event_resetinging_cam_placement(event, camera, canvas, name_level, floor_level))

    def __event_move_cam(self, event, camera, canvas):
        ''' Привязка камеры к курсору мыши '''
        x, y = canvas.canvasx(event.x), canvas.canvasy(event.y)
        canvas.coords(camera.camera, x - camera.camera_radius, y - camera.camera_radius, x + camera.camera_radius, y + camera.camera_radius)
    
    def __event_place_cam(self, event, camera, canvas):
        canvas.unbind("<Motion>")
        canvas.unbind("<Button-1>")
        x, y = canvas.canvasx(event.x), canvas.canvasy(event.y)
        camera.set_camera_center_coord(x, y)
        camera.set_camera_build_center_coord(*self.__crd_revers(x, y))
        canvas.itemconfig(camera.camera, fill="#00FF00")
        camera.set_field_of_view(canvas.create_arc((x - camera.camera_radius * 2, y - camera.camera_radius * 2), 
                                              (x + camera.camera_radius * 2, y + camera.camera_radius * 2), 
                                              fill="#FF0000", outline="#000000"))
        canvas.bind("<Motion>", lambda event: self.__event_rotation_cams_field_view(event, camera, canvas))
        canvas.bind("<Button-1>", lambda event: self.__event_place_field_view(event, camera, canvas))

    def __event_rotation_cams_field_view(self, event, camera, canvas):
        canvas.itemconfig(camera.field_of_view, start = degrees(
            atan2(canvas.canvasx(event.x) - camera.center_coord["x"], canvas.canvasy(event.y) - camera.center_coord["y"])) + 225)

    def __event_place_field_view(self, event, camera, canvas):
        canvas.unbind("<Motion>")
        canvas.unbind("<Button-1>")
        canvas.tag_raise(camera.camera)
        canvas.itemconfig(camera.field_of_view, fill="#00FF00")
        data = {
            "FloorLevel": camera.floor_level,
            "NameLevel": camera.name_level,
            "CenterX": camera.build_center_ccord["x"],
            "CenterY": camera.build_center_ccord["y"],
            "AngleOfRotation": canvas.itemcget(camera.field_of_view, "start")
        }
        self.__data_filling_window(data)

    def __data_filling_window(self, data):
        top = tk.Toplevel()
        top.geometry("300x300")
        frame = tk.Frame(top)
        frame.pack(expand=True, fill="both", anchor="center")
        label_name = tk.Label(frame, text="Введите название:")
        entry_name = tk.Entry(frame)
        label_address = tk.Label(frame, text="Введите адрес для подключения:")
        entry_address = tk.Entry(frame)
        label_name.pack()
        entry_name.pack()
        label_address.pack()
        entry_address.pack()
        tk.Button(frame, text="Ввод", command=lambda entry_name = entry_name, entry_address = entry_address, 
                  data = data, top = top : self.__event_data_filling(entry_name, entry_address, data, top)).pack()

    def __event_data_filling(self, entry_name, entry_address, data, top):
        if(entry_name.get()):
            data["Name"] = entry_name.get()
            data["Address"] = entry_address.get()
            top.destroy()
            name_f = "cams_position"
            for lvl in self.j_cam["Level"]:
                if lvl["ZLevel"] == data["FloorLevel"] and lvl["NameLevel"] == data["NameLevel"]:
                    lvl["BuildElement"].append(
                        { "Name": data["Name"], "Id": f"{uuid.uuid1()}", "Sign": "Camera", "AngleOfRotation": data["AngleOfRotation"], "Address": data["Address"], "SizeZ": 0.0, "XY": [{ "points": [{ "x": data["CenterX"], "y": data["CenterY"] }] }] }
                    )
                break
            with open(path.join(rf"{path.dirname(__file__)}/res/", f"{name_f}.json"), "w") as json_file:
                json.dump(self.j_cam, json_file, ensure_ascii=False, indent=4)

    def __event_resetinging_cam_placement(self, event, camera, canvas, name_level, floor_level):
        camera.destroy(canvas)
        self.__create_camera(canvas, name_level, floor_level)

    def __place_all_cameras(self, canvas, name_level, floor_level, callback):
        camera_radius = min(self.max_x * 0.05 * self.scale / 2, self.max_y * 0.05 * self.scale / 2)
        for lvl in self.j_cam["Level"]:
            if lvl["ZLevel"] == floor_level and lvl["NameLevel"] == name_level:
                camera_center = {}
                for el in lvl["BuildElement"]:
                    for x, y in points(el):
                        camera_center["x"], camera_center["y"] = self.__crd(x, y)
                    camera = CameraCanvas(
                            camera = canvas.create_oval( 
                                    camera_center["x"] - camera_radius, camera_center["y"] - camera_radius, 
                                    camera_center["x"] + camera_radius, camera_center["y"] + camera_radius, 
                                    fill = "#00FF00", outline = "#000000"), 
                            camera_radius = camera_radius,
                            field_of_view = canvas.create_arc( 
                                    (camera_center["x"] - camera_radius * 2, camera_center["y"] - camera_radius * 2), 
                                    (camera_center["x"] + camera_radius * 2, camera_center["y"] + camera_radius * 2), 
                                    fill = "#00FF00", outline = "#000000", start = el["AngleOfRotation"]), 
                            floor_level = floor_level, name_level = name_level)
                    canvas.tag_bind(camera.camera, "<Enter>", lambda event, camera=camera: change_color(camera, canvas, fill="#0000FF"))
                    canvas.tag_bind(camera.camera, "<Leave>", lambda event, camera=camera: change_color(camera, canvas, fill="#00FF00"))
                    canvas.tag_bind(camera.field_of_view, "<Enter>", lambda event, camera=camera: change_color(camera, canvas, fill="#0000FF"))
                    canvas.tag_bind(camera.field_of_view, "<Leave>", lambda event, camera=camera: change_color(camera, canvas, fill="#00FF00"))
                    canvas.tag_bind(camera.camera, "<Button-1>", lambda event, address=el["Address"], name=el["Name"], schemeSelf=self, 
                                    callback=callback: cam_click(schemeSelf=schemeSelf, address=address, name=name, callback=callback))
                    canvas.tag_bind(camera.field_of_view, "<Button-1>", lambda event, address=el["Address"], name=el["Name"], schemeSelf=self, 
                                    callback=callback: cam_click(schemeSelf=schemeSelf, address=address, name=name, callback=callback))
                    self.canvas_cams.append((canvas, camera))

        def change_color(camera, canvas, fill):
            canvas.itemconfig(camera.camera, fill=fill)
            canvas.itemconfig(camera.field_of_view, fill=fill)

        def cam_click(schemeSelf, address, name, callback):
            callback(choice=address, name=name, isAddress=True)
            for elem in schemeSelf.tops_list:
                elem.destroy()
            schemeSelf.tops_list = []
            schemeSelf.canvas_floor = []
            schemeSelf.canvas_floor = []

    def get_sources_names(self):
        return [el["Name"] for lvl in self.j_cam["Level"] for el in lvl["BuildElement"]]
    
    def get_sources_address_and_names(self):
        return [(el["Address"], el["Name"]) for lvl in self.j_cam["Level"] for el in lvl["BuildElement"]]
    
    def get_sources_address_using_name(self, name):
        for lvl in self.j_cam["Level"]:
            for el in lvl["BuildElement"]:
                if el["Name"] == name:
                    return el["Address"]
                
    def get_sources_count(self):
        for lvl in self.j_cam["Level"]:
            return ceil(sqrt(len(lvl["BuildElement"])))

    def process(self, callback = lambda:None, isNewCam = False):
        ''' Отрисовка схемы территории '''
        # Tkinter окно для каждого этажа
        for lvl in self.j["Level"]:
            top = tk.Toplevel()
            top.bind("<Escape>", lambda event: top.destroy())
            top.title(lvl["NameLevel"])
            frame = tk.Frame(top)
            frame.pack(expand=True, fill=tk.BOTH)
            canvas = tk.Canvas(frame, scrollregion=(*self.__crd(self.min_x, self.max_y), *self.__crd(self.max_x, self.min_y)))
            v = tk.Scrollbar(frame, orient = 'vertical')
            v.pack(side=tk.RIGHT, fill=tk.Y)
            v.config(command=canvas.yview)
            h = tk.Scrollbar(frame, orient = 'horizontal')
            h.pack(side=tk.BOTTOM, fill=tk.X)
            h.config(command=canvas.xview)
            canvas.config(xscrollcommand = h.set, yscrollcommand = v.set)
            canvas.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
            try:
                top.attributes("-zoomed", True)
            except tk.TclError:
                top.wm_state("zoomed")
            self.canvas_floor.append((lvl, canvas))
            self.tops_list.append(top)
        # Рисуем фон
        colors = {"Room": "", "DoorWayInt": "yellow", "DoorWayOut": "brown", "DoorWay": "", "Staircase": "green"}
        for lvl, canvas in self.canvas_floor:
            for el in lvl['BuildElement']:
                polygon = canvas.create_polygon([self.__crd(x, y) for x, y in points(el)], fill=colors[el['Sign']], outline='black')
                # canvas.tag_bind(polygon, "<Button-1>", lambda e, el=el: tk.messagebox.showinfo("Инфо об объекте", pformat(el, compact=True, depth=5)))
            if isNewCam:
                self.__create_camera(canvas, lvl["NameLevel"], lvl["ZLevel"])
            else:
                self.__place_all_cameras(canvas, lvl["NameLevel"], lvl["ZLevel"], callback)

class CameraCanvas():
    def __init__(self, camera, field_of_view = None, camera_radius = None, field_of_view_radius = None, name_level = None, floor_level = None):
        self.camera = camera
        self.field_of_view = field_of_view
        self.center_coord = {
            "x": None,
            "y": None
        }
        self.build_center_ccord = {
            "x": None,
            "y": None
        }
        self.camera_radius = camera_radius
        self.field_of_view_radius = field_of_view_radius
        self.name_level = name_level
        self.floor_level = floor_level

    def set_field_of_view(self, field_of_view):
        self.field_of_view = field_of_view

    def set_camera_radius(self, r):
        self.camera_radius = r
        
    def set_camera_center_coord(self, x, y):
        self.center_coord["x"] = x
        self.center_coord["y"] = y

    def set_camera_build_center_coord(self, x, y):
        self.build_center_ccord["x"] = x
        self.build_center_ccord["y"] = y

    def destroy(self, canvas):
        if self.camera:
            canvas.delete(self.camera)
        if self.field_of_view:
            canvas.delete(self.field_of_view)