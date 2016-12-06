#!/usr/bin/env python3

'''Cozmo Pictionary'''

import sys
from cozmo.util import degrees, distance_mm, speed_mmps
import asyncio
import cozmo

class States:
    FINDING_CUBE = "FINDING CUBE"
    LIFTING = "LIFTING"
    GOING_TO_CUBE = "GOING TO CUBE"
    READY = "READY"
    DONE = "DONE"

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
    action = robot.go_to_object(cube, distance_mm(65.0))
    action.wait_for_completed()

    if action._state == cozmo.action.ACTION_SUCCEEDED:
        # get a bit closer to the cube
        robot.drive_straight(distance_mm(20), speed_mmps(10)).wait_for_completed()
        return True
    else:
        # cozmo got confused, back up a bit
        robot.drive_straight(distance_mm(-50), speed_mmps(30)).wait_for_completed()
        return False

def run(sdk_conn):
    robot = sdk_conn.wait_for_robot()

    robot.abort_all_actions()

    state = States.FINDING_CUBE
    while True:
        print(state)
        if state == States.FINDING_CUBE:
            # go to nearest cube
            cube = find_cube(robot)
            if cube:
                state = States.LIFTING

        if state == States.LIFTING:
            # lift the lift
            action = robot.set_lift_height(1, 5, 5, 0.1)
            action.wait_for_completed()

            if action._state == cozmo.action.ACTION_SUCCEEDED:
                state = States.GOING_TO_CUBE
            else:
                print("action failed: %s" % action)

        elif state == States.GOING_TO_CUBE:
            success = go_to_cube(robot, cube)
            if success:
                state = States.READY
            else:
                state = States.FINDING_CUBE

        elif state == States.READY:
            # take a picture
            print("taking picture")

            # thinking animation

            # tap cube to guess

            # make the guess
            robot.say_text("Is it a taco").wait_for_completed()
            state = States.DONE
        else:
            print("giving up.")
            return

if __name__ == '__main__':
    cozmo.setup_basic_logging()

    try:
        cozmo.connect(run)
    except cozmo.ConnectionError as e:
        sys.exit("A connection error occurred: %s" % e)
