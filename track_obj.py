from collections import defaultdict
from pathlib import Path

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

weights="yolo11x.pt"
source="rtsp://admin:Qwerty123@192.168.1.72:554/cam/realmonitor?channel=3&subtype=1"
view_img=True
save_img=False
exist_ok=False
classes=None
line_thickness=2
track_thickness=2
region_thickness=2

def main():
    
    vid_frame_count = 0

    model = YOLO(f"{weights}")
    model.to("cuda") if device == "0" else model.to("cpu")

    names = model.names

    video_cap = cv2.VideoCapture(source)
    frame_width = int(video_cap.get(3))
    frame_height = int(video_cap.get(4))
    fps = int(video_cap.get(5))
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")

    save_dir = increment_path(Path("ultralytics_rc_output") / "exp", exist_ok)
    save_dir.mkdir(parents=True, exist_ok=True)
    video_writer = cv2.VideoWriter(str(save_dir / f"{Path(source).stem}.avi"), fourcc, fps, (frame_width, frame_height))

    while video_cap.isOpened():
        success, frame = video_cap.read()
        if not success:
            break
        vid_frame_count += 1

        frame = cv2.resize(frame, (int(frame_width * 0.25), int(frame_height * 0.25)), interpolation=cv2.INTER_AREA)

        results = model.track(frame, persist=True, classes=classes)

        if results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cuda()
            track_ids = results[0].boxes.id.int().cuda().tolist()
            clss = results[0].boxes.cls.cuda().tolist()

            annotator = Annotator(frame, line_width=line_thickness, example=str(names))

            for box, track_id, cls in zip(boxes, track_ids, clss):
                annotator.box_label(box, str(names[cls]), color=colors(cls, True))
                bbox_center = (box[0] + box[2]) / 2, (box[1] + box[3] / 2)
                track = track_history[track_id]
                track.append((float(bbox_center[0]), float(bbox_center[1])))
                if len(track) > 30:
                    track.pop(0)
                points = np.hstack(track).astype(np.int32).reshape((-1, 1, 2))
                cv2.polylines(frame, [points], isClosed=False, color=colors(cls, True), thickness=track_thickness)

        if view_img:
            if vid_frame_count == 1:
                cv2.namedWindow("Ultralytics YOLOv8 Region Counter Movable")
            cv2.imshow("Ultralytics YOLOv8 Region Counter Movable", frame)

        if save_img:
            video_writer.write(frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    del vid_frame_count
    video_writer.release()
    video_cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()