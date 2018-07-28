import tkinter
import cv2
import PIL.Image, PIL.ImageTk
import time
import json
import os
import math
from darkflow.net.build import TFNet
import numpy as np
from django.conf import settings
from .models import *

model_path = os.path.join(settings.BASE_DIR,'cfg/yolo-obj.cfg')
weights_path = os.path.join(settings.BASE_DIR,'bin/yolo-obj_1000.weights')
options = {
    'model': model_path,
    'load': weights_path,
    'threshold': 0.4,
    'gpu': 0.7
}
tfnet = None
getcolor = {
    0:(0,0,0),
    1:(255,0,0),
    2:(0,0,255),
    3:(0,255,255),
    4:(0,255,0),
    5:(255,255,0),
    6:(255,0,255),
    7:(100,50,100)
}
area_pts = [[0,719],[0,352],[478,0],[936,0],[1073,250],[1279,495],[1279,719]]   # This is the default area mask. In actual scenario, change according to videoid

vclass_name = ['Tempo','Bike','Car','Taxi','Micro','Pickup','Bus','Truck']


class Analytics:
    def __init__(self):
        self.total_vcount = np.zeros(8, dtype=int)  # Total vehicles count
        self.count_jsondata = []    # For storing in json ...below 2 as well
        self.congestion_jsondata = []
        self.contrib_jsondata = []

        self.numbercount = []
        self.congcount = []
        self.xs = []

        self.realtime_count = np.zeros(8, dtype=int)
        self.report_count = np.zeros(8, dtype=int)

        self.road_area = None
        self.area_mask = None
        self.realtime_congestion = 0
        self.report_congestion = 0
        self.report_congestion_contrib = np.zeros(8, dtype=float)


analytics = Analytics()     # This object will hold all analytics related values


