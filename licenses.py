
from jsonutils import Values
import logging


class Licenses(Values):
	def __init__(self, templates):
		Values.__init__(self, templates)
		
		
	def process(self, license):
		if license is None:
			logging.warning("No license information available!")
			return license
		
		if 'template' not in license:
			return license
		
		template = self.get('/' + license['template'])
		if template is None:
			logging.warning("Invalid license template %s" % template)
			return license
		
		ovrlic = license
		license = dict(template)
		for k, v in ovrlic.items():
			license[k] = v
		
		return license
