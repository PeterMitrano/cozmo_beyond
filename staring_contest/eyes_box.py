#!/usr/bin/python3

import sys
import cozmo
from cozmo.util import degrees
import asyncio
from PIL import ImageColor, Image


class Pt():
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __round__(self):
        self.x = round(self.x)
        self.y = round(self.y)

    def __repr__(self):
        return "%i, %i" % (self.x, self.y)


class StaringContest(cozmo.annotate.Annotator):

    def __init__(self):
        self.eye_region_of_interest = [Pt(0, 0), Pt(320, 240)]
        self.enabled = True
        self.has_roi = False

    @cozmo.event.filter_handler(cozmo.faces.EvtFaceObserved)
    def observed_face_handler(self, evt, obj=None, tap_count=None, **kwargs):
        # when we get a new face detection, save the area around the eyes
        eye_padding = 20

        if len(evt.face.left_eye) > 2 and len(evt.face.right_eye) > 2:
            roi_x1 = round(max(evt.face.left_eye[0].x - eye_padding, 0))
            roi_y1 = round(max(evt.face.left_eye[0].y - eye_padding, 0))
            roi_x2 = round(min(evt.face.right_eye[2].x + eye_padding, 320))
            roit_y2 = round(min(evt.face.right_eye[2].y + eye_padding, 240))
            self.eye_region_of_interest = [Pt(roi_x1, roi_y1), Pt(roi_x2, roit_y2)]
            self.has_roi = True

    async def run(self, sdk_conn: cozmo.conn.CozmoConnection):
        robot = await sdk_conn.wait_for_robot()

        print("BATTERY LEVEL: %f" % robot.battery_voltage)
        if robot.battery_voltage < 3.5:
            while True:
                print("BATTERY LEVEL: %f" % robot.battery_voltage)

        robot.move_lift(-1)
        await asyncio.sleep(1)
        await robot.set_head_angle(degrees(40)).wait_for_completed()

        robot.world.image_annotator.annotation_enabled = True

        robot.add_event_handler(cozmo.faces.EvtFaceObserved, self.observed_face_handler)

        robot.camera.image_stream_enabled = True
        robot.world.image_annotator.add_annotator('roi', self)

        # infinite loop that doesn't hog CPU
        while True:
            await asyncio.sleep(1)

    def apply(self, image, scale):
        blue = ImageColor.getrgb("#f00")
        print(scale)
        #scale = scale/0.625
        roi = [Pt(scale * self.eye_region_of_interest[0].x, scale * self.eye_region_of_interest[0].y),
            Pt(scale * self.eye_region_of_interest[1].x, scale * self.eye_region_of_interest[0].y),
            Pt(scale * self.eye_region_of_interest[1].x, scale * self.eye_region_of_interest[1].y),
            Pt(scale * self.eye_region_of_interest[0].x, scale * self.eye_region_of_interest[1].y)]
        cozmo.annotate.add_polygon_to_image(image, roi, 1, blue)


if __name__ == "__main__":
    cozmo.setup_basic_logging()
    cozmo.robot.Robot.drive_off_charger_on_connect = False

    try:
        sc = StaringContest()
        # cozmo.connect(sc.run)
        cozmo.connect_with_tkviewer(sc.run)
    except cozmo.ConnectionError as e:
        sys.exit("Connection error: %s" % e)
