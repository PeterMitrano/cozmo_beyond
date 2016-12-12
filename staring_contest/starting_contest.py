import sys
import cozmo
import asyncio
import cv2
import BlinkPipeline


class StaringContest:

    def __init__(self):
        # order: top left x, top left y, bottom right x, bottom right y
        # top left pixel is 0,0
        self.eye_region_of_interest = [0, 0, 320, 240]

    def new_image_handler(self, evt, obj=None, tap_count=None, **kwargs):
        roi = evt.image.crop(*self.eye_region_of_interest)
        roi.save('roi.png', "PNG")

    @cozmo.event.filter_handler(cozmo.faces.EvtFaceObserved)
    def observed_face_handler(self, evt, obj=None, tap_count=None, **kwargs):
        self.eye_region_of_interest = [evt.face.left_eye[0][0], evt.face.left_eye[0][1], evt.face.right_eye[2][0],
                                       evt.face.right_eye[2][1]]

    async def run(self, sdk_conn: cozmo.conn.CozmoConnection):
        robot = await sdk_conn.wait_for_robot()
        robot.add_event_handler(cozmo.faces.EvtFaceObserved, self.observed_face_handler)
        robot.camera.image_stream_enabled = True
        robot.camera.add_event_handler(cozmo.robot.camera.EvtNewRawCameraImage, self.new_image_handler)


if __name__ == "__main__":
    cozmo.setup_basic_logging()

    try:
        sc = StaringContest()
        cozmo.connect(sc.run)
    except cozmo.ConnectionError as e:
        sys.exit("Connection error: %s" % e)
