import os
import cv2
import time
from threading import Timer

from camera import VideoStream
from file_output import FileOutput
from publish import Publisher
from inference import Infer

IOT_TOPIC = 'custom_object_detection/inference'
IOT_TOPIC_ADMIN = 'custom_object_detection/admin'

def get_parameter(name, default):
    if name in os.environ and os.environ[name] != "":
        return os.environ[name]
    return default

THING_NAME = get_parameter('THING_NAME', "Unknown")

PUB = Publisher(IOT_TOPIC_ADMIN, IOT_TOPIC, THING_NAME)

PUB.info("Loading new Thread")
PUB.info('OpenCV '+cv2.__version__)

def lambda_handler(event, context):
    return

try:
    VS = VideoStream().start()
except Exception as err:
    PUB.exception(str(err))
PUB.info('Camera is ' + VS.device)

OUTPUT = FileOutput('/tmp/results.mjpeg', VS.read(), PUB)
OUTPUT.start()

model = Infer()
def main_loop():
    try:
        last_update = time.time()
        results = []
        fps = 0
        while 42 :
            frame = VS.read()
            frame = cv2.resize(frame, (model.data_shape, model.data_shape))
            try:
                category = model.do(frame)
                results.append(category)
                font = cv2.FONT_HERSHEY_DUPLEX
                title = str(fps) + " - " + category
                cv2.putText(frame, title, (6, 24), font, 0.5, (255, 255, 255), 1)

            except Exception as err:
                PUB.exception(str(err))
                raise err
            
            now = time.time()
            if now - last_update >= 1:
                last_update = time.time()
                PUB.events(results)
                fps = len(results)
                results = []
            OUTPUT.update(frame)

    except Exception as err:
        PUB.exception(str(err))

    Timer(0, main_loop).start()

# OUTPUT.stop()
# VS.stop()

main_loop()
