#!/usr/bin/env python3

'''Cozmo Shuffle'''

import random
import sys
import cozmo
import asyncio
from cozmo.util import degrees
from cube_blinker import BlinkyCube

# Make sure World knows how to instantiate the subclass
cozmo.world.World.light_cube_factory = BlinkyCube

class States:
    LOOKING_FOR_CUBES = "LOOKING FOR CUBES"
    READY_ANIM = "READY ANIMATION"
    PICKING_CUBE = "PICKING CUBE"
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

async def look_for_three_cubes(robot: cozmo.robot.Robot, existing_cubes=[]):
    cubes_found = existing_cubes
    # cube_colors = [cozmo.lights.green_light, cozmo.lights.blue_light, cozmo.lights.red_light]
    cube_colors = 3 * [cozmo.lights.green_light]
    cubes_count = len(cubes_found)
    while True:
        # check for cubes
        # note this timeout means very little. If we see a cube and it's the wrong one,
        # it will return immediately with cube = None, not wait for timeout.
        cube = await robot.world.wait_for_observed_light_cube(timeout=5, include_existing=False)

        # if we found something new, add it and tell friend
        if cube not in cubes_found:
            cubes_found.append(cube)

            # indicate to friend that we found the blocks
            cube.set_lights(cube_colors[cubes_count])
            cubes_count += 1
            found_block_anim = robot.play_anim_trigger(cozmo.anim.Triggers.BlockReact)
            await found_block_anim.wait_for_completed()

        # we're done once we have all three (unique) cubes
        if len(cubes_found) == 3:
            state = States.READY_ANIM
            return cubes_found

    return None

async def wait_for_three_cubes(robot : cozmo.robot.Robot):
    cubes = []
    look_around_gen = small_random_angle(-20, 20, 2)
    while True:
        try:
            cubes = await asyncio.wait_for(look_for_three_cubes(robot, existing_cubes=cubes), timeout=10)
            return cubes
        except asyncio.TimeoutError:
            # tell friend we're confused and look around a bit
            robot.abort_all_actions()
            await robot.play_anim("anim_memorymatch_failhand_01").wait_for_completed()
            robot_angle = next(look_around_gen)
            await robot.turn_in_place(degrees(robot_angle)).wait_for_completed()

async def run(sdk_conn):
    robot = await sdk_conn.wait_for_robot()
    print("BATTERY LEVEL: %f" % robot.battery_voltage)

    # setup camera
    robot.camera.image_stream_enabled = True
    robot.camera.add_event_handler(cozmo.robot.camera.EvtNewRawCameraImage, new_image_handler)
    await robot.set_head_angle(degrees(0)).wait_for_completed()
    robot.move_lift(-1)

    state = States.LOOKING_FOR_CUBES
    cubes = []
    while True:
        print(state)
        if state == States.LOOKING_FOR_CUBES:
            cubes = await wait_for_three_cubes(robot)
            state = States.PICKING_CUBE

        elif state == States.PICKING_CUBE:
            # friend picks the cube we're going to track
            tap_events = []
            for cube in cubes:
                cube.start_light_chaser(cozmo.lights.blue_light)
                tap_events.append(cube.wait_for_tap())

            tap_event = await cozmo.event.wait_for_first(*tap_events)
            friend_cube = tap_event.obj
            friend_cube.stop_light_chaser()
            friend_cube.set_lights(cozmo.lights.blue_light)
            cubes.remove(friend_cube)

            # we've got the right one. turn the others off
            for cube in cubes:
                cube.stop_light_chaser()
                cube.set_lights(cozmo.lights.off_light)

            state = States.READY_ANIM

        elif state == States.READY_ANIM:
            # tell friend we're ready with an animation, and by flashing the cubes
            for cube in cubes:
                cube.set_lights(cozmo.lights.white_light)
            await robot.play_anim("anim_speedtap_findsplayer_01").wait_for_completed()
            state = States.WATCHING

        elif state == States.WATCHING:
            await robot.play_anim("anim_hiking_edgesquintgetin_01").wait_for_completed()

            look_around_gen = small_random_angle()
            for i in range(5):
                robot_angle = next(look_around_gen)
                await robot.turn_in_place(degrees(robot_angle)).wait_for_completed()
            print("done.")
            state = States.THINKING

        elif state == States.THINKING:
            # try to find the cubes again
            cubes = await wait_for_three_cubes(robot)
            # determine the order
            print(cubes[0].pose.position)
            print(cubes[1].pose.position)
            print(cubes[2].pose.position)
            state = States.GUESSING

        elif state == States.GUESSING:
            # show friend we're ready to guess
            await robot.play_anim("anim_rtpkeepaway_ideatoplay_02").wait_for_completed()
            state = States.DONE

        elif state == States.DONE:
            print("waiting for event loop to finish")
            await asyncio.sleep(10)
        else:
            print("ABORTING")
            return


if __name__ == '__main__':
    cozmo.setup_basic_logging()

    try:
        cozmo.connect(run)
    except cozmo.ConnectionError as e:
        sys.exit("A connection error occurred: %s" % e)
