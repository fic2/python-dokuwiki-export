
from collections import deque
import logging
import json


class ValuesEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Values):
            # build dict using comprehension
            return {prop: value for (prop, value) in obj.items()}

        return json.JSONEncoder.default(self, obj)

def json_serialize(data, cls=None):
	try:
		text = json.dumps(data, indent=4, cls=cls)
	except Exception as e:
		logging.warning("Exception occured: %s" % e)
		text = None
	return text

def json_deserialize(text):
	try:
		data = json.loads(text)
	except Exception as e:
		data = None
	return data


def split_path(path):
	return deque(path.strip('/').split('/'))

def json_get(json_data, path):
	parts = split_path(path)
	obj = json_data
	while len(parts) > 0:
		if obj is None:
			return None
		prop = parts.popleft()
		if prop not in obj:
			return None
		obj = obj[prop]
	return obj

def json_set(json_data, path, data):
	parts = split_path(path)
	obj = json_data
	while len(parts) > 1:
		prop = parts.popleft()
		if prop not in obj:
			obj[prop] = {}
		obj = obj[prop]
	obj[parts[-1]] = data


class Values(object):
	def __init__(self, values = None):
		self.internal_values = {} if values is None else values

	def get(self, path):
		obj = json_get(self.internal_values, path)
		if isinstance(obj, dict):
			obj = Values(obj)
		return obj

	def set(self, path, data):
		if isinstance(data, Values):
			data = data.internal_values
		json_set(self.internal_values, path, data)

	def __iter__(self):
		for item in self.internal_values:
			yield item
	
	def items(self):
		# return self.values.items()
		for k in self:
			yield (k, self.get(k))
	
	def keys(self):
		return self.internal_values.keys()
	
	def values(self):
		return self.internal_values.values()
		
	def clone(self):
		return Values(dict(self.internal_values))
	
	def __len__(self):
		return self.internal_values.__len__()
	
	def __getitem__(self, idx):
		return self.get(idx)

	def __setitem__(self, idx, val):
		return self.set(idx, val)

	# def __str__(self):
		# return str(self.values)
	
	def serialize(self):
		return json_serialize(self, cls=ValuesEncoder)
