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


async def turn_to_small_random_angle(robot : cozmo.robot.Robot):
    new_pose = robot.pose
    d_angle = random.randint(-6, 6) * 5 # from -30 to 30 by 5's
    print(new_pose)
    print(cozmo.util.pose_z_angle(0, 0, 0, degrees(d_angle)))
    await robot.go_to_pose(new_pose, relative_to_robot=False).wait_for_completed()


def new_image_handler(evt, obj=None, tap_count=None, **kwargs):
    pass


async def run(sdk_conn):
    robot = await sdk_conn.wait_for_robot()

    # setup camera
    robot.camera.image_stream_enabled = True
    robot.camera.add_event_handler(cozmo.robot.camera.EvtNewRawCameraImage, new_image_handler)
    await robot.set_head_angle(degrees(0)).wait_for_completed()
    robot.move_lift(-1)

    state = States.LOOKING_FOR_CUBES
    while True:
        print(state)
        if state == States.LOOKING_FOR_CUBES:
            cubes_found = []
            while True:
                cube = await robot.world.wait_for_observed_light_cube(timeout=30, include_existing=False)
                if cube not in cubes_found:
                    print("found %s" % cube)
                    cubes_found.append(cube)
                    cube.set_lights(cozmo.lights.green_light)
                    found_block_anim = robot.play_anim_trigger(cozmo.anim.Triggers.BlockReact)
                    await found_block_anim.wait_for_completed()

                if len(cubes_found) == 3:
                    state = States.READY_ANIM
                    break;

        elif state == States.READY_ANIM:
            await robot.play_anim("anim_speedtap_findsplayer_01").wait_for_completed()
            state = States.WATCHING
        elif state == States.WATCHING:
            await robot.play_anim("anim_hiking_edgesquintgetin_01").wait_for_completed()

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
