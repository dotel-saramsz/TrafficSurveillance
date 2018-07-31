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
vclass_name = ['Tempo','Bike','Car','Taxi','Micro','Pickup','Bus','Truck']

# setting the boundary box colors for the vehicle classes
getcolor = [] ##############
for i in range(0, len(vclass_name)):
    hue = 255 * i / len(vclass_name)
    col = np.zeros((1, 1, 3)).astype('uint8')
    col[0][0][0] = hue
    col[0][0][1] = 128
    col[0][0][2] = 255
    cvcol = cv2.cvtColor(col, cv2.COLOR_HSV2BGR)
    col = (int(cvcol[0][0][0]), int(cvcol[0][0][1]), int(cvcol[0][0][2]))
    getcolor.append(col)

# area_pts = [[0,719],[0,352],[478,0],[936,0],[1073,250],[1279,495],[1279,719]]   # This is the default area mask. In actual scenario, change according to videoid
analysed_percentage = 0
totalframes = 0

class Analytics:
    def __init__(self):
        self.total_vcount = np.zeros(8, dtype=int)  # Total vehicles count
        self.count_jsondata = []    # For storing in json ...below 2 as well
        self.congestion_jsondata = []
        self.contrib_jsondata = []

        self.numbercount = []
        self.congcount = []
        self.xs = []
        self.class_count_list = np.zeros(8, dtype=int)

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
        self.progress_framecount = 0
        self.overall_framecount = 0
        self.count = 0
        self.prev_points = np.array([])
        self.old_frame = None
        self.outgoing_changed = False

        # open video source (by default this will try to open the computer webcam)
        self.vid = MyVideoCapture(self.video_source.video_filename)

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

    def track(self, frame):
        lk_params = dict(winSize=(15, 15),
                         maxLevel=3,
                         criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))
        # gray frames need to be passed?
        tracked, st, err = cv2.calcOpticalFlowPyrLK(self.old_frame, frame, np.array(self.prev_points, dtype=np.float32), None, **lk_params)
        return tracked

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
                confidence = result['confidence']
                vclass_index = vclass_name.index(label)
                analytics.realtime_count[vclass_index] += 1
                analytics.report_count[vclass_index] += 1

                tl = (result['topleft']['x'], result['topleft']['y'])
                br = (result['bottomright']['x'], result['bottomright']['y'])

                x_center = (tl[0] + (br[0] - tl[0]) / 2)
                y_center = (tl[1] + (br[1] - tl[1]) / 2)

                points = np.array([list(tl), [br[0], tl[1]], list(br), [tl[0], br[1]]])
                # because, fillConvexPoly requires numpy array of points of the bbox polygon
                analytics.vehicle_mask = cv2.fillConvexPoly(analytics.vehicle_mask, points, (255, 255, 255))
                analytics.vclass_mask[vclass_index] = cv2.fillConvexPoly(analytics.vclass_mask[vclass_index], points, (255, 255, 255))

                if self.overall_framecount == 0:
                    BB_center = np.array([[x_center, y_center]])
                    self.prev_points = np.append(self.prev_points, BB_center).reshape(-1, 1, 2)
                    analytics.class_count_list[vclass_index] += 1
                    self.outgoing_changed = True
                else:
                    if y_center >= 200 and y_center < 400:

                        # making some criteria for the new center to be tracked     WHY DIFFERENT THRESHOLDS?
                        if label == 'Bus' or label == 'Truck':
                            xthresh, ythresh = 150, 150
                        else:
                            xthresh, ythresh = 80, 80

                        add_center = True

                        for new_center in self.prev_points:
                            x, y = new_center[0].ravel()
                            if abs(x - x_center) < xthresh and abs(y - y_center) < ythresh:
                                add_center = False
                                break

                        if add_center is True:
                            # This is the point where we have found a new incoming vehicle
                            BB_center = np.array([[x_center, y_center]])
                            self.prev_points = np.append(self.prev_points, BB_center).reshape(-1, 1, 2)
                            analytics.class_count_list[vclass_index] += 1
                            self.outgoing_changed = True


                frame = cv2.rectangle(frame, tl, br, getcolor[vclass_index], 2)
                boxtitle = label + " " + ('%.2f' %confidence)
                cv2.rectangle(frame, (tl[0], tl[1] - 15), (tl[0] + 100, tl[1] + 5), getcolor[vclass_index], -1)
                cv2.putText(frame, boxtitle, tl, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)


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

            if self.overall_framecount is not 0:
                if len(self.prev_points) is not 0:
                    tracked_points = self.track(frame)
                    self.prev_points = np.array([])
                    for points in tracked_points:
                        x, y = points[0].ravel()
                        if y < 600:
                            self.prev_points = np.append(self.prev_points, np.array([[x, y]])).reshape(-1, 1, 2)

            #update frame
            self.old_frame = frame

            vclass_congestion = []
            for mask in analytics.vclass_mask:
                mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
                mret, mask = cv2.threshold(mask, 254, 255, cv2.THRESH_BINARY)
                vclass_congestion.append(np.round((np.count_nonzero(mask) / mask.size) / analytics.road_area, 3))

            # Sum of all vclass_areas may not be equal to vehicle_area due to overlapping, hence to compute contribution of each
            # vclass_area in vehicle area, we subtract each by the overlapped area / total vclass

            if vehicle_congestion != 0: #Check if road is empty or not!
                overlap_portion = (sum(vclass_congestion) - vehicle_congestion) / len([each for each in vclass_congestion if each != 0])
                vclass_congestion = [each - overlap_portion if each >= 0 else 0 for each in vclass_congestion]
                for i, congestion in enumerate(vclass_congestion):
                    analytics.report_congestion_contrib[i] += congestion / vehicle_congestion
            else:   #Road is empty if this happens, so we avoid the 0/0 error case
                for i in range(len(vclass_congestion)):
                    analytics.report_congestion_contrib[i] += 0

            self.realtime_framecount += 1
            self.report_framecount += 1
            self.progress_framecount += 1


            # Two types of analysis scenario: One for real-time viewing corresponding to compute power, another for actual video time interval
            # Real-time analysis
            if time.time() - self.starttime >= 1.0:
                self.timeelapsed = math.floor(float(np.round(time.time() - self.beginning, 1)))
                avg_rtimecount = np.round(analytics.realtime_count / self.realtime_framecount).astype(int)
                avg_rtimecongestion = float(np.round(analytics.realtime_congestion / self.realtime_framecount, 3))
                numbercount = int(sum(avg_rtimecount))
                congcount = avg_rtimecongestion
                analytics.numbercount.append(numbercount)
                analytics.congcount.append(avg_rtimecongestion)
                analytics.xs.append(self.timeelapsed)
                vclasscount = [int(count) for count in avg_rtimecount]
                # The following code will send data through channels to plot real-time graph
                self.channel.send({
                    'text': json.dumps({
                        'type': 'normal',
                        'numbercount': numbercount,
                        'congcount': congcount,
                        'vclasscount': vclasscount
                    })
                }, True)

                self.starttime = time.time()
                analytics.realtime_count = np.zeros(8, dtype=int)
                analytics.realtime_congestion = 0
                self.realtime_framecount = 0

            # Analysis for report generation; this corresponds to 1 second on the actual video
            if self.report_framecount == self.vid.initial_framerate:
                global mainvideo_timeelapsed

                # now, we can write into the json file
                avg_reportcount = np.round(analytics.report_count / self.report_framecount).astype(int)
                avg_reportcongestion = np.round(analytics.report_congestion / self.report_framecount, 3)
                avg_congestioncontrib = np.round(analytics.report_congestion_contrib / self.report_framecount, 3)
                analytics.count_jsondata.append(avg_reportcount.tolist())
                analytics.congestion_jsondata.append(avg_reportcongestion)
                analytics.contrib_jsondata.append(avg_congestioncontrib.tolist())
                analytics.report_count = np.zeros(8, dtype=int)
                analytics.report_congestion = 0
                analytics.report_congestion_contrib = np.zeros(8, dtype=float)

                self.report_framecount = 0

            # frame changes
            self.overall_framecount += 1

            cv2.line(frame, (0, 200), (self.vid.width, 200), (0, 255, 0), 1)
            cv2.line(frame, (0, 400), (self.vid.width, 400), (0, 255, 0), 1)
            timestr = 'Time elapsed: {:.1f}s'.format(self.timeelapsed)
            cv2.rectangle(frame, (0, 0), (170, 200), (255, 255, 255), -1)
            text_vloc = 15
            for vcount, vclass in zip(analytics.class_count_list, vclass_name):
                cv2.putText(frame, '{0:14}:{1}'.format(vclass, vcount), (5, text_vloc), cv2.FONT_HERSHEY_SIMPLEX,
                            0.5, (0, 0, 0), 1)
                text_vloc += 20

            cv2.putText(frame, timestr, (5, text_vloc + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Need to convert BGR to RGB for tkinter window
            self.photo = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame))
            self.canvas.create_image(0, 0, image=self.photo, anchor=tkinter.NW)
        else:
            print('Video stream ended possibly')
            self.window.destroy()

        global analysed_percentage
        analysed_percentage = int(self.progress_framecount/totalframes*100)

        # The following code will send data through channels to update the outgoing count box and progress bar
        outgoing_count_list = [int(eachcount) for eachcount in analytics.class_count_list]
        outgoing_count_dict = dict(zip(vclass_name,outgoing_count_list))
        self.channel.send({
            'text': json.dumps({
                'type': 'progress',
                'percentage': analysed_percentage,
                'outgoing_changed': self.outgoing_changed,
                'outgoing_count': outgoing_count_dict
            })
        }, True)
        self.outgoing_changed = False

        self.window.after(self.delay, self.update)

    def __del__(self):
        print('Main Window is closed')


