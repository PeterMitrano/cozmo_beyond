import numpy as np
from datetime import datetime
import os
import cv2
import cozmo
import argparse

from cozmo.util import distance_mm, degrees, speed_mmps

parser = argparse.ArgumentParser()
parser.add_argument('--dont-save', action="store_true", help="don't write the video file")
parser.add_argument('--square', action="store_true", help="drive in a square instead of sitting still")
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

    if args.square:
        lift_up = robot.set_lift_height(1)
        lift_up.wait_for_completed()
        head_down = robot.set_head_angle(cozmo.robot.MIN_HEAD_ANGLE)
        head_down.wait_for_completed()

        for _ in range(4):
            robot.drive_straight(distance_mm(150), speed_mmps(50)).wait_for_completed()
            robot.turn_in_place(degrees(90)).wait_for_completed()
    else:
        input("press q to exit")


cozmo.robot.Robot.drive_off_charger_on_connect = False
cozmo.run_program(program)