class App:
    def __init__(self, window, window_title, video_source, socketchannel):
        self.window = window
        self.window.title(window_title)
        self.video_source = video_source
        self.channel = socketchannel
        self.starttime = time.time()
        self.beginning = self.starttime
        self.timeelapsed = 0
        self.realtime_framecount = 0
        self.report_framecount = 0

        # open video source (by default this will try to open the computer webcam)
        self.vid = MyVideoCapture(self.video_source)

        # Create a canvas that can fit the above video source size
        self.canvas = tkinter.Canvas(window, width = self.vid.width, height = self.vid.height)
        self.canvas.pack()

        # Button that lets the user take a snapshot
        self.btn_snapshot=tkinter.Button(window, text="Snapshot", width=50, command=self.snapshot)
        self.btn_snapshot.pack(anchor=tkinter.CENTER, expand=True)

        # After it is called once, the update method will be automatically called every delay milliseconds
        self.delay = 1
        self.update()

        self.window.mainloop()

    def snapshot(self):
        # Get a frame from the video source
        ret, frame = self.vid.get_frame()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        if ret:
            cv2.imwrite("frame-" + time.strftime("%d-%m-%Y-%H-%M-%S") + ".jpg", cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

    def update(self):

        ret, frame = self.vid.get_frame()

        if self.realtime_framecount == 0:
            analytics.area_mask = np.copy(frame)
        analytics.vehicle_mask = np.copy(frame)
        analytics.vclass_mask = [np.copy(frame) for i in range(len(vclass_name))]

        if ret:
            results = tfnet.return_predict(frame)

            for result in results:
                label = result['label']
                vclass_index = vclass_name.index(label)
                analytics.realtime_count[vclass_index] += 1
                analytics.report_count[vclass_index] += 1

                tl = (result['topleft']['x'], result['topleft']['y'])
                br = (result['bottomright']['x'], result['bottomright']['y'])
                points = np.array([list(tl), [br[0], tl[1]], list(br), [tl[0], br[1]]])
                # because, fillConvexPoly requires numpy array of points of the bbox polygon
                analytics.vehicle_mask = cv2.fillConvexPoly(analytics.vehicle_mask, points, (255, 255, 255))
                analytics.vclass_mask[vclass_index] = cv2.fillConvexPoly(analytics.vclass_mask[vclass_index], points, (255, 255, 255))

                frame = cv2.rectangle(frame, tl, br, getcolor[vclass_index], 4)
                frame = cv2.putText(frame, label, tl, cv2.FONT_HERSHEY_COMPLEX, 1, getcolor[vclass_index], 2)

            if self.realtime_framecount == 0:
                analytics.area_mask = cv2.fillConvexPoly(analytics.area_mask, np.array(area_pts), (255, 255, 255))
                analytics.area_mask = cv2.cvtColor(analytics.area_mask, cv2.COLOR_BGR2GRAY)
                thret, analytics.area_mask = cv2.threshold(analytics.area_mask, 254, 255, cv2.THRESH_BINARY)
                analytics.road_area = np.round(np.count_nonzero(analytics.area_mask) / analytics.area_mask.size, 3)

            analytics.vehicle_mask = cv2.cvtColor(analytics.vehicle_mask, cv2.COLOR_BGR2GRAY)
            thret, analytics.vehicle_mask = cv2.threshold(analytics.vehicle_mask, 254, 255, cv2.THRESH_BINARY)
            vehicle_congestion = np.round((np.count_nonzero(analytics.vehicle_mask) / analytics.vehicle_mask.size) / analytics.road_area, 3)
            analytics.realtime_congestion += vehicle_congestion
            analytics.report_congestion += vehicle_congestion

            vclass_congestion = []
            for mask in analytics.vclass_mask:
                mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
                mret, mask = cv2.threshold(mask, 254, 255, cv2.THRESH_BINARY)
                vclass_congestion.append(np.round((np.count_nonzero(mask) / mask.size) / analytics.road_area, 3))

            # Sum of all vclass_areas may not be equal to vehicle_area due to overlapping, hence to compute contribution of each
            # vclass_area in vehicle area, we subtract each by the overlapped area / total vclass
            overlap_portion = (sum(vclass_congestion) - vehicle_congestion) / len([each for each in vclass_congestion if each != 0])
            vclass_congestion = [each - overlap_portion if each >= 0 else 0 for each in vclass_congestion]
            for i, congestion in enumerate(vclass_congestion):
                analytics.report_congestion_contrib[i] += congestion / vehicle_congestion

            self.realtime_framecount += 1
            self.report_framecount += 1

            # Two types of analysis scenario: One for real-time viewing corresponding to compute power, another for actual video time interval
            # Real-time analysis
            if time.time() - self.starttime >= 1.0:
                print('Framecount since last bunch: {}'.format(self.realtime_framecount))
                self.timeelapsed = math.floor(float(np.round(time.time() - self.beginning, 1)))
                avg_rtimecount = np.round(analytics.realtime_count / self.realtime_framecount).astype(int)
                avg_rtimecongestion = float(np.round(analytics.realtime_congestion / self.realtime_framecount, 3))
                print('Average realtime congestion in this interval is {}'.format(avg_rtimecongestion))
                print('Sum of average no.of vehicles in this interval is {}'.format(avg_rtimecount))
                numbercount = int(sum(avg_rtimecount))
                congcount = avg_rtimecongestion
                analytics.numbercount.append(numbercount)
                analytics.congcount.append(avg_rtimecongestion)
                analytics.xs.append(self.timeelapsed)
                vclasscount = [int(count) for count in avg_rtimecount]
                # The following code will send data through channels to plot real-time graph

                self.channel.send({
                    'text': json.dumps({
                        'eof': False,
                        'numbercount': numbercount,
                        'congcount': congcount,
                        'vclasscount': vclasscount
                    })
                }, True)

                self.starttime = time.time()
                analytics.realtime_count = np.zeros(8, dtype=int)
                analytics.realtime_congestion = 0
                self.realtime_framecount = 0

            # Analysis for report generation
            if self.report_framecount == self.vid.initial_framerate:
                # now, we can write into the json file
                avg_reportcount = np.round(analytics.report_count / self.report_framecount).astype(int)
                avg_reportcongestion = np.round(analytics.report_congestion / self.report_framecount, 3)
                avg_congestioncontrib = np.round(analytics.report_congestion_contrib / self.report_framecount, 3)
                print('Just appended to json: {} with total vehicles:{}'.format(avg_reportcount.tolist(),
                                                                                sum(avg_reportcount)))
                print('Just appended total congestion in 1sec of video: {}'.format(avg_reportcongestion))
                print('Just appended congestion contrib in 1sec of video as: {}'.format(avg_congestioncontrib.tolist()))
                analytics.count_jsondata.append(avg_reportcount.tolist())
                analytics.congestion_jsondata.append(avg_reportcongestion)
                analytics.contrib_jsondata.append(avg_congestioncontrib.tolist())
                analytics.report_count = np.zeros(8, dtype=int)
                analytics.report_congestion = 0
                analytics.report_congestion_contrib = np.zeros(8, dtype=float)
                self.report_framecount = 0

            timestr = 'Time elapsed: {:.1f} seconds'.format(self.timeelapsed)
            frame = cv2.putText(frame, timestr, (300, 20), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 0), 2)

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Need to convert BGR to RGB for tkinter window
            self.photo = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame))
            self.canvas.create_image(0, 0, image=self.photo, anchor=tkinter.NW)
        else:
            print('Video stream ended possibly')
            self.window.destroy()

        self.window.after(self.delay, self.update)

    def __del__(self):
        print('Main Window is closed')
        self.channel.send({
            'text': json.dumps({
                'eof': True,
            })
        }, True)


