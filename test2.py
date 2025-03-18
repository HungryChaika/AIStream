import cv2
from ultralytics import YOLO

model = YOLO("yolo11x.pt")
results = model.track(source='rtsp://admin:Qwerty123@192.168.1.33:554/cam/realmonitor?channel=1&subtype=1', show=True)
video_cap = cv2.VideoCapture(results)

while True:
    ret, frame = video_cap.read()
    model.cpu()

    if not ret:
        break

    cv2.imshow("Frame", frame)

    if cv2.waitKey(1) == ord("q"):
        break

video_cap.release()
cv2.destroyAllWindows()