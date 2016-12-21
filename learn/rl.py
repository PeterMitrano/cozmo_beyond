import threading
from collections import namedtuple
from cozmo.util import degrees
import sys
import select
import cozmo
import numpy as np


Action = namedtuple('Action', ['lift', 'head', 'wheels'])
State = namedtuple('State', ['dx', 'dy', 'dz', 'd_angle', 'lift', 'head'])


class RL:

    def __init__(self):
        min_wheel_speed = -100
        max_wheel_speed = 100
        wheel_speed_step = 10
        min_head = -1
        max_head = 1
        head_step = 1
        min_lift = -1
        max_lift = 1
        lift_step = 1

        # create all possible actions (wow there are a lot)
        self.actions = []
        for lw in range(min_wheel_speed, max_wheel_speed + wheel_speed_step, wheel_speed_step):
            for rw in range(min_wheel_speed, max_wheel_speed + wheel_speed_step, wheel_speed_step):
                for h in range(min_head, max_head + head_step, head_step):
                    for l in range(min_lift, max_lift + lift_step, lift_step):
                        action = Action(lift=l, head=h, wheels=(lw, rw))
                        self.actions.append(action)

        # the states array is dynamically sized (woah fancy!)
        self.states = []
        state = State(dx=0, dy=0, dz=0, d_angle=0, head=0, lift=0)
        self.states.append(state)
        self.Q = np.zeros([len(self.states), len(self.actions)])

        self.lr = 0.85
        self.time_step_size = 0.2
        self.gamma = 0.99
        self.cube = None
        self.robot = None

        # kick off user input thread
        self.success_event = threading.Event()
        self.ui_thread = threading.Thread(target=self.user_input)
        self.ui_thread.start()

    def user_input(self):
        while True:
            input()
            print("SUCCESS!")
            self.success_event.set()

    async def run(self, sdk_conn):
        robot = await sdk_conn.wait_for_robot()
        self.robot = robot
        self.robot.camera.image_stream_enabled = True
        print("BATTERY LEVEL: %f" % self.robot.battery_voltage)

        # find the initial cube
        await self.reset()
        self.cube = await robot.world.wait_for_observed_light_cube(timeout=60)
        await self.robot.play_anim("anim_speedtap_findsplayer_01").wait_for_completed()

        train_iters = 0
        while True:
            # inital state
            await self.reset()
            state_idx = 0
            total_reward = 0
            rewards = []
            done = False
            j = 0

            # The Q-Table learning algorithm
            while j < 99 and not done:
                j += 1

                # Choose an action by greedily (with noise) picking from Q table
                noise = np.random.randn(len(self.states), len(self.actions)) * (1/(train_iters+1))
                action_idx = np.argmax(self.Q[state_idx] + noise) % len(self.Q[0])

                # Get new state and reward from environment
                next_state_idx, instant_reward = await self.execute_action(action_idx)

                # Update Q-Table with new knowledge
                dq = instant_reward + self.gamma * np.max(self.Q[next_state_idx])
                self.Q[state_idx, action_idx] = (1-self.lr) * self.Q[state_idx, action_idx] + self.lr * dq
                total_reward += instant_reward
                state_idx = next_state_idx

            rewards.append(total_reward)
            print(total_reward, rewards)
            print(self.Q)
            train_iters += 1

    async def reset(self, anim=False):
        await self.robot.set_head_angle(degrees(0), duration=0.2).wait_for_completed()
        await self.robot.set_lift_height(0, duration=0.3).wait_for_completed()
        if anim:
            await self.robot.play_anim("anim_meetcozmo_lookface_getout").wait_for_completed()

    async def execute_action(self, action_idx, verbose=False):
        action = self.actions[action_idx]
        if verbose:
            print(action)

        self.robot.move_lift(action.lift)
        self.robot.move_head(action.head)
        await self.robot.drive_wheels(*action.wheels, l_wheel_acc=1000, r_wheel_acc=1000, duration=self.time_step_size)

        # return the new state
        dx = self.robot.pose.position.x - self.cube.pose.position.x
        dy = self.robot.pose.position.y - self.cube.pose.position.y
        dz = self.robot.pose.position.z - self.cube.pose.position.z
        d_angle = self.robot.pose.rotation.angle_z - self.cube.pose.rotation.angle_z
        head = self.robot.head_angle.degrees
        lift = self.robot.lift_height.distance_mm
        new_state = State(dx=dx, dy=dy, dz=dz, d_angle=d_angle, head=head, lift=lift)

        # check if we succeeded
        if self.success_event.isSet():
            reward = 1
            self.success_event.clear()
        else:
            reward = 0

        try:
            return self.states.index(new_state), reward
        except ValueError:
            self.states.append(new_state)
            new_actions = np.zeros([1, len(self.actions)])
            self.Q = np.append(self.Q, new_actions, 0)
            return len(self.states) - 1, reward

if __name__ == '__main__':
    cozmo.robot.Robot.drive_off_charger_on_connect = False
    cozmo.setup_basic_logging()

    try:
        rl = RL()
        cozmo.connect(rl.run)
        # cozmo.connect_with_tkviewer(rl.run)
    except cozmo.ConnectionError as e:
        sys.exit("A connection error occurred: %s" % e)
