import cv2
import torch
from ultralytics import YOLO

print(torch.cuda.is_available())
device = "0" if torch.cuda.is_available() else "cpu"
if device == "0":
    torch.cuda.set_device(0)

model = YOLO("yolo11x.pt")
results = model.track(source='rtsp://admin:Qwerty123@192.168.1.33:554/cam/realmonitor?channel=1&subtype=1', show=True)
video_cap = cv2.VideoCapture(results)

while True:
    ret, frame = video_cap.read()
    model.cuda()

    if not ret:
        break

    cv2.imshow("Frame", frame)

    if cv2.waitKey(1) == ord("q"):
        break

video_cap.release()
cv2.destroyAllWindows()