import numpy as np
from datetime import datetime
import os
import cv2
import cozmo
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--dont-save', action="store_true")
args = parser.parse_args()

now = datetime.now()
stamp = now.strftime("%d-%m-%y_%H-%M-%S")
filename = os.path.join("videos", stamp + "_out.avi")
video = cv2.VideoWriter(filename, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'), 15, (320, 240))

if not args.dont_save:
    print("Writing to", filename)


def raw_image_handler(evt, obj=None, tap_cout=None, **kwargs):
    t = evt.image.image_recv_time
    print(t)
    if not args.dont_save:
        video.write(cv2.cvtColor(np.array(evt.image.raw_image), cv2.COLOR_RGB2BGR))


def new_image_handler(evt, obj=None, tap_cout=None, **kwargs):
    t = evt.image.image_recv_time
    print(t)
    if not args.dont_save:
        video.write(cv2.cvtColor(np.array(evt.image.raw_image), cv2.COLOR_RGB2BGR))


def program(robot: cozmo.robot.Robot):
    robot.camera.image_stream_enabled = True
    robot.world.add_event_handler(cozmo.world.EvtNewCameraImage, new_image_handler)

    input("press q to exit")


cozmo.robot.Robot.drive_off_charger_on_connect = False
cozmo.run_program(program)
