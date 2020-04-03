'''
SOURCES :
https://www.pyimagesearch.com/2019/09/02/opencv-stream-video-to-web-browser-html-page/

autopep8 -i streamoutput.py
python3 streamoutput.py

Streams live output to port 5000
Implements :
1. Yolo with Indexing
2. TextBox++
3. Tesseract
'''

# import the necessary packages
from imutils.video import VideoStream
from flask import Response
from flask import Flask
from flask import render_template
import threading
import argparse
import datetime
import imutils
import time
import cv2

# To make sure stream is being read before initialising ML MODEL
url = 'http://192.168.1.6:8080/'
cap = cv2.VideoCapture(url)

import os
import time
import requests
import PIL
from PIL import Image
from io import BytesIO
import tensorflow as tf
import numpy as np
import cv2
from timeit import default_timer as timer
from tbpp_model import TBPP512, TBPP512_dense
from tbpp_utils import PriorUtil
from ssd_data import preprocess
from sl_utils import rbox3_to_polygon, polygon_to_rbox, rbox_to_polygon

# To import PyTesseract
import pytesseract

# Place ML MODEL initializers
Model = TBPP512_dense
input_shape = (512,512,3)
weights_path = 'weights.022.h5'
confidence_threshold = 0.35
confidence_threshold = 0.25
sl_graph = tf.Graph()
with sl_graph.as_default():
    sl_session = tf.Session()
    with sl_session.as_default():
        sl_model = Model(input_shape)
        prior_util = PriorUtil(sl_model)
        sl_model.load_weights(weights_path, by_name=True)
    input_width = 256
    input_height = 32
    weights_path = 'weights.022.h5'

input_size = input_shape[:2]

from darkflow.net.build import TFNet
import numpy as np

yolo9000 = {"model" : "cfg/yolo9000.cfg", "load" : "yolo9000.weights", "threshold": 0.01}
tfnet = TFNet(yolo9000)


# initialize the output frame and a lock used to ensure thread-safe
# exchanges of the output frames (useful for multiple browsers/tabs
# are viewing tthe stream)
outputFrame = None
lock = threading.Lock()

# initialize a flask object
app = Flask(__name__)

# initialize the video stream and allow the camera sensor to
# warmup
vs = cap
time.sleep(2.0)

@app.route("/")
def index():
    # return the rendered template
    return render_template("index.html")

