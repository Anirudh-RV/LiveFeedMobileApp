'''
SOURCES :
https://www.pyimagesearch.com/2019/09/02/opencv-stream-video-to-web-browser-html-page/

autopep8 -i LstreamoutputTP.py
python3 streamoutput.py

http://192.168.1.8:5000/

Streams live output to port 5000
Implements :
1. TextBox++
2. Tesseract
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
        ret, frame = cap.read()
        print("READING FRAME")
        if frame is not None:
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
            # draw fps
            frame = img1
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
    args["ip"] = "192.168.1.8"
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
