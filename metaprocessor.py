
from metagrammar import *


# TODO: rename to MetaAdapter
class MetaData(object):
	def __init__(self, partners, warning = print, error = print):
		# self.ge = {}
		# self.se = {}
		# self.loc = {}
		# self.app = {}
		self.partners = partners
		self.ids = set()
		self.entities = {}
		
		self.warning = warning
		self.error = error
		
		# self.insert_default(self.se, SE, "Unknown Specific/Generic Enabler")
		# self.insert_default(self.app, APP, "Unknown Application")
		# self.insert_default(self.loc, LOC, "Unknown Deployment Location")

	def add_id(self, id):
		if id in self.ids:
			return True
		self.ids.add(id)
		return False
	
	def map(self, stmt, entity):
		self.entities[stmt.get_identifier()] = entity
		for id in stmt.get_aliases():
			self.entities[id] = entity
		
	def find(self, id):
		return self.entities[id] if id in self.entities else None
	


		# def location(self, id):
		# if id in self.loc:
			# return self.loc[id]
		# return None
		
	# def contact(self, id):
		# return self.partners.get_person(id)
		
		
	# def insert_default(self, map, grammar, name):
		# g = grammar()
		# g.identifier = name
		# g.aliases = []
		# g.entity = grammar.__name__
		# map[name] = g

		

class MetaProcessor:
	def __init__(self, data):
		self.data = data
	
	def process(self, metadoc):
		# meta = '\n'.join(doc)
		
		p = MetaStructureGrammar.parser(self.data)
		try:
			result = p.parse_text(metadoc, reset=True, bol=True, eof=True)
				
			if len(p.remainder()):
				self.data.error("Unable to parse: %s ..." % p.remainder()[:60])
				return None
				
			# print()
			# print(p.remainder())
			
			return result

		except (ParseError, MetaError) as e:
			self.data.error('Parsing failed!')
			self.data.error(str(e))
			return None
		pass

	
	# def get_stmts(self, meta_ast, stmt):
		# return meta_ast.find_all(stmt)
		
	# def get_referenced_stmt(self, meta_ast, stmt):
		# TODO: use find and 
		# return None
		
	