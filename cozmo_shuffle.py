#!/usr/bin/env python3

'''Cozmo Shuffle'''

import random
import sys
import cozmo
import asyncio
from cozmo.util import degrees


class States:
    LOOKING_FOR_CUBES = "LOOKING FOR CUBES"
    READY_ANIM = "READY ANIMATION"
    WATCHING = "WATCHING"
    THINKING = "THINKING"
    GUESSING = "GUESSING"
    CORRECT = "CORRECT"
    INCORRECT = "INCORRECT"
    DONE = "DONE"


def new_image_handler(evt, obj=None, tap_count=None, **kwargs):
    pass


async def run(sdk_conn):
    robot = await sdk_conn.wait_for_robot()

    # setup camera
    robot.camera.image_stream_enabled = True
    robot.camera.add_event_handler(cozmo.robot.camera.EvtNewRawCameraImage, new_image_handler)

    state = States.LOOKING_FOR_CUBES
    cubes = []
    while True:
        print(state)
        if state == States.LOOKING_FOR_CUBES:
            cubes = await robot.world.wait_until_observe_num_objects(num=3, object_type=cozmo.objects.LightCube, timeout=10)
            if len(cubes) == 3:
                state = States.READY_ANIM
        elif state == States.READY_ANIM:
            await robot.play_anim("anim_speedtap_findsplayer_01").wait_for_completed()
            state = States.WATCHING
        elif state == States.WATCHING:
            await robot.play_anim("anim_hiking_edgesquintgetin_01").wait_for_completed()

            initial_pose = robot.pose
            for i in range(5):
                new_pose = initial_pose
                d_angle = random.randint(-6, 6) * 5 # from -30 to 30 by 5's
                print(d_angle)
                new_pose += cozmo.util.pose_z_angle(0, 0, 0, d_angle)
                await robot.go_to_pose(new_pose, relative_to_robot=False).wait_for_completed()

            state = States.THINKING
        else:
            print("giving up.")
            return


if __name__ == '__main__':
    cozmo.setup_basic_logging()

    try:
        cozmo.connect(run)
    except cozmo.ConnectionError as e:
        sys.exit("A connection error occurred: %s" % e)