class MyVideoCapture:
    def __init__(self, video_source):
        # Open the video source
        self.vid = cv2.VideoCapture(video_source)
        if not self.vid.isOpened():
            raise ValueError("Unable to open video source", video_source)

        # Get video source width and height
        self.width = int(self.vid.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT))

        self.initial_framerate = math.floor(self.vid.get(5))  # initial frame rate of the video
        global totalframes
        totalframes = self.vid.get(cv2.CAP_PROP_FRAME_COUNT)

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

    global analysed_percentage
    analysed_percentage = 0

    global area_pts
    if video.lane_dimens:
        area_pts = video.parsedimens()  # To get the polygon vertices for generating the area mask

    App(tkinter.Tk(), "Tkinter and OpenCV",video, socketchannel)
    print('Main loop has now ended. Writing into JSON files...')
    socketchannel.send({
        'text': json.dumps({
            'type': 'eof',
        })
    }, True)

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

    report.outgoing_tempo_count = int(analytics.class_count_list[0])
    report.outgoing_bike_count = int(analytics.class_count_list[1])
    report.outgoing_car_count = int(analytics.class_count_list[2])
    report.outgoing_taxi_count = int(analytics.class_count_list[3])
    report.outgoing_micro_count = int(analytics.class_count_list[4])
    report.outgoing_pickup_count = int(analytics.class_count_list[5])
    report.outgoing_bus_count = int(analytics.class_count_list[6])
    report.outgoing_truck_count = int(analytics.class_count_list[7])
    report.outgoing_vehicle_count = int(sum(analytics.class_count_list))

    report.avg_congestion_index = float(sum(analytics.congestion_jsondata)/len(analytics.congestion_jsondata))
    report.avg_count_index = float(sum([sum(vclasscount) for vclasscount in analytics.count_jsondata])/len(analytics.count_jsondata))

    report.save()

    with open(report.count_jsonfile, 'w') as outfile:
        json.dump(analytics.count_jsondata, outfile)
    with open(report.congestion_jsonfile, 'w') as outfile:
        json.dump(analytics.congestion_jsondata, outfile)
    with open(report.contribution_jsonfile, 'w') as outfile:
        json.dump(analytics.contrib_jsondata, outfile)

    video.analysed_percentage = analysed_percentage
    video.report = True
    video.save()