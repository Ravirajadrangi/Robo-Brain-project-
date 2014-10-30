####################
# Class: Video
# ------------
# used to contain all information relevant to a single video
# contains the frames data in a pandas dataframe
####################
import os
import itertools
import random
import numpy as np
import pandas as pd

from DataObject import DataObject
from Frame import Frame

class Video(DataObject):
	"""
		Ideal Usage:
		------------

		# Frame retrieval
		frame = video.get_random_frame()
		frame = video.get_frame(0)
		for frame in video.iter_frames():
			...
	"""

	def __init__(self, db, mongo_dict, root):
		"""
			video_dict: dict containing mongodb description of video
			schema: dict describing how frames are represented in DB
			frames: list of frames
		"""
		super(Video, self).__init__(db, mongo_dict, root)

		#=====[ build a faster index of frames	]=====
		self.frames_df = self.get_frames_df(mongo_dict)





	################################################################################
	####################[ Frame Data	]###########################################
	################################################################################

	def get_frames_df(self, mongo_dict):
		"""
			sets self.frames_df to be a more complete index of 
			which frames, including which has what items already

		"""
		rows = []
		for frame_dict in mongo_dict['frames']:
			frame = Frame(self.db, frame_dict, frame_dict['root_dir'])
			d = {k:frame.item_exists(k) for k in frame.keys() if not k == '_id'}
			d['_id'] = frame_dict['_id']
			d['root'] = frame_dict['root_dir']
			rows.append(d)
		df = pd.DataFrame(rows)
		df.index = df['_id'].astype(int)
		df.drop('_id', axis=1, inplace=True)
		df.sort(inplace=True)
		return df


	def __len__(self):
		return len(self.frames_df)


	def get_frame(self, t):
		"""
			returns Frame object occurring at timestep t, loaded
			returns None if t is too large. 
			Note: t is 1-indexed
		"""
		if t > len(self):
			return None
		else:
			row = self.frames_df.loc[t]
			return Frame(self.db, self.mongo_dict['frames'][t], self.mongo_dict['frames'][t]['root_dir'])


	def get_random_frame(self):
		"""
			returns random Frame object from this video, with the 
			requirement that it's 'processed'
		"""
		return self.get_frame(random.choice(self.frames_df.index))


	def iter_frames(self, stepsize=1, verbose=False):
		"""
			iterates over all frames
			stepsize: describes how to subsample frames.
				i.e. stepsize=2 means every other frame is returned 
		"""
		for i in range(1, len(self)+1):
			f = self.get_frame(i)
			if verbose:
				print '	', f
			yield f
