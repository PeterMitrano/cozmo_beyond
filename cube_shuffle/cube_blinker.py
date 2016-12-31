from collections import deque
import asyncio
import cozmo

cozmo.lights.rainbow_light = cozmo.lights.Color(name='rainbow')

class BlinkyCube(cozmo.objects.LightCube):
    '''Subclass LightCube and add a light-chaser effect.

    # EXAMPLE USAGE
    # cube.start_light_chaser()
    # try:
    #     print("Waiting for cube to be tapped")
    #     await cube.wait_for_tap(timeout=10)
    #     print("Cube tapped")
    # except asyncio.TimeoutError:
    #     print("No-one tapped our cube :-(")
    # finally:
    #     cube.stop_light_chaser()
    #     cube.set_lights_off()
    '''

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._chaser = None
        self.current_light = cozmo.lights.off_light

    def blink(self, period_seconds, light_color=None):
        if light_color is None:
            light_color = self.current_light

        async def _blink():
            while True:
                await asyncio.sleep(period_seconds, loop=self._loop)
                self.set_lights(cozmo.lights.off_light)
                await asyncio.sleep(period_seconds, loop=self._loop)
                self.set_lights(light_color)
        self._chaser = asyncio.ensure_future(_blink(), loop=self._loop)

    async def blink_once(self, light_color):
        self.set_lights(cozmo.lights.off_light)
        await asyncio.sleep(0.1, loop=self._loop)
        self.set_lights(light_color)
        await asyncio.sleep(0.3, loop=self._loop)
        self.set_lights(cozmo.lights.off_light)
        await asyncio.sleep(0.1, loop=self._loop)
        self.set_lights(self.current_light)

    def start_light_chaser(self, light_color):
        '''Cycles the lights around the cube with 1 corner lit up,
        changing to the next corner every time step
        '''
        if self._chaser:
            raise ValueError("Light chaser already running")

        async def _chaser():
            self.current_light = light_color
            while True:
                for i in range(4):
                    cols = [cozmo.lights.off_light] * 4
                    cols[i] = light_color
                    cols[(i + 2) % 4] = light_color
                    self.set_light_corners(*cols)
                    await asyncio.sleep(0.2, loop=self._loop)

        self._chaser = asyncio.ensure_future(_chaser(), loop=self._loop)

    def start_rainbow_chaser(self):
        if self._chaser:
            raise ValueError("Light chaser already running")

        async def _chaser():
            rainbow = deque([cozmo.lights.red_light, cozmo.lights.blue_light, cozmo.lights.green_light,
                       cozmo.lights.white_light])
            self.current_light = cozmo.lights.rainbow_light
            while True:
                rainbow.rotate()
                self.set_light_corners(*list(rainbow))
                await asyncio.sleep(0.5, loop=self._loop)

        self._chaser = asyncio.ensure_future(_chaser(), loop=self._loop)

    def stop_light_chaser(self):
        if self._chaser:
            self.current_light = cozmo.lights.off_light
            self._chaser.cancel()
            self._chaser = None
            self.set_lights(cozmo.lights.off_light)

    def set_light(self, light):
        self.current_light = light
        self.set_lights(light)
