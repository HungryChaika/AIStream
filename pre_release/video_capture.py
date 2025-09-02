import cv2
import PIL.Image, PIL.ImageTk
import time
import threading

class MyVideoCapture:
    def __init__(self, video_source=0, width=None, height=None, fps=None):
        self.video_source = video_source
        self.width = width
        self.height = height
        self.fps = fps
        self.vid = cv2.VideoCapture(video_source)
        if not self.vid.isOpened():
            raise ValueError("[MyVideoCapture] Unable to open video source", video_source)
        if not self.width:
            self.width = int(self.vid.get(cv2.CAP_PROP_FRAME_WIDTH))    # convert float to int
        if not self.height:
            self.height = int(self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT))  # convert float to int
        if not self.fps:
            self.fps = int(self.vid.get(cv2.CAP_PROP_FPS))  # convert float to int
        self.ret = False
        self.frame = None
        self.convert_color = cv2.COLOR_BGR2RGB
        self.convert_pillow = True        
        self.recording = False
        self.recording_filename = 'output.mp4'
        self.recording_writer = None        
        self.running = True
        self.thread = threading.Thread(target=self.process)
        self.thread.start()
        
    def start_recording(self, filename=None):
        if self.recording:
            print('[MyVideoCapture] already recording:', self.recording_filename)
        else:
            if filename:
                self.recording_filename = filename
            else:
                self.recording_filename = time.strftime("%Y.%m.%d %H.%M.%S", time.localtime()) + ".avi"
            fourcc = cv2.VideoWriter_fourcc(*'MP42') # .avi
            self.recording_writer = cv2.VideoWriter(self.recording_filename, fourcc, self.fps, (self.width, self.height))
            self.recording = True
            print('[MyVideoCapture] started recording:', self.recording_filename)
                   
    def stop_recording(self):
        if not self.recording:
            print('[MyVideoCapture] not recording')
        else:
            self.recording = False
            self.recording_writer.release() 
            print('[MyVideoCapture] stop recording:', self.recording_filename)
               
    def record(self, frame):
        if self.recording_writer and self.recording_writer.isOpened():
            self.recording_writer.write(frame)
 
    def process(self):
        while self.running:
            ret, frame = self.vid.read()
            if ret:
                frame = cv2.resize(frame, (int(self.width), int(self.height)))
                if self.recording:
                    self.record(frame)
                if self.convert_pillow:
                    frame = cv2.cvtColor(frame, self.convert_color)
                    frame = PIL.Image.fromarray(frame)
            else:
                print('[MyVideoCapture] stream end:', self.video_source)
                self.running = False
                if self.recording:
                    self.stop_recording()
                break

            self.ret = ret
            self.frame = frame

            time.sleep(1/self.fps)
        
    def get_frame(self):
        return self.ret, self.frame
    
    def set_frame_size(self, w, h):
        self.width = w
        self.height = h
    
    def off(self):
        self.running = False
        if self.vid.isOpened():
            self.vid.release()
        self.thread.join()