
import re
from wiki import *
import logging


def increment_numbering(numbers, level):
	while len(numbers) < level:
		numbers.append(0)
	while len(numbers) > level:
		numbers.pop()
		
	numbers[level-1] += 1

def pretty_numbering(numbers):
	s = ""
	for n in numbers:
		s += str(n) + "."
	return s[:-1]

def resolve_link(dw, ns, match):
	page, section, text = dw.parselink(match.group())
	if page.startswith('http'):
		fullname = page
	else:
		fullname = dw.resolve(page, ns)
	return dw.buildlink(fullname, section, text)
	

rx_tocline = re.compile(r"^([ ]{2,})\- (\[\[[^\|\]]+(\|[^\]]+)?\]\])")

def aggregate(dw, toc, tocns, showwikiurl = False):
	newdoc = []
	chapters = {}
	numbering = [0]
	
	pageheading = False
	
	for tocline in toc:
		result = rx_tocline.match(tocline)
		# print line
		# print result
		
		if result is None:
			continue
		
		# print result.groups()
		
		indent = result.group(1)
		link = result.group(2)
		
		level = int(len(indent) / 2)
		page, section, heading = dw.parselink(link)
		if section is not None:
			logging.warning("Ignoring section attribute of ToC. Including complete page %s instead." % page)
		# print level, page, "(", heading, ")"
		
		# append page with level offset
		
		pagens = []
		content = dw.getpage(page, tocns, pagens)
		# print(pagens)
		
		# resolve page to full page name
		page = dw.resolve(page, pagens)
		
		if content is None:
			if heading is None:
				heading = "Missing page " + page
			content = []
		
		if heading is not None:
			increment_numbering(numbering, level)
			target = page
			chapters[target.lower()] = (numbering[:], heading)

			# logging.info("%s - %s" % (pretty_numbering(numbering), heading))

			newdoc.append(dw.heading(level, heading))
			# newdoc.append("\n")
			level += 1
			
			if showwikiurl:
				url = dw.pageurl(page)
				# print(url)
				newdoc.append("__ %s __\n" % url)
				# newdoc.append("\n")
		else:
			pageheading = True
			
		for line in content:
			result = wiki.rx_heading.match(line)
			if result is None:
				# resolve link namespaces
				resline = wiki.rx_link.sub(lambda m: resolve_link(dw, pagens, m), line)
				newdoc.append(resline)
				continue
				
			indent1 = len(result.group(1))
			indent2 = len(result.group(3))
			if indent1 != indent2:
				logging.warning("Warning! Invalid heading.")
				
			subleveloffset = 6 - indent1
			
			sublevel = level + subleveloffset
			subheading = result.group(2)
			
			increment_numbering(numbering, sublevel)
			target = page + "#" + dw.target(subheading)
			chapters[target.lower()] = (numbering[:], subheading)
			if pageheading:
				chapters[page.lower()] = (numbering[:], subheading)
				pageheading = False
				

			# logging.info("%s - %s" % (pretty_numbering(numbering), subheading))
			# print pretty_numbering(numbering), " - ", subheading
			
			newdoc.append(dw.heading(sublevel, subheading))

			if showwikiurl:
				url = dw.pageurl(page, heading=subheading)
				# print(url)
				newdoc.append("")
				newdoc.append("__ %s __\n" % url)
				# newdoc.append("\n")

		newdoc.append("\n")
		# newdoc.append("\n")
		
	return newdoc, chapters
		


if __name__ == "__main__":
	import sys
	import wikiconfig

	tocpage = ":ficontent:private:deliverables:d65:toc"
	if len(sys.argv) > 1:
		tocpage = sys.argv[1]

	outpage = ":ficontent:private:deliverables:d65:"
	if len(sys.argv) > 2:
		outpage = sys.argv[2]

	embedwikilinks = True

	logging.info("Connecting to remote DokuWiki at %s" % wikiconfig.url)
	# dw = wiki.DokuWikiLocal(url, 'pages', 'media')
	dw = DokuWikiRemote(wikiconfig.url, wikiconfig.user, wikiconfig.passwd)
	
	logging.info("Loading table of contents %s ..." % tocpage)
	# toc = getpage(tocpage)
	tocns = []
	toc = dw.getpage(tocpage, pagens = tocns)
	if toc is None:
		logging.fatal("Table of contents %s not found." % tocpage)
		
	logging.info("Aggregating pages ...")
	doc, chapters = aggregate(dw, toc, tocns, embedwikilinks)

	logging.info("Flushing generated content to page %s ..." % outpage)
	dw.putpage(doc, outpage)

	if len(sys.argv) > 3:
		outfile = sys.argv[3]
		logging.info("Writing aggregated file %s ..." % outfile)

		with open(outfile, "w") as fo:
			fo.writelines(doc)


	if len(sys.argv) > 4:
		chapterfile = sys.argv[4]
		logging.info("Writing chapter file %s ..." % chapterfile)

		import json
		with open(chapterfile, 'w') as cf:
			json.dump(chapters, cf, sort_keys = False, indent = 4)

	logging.info("Finished")
