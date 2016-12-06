#!/usr/bin/env python3

'''Cozmo Pictionary'''

import sys
from cozmo.util import degrees, distance_mm
import asyncio
import cozmo

def find_cube(robot, timeout=30):
    # Move lift down and tilt the head up
    robot.move_lift(-3)
    robot.set_head_angle(degrees(0)).wait_for_completed()

    # look around and try to find a cube
    look_around = robot.start_behavior(cozmo.behavior.BehaviorTypes.LookAroundInPlace)

    cube = None

    try:
        cube = robot.world.wait_for_observed_light_cube(timeout=timeout)
    except asyncio.TimeoutError:
        print("No cube found within %s seconds" % timeout)
    finally:
        # whether we find it or not, we want to stop the behavior
        look_around.stop()

    return cube

def go_to_cube(robot, cube):
    action = robot.go_to_object(cube, distance_mm(60.0))
    action.wait_for_completed()
    print("Completed action: result = %s" % action)
    print("Done.")


def run(sdk_conn):
    robot = sdk_conn.wait_for_robot()

    # go to nearest cube
    cube = find_cube(robot)
    if cube:
        # play an "I'm ready" animation
        robot.play_anim('anim_keepaway_getready_02').wait_for_completed()
        go_to_cube(robot, cube)

        done = False
        while not done:
            # take a picture
            print("taking picture")

            # thinking animation

            # tap cube to guess

            # make the guess
            robot.say_text("Is it a taco").wait_for_completed()
            done = True
    else:
        # abort mission
        robot.play_anim('anim_keepaway_losegame_02').wait_for_completed()

if __name__ == '__main__':
    cozmo.setup_basic_logging()

    try:
        cozmo.connect(run)
    except cozmo.ConnectionError as e:
        sys.exit("A connection error occurred: %s" % e)
