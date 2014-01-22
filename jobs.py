
from aggregate import *
import sys
import wikiconfig
import logging
import datetime
from outbuffer import PageBuffer
import metagenerate


class Job(object):
	def __init__(self):
		pass
		
	def summary(self):
		return "Unknown Job"

	def required(self):
		return False
		
	def perform(self, dw):
		return False
		
	def responsible(self, dw):
		return None
		

class Aggregation(Job):
	def __init__(self, tocpage, outpage, editor = None, embedwikilinks = True):
		Job.__init__(self)
		self.tocpage = tocpage
		self.outpage = outpage
		self.embedwikilinks = embedwikilinks
		self.editor = editor
	
	def summary(self):
		return "Aggregating %s" % self.tocpage
	
	def required(self):
		return True

	def perform(self, dw):
		logging.info("Loading table of contents %s ..." % self.tocpage)
		tocns = []
		toc = dw.getpage(self.tocpage, pagens = tocns)
		if toc is None:
			logging.error("Table of contents %s not found." % self.tocpage)
			return False
			
		logging.info("Aggregating pages ...")
		doc, chapters = aggregate(dw, toc, tocns, self.embedwikilinks)

		logging.info("Flushing generated content to page %s ..." % self.outpage)
		dw.putpage(doc, self.outpage)
		locks = dw.lockpage(self.outpage)
		# logging.info("Locks: %s" % locks)
		return True
		
	def responsible(self, dw):
		return self.editor

		
class MetaProcessing(Job):
	def __init__(self, metapage, outpage):
		Job.__init__(self)
		self.metapage = metapage
		self.outpage = outpage
	
	def summary(self):
		return "Processing Meta Structure %s" % self.metapage
	
	def required(self):
		return True

	def perform(self, dw):
		logging.info("Loading page of meta structure %s ..." % self.metapage)
		metadoc = dw.getpage(self.metapage)
		if metadoc is None:
			logging.fatal("Meta structure %s not found." % self.metapage)

		meta, data = metagenerate.process_meta(metadoc)
		if meta is None:
			logging.fatal("Invalid meta structure %s" % self.metapage)
		
		metagenerate.generate_page(dw, self.outpage, meta, data)
		return True

	def responsible(self, dw):
		# TODO: retrieve last author of metapage
		info = dw.pageinfo(self.metapage)
		return info['author']


jobs = [
	MetaProcessing(":FIcontent:private:meta:", ":FIcontent:private:meta:generated"),
	Aggregation(":ficontent:private:deliverables:d65:toc", ":ficontent:private:deliverables:d65:"),
	Aggregation(":ficontent:private:deliverables:d42:toc", ":ficontent:private:deliverables:d42:", "stefan", False),
	Aggregation(":ficontent:private:deliverables:d331:toc", ":ficontent:private:deliverables:d331:", "stefan_go")
]

jobslog = ":ficontent:private:wikijobs.log"

class PageLog(PageBuffer):
	def __init__(self, wiki, page):
		PageBuffer.__init__(self, wiki, page)
		self.current = ""

	def write(self, text):
		lines = text.split('\n')
		self.current += lines[0]
		if len(lines) == 1:
			return
		
		for l in lines[1:-1]:
			PageBuffer.write(self, l)
		
		PageBuffer.write(self, self.current)
		self.current = lines[-1]
	
	def flush(self):
		PageBuffer.write(self, self.current)
		self.current = ""
		PageBuffer.flush(self)


if __name__ == "__main__":
	dw = DokuWikiRemote(wikiconfig.url, wikiconfig.user, wikiconfig.passwd)
	log = PageLog(dw, jobslog)
	logging.out = log
	logging.cliplines = False
	
	log << dw.heading(1, "Log of dokuwikibot's jobs")
	log << ""
	log << "Latest run at %s" % datetime.datetime.now()
	log << ""
	log << "<code>"

	logging.info("Connected to remote DokuWiki at %s" % wikiconfig.url)
	
	notify = []
	
	try:
		n = len(jobs)
		for i, j in enumerate(jobs):
			p = i+1
			logging.info("JOB %d of %d: %s" % (p, n, j.summary()))
			
			if not j.required():
				logging.info("Skipped!")
				continue
				
			try:
				success = j.perform(dw)
			except logging.FatalError:
				success = False
				
			if not success:
				logging.error("JOB %d of %d: Aborted!" % (p, n))
				person = j.responsible(dw)
				logging.info("Notify %s about failed JOB %d" % (person, p))
				if person is not None:
					notify.append(person)

	except Exception as e:
		logging.error("Exception occured!\n%s" % e)
		notify.append("stefan")

	logging.info("All done.")

	log << ""
	log << "</code>"
	log << ""

	log.flush()

	# TODO: notify responsible persons
	# import notification
	
	# for p in notify:
		# notification.notify(p)
		

