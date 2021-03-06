
import sys

# overwrite to redirect output to file for instance
out = sys.stdout
verbose = False
cliplines = True

def split_len(seq, length): 
    return [seq[i:i+length] for i in range(0, len(seq), length)] 

def output(intro, text):
	lines = text.split('\n')
	n = len(intro)
	m = 79 - n
	
	if cliplines:
		clippedlines = []
		for l in lines:
			clippedlines.extend(split_len(l, m))
	else:
		clippedlines = lines
	
	out.write(intro)
	out.write(clippedlines[0])
	out.write('\n')
	for l in clippedlines[1:]:
		out.write(" "*n)
		out.write(l)
		out.write('\n')
	
def seperator():
	out.write('\n')

def debug(text):
	if verbose:
		output("[Debug]   ", text)
	
def info(text):
	output("[Info]    ", text)
	
def warning(text):
	output("[Warning] ", text)
	
def error(text):
	output("[Error]   ", text)
	

class FatalError(Exception):
	pass

def fatal(text):
	output("[Fatal]   ", text)
	raise FatalError()
