import sys
import cozmo
import asyncio
import cv2
import BlinkPipeline

def new_image_handler(evt, obj=None, tap_count=None, **kwargs):
    #
    evt.image

@cozmo.event.filter_handler(cozmo.faces.EvtFaceObserved)
def observed_face_handler(evt, obj=None, tap_count=None, **kwargs):
    print(evt.face.left_eye)
    print(evt.face.right_eye)


async def run(sdk_conn : cozmo.conn.CozmoConnection):
    robot = await sdk_conn.wait_for_robot()
    robot.add_event_handler(cozmo.faces.EvtFaceObserved, observed_face_handler)
    robot.camera.image_stream_enabled = True
    robot.camera.add_event_handler(cozmo.robot.camera.EvtNewRawCameraImage, new_image_handler)

if __name__ == "__main__":
    cozmo.setup_basic_logging()

    try:
        cozmo.connect(run)
    except cozmo.ConnectionError as e:
        sys.exit("Connection error: %s" % e)
