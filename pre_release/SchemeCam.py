import tkinter as tk
from tkinter import filedialog
import json
from pprint import pformat
from os import path
from math import atan2, degrees
# import math

def points(el):
    if "points" in el["XY"][0]:
        return [(xy["x"], xy["y"]) for xy in el["XY"][0]["points"]]
    else:
        return el["XY"][0][:-1]

class SchemeCam():
    def __init__(self):
        self.j = self.__open_json()
        self.scale = 18
        self.cameras = {}
        self.canvas_floor = []  # пары этаж-canvas
        self.min_x, self.min_y, self.max_x, self.max_y = self.__calc_max_min()
        self.offset_x, self.offset_y = -self.min_x, -self.min_y
        self.__process()

    def __open_json(self):
        ''' Открытие json, имеющиего информацию наблюдаемой территории '''
        filename = rf"{path.dirname(__file__)}/res/6k3f.json"
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
    
    def __create_camera_user(self, canvas, floor_name, floor_level):
        camera = CameraCanvas(canvas.create_oval(0, 0, 0, 0, fill = "#FF0000", outline = "#000000"), 
                              camera_radius = min(self.max_x * 0.05 * self.scale / 2, self.max_y * 0.05 * self.scale / 2))
        canvas.bind("<Motion>", lambda event: self.__event_move_cam(event, camera, canvas))
        canvas.bind("<Button-1>", lambda event: self.__event_place_cam(event, camera, canvas, floor_name, floor_level))
        canvas.bind("<Tab>", lambda event: self.__event_resetinging_cam_placement(event, camera, canvas, floor_name, floor_level))

    def __event_move_cam(self, event, camera, canvas):
        ''' Привязка камеры к курсору мыши '''
        x, y = canvas.canvasx(event.x), canvas.canvasy(event.y)
        canvas.coords(camera.camera, x - camera.camera_radius, y - camera.camera_radius, x + camera.camera_radius, y + camera.camera_radius)
    
    def __event_place_cam(self, event, camera, canvas, floor_name, floor_level):
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
        canvas.bind("<Button-1>", lambda event: self.__event_place_field_view(event, camera, canvas, floor_name, floor_level))

    def __event_rotation_cams_field_view(self, event, camera, canvas):
        canvas.itemconfig(camera.field_of_view, start = degrees(
            atan2(canvas.canvasx(event.x) - camera.center_coord["x"], canvas.canvasy(event.y) - camera.center_coord["y"])) + 225)

    def __event_place_field_view(self, event, camera, canvas, floor_name, floor_level):
        canvas.unbind("<Motion>")
        canvas.unbind("<Button-1>")
        canvas.tag_raise(camera.camera)
        canvas.itemconfig(camera.field_of_view, fill="#00FF00")
        print(floor_name, floor_level)



        self.test(camera, canvas)



    def test(self, camera, canvas):
        canvas.tag_bind(camera.camera, "<Enter>", lambda event: self.aaaa(event, camera, canvas, fill="#0000FF"))
        canvas.tag_bind(camera.camera, "<Leave>", lambda event: self.aaaa(event, camera, canvas, fill="#00FF00"))
        canvas.tag_bind(camera.field_of_view, "<Enter>", lambda event: self.aaaa(event, camera, canvas, fill="#0000FF"))
        canvas.tag_bind(camera.field_of_view, "<Leave>", lambda event: self.aaaa(event, camera, canvas, fill="#00FF00"))

    def aaaa(self, event, camera, canvas, fill):
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        canvas.itemconfig(camera.camera, fill=fill)
        canvas.itemconfig(camera.field_of_view, fill=fill)





    def __event_resetinging_cam_placement(self, event, camera, canvas, floor_name, floor_level):
        camera.destroy(canvas)
        self.__create_camera_user(canvas, floor_name, floor_level)

    def __process(self):
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
            
        # Рисуем фон
        colors = {"Room": "", "DoorWayInt": "yellow", "DoorWayOut": "brown", "DoorWay": "", "Staircase": "green"}
        for lvl, canvas in self.canvas_floor:
            for el in lvl['BuildElement']:
                polygon = canvas.create_polygon([self.__crd(x, y) for x, y in points(el)], fill=colors[el['Sign']], outline='black')
                # canvas.tag_bind(polygon, "<Button-1>", lambda e, el=el: tk.messagebox.showinfo("Инфо об объекте", pformat(el, compact=True, depth=2)))
            self.__create_camera_user(canvas, lvl["NameLevel"], lvl["ZLevel"])

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Визуализация")
        self.bind("<Escape>", lambda event: self.destroy())
        self.scheme = SchemeCam()
        self.mainloop()

class CameraCanvas():
    def __init__(self, camera, field_of_view = None, camera_radius = None, field_of_view_radius = None):
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

    def set_field_of_view(self, field_of_view):
        self.field_of_view = field_of_view

    def set_camera_radius(self, x, y):
        self.camera_radius["x"] = x
        self.camera_radius["y"] = y

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

app = App()


#     # def cntr(el):
#     #     ''' Центр для canvas по координатам здания '''
#     #     xy = [crd(x, y) for x, y in points(el)]
#     #     return sum((x for x, y in xy))/len(xy), sum((y for x, y in xy))/len(xy)