def detect_motion(frameCount):
    # lock variables
    global vs, outputFrame, lock

    # loop over frames from the video stream and edit anything here...
    while True:
        # read the next frame from the video stream, resize it,
        # convert the frame to grayscale, and blur it
        previousCoordinates = ""
        peopleindex = 0
        peoplemapping = {}
        strPeopleMapping = ""
        ret, frame = cap.read()
        print("READING FRAME")
        if frame is not None:
            # yolo
            resultyolo = tfnet.return_predict(frame)
            # model to predict
            img = np.array(frame)
            img_h = img.shape[0]
            img_w = img.shape[1]
            img1 = np.copy(img)
            img2 = np.zeros_like(img)
            # model to predict
            x = np.array([preprocess(img, input_size)])
            #Model start
            start_time = time.time()
            with sl_graph.as_default():
                with sl_session.as_default():
                    y = sl_model.predict(x)
            #Model end
            result = prior_util.decode(y[0], confidence_threshold)
            if len(result) > 0:
                bboxs = result[:,0:4]
                quads = result[:,4:12]
                rboxes = result[:,12:17]
                boxes = np.asarray([rbox3_to_polygon(r) for r in rboxes])
                xy = boxes
                xy = xy * [img_w, img_h]
                xy = np.round(xy)
                xy = xy.astype(np.int32)
                cv2.polylines(img1, tuple(xy), True, (0,0,255))
                rboxes = np.array([polygon_to_rbox(b) for b in np.reshape(boxes, (-1,4,2))])
                bh = rboxes[:,3]
                rboxes[:,2] += bh * 0.1
                rboxes[:,3] += bh * 0.2
                boxes = np.array([rbox_to_polygon(f) for f in rboxes])
                boxes = np.flip(boxes, axis=1) # TODO: fix order of points, why?
                boxes = np.reshape(boxes, (-1, 8))
                boxes_mask_a = np.array([b[2] > b[3] for b in rboxes]) # width > height, in square world
                boxes_mask_b = np.array([not (np.any(b < 0) or np.any(b > 512)) for b in boxes]) # box inside image
                boxes_mask = np.logical_and(boxes_mask_a, boxes_mask_b)
                boxes = boxes[boxes_mask]
                rboxes = rboxes[boxes_mask]
                xy = xy[boxes_mask]

                if len(boxes) == 0:
                    boxes = np.empty((0,8))

            top = 10
            bottom = 10
            left = 10
            right = 10
            total_transcript = ""

            # To get the cropped out boxes and run pytesseract over it
            for i in xy:
                crop_img = img1[i[0][1]-5:i[2][1]+5,i[0][0]-5:i[2][0]+5]
                color = [255,255,255]
                crop_img = cv2.copyMakeBorder(crop_img, top, bottom, left, right, cv2.BORDER_CONSTANT,value=color)
                transcript = pytesseract.image_to_string(crop_img, lang='eng').upper()
                total_transcript += transcript + "\n"
                print(transcript)

            print(total_transcript)
            # draw fps
            frame = img1

            # Start yolo process here
            currentCoordinates = ""

            # textbox++
            img = frame
            img_h = img.shape[0]
            img_w = img.shape[1]
            img1 = np.copy(img)
            coordinates = previousCoordinates.split("\n")
            coordinates.pop()
            # YOLO-9000 : Drawing Boxes
            peopleCount = 0
            for res in resultyolo:
                if res["label"] == "whole":
                    continue
                elif res["label"] != "person":
                    color = int(255 * res["confidence"])
                    top = (res["topleft"]["x"], res["topleft"]["y"])
                    bottom = (res["bottomright"]["x"], res["bottomright"]["y"])
                    # for each person
                    cv2.rectangle(frame, top, bottom, (255,0,0) , 2)
                    cv2.putText(frame, res["label"], top, cv2.FONT_HERSHEY_DUPLEX, 1.0, (0,0,255))

                elif res["label"] == "person":
                    peopleCount = peopleCount + 1
                    color = int(255 * res["confidence"])
                    top = (res["topleft"]["x"], res["topleft"]["y"])
                    bottom = (res["bottomright"]["x"], res["bottomright"]["y"])
                    topstr = "("+str(res["topleft"]["x"]) + \
                        ","+str(res["topleft"]["y"])+")"
                    bottomstr = "("+str(res["bottomright"]["x"]) + \
                        ","+str(res["bottomright"]["y"])+")"
                    coordinatesStr = {}
                    coordinatesStr['x1'] = top[0]
                    coordinatesStr['x2'] = bottom[0]
                    coordinatesStr['y1'] = top[1]
                    coordinatesStr['y2'] = bottom[1]
                    currentValue = topstr+" "+bottomstr
                    # IOU PART - BEGIN
                    currentCoordinates = currentCoordinates+topstr+" "+bottomstr+"\n"

                    # Calculate IoU here with top and bottom, compare each drawn image with top and bottom, select the max IoU
                    if previousCoordinates != "":
                        bb2 = {}
                        bb2['x1'] = top[0]
                        bb2['x2'] = bottom[0]
                        bb2['y1'] = top[1]
                        bb2['y2'] = bottom[1]

                        currentIou = 0
                        iouIndex = 0
                        for currentIndex, boxes in enumerate(coordinates):
                            boxesarr = boxes.split(" ")
                            top = ast.literal_eval(boxesarr[0])
                            bottom = ast.literal_eval(boxesarr[1])
                            bb1 = {}
                            bb1['x1'] = top[0]
                            bb1['x2'] = bottom[0]
                            bb1['y1'] = top[1]
                            bb1['y2'] = bottom[1]
                            result = get_iou(bb1, bb2)
                            temp = currentIou
                            currentIou = max(result, currentIou)
                            if temp != currentIou:
                                iouIndex = currentIndex
                        if currentIou != 0:
                            peoplemapping[currentValue] = peoplemapping[coordinates[iouIndex]]
                        # check for index:
                        try:
                            if peoplemapping[currentValue]:
                                pass
                        except:
                            peopleindex = peopleindex + 1
                            peoplemapping[currentValue] = peopleindex
                    else:
                        try:
                            if peoplemapping[currentValue]:
                                pass
                        except:
                            peopleindex = peopleindex + 1
                            peoplemapping[currentValue] = peopleindex

                    # IOU PART - END
                    strPeopleMapping = strPeopleMapping+currentValue+":"+str(peoplemapping[currentValue])+"|"
                    cv2.rectangle(img1,(coordinatesStr['x1'],coordinatesStr['y1']),(coordinatesStr['x2'],coordinatesStr['y2']), (255,0,0) , 2)
                    cv2.putText(img1,"index : "+str(peoplemapping[currentValue]),(coordinatesStr['x1'],coordinatesStr['y1']),cv2.FONT_HERSHEY_DUPLEX,1.0,(0,0,255))
                    frame = img1

        previousCoordinates = currentCoordinates
        strPeopleMapping = strPeopleMapping+"\n"
        # acquire the lock, set the output frame, and release the
        # lock
        with lock:
            outputFrame = frame.copy()

def generate():
    # grab global references to the output frame and lock variables
    global outputFrame, lock

    # loop over frames from the output stream
    while True:
        # wait until the lock is acquired
        with lock:
            # check if the output frame is available, otherwise skip
            # the iteration of the loop
            if outputFrame is None:
                continue
            # encode the frame in JPEG format
            (flag, encodedImage) = cv2.imencode(".jpg", outputFrame)
            # ensure the frame was successfully encoded
            if not flag:
                continue
        # yield the output frame in the byte format
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
              bytearray(encodedImage) + b'\r\n')

@app.route("/video_feed")
def video_feed():
    # return the response generated along with the specific media
    # type (mime type)
    return Response(generate(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

# check to see if this is the main thread of execution
if __name__ == '__main__':
    args = {}
    args["ip"] = "0.0.0.0"
    args["port"] = "5000"
    args["frame_count"] = 15
    # start a thread that will perform motion detection
    t = threading.Thread(target=detect_motion, args=(
        args["frame_count"],))
    t.daemon = True
    t.start()
    # start the flask app
    app.run(host=args["ip"], port=args["port"], debug=True,
            threaded=True, use_reloader=False)
# release the video stream pointer
vs.stop()
