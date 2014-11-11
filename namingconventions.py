
import re


class NamingConventions(object):
	def __init__(self, dw, se_spec):
		self.dw = dw
		self.name = se_spec.get('name')
		self.spec = se_spec
		self.group = None
	
	def fullname(self):
		return self.name
	
	def specpage(self):
		page = ':' + ':'.join(self.wikipath()) + ':meta'
		# TODO: check existence of the page
		return page
		
	def nameparts(self):
		name = self.name.lower()
		nameparts = name.split(' - ')
		return [re.sub(r'[^a-z0-9]+', '', name) for name in nameparts]
		
	def roadmap(self):
		platforms = self.spec.get('platforms')
		if len(platforms) == 1:
			return platforms[0]
		elif len(platforms) > 1:
			return 'common'
		else:
			return None

	def wikipath(self):
		return ['ficontent', self.roadmap(), 'enabler'] + self.nameparts()
		
	def wikinamespace(self):
		return ':' + ':'.join(self.wikipath()) + ':'
		
	def wikipage(self):
		page = self.wikinamespace() + 'start'
		# TODO: check existence of the page
		return page
	
	def devguide(self):
		page = self.wikinamespace() + 'developerguide'
		# TODO: check existence of the page
		return page
	
	def catalogid(self):
		name = self.name.lower()
		name = re.sub(r'[\s\-]+', '-', name)
		return name
		
	def catalogurl(self):
		url = 'http://mediafi.org/?portfolio=' + self.catalogid()
		return url
		
	def tncurl(self):
		return self.catalogurl() + '#tab-terms-conditions'
		
	def group(self):
		nameparts = self.nameparts()
		if len(nameparts) > 1:
			return nameparts[0]
		return None
	
	def platforms(self):
		return self.spec.get('platforms')
