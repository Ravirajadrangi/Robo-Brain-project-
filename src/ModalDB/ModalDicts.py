'''
Module: ModalDicts
==================

Description:
------------
	
	Facilitates access to items in different modes of memory

Example Usage:
--------------
	
	disk_dict = DiskDict(mongo_doc)
	memory_dict = DiskDict(mongo_doc)
	...
	etc

##################
Jay Hack
Fall 2014
jhack@stanford.edu
##################
'''
import os

class ModalDict(object):
	"""
		Base class for DiskDict, MemoryDict, DynamicDict
	"""

	def __init__(self, mongo_doc, datatype_schema):
		"""
			initializes self.keys, self.metadata, self.data
		"""
		assert not self.mode is None
		self.mongo_doc 	= mongo_doc
		self.keys 		= set([k for k,v in datatype_schema.items() if v['mode'] == self.mode])
		self.metadata 	= {k:mongo_doc['items'][k] for k in self.keys}
		self.data 		= {k:None for k in self.keys}


	def update_item_metadata(self):
		"""
			updates metadata on items. Override
		"""
		for k in self.keys:
			self.metadata[k]['present'] = self.item_present(k)


	def item_present(self, key):
		"""
			returns true if the named item present. Override.
		"""
		raise NotImplementedError


	def present_items(self):
		"""
			returns names of items that are present.
		"""
		self.update_item_metadata()
		return set([k for k in self.keys if self.metadata[k]['present']])


	def absent_items(self):
		"""
			returns set of items that are not present.
		"""
		return self.keys.difference(self.present_items())


	def __contains__(self, key):
		return key in self.keys


	def detect_keyerror(self, key):
		if not key in self:
			raise KeyError("No such item: %s" % key)


	def __getitem__(self, key):
		self.detect_keyerror(key)
		return self.get_item(key)


	def get_item(self, key):
		raise NotImplementedError


	def __setitem__(self, key, value):
		self.detect_keyerror(key)
		self.metadata[key]['present'] = True
		return self.set_item(key, value)


	def set_item(self, key, value):
		raise NotImplementedError


	def __delitem__(self, key):
		self.detect_keyerror(key)
		self.metadata[key]['present'] = False
		self.del_item(key)


	def del_item(self, key):
		raise NotImplementedError







################################################################################
####################[ MemoryDict ]##############################################
################################################################################

class MemoryDict(ModalDict):
	"""
		Class: MemoryDict
		-----------------
		Facilitates access to items in memory (MongoDB)
	"""
	mode = 'memory'

	def __init__(self, mongo_doc, datatype_schema):
		super(MemoryDict, self).__init__(mongo_doc, datatype_schema)
		self.data = {k:mongo_doc['items'][k]['data'] for k in self.keys}
		self.update_item_metadata()


	def item_present(self, key):
		return not self[key] is None


	def get_item(self, key):
		self.detect_keyerror(key)
		return self.data[key]


	def set_item(self, key, value):
		self.data[key] = value


	def del_item(self, key):
		self.data[key] = None





################################################################################
####################[ DiskDict ]################################################
################################################################################

class DiskDict(ModalDict):
	"""
		Class: DiskDict
		---------------
		Facilitates access to items on disk
	"""
	mode = 'disk'

	def __init__(self, mongo_doc, datatype_schema):
		super(DiskDict, self).__init__(mongo_doc, datatype_schema)

		root = mongo_doc['root']
		items = datatype_schema

		self.load_funcs = {k:items[k]['load_func'] for k in self.keys}
		self.save_funcs = {k:items[k]['save_func'] for k in self.keys}
		self.paths 		= {k:os.path.join(root, items[k]['filename']) for k in self.keys}
		self.data 		= {k:None for k in self.keys}

		self.update_item_metadata()


	def item_present(self, key):
		"""
			returns true if the item present on disk 
		"""
		return os.path.exists(self.paths[key])


	def load_item(self, key):
		"""
			loads the specified item 
		"""
		assert key in self
		self.data[key] = self.load_funcs[key](self.paths[key])


	def save_item(self, key):
		"""
			saves the specified item 
		"""
		assert key in self
		assert not self.save_funcs[key] is None
		self.save_funcs[key](self.data[key], self.paths[key])


	def get_item(self, key):
		"""
			returns named item; loads from disk if necessary
		"""
		if self.data[key] is None and self.item_present(key):
			self.load_item(key)
		return self.data[key]


	def set_item(self, key, value):
		"""
			sets named item; saves to disk immediately
		"""
		self.data[key] = value
		self.save_item(key)


	def del_item(self, key):
		"""
			sets self.data[key] to None, removes item 
			from disk
		"""
		del self.data[key]
		os.remove(self.paths[key])
		self.data[key] = None









