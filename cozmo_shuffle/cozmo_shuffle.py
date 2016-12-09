#!/usr/bin/env python3
'''Cozmo Shuffle'''

import random
import sys
import cozmo
import asyncio
from cozmo.util import degrees
from cube_blinker import BlinkyCube

from math import cos
from math import sin
from math import acos
from math import sqrt


def length(v):
    return sqrt(v[0]**2+v[1]**2)


def dot_product(v, w):
    return v[0]*w[0]+v[1]*w[1]


def determinant(v,w):
    return v[0]*w[1]-v[1]*w[0]


def inner_angle(v, w):
    cosx = dot_product(v, w)/(length(v)*length(w))
    rad = acos(cosx)  # in radians
    return rad


def angle_clockwise(a, b):
    inner = inner_angle(a, b)
    det = determinant(a, b)
    if det < 0:  # this is a property of the det. If the det < 0 then B is clockwise of A
        return inner
    else:  # if the det > 0 then A is immediately clockwise of B
        return -inner


def angle_to_cube(robot_pose, cube):
    cube_vector = (cube.pose.position.x - robot_pose.position.x, cube.pose.position.y - robot_pose.position.y)
    robot_vector = (cos(robot_pose.rotation.angle_z.radians), sin(robot_pose.rotation.angle_z.radians))
    return angle_clockwise(cube_vector, robot_vector)


# Make sure World knows how to instantiate the subclass
cozmo.world.World.light_cube_factory = BlinkyCube


class States:
    LOOKING_FOR_CUBES = "LOOKING FOR CUBES"
    READY_ANIM = "READY ANIMATION"
    PICKING_CUBE = "PICKING CUBE"
    WATCHING = "WATCHING"
    REFINDING_CUBES = "RE-FINDING CUBES"
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
        yield current_angle, turn_angle


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
            # found_block_anim = robot.play_anim_trigger(cozmo.anim.Triggers.BlockReact)  # pylint: disable=no-member
            # await found_block_anim.wait_for_completed()

        # we're done once we have all three (unique) cubes
        if len(cubes_found) == 3:
            state = States.READY_ANIM
            return cubes_found

    return None


async def wait_for_three_cubes(robot: cozmo.robot.Robot):
    cubes = []
    look_around_gen = small_random_angle(-20, 20, 2)
    while True:
        try:
            cubes = await asyncio.wait_for(
                look_for_three_cubes(
                    robot, existing_cubes=cubes), timeout=10)
            return cubes
        except asyncio.TimeoutError:
            # tell friend we're confused and look around a bit
            robot.abort_all_actions()
            await robot.play_anim("anim_memorymatch_failhand_01").wait_for_completed()
            _, robot_angle = next(look_around_gen)
            await robot.turn_in_place(degrees(robot_angle)).wait_for_completed()


async def run(sdk_conn):
    robot = await sdk_conn.wait_for_robot()
    print("BATTERY LEVEL: %f" % robot.battery_voltage)

    await robot.set_head_angle(degrees(0)).wait_for_completed()
    robot.move_lift(-1)

    correct_guess_rate = 0.95

    state = States.LOOKING_FOR_CUBES
    cubes = []
    non_friend_cubes = []
    friend_cube = None
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
            non_friend_cubes = cubes

            # we've got the right one. turn the others off
            for cube in cubes:
                cube.stop_light_chaser()
                cube.set_lights(cozmo.lights.off_light)

            state = States.READY_ANIM
            print(friend_cube)

        elif state == States.READY_ANIM:
            # tell friend we're ready with an animation, and by flashing the cubes
            for cube in cubes:
                cube.set_lights(cozmo.lights.white_light)
            await robot.play_anim("anim_speedtap_findsplayer_01").wait_for_completed()

            state = States.WATCHING

        elif state == States.WATCHING:
            await robot.play_anim("anim_hiking_edgesquintgetin_01").wait_for_completed()

            # turn around a bit while we watch
            look_around_gen = small_random_angle()
            current_angle = 0
            for i in range(5):
                current_angle, robot_angle = next(look_around_gen)
                await robot.turn_in_place(degrees(robot_angle)).wait_for_completed()

            # turn back to center
            await robot.turn_in_place(degrees(-current_angle)).wait_for_completed()
            print("done watching")

            state = States.GUESSING

        # elif state == States.REFINDING_CUBES:
        #     # try to find the cubes again
        #     cubes = await wait_for_three_cubes(robot)
        #     # determine the order
        #     state = States.GUESSING

        elif state == States.GUESSING:
            # show friend we're ready to guess
            # await robot.play_anim("anim_launch_firsttimewakeup_helloplayer").wait_for_completed()

            # pick a cube
            # use friend_cube_idx
            if random.random() < correct_guess_rate:
                guessed_cube = friend_cube
                print("guessing right")
            else:
                guessed_cube = non_friend_cubes[random.randint(0, 1)]
                print("guessing wrong")

            print(guessed_cube)
            turn_to_face_angle = angle_to_cube(robot.pose, guessed_cube)
            await robot.turn_in_place(degrees(turn_to_face_angle)).wait_for_completed()
            await robot.play_anim("anim_pounce_long_01").wait_for_completed()
            robot.move_head(1)
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
