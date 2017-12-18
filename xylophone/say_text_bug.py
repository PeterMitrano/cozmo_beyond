#!/usr/bin/python3.5
import cozmo


def run(robot):
    txt = 'ooooooooo'
    robot.say_text(txt, duration_scalar=0.04).wait_for_completed()


if __name__ == "__main__":
    cozmo.robot.Robot.drive_off_charger_on_connect = False
    cozmo.run_program(run)
