import gymnasium as gym
from gymnasium import spaces
import numpy as np
import subprocess
import pickle
import os

class Sc2Env(gym.Env):
	"""Custom Environment that follows gym interface"""
	def __init__(self):
		super(Sc2Env, self).__init__()
		# Define action and observation space
		# They must be gym.spaces objects
		# Example when using discrete actions:
		self.action_space = spaces.Discrete(6)
		self.observation_space = spaces.Box(0, 255, shape=(200, 176, 3), dtype=np.uint8)

	def step(self, action):
		observation = np.zeros((200, 176, 3), dtype=np.uint8)
		reward = 0
		terminated = False
		truncated = False
		info = {}

		# write action to file:
		with open('state_rwd_action.pkl', 'rb') as f:
			state_rwd_action = pickle.load(f)

			wait_for_action = False
			state_rwd_action['action'] = action
			with open('state_rwd_action.pkl', 'wb') as f:
				pickle.dump(state_rwd_action, f)

		# read result of previous action:
		wait_for_action = True
		while wait_for_action:
			try:
				with open('state_rwd_action.pkl', 'rb') as f:
					state_rwd_action = pickle.load(f)

					if state_rwd_action['action'] is None:
						wait_for_action = False
						observation = state_rwd_action['state']
						reward = state_rwd_action['reward']
						terminated = state_rwd_action['terminated']
			except Exception as e:
				# occurs because of concurrency issues
				# print("Error while waiting for bot to perform action:", str(e))
				pass

		return observation, reward, terminated, truncated, info


	def reset(self, seed=None, options=None):
		print("RESETTING ENVIRONMENT!!!!!!!!!!!!!")
		map = np.zeros((200, 176, 3), dtype=np.uint8)
		observation = map
		info = {}
		data = {"state": map, "reward": 0, "action": None, "terminated": False}  # empty action waiting for the next one!
		with open('state_rwd_action.pkl', 'wb') as f:
			pickle.dump(data, f)

		# run serralBot.py non-blocking:
		subprocess.Popen(['python3', 'src/serralBot.py'])
		return observation, info
	
	def render(self):
		pass

	def close(self):
		pass
