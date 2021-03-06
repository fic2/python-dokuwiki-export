
from presenter import PresenterBase
import re
# from visitor import ExperimentsVisitor, DependencyVisitor


class SEGraphPresenter(PresenterBase):
	def __init__(self, se, nice = lambda item: item):
		PresenterBase.__init__(self)
		self.se = se
		self.nice = nice
		# self.relations = relations
		
		# self.ev = ExperimentsVisitor(site = self.site, scenario = self.scenario)
		# self.dv = DependencyVisitor(self.relations)

		self.design = {
			'labeljust': 'left',
			'labelloc': 'top',
			'fontsize': 8,
			'APP_fillcolor': '#fff2cc',
			'APP_color': '#efbc00',
			'SE_fillcolor': '#deebf7',
			'SE_color': '#4a76ca',
			'GE_fillcolor': '#e2f0d9',
			'GE_color': '#548235',
			'EDGE_tailport': 'e',
			'EDGE_headport': 'w',
			'EDGE_color': '#000000',
			'EDGE_USES_style': 'solid',
			'EDGE_WILL_USE_style': 'dashed',
			'EDGE_MAY_USE_style': 'dashed',
			'EDGE_MAY_USE_color': '#838383',
			'splines': 'line'
		}
		self.indent = '  '
		
	def present(self, meta):
		self.relations = meta.find_relations(self.se)
		self.top = [rel[0] for rel in self.relations if rel[1] == self.se]
		self.bottom = [rel[1] for rel in self.relations if rel[0] == self.se]
		self.nodes = self.top + self.bottom + [self.se]
	
	def dump_node(self, node):
		stripid = self.cleanid(str(node))
		# print("%s -> %s" % (node, stripid))
		self.nodemap[node] = stripid
		self.dump_line('%s [label = "%s"];' % (stripid, self.nice(node)), indent=2)
	
	def dump_edge(self, node1, node2, edge):
		# App10913 -> GhiGE;
		id1 = self.nodemap[node1]
		id2 = self.nodemap[node2]
		# TODO: select appearance depending on edge
		sedge = edge.replace(' ', '_')
		self.dump_line('%s:%s -> %s:%s [style = %s, color = "%s", fontsize = %s, fontcolor = "%s"];' % (
				id1,
				self.lookup_design('tailport', ['EDGE_%s' % sedge, 'EDGE']),
				id2,
				self.lookup_design('headport', ['EDGE_%s' % sedge, 'EDGE']),
				self.lookup_design('style', ['EDGE_%s' % sedge, 'EDGE']),
				self.lookup_design('color', ['EDGE_%s' % sedge, 'EDGE']),
				self.lookup_design('fontsize', ['EDGE_%s' % sedge, 'EDGE']),
				self.lookup_design('color', ['EDGE_%s' % sedge, 'EDGE'])
			), indent=1)
		
	def dump_line(self, line, indent = 0):
		self.out.write(self.indent * indent + line)
		
	def cleanid(self, id):
		return re.sub(r'[^a-zA-Z_]+', '_', id)
		
	def lookup_design(self, var, prefix):
		if not type(prefix) is list:
			prefix = [prefix]
		val = ['%s_%s' % (p, var) for p in prefix]
		for v in val:
			if v in self.design:
				return self.design[v]
		if var in self.design:
			return self.design[var]
		return None

	def dump_cluster(self, label, nodes, type):
		self.dump_line('subgraph cluster_%s {' % type, indent=1)
		self.dump_line('rank = same;', indent=2)
		self.dump_line('style = filled;', indent=2)
		self.dump_line('color = "%s";' % self.lookup_design('color', type), indent=2)
		self.dump_line('label = "%s";' % label, indent=2)
		self.dump_line('labeljust = %s;' % self.lookup_design('labeljust', type), indent=2)
		self.dump_line('labelloc = %s;' % self.lookup_design('labelloc', type), indent=2)
		self.dump_line('node [fillcolor = "%s"];' % self.lookup_design('fillcolor', type), indent=2)
		self.dump_line('')
		for n in nodes:
			self.dump_node(n)
		# self.dump_line('cluster_%s_DUMMY [style = invis, shape = point]' % type, indent=2)
		self.dump_line('};', indent=1)
		self.dump_line('')

	def dump(self, out):
		self.nodemap = {}
		self.out = out
		
		self.dump_line('<graphviz dot center>')
		self.dump_line('digraph se_%s {' % self.cleanid(self.se.get_name()))
		self.dump_line('rankdir = LR;', indent=1)
		self.dump_line('compound = true;', indent=1)
		self.dump_line('outputorder = edgesfirst;', indent=2)
		self.dump_line('fontsize = %s;' % self.design['fontsize'], indent=1)
		self.dump_line('splines = %s;' % self.design['splines'], indent=1)
		self.dump_line('node [shape = box fontsize=%s style=filled fillcolor=grey];' % self.design['fontsize'], indent=1)
		self.dump_line('')
		
		self.dump_cluster('Applications', self.top, 'APP')
		self.dump_cluster('Specific Enabler', [self.se], 'SE')
		self.dump_cluster('Generic Enablers', self.bottom, 'GE')
		
		for e in self.relations:
			self.dump_edge(e[0], e[1], e[2])
		
		# self.dump_line('cluster_APP_DUMMY -> cluster_SE_DUMMY [style = invis];')
		# self.dump_line('cluster_SE_DUMMY -> cluster_GE_DUMMY [style = invis];')
		
		self.dump_line('}')
		self.dump_line('</graphviz>')
		
		self.dump_fixmes(out)
		
		self.out = None
