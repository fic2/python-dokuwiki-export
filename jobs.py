
from aggregate import *
import sys
import wikiconfig
import logging
import datetime
from outbuffer import PageBuffer
import metagenerate
import actionitems


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
		res = dw.putpage(doc, self.outpage)
		# print(res)
		# locks = dw.lockpage(self.outpage)
		# logging.info("Locks: %s" % locks)
		return res
		
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


class UpdateActionItems(Job):
	def __init__(self, outpage, namespace = ':ficontent:', exceptions = []):
		Job.__init__(self)
		self.outpage = outpage
		self.namespace = namespace
		self.exceptions = exceptions
	
	def summary(self):
		return "Updating action items of namespace %s" % self.namespace
	
	def required(self):
		return True

	def perform(self, dw):
		actionitems.updateactionitems(dw, self.outpage, self.namespace, self.exceptions)
		return True

	def responsible(self, dw):
		return 'DFKI-Stefan'


class JobFactory(object):
	jobs = {}
	
	def __init__(self):
		pass
		
	def create_job(self, jtype, params):
		jtype = jtype.lower()
		
		if jtype not in self.jobs:
			return None
		
		jclass = self.jobs[jtype]
		
		try:
			job = jclass(**params)
		except Exception as e:
			logging.error("Unable to create job instance - exception occurred!\n%s" % e)
			job = None
		
		return job

	@classmethod
	def register_job(self, jclass):
		self.jobs[jclass.__name__.lower()] = jclass

# jobs = [
	# MetaProcessing(":FIcontent:private:meta:", ":FIcontent:private:meta:generated"),
	# Aggregation(":ficontent:private:deliverables:d65:toc", ":ficontent:private:deliverables:d65:"),
	# Aggregation(":ficontent:private:deliverables:d42:toc", ":ficontent:private:deliverables:d42:", "stefan", False),
	# Aggregation(":ficontent:private:deliverables:d331:toc", ":ficontent:private:deliverables:d331:", "stefan_go")
# ]

# jobslog = ":ficontent:private:wikijobs.log"


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


def loadjobfile(jobfile):
	logging.info("Loading job file %s ..." % jobfile)

	try:
		import json
		with open(jobfile, 'r') as cf:
			jobdata = json.load(cf)
		return jobdata
	except Exception as e:
		logging.error("Unable to load job file - exception occurred!\n%s" % e)

	return None


def createjobs(jobdata):
	if jobdata is None:
		return []

	jobs = []
	f = JobFactory()
	
	for jname, jdata in jobdata["jobs"].items():
		# print(jname)
		# print(jdata)
		if specificjobs is not None:
			if jname.lower() not in specificjobs:
				continue
		
		j = f.create_job(jdata["job"], jdata["params"])
		
		if j is None:
			logging.error("Unable to queue job '%s'." % jname)
			continue
		
		jobs.append(j)

	return jobs


def executejobs(jobs, jobsuccess = None):
	overallsuccess = True
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
		
		if jobsuccess is not None:
			jobsuccess[j] = success
			
		overallsuccess &= success

		if not success:
			logging.error("JOB %d of %d: Aborted!" % (p, n))
			person = j.responsible(dw)
			if person is not None:
				logging.info("Notify %s about failed JOB %d" % (person, p))


def broadcastfailedjobs(failedjobs, dw):
	import notification
	
	# notifier = notification.MetaNotifier(dw, ':ficontent:private:meta:')
	notifier = notification.UserFileNotifier(wikiconfig.userfile)
	
	subject = 'Job failed: %s'
	message = '\n'.join([
		'Hello %s,'
		'',
		'your Job "%s" has failed during last execution.',
		'Please refer to the log at %s for errors and fix them as soon as possible.' % jobslog,
		'',
		'If you got stuck, please contact Stefan (stefan.lemme@dfki.de) or Dirk (dirk.krause@pixelpark.de).',
		'',
		'Best,'
		'\tdokuwikibot'
	])

	for fj in failedJobs:
		person = fj.responsible(dw)
		if person is None:
			person = 'DFKI-Stefan'
		summary = fj.summary()
		notifier.notify(
			person,
			subject % summary,
			message % (person, summary)
		)



if __name__ == "__main__":

	JobFactory.register_job(Aggregation)
	JobFactory.register_job(MetaProcessing)
	JobFactory.register_job(UpdateActionItems)
	
	if len(sys.argv) > 1:
		jobdata = loadjobfile(sys.argv[1])
			
	# print(jobdata)
	if len(sys.argv) > 2:
		specificjobs = [job.lower() for job in sys.argv[2:]]
	else:
		specificjobs = None


	if jobdata is not None:
		jobslog = jobdata["log"]
	else:
		jobslog = None

	
	jobs = createjobs(jobdata)
	
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

	jobsuccess = {}
	
	try:
		overallsuccess = executejobs(jobs, jobsuccess)
	except Exception as e:
		logging.error("Exception occured!\n%s" % e)

	logging.info("All done.")

	log << ""
	log << "</code>"
	log << ""

	log.flush()

	if not overallsuccess:
		failedJobs = [j for j in jobs if not ((j in jobsuccess) and (jobsuccess[j]))]
		print(failedJobs)
		broadcastfailedjobs(failedJobs, dw)
