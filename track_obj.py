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

#For little NetRegistrator. IP is 192.168.1.72
stream_channel = {
    'fire_exit_imitif': "5",    #192.168.1.31
    'angle_imitif': "1",        #192.168.1.35
    'hallway_imitif': "7",      #192.168.1.37
    'hall_imitif': "8",         #192.168.1.38
    'street': "9",              #192.168.1.39
    'hall_igz': "6",            #192.168.1.36
    'hallway_igz': "3",         #192.168.1.34
    'angle_igz': "4",           #192.168.1.32
    'fire_exit_igz': "10",      #192.168.1.40
    '301_6k': "2",              #192.168.1.33
    '323_6k_window': "11",      #192.168.1.41
    '323_6k_door': "12"         #192.168.1.42
}
stream_type = {
    'main_stream': "0",
    'sub_stream': "1"
}

key_stream_channel = '301_6k'
key_stream_type = 'sub_stream'

stream_params = f"channel={ stream_channel[key_stream_channel] }&subtype={ stream_type[key_stream_type] }"
source=f"rtsp://admin:Qwerty123@192.168.1.72:554/cam/realmonitor?{ stream_params }"
view_img=True
save_img=False
exist_ok=False
classes=None
line_thickness=2
track_thickness=2
resize_coeff=1

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

    save_dir = increment_path(Path("saved_streams") / "exp", exist_ok)
    save_dir.mkdir(parents=True, exist_ok=True)
    video_writer = cv2.VideoWriter(f"{save_dir}/{key_stream_channel}_{key_stream_type}.avi", fourcc, fps, (frame_width, frame_height))
    while video_cap.isOpened():
        success, frame = video_cap.read()
        if not success:
            break
        vid_frame_count += 1

        frame = cv2.resize(frame, (int(frame_width * resize_coeff), int(frame_height * resize_coeff)), interpolation=cv2.INTER_AREA)

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