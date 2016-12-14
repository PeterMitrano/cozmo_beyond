import queue
import sys
import cozmo
from cozmo.util import degrees
import asyncio
import numpy
import cv2
from PIL import ImageColor
from GripWrapper import GripWrapper


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
        self.blob_history = []
        self.enabled = True
        self.eye_padding = 10
        self.has_roi = False
        self.pipeline = GripWrapper()
        self.blinks = 0
        self.pipeline_completions = 0
        self.w = 320
        self.h = 240
        self.video_writer = cv2.VideoWriter('output.avi', cv2.VideoWriter_fourcc(*'XVID'), 15, (self.w, self.h))
        self.blank_frame = numpy.zeros([self.h, self.w, 3]).astype(numpy.uint8)
        self.done = False

    def new_image_handler(self, evt, obj=None, tap_count=None, **kwargs):
        if self.has_roi:
            bounds = (self.eye_region_of_interest[0].x, self.eye_region_of_interest[0].y,
                      self.eye_region_of_interest[1].x, self.eye_region_of_interest[1].y)
            cropped_image = evt.image.crop(bounds)
            roi = numpy.array(cropped_image, dtype=numpy.uint8)
            # go from 3 channel image to 1 channel
            new_roi = []
            for row in roi:
                new_col = []
                for col in row:
                    new_col.append(col[0])
                new_roi.append(new_col)
            roi = numpy.array(new_roi)

            # GRIP time!!!!
            (output_image, blink) = self.pipeline.run(roi)
            self.blob_history.append(blink)

            # limited blob history
            if len(self.blob_history) > 5:
                self.blob_history = self.blob_history[1:]

            if self.blob_history == [0, 0, 1, 0, 0]:
                print("BLINK! %i" % self.blinks)
                self.blinks += 1

            # go from 1 channel image to 3 channel
            # new_output_image = []
            # for row in output_image:
            #     new_col = []
            #     for col in row:
            #         new_col.append([col, col, col]) # 3 channel
            #     new_output_image.append(new_col)
            # output_image = numpy.array(new_output_image)
            # padd_h = self.h - output_image.shape[0]
            # padd_w = self.w - output_image.shape[1]
            # padding = ((0, padd_h), (0, padd_w), (0, 0))
            # padded_output_image = numpy.pad(output_image, padding, 'constant')

            # for debugging, write to video
            # self.video_writer.write(padded_output_image)
            # self.pipeline_completions += 1

            # filter out the blobs

    @cozmo.event.filter_handler(cozmo.faces.EvtFaceObserved)
    def observed_face_handler(self, evt, obj=None, tap_count=None, **kwargs):
        # when we get a new face detection, save the area around the eyes

        if len(evt.face.left_eye) > 2 and len(evt.face.right_eye) > 2:
            roi_x1 = round(max(evt.face.left_eye[0].x - self.eye_padding, 0))
            roi_y1 = round(max(evt.face.left_eye[0].y - self.eye_padding, 0))
            roi_x2 = round(min(evt.face.right_eye[2].x + self.eye_padding, 320))
            roit_y2 = round(min(evt.face.right_eye[2].y + self.eye_padding, 240))
            self.self.eye_region_of_interest = [Pt(roi_x1, roi_y1), Pt(roi_x2, roit_y2)]
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

        # robot.add_event_handler(cozmo.faces.EvtFaceObserved, self.observed_face_handler)
        evt = await robot.world.wait_for(cozmo.faces.EvtFaceObserved)

        # when we get a new face detection, save the area around the eyes

        if len(evt.face.left_eye) > 2 and len(evt.face.right_eye) > 2:
            roi_x1 = round(max(evt.face.left_eye[0].x - self.eye_padding, 0))
            roi_y1 = round(max(evt.face.left_eye[0].y - self.eye_padding, 0))
            roi_x2 = round(min(evt.face.right_eye[2].x + self.eye_padding, 320))
            roit_y2 = round(min(evt.face.right_eye[2].y + self.eye_padding, 240))
            self.eye_region_of_interest = [Pt(roi_x1, roi_y1), Pt(roi_x2, roit_y2)]
            self.has_roi = True

        robot.camera.image_stream_enabled = True
        robot.camera.add_event_handler(cozmo.robot.camera.EvtNewRawCameraImage, self.new_image_handler)
        robot.world.image_annotator.add_annotator('roi', self)

        # infinite loop that doesn't hog CPU
        while True:
            await asyncio.sleep(1)

    def apply(self, image, scale):
        blue = ImageColor.getrgb("#f00")
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
        cozmo.connect(sc.run)
        # cozmo.connect_with_tkviewer(sc.run)
    except cozmo.ConnectionError as e:
        sys.exit("Connection error: %s" % e)
