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


def small_random_angle(min_deg=-30, max_deg=30, step=2):
    current_angle = 0
    while True:
        if current_angle >= 0:
            r = random.randrange(min_deg, -step, step)
        else:
            r = random.randrange(step, max_deg, step)
        turn_angle = r - current_angle
        current_angle += turn_angle
        yield turn_angle


def new_image_handler(evt, obj=None, tap_count=None, **kwargs):
    pass

async def run(sdk_conn):
    robot = await sdk_conn.wait_for_robot()
    print("BATTERY LEVEL: %f" % robot.battery_voltage)

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
            cube_colors = [cozmo.lights.green_light, cozmo.lights.blue_light, cozmo.lights.red_light]
            while True:

                # check for cubes
                cube = await robot.world.wait_for_observed_light_cube(timeout=30, include_existing=False)
                if cube not in cubes_found:
                    print("found %s" % cube)
                    cubes_found.append(cube)

                    # indicate to friend that we found the blocks
                    cube.set_lights(cube_colors.pop())
                    found_block_anim = robot.play_anim_trigger(cozmo.anim.Triggers.BlockReact)
                    await found_block_anim.wait_for_completed()

                # we're done once we have all three (unique) cubes
                if len(cubes_found) == 3:
                    state = States.READY_ANIM
                    break;

        elif state == States.READY_ANIM:
            await robot.play_anim("anim_speedtap_findsplayer_01").wait_for_completed()
            state = States.WATCHING
        elif state == States.WATCHING:
            await robot.play_anim("anim_hiking_edgesquintgetin_01").wait_for_completed()

            s_gen = small_random_angle()
            for i in range(5):
                angle = next(s_gen)
                await robot.turn_in_place(degrees(angle)).wait_for_completed()
            print("done.")
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
