import sys
import cozmo
from cozmo.util import degrees
import asyncio
import numpy
import cv2
from PIL import ImageColor

import BlinkPipeline

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
        self.pipeline = BlinkPipeline.Pipeline()

    def new_image_handler(self, evt, obj=None, tap_count=None, **kwargs):
        if self.has_roi:
            bounds = (self.eye_region_of_interest[0].x, self.eye_region_of_interest[0].y,
                      self.eye_region_of_interest[1].x, self.eye_region_of_interest[1].y)
            roi = numpy.array(evt.image.crop(bounds), dtype=numpy.float32)

            # grip!!!!
            self.pipeline.set_source0(roi)
            self.pipeline.process()
            print(self.pipeline.cv_adaptivethreshold_output)

    @cozmo.event.filter_handler(cozmo.faces.EvtFaceObserved)
    def observed_face_handler(self, evt, obj=None, tap_count=None, **kwargs):
        # when we get a new face detection, save the area around the eyes
        eye_padding = 20

        # totally guessed this, idk what/why it is
        scale = 2.15

        if len(evt.face.left_eye) > 2 and len(evt.face.right_eye) > 2:
            roi_x1 = round(max(evt.face.left_eye[0].x - eye_padding, 0) * scale)
            roi_y1 = round(max(evt.face.left_eye[0].y - eye_padding, 0) * scale)
            roi_x2 = round(min(evt.face.right_eye[2].x + eye_padding, 320) * scale)
            roit_y2 = round(min(evt.face.right_eye[2].y + eye_padding, 240) * scale)
            self.eye_region_of_interest = [Pt(roi_x1, roi_y1), Pt(roi_x2, roit_y2)]
            self.has_roi = True

    async def run(self, sdk_conn: cozmo.conn.CozmoConnection):
        robot = await sdk_conn.wait_for_robot()

        await robot.set_head_angle(degrees(40)).wait_for_completed()
        await asyncio.sleep(1)

        robot.world.image_annotator.annotation_enabled = True
        robot.add_event_handler(cozmo.faces.EvtFaceObserved, self.observed_face_handler)
        robot.camera.image_stream_enabled = True
        robot.camera.add_event_handler(cozmo.robot.camera.EvtNewRawCameraImage, self.new_image_handler)
        robot.world.image_annotator.add_annotator('roi', self)

        # infinite loop that doesn't hog CPU
        while True:
            await asyncio.sleep(0.1)

    def apply(self, image, scale):
        blue = ImageColor.getrgb("#f00")
        roi = [Pt(self.eye_region_of_interest[0].x, self.eye_region_of_interest[0].y),
            Pt(self.eye_region_of_interest[1].x, self.eye_region_of_interest[0].y),
            Pt(self.eye_region_of_interest[1].x, self.eye_region_of_interest[1].y),
        Pt(self.eye_region_of_interest[0].x, self.eye_region_of_interest[1].y)]
        cozmo.annotate.add_polygon_to_image(image, roi, 1, blue)


if __name__ == "__main__":
    cozmo.setup_basic_logging()

    try:
        sc = StaringContest()
        cozmo.connect_with_tkviewer(sc.run)
    except cozmo.ConnectionError as e:
        sys.exit("Connection error: %s" % e)
