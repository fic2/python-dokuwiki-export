
import sys

# overwrite to redirect output to file for instance
out = sys.stdout
verbose = False

def output(intro, text):
	lines = text.split('\n')
	out.write(intro)
	out.write(lines[0])
	out.write('\n')
	for l in lines[1:]:
		out.write(" "*len(intro))
		out.write(l)
		out.write('\n')
	
def debug(text):
	if verbose:
		output("[Debug]  ", text)
	
def info(text):
	output("[Info]   ", text)
	
def warning(text):
	output("[Warning]", text)
	
def error(text):
	output("[Error]  ", text)
	
class FatalError(Exception):
	pass

def fatal(text):
	output("[Fatal]  ", text)
	raise FatalError()
