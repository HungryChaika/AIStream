import tkinter as tk
from tkinter import filedialog
import json
from pprint import pformat
from os import path

master = tk.Tk()
master.title("Новая камера")
frame = tk.Frame(master)
frame.pack(expand=True, fill="both", anchor="center")

label_name = tk.Label(frame, text="Введите название:")
entry_name = tk.Entry(frame)

label_address = tk.Label(frame, text="Введите адрес:")
entry_address = tk.Entry(frame)

label_name.pack()
entry_name.pack()
label_address.pack()
entry_address.pack()
tk.Button(frame, text="Ввод", command=lambda: next_step()).pack()

def next_step():
    pass

master.mainloop()