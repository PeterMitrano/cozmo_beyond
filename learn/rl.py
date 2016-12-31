import threading
import asyncio
import os
import pickle
from collections import namedtuple
from cozmo.util import degrees
import sys
import cozmo
import numpy as np


Action = namedtuple('Action', ['lift', 'wheels', 'head'])
State = namedtuple('State', ['dx', 'dy', 'dz', 'd_angle', 'head', 'lift'])


class RL:

    def __init__(self):
        self.x_step = 5
        self.y_step = 5
        self.z_step = 5
        self.angle_step = 5  # degrees
        self.lift_step = 5  # millimeters
        self.head_step = 5  # degrees
        min_wheel_speed = -50
        max_wheel_speed = 50
        wheel_speed_step = 10
        min_head = -1
        max_head = 1
        head_step = 1
        min_lift = -1
        max_lift = 1
        lift_step = 1

        # create all possible actions (wow there are a lot)
        self.actions = []
        # for lw in range(min_wheel_speed, max_wheel_speed + wheel_speed_step, wheel_speed_step):
        #     for rw in range(min_wheel_speed, max_wheel_speed + wheel_speed_step, wheel_speed_step):
        for lw in [-50, 0, 50]:
            for rw in [-50, 0, 50]:
                # for h in range(min_head, max_head + head_step, head_step):
                    for l in range(min_lift, max_lift + lift_step, lift_step):
                        action = Action(lift=l, wheels=(lw, rw), head=0)
                        self.actions.append(action)

        # the states array is dynamically sized (woah fancy!)
        self.states = []
        state = State(dx=0, dy=0, dz=0, d_angle=0, lift=0, head=0)
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

    def user_input(self):
        while True:
            input()
            self.success_event.set()

    async def run(self, robot: cozmo.robot.Robot):
        self.robot = robot
        self.robot.camera.image_stream_enabled = True
        print("BATTERY LEVEL: %f" % self.robot.battery_voltage)

        # find the initial cube
        await self.reset()
        self.cube = await self.robot.world.wait_for_observed_light_cube(timeout=60)
        await self.robot.play_anim("anim_speedtap_findsplayer_01").wait_for_completed()

        # demonstrations!
        print(self.Q.shape)
        await self.demo()
        print(self.Q.shape)

        # monitor enter key for rewards
        self.ui_thread.start()
        # for state_idx in range(self.Q.shape[0]):
        #     for action_idx in range(self.Q.shape[1]):
        #         q = self.Q[state_idx][action_idx]
        #         if q > 0:
        #             print(self.states[state_idx], self.actions[action_idx], q)

        # training
        await self.train()

    async def demo(self):
        demo_action_map = {
            'w': 25,
            'a': 6,
            's': 1,
            'd': 19,
            'wi': 26,
            'k': 12,
            'i': 14,
        }

        state_idx = 0
        while True:
            action_name = input("Pick an action:")
            if action_name == 'done':
                break

            if action_name in demo_action_map:
                action_idx = demo_action_map[action_name]
                print("executing action %s,%i" % (action_name, action_idx))
                self.Q[state_idx][action_idx] += 1
                state_idx, instant_reward, done = await self.execute_action(action_idx)
                print(state_idx, instant_reward, done)
            else:
                print("invalid action, ignoring.")

        print("Demonstrations complete.")

    async def train(self):
        train_iters = 0
        while True:
            # inital state
            await self.reset()
            state_idx = 0
            j = 0
            done = False
            rewards = []
            total_reward = 0

            # The Q-Table learning algorithm
            while j < 200 and not done:
                j += 1

                # Choose an action by greedily (with noise) picking from Q table
                noise = np.random.randn(len(self.states), len(self.actions)) * (1e-3 / (train_iters + 1))
                action_idx = np.argmax(self.Q[state_idx] + noise) % len(self.Q[0])

                # Get new state and reward from environment
                next_state_idx, instant_reward, done = await self.execute_action(action_idx)

                # Update Q-Table with new knowledge
                dq = instant_reward + self.gamma * np.max(self.Q[next_state_idx])
                self.Q[state_idx, action_idx] = (1 - self.lr) * self.Q[state_idx, action_idx] + self.lr * dq
                total_reward += instant_reward
                rewards.append(instant_reward)
                state_idx = next_state_idx
                print(j)

            print(train_iters, total_reward, rewards)
            print("RESET THE ROBOT POSITION")
            pickle.dump(self.states, open('visited_states.pickle', 'wb'))
            pickle.dump(self.Q, open('learned_q.pickle', 'wb'))
            self.success_event.wait()
            self.success_event.clear()
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
        # self.robot.move_head(action.head)
        await self.robot.drive_wheels(*action.wheels, l_wheel_acc=1000, r_wheel_acc=1000, duration=self.time_step_size)

        # return the new state
        dx = abs(self.robot.pose.position.x - self.cube.pose.position.x) // self.x_step
        dy = abs(self.robot.pose.position.y - self.cube.pose.position.y) // self.y_step
        dz = abs(self.robot.pose.position.z - self.cube.pose.position.z) // self.z_step
        d_angle = abs(self.robot.pose.rotation.angle_z.radians - self.cube.pose.rotation.angle_z.radians) // self.angle_step
        head = abs(self.robot.head_angle.degrees) // self.head_step
        lift = abs(self.robot.lift_height.distance_mm) // self.lift_step
        new_state = State(dx=dx, dy=dy, dz=dz, d_angle=d_angle, head=head, lift=lift)

        # check if we succeeded
        if self.success_event.isSet():
            done = True
            reward = 10
            print("SUCCESS!")
            self.success_event.clear()
        else:
            done = False
            reward = 0

        # manual reward function
        euler_distance = np.hypot(dx, dy)
        reward += 1 / (1 + euler_distance**2)

        try:
            result = (self.states.index(new_state), reward, done)
        except ValueError:
            self.states.append(new_state)
            new_actions = np.zeros([1, len(self.actions)])
            self.Q = np.append(self.Q, new_actions, 0)
            result = (len(self.states) - 1, reward, done)
        finally:
            return result

if __name__ == '__main__':
    cozmo.robot.Robot.drive_off_charger_on_connect = False
    rl = RL()
    cozmo.run_program(rl.run)

