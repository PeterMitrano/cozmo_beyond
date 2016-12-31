import queue
from cube_shuffle import BlinkyCube
import asyncio
import cozmo


# Make sure World knows how to instantiate the subclass
cozmo.world.World.light_cube_factory = BlinkyCube


class Xylophone:

    def __init__(self):
        self.tap_queue = queue.Queue()
        self.robot = None

    async def tap_handler(self, evt, obj=None, tap_count=None, **kwargs):
        cube = evt.obj
        cube.set_lights(cozmo.lights.blue_light)
        await asyncio.sleep(0.1)
        cube.set_lights(cozmo.lights.white_light)
        self.tap_queue.put(cube)

    async def run(self, robot: cozmo.robot.Robot):
        self.robot = robot
        print("BATTERY LEVEL: %f" % self.robot.battery_voltage)

        # add handlers
        self.robot.world.add_event_handler(cozmo.objects.EvtObjectTapped, self.tap_handler)

        cubes = robot.world.light_cubes.values()
        note_map = {}
        notes = [0.15, 0.55, 1]
        for cube, note in zip(cubes, notes):
            cube.set_lights(cozmo.lights.white_light)
            note_map[cube.object_id] = note

        while True:
            # wait for cube tap
            await asyncio.sleep(0.05)
            try:
                cube = self.tap_queue.get_nowait()
                cube_id = cube.object_id
                pitch = note_map[cube_id]
                txt = 'ooooooooooooooooooooooooooooooooo'
                await robot.say_text(txt, duration_scalar=0.1, use_cozmo_voice=False, voice_pitch=pitch).wait_for_completed()
                self.tap_queue.task_done()
            except queue.Empty:
                pass



if __name__ == "__main__":
    cozmo.robot.Robot.drive_off_charger_on_connect = False
    x = Xylophone()
    cozmo.run_program(x.run)
