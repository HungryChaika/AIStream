from collections import defaultdict
from settings_local import SETTINGS

import numpy as np
import cv2
import torch

from ultralytics import YOLO
from ultralytics.utils.plotting import Annotator, colors

import threading


MODEL_NAMES = ["models/yolo11n.pt", "models/yolo11n.pt"]
SOURCES = [ "rtsp://admin:Qwerty123@192.168.1.72:554/cam/realmonitor?channel=9&subtype=1",
            "rtsp://admin:Qwerty123@192.168.1.72:554/cam/realmonitor?channel=2&subtype=1" ]


def test(model_name, video_file, nameWindow):
    track_history = defaultdict(list)

    device = "0" if torch.cuda.is_available() else "cpu"
    if device == "0":
        torch.cuda.set_device(0)
    
    vid_frame_count = 0

    model = YOLO(model_name)
    model.to("cuda") if device == "0" else model.to("cpu")

    names = model.names

    video_cap = cv2.VideoCapture(video_file)
    frame_width = int(video_cap.get(3))
    frame_height = int(video_cap.get(4))

    while video_cap.isOpened():
        success, frame = video_cap.read()
        if not success:
            break
        vid_frame_count += 1

        frame = cv2.resize(frame, (int(frame_width * SETTINGS["resize_coeff"]), int(frame_height * SETTINGS["resize_coeff"])), interpolation=cv2.INTER_AREA)

        results = model.track(frame, persist=True, classes=SETTINGS["classes"])

        if results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cuda()
            track_ids = results[0].boxes.id.int().cuda().tolist()
            clss = results[0].boxes.cls.cuda().tolist()

            annotator = Annotator(frame, line_width=SETTINGS["line_thickness"], example=str(names))

            for box, track_id, cls in zip(boxes, track_ids, clss):
                annotator.box_label(box, str(names[cls]) + ", id: " + str(track_id), color=colors(cls, True))
                bbox_center = (box[0] + box[2]) / 2, (box[1] + box[3] / 2)
                track = track_history[track_id]
                track.append((float(bbox_center[0]), float(bbox_center[1])))
                if len(track) > 30:
                    track.pop(0)
                points = np.hstack(track).astype(np.int32).reshape((-1, 1, 2))
                cv2.polylines(frame, [points], isClosed=False, color=colors(cls, True), thickness=SETTINGS["track_thickness"])

        if SETTINGS["view_img"]:
            
            if vid_frame_count == 1:
                cv2.namedWindow(nameWindow)
            cv2.imshow(nameWindow, frame)

        if cv2.waitKey(1) & 0xFF == ord(SETTINGS["exitButton"]):
            break

    del vid_frame_count
    video_cap.release()
    cv2.destroyWindow(nameWindow)




tracker_threads = []
nameWindow = "1"
for video_file, model_name in zip(SOURCES, MODEL_NAMES):
    if video_file == SOURCES[0]:
        nameWindow = "channel_9_street"
    else:
        nameWindow = "channel_2_301_6k"
    thread = threading.Thread(target=test, args=(model_name, video_file, nameWindow), daemon=True)
    tracker_threads.append(thread)
    thread.start()


for thread in tracker_threads:
    thread.join()