#!/usr/bin/env python3
'''Cozmo Shuffle'''

import random
import sys
import cozmo
import asyncio
from cozmo.util import degrees, radians, distance_mm, speed_mmps
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


async def blink_cubes(cubes, color, count):
    for i in range(count):
        for cube in cubes:
            cube.set_light(cozmo.lights.off_light)
        await asyncio.sleep(0.1)
        for cube in cubes:
            cube.set_light(color)
        await asyncio.sleep(0.3)

    for cube in cubes:
        cube.set_light(cozmo.lights.off_light)
    await asyncio.sleep(0.1)


async def look_for_three_cubes(robot: cozmo.robot.Robot, existing_cubes=[], play_anim=False, show_colors=True):
    cubes_found = existing_cubes
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
            if show_colors:
                cube.set_light(cube_colors[cubes_count])
            if play_anim:
                found_block_anim = robot.play_anim_trigger(cozmo.anim.Triggers.BlockReact)  # pylint: disable=no-member
                await found_block_anim.wait_for_completed()
            cubes_count += 1

        # we're done once we have all three (unique) cubes
        if len(cubes_found) == 3:
            state = States.READY_ANIM
            return cubes_found

    return None


async def wait_for_three_cubes(robot: cozmo.robot.Robot, play_anim=False, show_colors=True):
    cubes = []
    look_around_gen = small_random_angle(-20, 20, 2)
    while True:
        try:
            cubes = await asyncio.wait_for(
                look_for_three_cubes(
                    robot, existing_cubes=cubes, play_anim=play_anim, show_colors=show_colors), timeout=5)
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

    correct_guess_rate = 0.50

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

            # we've got the right one. turn the others off
            for cube in cubes:
                cube.stop_light_chaser()
                cube.set_light(cozmo.lights.off_light)

            # make the clubes blink so friend knows to start
            await blink_cubes(cubes, cozmo.lights.green_light, 2)

            # prep work so guessing correct/incorrect is easy
            cubes.remove(friend_cube)
            friend_cube.set_light(cozmo.lights.blue_light)
            non_friend_cubes = cubes
            state = States.READY_ANIM

        elif state == States.READY_ANIM:
            # tell friend we're ready with an animation, and by flashing the cubes
            for cube in cubes:
                cube.set_light(cozmo.lights.white_light)
            await robot.play_anim("anim_speedtap_findsplayer_01").wait_for_completed()

            state = States.WATCHING

        elif state == States.WATCHING:

            await robot.play_anim("anim_hiking_edgesquintgetin_01").wait_for_completed()

            # turn around a bit while we watch
            look_around_gen = small_random_angle()
            current_angle = 0
            for i in range(3):
                current_angle, robot_angle = next(look_around_gen)
                await robot.turn_in_place(degrees(robot_angle)).wait_for_completed()

            # turn back to center
            await robot.turn_in_place(degrees(-current_angle)).wait_for_completed()

            state = States.REFINDING_CUBES

        elif state == States.REFINDING_CUBES:
            # try to find the cubes again
            # back up so we are more likely to see them
            await robot.drive_straight(distance_mm(-50), speed_mmps(80)).wait_for_completed()
            cubes = await wait_for_three_cubes(robot, show_colors=False)
            # determine the order
            state = States.GUESSING

        elif state == States.GUESSING:
            # show friend we're ready to guess
            await robot.play_anim("anim_meetcozmo_lookface_02").wait_for_completed()

            # pick a cube
            if random.random() < correct_guess_rate:
                guessed_cube = friend_cube
                state = States.CORRECT
            else:
                guessed_cube = non_friend_cubes[random.randint(0, 1)]
                state = States.INCORRECT

            turn_to_face_angle = angle_to_cube(robot.pose, guessed_cube)
            await robot.turn_in_place(radians(turn_to_face_angle)).wait_for_completed()
            await robot.play_anim("anim_pounce_long_01").wait_for_completed()
            robot.move_head(1)

        elif state == States.INCORRECT:
            for cube in cubes:
                cube.set_light(cozmo.lights.red_light)
            await robot.play_anim("anim_reacttocliff_stuckleftside_01").wait_for_completed()
            state = States.DONE

        elif state == States.CORRECT:
            pre_celebration_pose = robot.pose
            for cube in cubes:
                cube.start_light_chaser(cozmo.lights.green_light)
            await robot.play_anim("anim_speedtap_wingame_intensity02_01").wait_for_completed()
            for cube in cubes:
                cube.stop_light_chaser()
            await robot.go_to_pose(pre_celebration_pose, relative_to_robot=False).wait_for_completed()
            state = States.DONE

        elif state == States.DONE:
            await asyncio.sleep(1)
            return


if __name__ == '__main__':
    cozmo.setup_basic_logging()

    try:
        cozmo.connect(run)
    except cozmo.ConnectionError as e:
        sys.exit("A connection error occurred: %s" % e)
