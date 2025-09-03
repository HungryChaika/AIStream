from collections import defaultdict
from pathlib import Path
from settings_local import SETTINGS

import numpy as np
import cv2
import torch

from ultralytics import YOLO
from ultralytics.utils.files import increment_path
from ultralytics.utils.plotting import Annotator, colors

track_history = defaultdict(list)

print("CUDA is available: ", torch.cuda.is_available())
device = "0" if torch.cuda.is_available() else "cpu"
if device == "0":
    torch.cuda.set_device(0)

class AiDetection:
    def __init__(self):    
        self.model = YOLO("{}".format(SETTINGS["weights"]))
        self.model.to("cuda") if device == "0" else self.model.to("cpu")
        self.names = self.model.names

    def detect(self, frame):
        results = self.model.track(frame, persist=True, classes=SETTINGS["classes"])
        if results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cuda()
            track_ids = results[0].boxes.id.int().cuda().tolist()
            clss = results[0].boxes.cls.cuda().tolist()

            annotator = Annotator(frame, line_width=SETTINGS["line_thickness"], example=str(self.names))

            for box, track_id, cls in zip(boxes, track_ids, clss):
                annotator.box_label(box, str(self.names[cls]) + ", id: " + str(track_id), color=colors(cls, True))
                bbox_center = (box[0] + box[2]) / 2, (box[1] + box[3] / 2)
                track = track_history[track_id]
                track.append((float(bbox_center[0]), float(bbox_center[1])))
                if len(track) > 30:
                    track.pop(0)
                points = np.hstack(track).astype(np.int32).reshape((-1, 1, 2))
                cv2.polylines(frame, [points], isClosed=False, color=colors(cls, True), thickness=SETTINGS["track_thickness"])
        return frame