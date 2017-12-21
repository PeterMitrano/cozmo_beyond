import PIL
import numpy as np
import threading
from datetime import datetime
import os
import cv2
import cozmo
import argparse
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from io import BytesIO
from socketserver import ThreadingMixIn

from cozmo.util import distance_mm, degrees, speed_mmps

parser = argparse.ArgumentParser()
parser.add_argument('--dont-save', action="store_true", help="don't write the video file")
parser.add_argument('--square', action="store_true", help="drive in a square instead of sitting still")
args = parser.parse_args()

now = datetime.now()
stamp = now.strftime("%d-%m-%y_%H-%M-%S")
filename = os.path.join("videos", stamp + "_out.avi")
video = cv2.VideoWriter(filename, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'), 15, (320, 240))

pil_img = None

if not args.dont_save:
    print("Writing to", filename)


class CamHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global pil_img
        if self.path.endswith('.mjpg'):
            self.send_response(200)
            self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=--jpgboundary')
            self.end_headers()
            while True:
                try:
                    tmpFile = BytesIO()
                    pil_img.save(tmpFile, 'JPEG')
                    self.wfile.write("--jpgboundary".encode())
                    self.send_header('Content-type', 'image/jpeg')
                    self.send_header('Content-length', str(tmpFile.getbuffer().nbytes))
                    self.end_headers()
                    pil_img.save(self.wfile, 'JPEG')
                    time.sleep(0.05)
                except KeyboardInterrupt:
                    break
            return
        if self.path.endswith('.html'):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write('<html><head></head><body>'.encode())
            self.wfile.write('<img src="http://127.0.0.1:8087/cam.mjpg"/>'.encode())
            self.wfile.write('</body></html>'.encode())
            return


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""


def new_image_handler(evt, obj=None, tap_cout=None, **kwargs):
    # print(evt.image.image_recv_time)
    global pil_img
    pil_img = evt.image.raw_image
    if not args.dont_save:
        video.write(cv2.cvtColor(np.array(evt.image.raw_image), cv2.COLOR_RGB2BGR))


def camera_server():
    try:
        server = ThreadedHTTPServer(('localhost', 8087), CamHandler)
        print("server started")
        server.serve_forever()
    except KeyboardInterrupt:
        server.socket.close()


def program(robot: cozmo.robot.Robot):
    robot.camera.image_stream_enabled = True
    robot.world.add_event_handler(cozmo.world.EvtNewCameraImage, new_image_handler)

    thread = threading.Thread(target=camera_server)
    thread.start()

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

    thread.join()


cozmo.robot.Robot.drive_off_charger_on_connect = False
cozmo.run_program(program)