class MyVideoCapture:
    def __init__(self, video_source):
        # Open the video source
        self.vid = cv2.VideoCapture(video_source)
        if not self.vid.isOpened():
            raise ValueError("Unable to open video source", video_source)

        # Get video source width and height
        self.width = self.vid.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.height = self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.initial_framerate = math.floor(self.vid.get(5))  # initial frame rate of the video

    def get_frame(self):
        if self.vid.isOpened():
            ret, frame = self.vid.read()
            if ret:
                # Return a boolean success flag and the current frame converted to BGR
                return (ret, frame)
            else:
                return (ret, None)
        else:
            return (None, None)

    # Release the video source when the object is destroyed
    def __del__(self):
        print('Video stream is now closed')
        if self.vid.isOpened():
            self.vid.release()


# Create a window and pass it to the Application object
def runvideo(video, socketchannel):

    global tfnet
    tfnet = TFNet(options)

    global analytics
    analytics = Analytics()

    global area_pts
    if video.lane_dimens:
        area_pts = video.parsedimens()  # To get the polygon vertices for generating the area mask

    App(tkinter.Tk(), "Tkinter and OpenCV",video.video_filename, socketchannel)
    print('Main loop has now ended. Writing into JSON files...')

    # Create or open surveillance report model and store the json files in the specified directory
    try:
        report = video.surveillance_report
        print('Report already exists')
    except: #When report is not created yet, exception is thrown
        print('New Report Created')
        report = SurveillanceReport(video=video)
        report.count_jsonfile = os.path.join(settings.COUNT_JSON_DIR, '{}.json'.format(video.video_name))
        report.congestion_jsonfile = os.path.join(settings.CONGESTION_JSON_DIR, '{}.json'.format(video.video_name))
        report.contribution_jsonfile = os.path.join(settings.CONTRIB_JSON_DIR, '{}.json'.format(video.video_name))
        report.save()

    with open(report.count_jsonfile, 'w') as outfile:
        json.dump(analytics.count_jsondata, outfile)
    with open(report.congestion_jsonfile, 'w') as outfile:
        json.dump(analytics.congestion_jsondata, outfile)
    with open(report.contribution_jsonfile, 'w') as outfile:
        json.dump(analytics.contrib_jsondata, outfile)