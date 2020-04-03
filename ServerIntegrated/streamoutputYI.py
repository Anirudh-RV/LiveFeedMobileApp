'''
SOURCES :
https://www.pyimagesearch.com/2019/09/02/opencv-stream-video-to-web-browser-html-page/

python3 streamoutput.py -i 0.0.0.0 -o 5000 -f 15

autopep8 -i streamoutput.py

TODO :
1. Add textbox++
2. Test is the output is accurate

'''
# USAGE
# python webstreaming.py --ip 0.0.0.0 --port 8000
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
url = 'http://192.168.1.6:8080/'
cap = cv2.VideoCapture(url)

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
#vs = VideoStream(usePiCamera=1).start()
vid_file = "twoPeopleWalking.mp4"
vid_name = "twoPeopleWalking"

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
            currentCoordinates = ""
            # yolo
            resultyolo = tfnet.return_predict(frame)
            # textbox++
            img = frame
            img_h = img.shape[0]
            img_w = img.shape[1]
            img1 = np.copy(img)
            coordinates = previousCoordinates.split("\n")
            coordinates.pop()
            # print(coordinates)
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
                        #print("comparing now : "+str(bb2))
                        for currentIndex, boxes in enumerate(coordinates):
                            boxesarr = boxes.split(" ")
                            top = ast.literal_eval(boxesarr[0])
                            bottom = ast.literal_eval(boxesarr[1])
                            bb1 = {}
                            bb1['x1'] = top[0]
                            bb1['x2'] = bottom[0]
                            bb1['y1'] = top[1]
                            bb1['y2'] = bottom[1]
                            #print("with bb1 : "+str(bb1))
                            result = get_iou(bb1, bb2)
                            #print("result : "+str(result))
                            temp = currentIou
                            currentIou = max(result, currentIou)
                            if temp != currentIou:
                                iouIndex = currentIndex

                        #print("Current coordinate : "+str(bb2))
                        #print("MAX IoU : "+str(currentIou))
                        #print("Max IoU Index :"+str(iouIndex))
                        #print("Previous coordinate : "+str(coordinates[iouIndex]))
                        if currentIou != 0:
                            #print("transfering index :"+str(peoplemapping[coordinates[iouIndex]]))
                            peoplemapping[currentValue] = peoplemapping[coordinates[iouIndex]]
                        # check for index:
                        try:
                            if peoplemapping[currentValue]:
                                pass
                                #print("person taken into account : "+str(peoplemapping[currentValue]))
                        except:
                            peopleindex = peopleindex + 1
                            peoplemapping[currentValue] = peopleindex
                            #print("person accounted: "+str(peoplemapping[currentValue]))
                    else:
                        #print("adding people here : ")
                        try:
                            if peoplemapping[currentValue]:
                                #print("person taken into account : "+str(peoplemapping[currentValue]))
                                pass
                        except:
                            peopleindex = peopleindex + 1
                            peoplemapping[currentValue] = peopleindex
                            #print("person coordinate : "+str(currentValue))
                            #print("person accounted: "+str(peoplemapping[currentValue]))

                    # IOU PART - END
                    strPeopleMapping = strPeopleMapping+currentValue+":"+str(peoplemapping[currentValue])+"|"
                    cv2.rectangle(img1,(coordinatesStr['x1'],coordinatesStr['y1']),(coordinatesStr['x2'],coordinatesStr['y2']), (255,0,0) , 2)
                    cv2.putText(img1,"index : "+str(peoplemapping[currentValue]),(coordinatesStr['x1'],coordinatesStr['y1']),cv2.FONT_HERSHEY_DUPLEX,1.0,(0,0,255))
                    frame = img1

        #print("previousCoordinates : "+previousCoordinates)
        #print("currentcoordinates : "+currentCoordinates)
        #print("People Count : "+str(peopleCount))
        #print("peoplemapping: "+str(peoplemapping))
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
