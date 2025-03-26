from ultralytics import YOLO
import torch

print(torch.cuda.is_available())
device = "0" if torch.cuda.is_available() else "cpu"
if device == "0":
    torch.cuda.set_device(0)

print("Device: ", device)
model = YOLO("yolo11n.pt")
print("Before: ", model.device.type)
result = model("image.png")
print("After: ", model.device.type)