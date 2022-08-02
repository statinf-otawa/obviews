#!/usr/bin/env python3
 
from functools import partial
import argparse
import datetime
import glob
import io
import json
import mimetypes
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import urllib.parse
import webbrowser
import xml.etree.ElementTree as ET

from http import server
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread


######### global state #########
HOST = '127.0.0.1'
PORT = 8000
DATA_DIR = None
APPLICATION = None
TASK = None
SOURCE_MANAGER = None
STATS = None
DOT_PATH = None


######### Convenient functions #########

def error(msg):
	sys.stderr.write("ERROR: %s\n" % msg)

def fatal(msg):
	error(msg)
	exit(1)

def norm(name):
	return name.replace("-", "_")


class StringBuffer():
	def __init__(self, init = ""):
		self.str = init
	
	def write(self, value):
		self.str += value
	
	def make(self):
		return self.to_utf8()

	def to_utf8(self):
		return self.str.encode("utf-8")

	def to_str(self):
		return self.str


def escape_dot(s):
	"""Escape a string to be compatible with dot."""
	return s. \
		replace("{", "\\{").\
		replace("}", "\\}").\
		replace("\n", "").\
		replace("\r", "")


def escape_html(s):
	"""Escape a string to be compatible with HTML text."""
	return s. \
		replace("<", "&lt;"). \
		replace(">", "&gt;"). \
		replace("&", "&amp;"). \
		replace(" ", "&nbsp;"). \
		replace("\t", "&nbsp;&nbsp;&nbsp;&nbsp;")



######## Source management #########


class SyntaxColorizer:
	
	def colorize(self, line, out):
		out.write(line)

NULL_COLORIZER = SyntaxColorizer()


class CColorizer:
	
	def __init__(self):
		self.re = re.compile("(^#[a-z]+)|" +
			"(if|else|for|while|switch|case|break|continue|do|return)|" +
			"(typedef|bool|int|char|float|double|short|long|signed|unsigned|struct|union|enum)|" +
			"(//.*)|" +
			"(/\*\*+/)|" + 
			"(/\*(\*[^/]|[^\*])*\*/)|" +
			"([a-zA-Z_0-9]+)")

	def colorize(self, line, out):
		while line:
			m = self.re.search(line)
			if not m:
				out.write(line)
				return
			out.write(line[:m.start()])
			if m.group(1):
				out.write("<font color='orange'><b>%s</b></font>" % m.group(1))
			elif m.group(2):
				out.write("<font color='red'><b>%s</b></font>" % m.group(2))
			elif m.group(3):
				out.write("<b>%s</b>" % m.group(3))
			elif m.group(4) or m.group(5) or m.group(6):
				out.write("<font color='green'><i>%s</i></font>" % m.group())
			else:
				out.write(m.group())
			line = line[m.end():]

SYNTAX_COLS = { ext: CColorizer \
	for ext in ['.c', '.h', '.cpp', '.hpp', '.cc', '.hh'] }


class Source:
	"""Represents a source used in the application."""

	def __init__(self, path):
		self.name = os.path.basename(path)
		self.path = path
		self.lines = list(open(path, "r"))
		try:
			self.colorizer = SYNTAX_COLS[os.path.splitext(self.path)[1]]()
		except KeyError:
			self.colorizer = NULL_COLORIZER

	def gen(self, stat = None):
		"""Generate a source output."""

		# collect statistics if required
		if stat:
			stats = [0] * len(self.lines)
			for g in task.cfgs:
				for b in g.verts:
					if b.type == BLOCK_CODE:
						for (f, l) in b.lines:
							if f == src:
								try:
									stats[l-1] = stats[l-1] + b.get_val(s)
								except IndexError:
									pass

		# generate the table
		out = StringBuffer()
		out.write('<table id="stats">\n')
		out.write(" <tr><th></th><th>source</th><th></th>\n")

		num = 0
		for l in self.lines:
				num = num + 1
				style = ""

				# prepare line
				if l.endswith("\n"):
					l = l[:-1]
				style = ""
				
				# compute indentation
				indent = 0
				while l:
					if l[0] == ' ':
						indent = indent + 8
					elif l[0] == '\t':
						indent = indent + 32
					else:
						break
					l = l[1:]
				if indent:
					style = style + " padding-left: %spt;" % indent

				# display the line
				out.write('<tr><td>%d</td><td class=\"source\"' % num)
				if style:
					out.write(" style=\"%s\"" % style)
				out.write(">")
				self.colorizer.colorize(l, out)
				out.write("</td><td></td>")

		out.write("</tr>\n")
		out.write("</table>\n")
		return out.to_utf8()


class SourceManager:
	"""The source manager manages sources of the processed program."""
	
	def __init__(self, paths = ["."]):
		self.paths = paths
		self.sources = {}

	def find_actual_path(self, path):
		"""Find the actual path to the given source.
		Return None if it cannot be found."""
		if os.path.isabs(path):
			return os.path.isfile(path)
		else:
			for p in self.paths:
				p = os.path.join(p, path)
				if os.path.isfile(p):
					return p
			return None
	
	def find(self, path):
		"""Lookup for a source file. If not already loaded, lookup
		for the source using the lookup paths."""
		try:
			return self.sources[path]
		except KeyError:
			source = None
			path = self.find_actual_path(path)
			if path != None:
				try:
					source = Source(path)
				except OSError:
					pass
			self.sources[path] = source
			return source

	def get_line(self, path, line):
		"""Get the line corresponding to the given source path and line.
		If not found, return None."""
		source = self.find(path)
		if source == None:
			return None
		else:
			try:
				return source.lines[line - 1]
			except IndexError:
				return None


######## Lookup definitions #########

class RGB:
	
	def __init__(self, r, g, b):
		self.val = "#%02x%02x%02x" % (r, g,b)

	def __str__(self):
		return self.val

WHITE = RGB(255, 255, 255)
BLACK = RGB(0, 0, 0)

COLORS = [
	RGB(234,231,255),
	RGB(214,207,255),
	RGB(192,183,255),
	RGB(171,158,255),
	RGB(161,148,250),
	RGB(155,142,245),
	RGB(140,125,237),
	RGB(123,108,227),
	RGB(113,98,221)
]
COLOR_TH = 4

def background(ratio):
	return COLORS[round(ratio * (len(COLORS) - 1))]

def foreground(ratio):
	if ratio * (len(COLORS) - 1) < COLOR_TH:
		return BLACK
	else:
		return WHITE


class Decorator:
	
	def __init__(self, sman = SourceManager()):
		self.sman = sman
	
	def major(self):
		return None

	def start_cfg(self, cfg):
		pass

	def end_cfg(self, cfg):
		pass

	def cfg_label(self, cfg, out):
		pass

	def bb_body(self, bb, out):
		pass

	def bb_attrs(self, bb, out):
		pass

	def bb_source(self, bb, out):
		source = None
		prev_file = None
		prev_line = None
		if bb.lines != []:
			for (f, l) in bb.lines:
				if f != prev_file:
					source = self.sman.find(f)
					prev_line = None
				if source == None or f != prev_file or l-1 != prev_line:
					out.write("<font color='blue'>%s:%d:</font><br align='left'/>" \
						% (escape_html(f), l))
				if source != None:
					source.colorizer.colorize(escape_html(source.lines[l-1]), out)
					out.write("<br align='left'/>")
				prev_file = f
				prev_line = l

	def bb_label(self, b, out):
		pass

NULL_DECORATOR = Decorator()

class BaseDecorator(Decorator):
	
	def __init__(self, main, task, stats):
		Decorator.__init__(self)
		self.main = main
		self.task = task
		self.stats = stats

		# assign maxes
		task.max = Data()
		task.sum = Data()
		for g in task.cfgs:
			g.max = Data()
			g.sum = Data()

		# compute maxes
		for g in task.cfgs:
			for b in g.verts:
				for id in self.stats:
					g.max.set_max(id, b.get_val(id))
					g.sum.add_val(id, b.get_val(id))
			for id in self.stats:
				task.max.set_max(id, g.max.get_val(id))
				task.sum.add_val(id, g.sum.get_val(id))
	
	def major(self):
		return self.main
	
	def bb_label(self, bb, out):
		for id in self.stats:
			val = bb.get_val(id)
			out.write("%s=%d (%3.2f%%)<br/>" % (id, val, val * 100. / self.task.sum.get_val(id)))
	
	def start_cfg(self, cfg):
		self.max = 0
		for b in cfg.verts:
			try:
				v = b.data[self.main]
				if v > self.max:
					self.max = v
			except KeyError:
				pass
		self.max = float(self.max)


class ColorDecorator(BaseDecorator):

	def __init__(self, main, task, stats):
		BaseDecorator.__init__(self, main, task, stats)

	def bb_attrs(self, bb, out):
		if bb.type == BLOCK_CALL:
			val = bb.callee.max.get_val(self.main)
		else:
			val = bb.get_val(self.main)
		ratio = float(val) / self.task.max.get_val(self.main)
		if ratio != 0:
			out.write(",fillcolor=\"%s\",style=\"filled\"" % background(ratio)) 
			out.write(",fontcolor=\"%s\"" % foreground(ratio))


######## Program Descriptions ########

BLOCK_ENTRY = 0
BLOCK_EXIT = 1
BLOCK_CODE = 2
BLOCK_CALL = 3

class Data:
	
	def __init__(self):
		self.data = { }
	
	def set_val(self, id, val):
		self.data[id] = val
	
	def get_val(self, id):
		try:
			r = self.data[id]
			return r
		except KeyError:
			return 0
	
	def set_max(self, id, val):
		if val != 0:
			try:
				self.data[id] = max(self.data[id], val)
			except KeyError:
				self.data[id] = val

	def add_val(self, id, val):
		if val != 0:
			try:
				self.data[id] = self.data[id] + val
			except KeyError:
				self.data[id] = val


class Block(Data):
	
	def __init__(self, type, id):
		Data.__init__(self)
		self.type = type
		self.id = id
		self.next = []
		self.pred = []
		self.lines = []
	
	def collect(self, id, val, addr, size):
		return 0
	

class BasicBlock(Block):
	
	def __init__(self, id, base, size, lines = []):
		Block.__init__(self, BLOCK_CODE, id)
		self.base = base
		self.size = size
		self.lines = lines

	def collect(self, id, val, addr, size):
		if self.base <= addr and addr < self.base + self.size:
			self.add_val(id, val)


class CallBlock(Block):

	def __init__(self, id, callee):
		Block.__init__(self, BLOCK_CALL, id)
		self.callee = callee


class Edge(Data):
	
	def __init__(self, src, snk):
		Data.__init__(self)
		self.src = src
		src.next.append(self)
		self.snk = snk
		snk.prev = self


class CFG:
	
	def __init__(self, id, label, ctx):
		self.id = id
		self.label = label
		self.ctx = ctx
		self.verts = []
		self.entry = None
		self.exit = None
		self.data = { }
	
	def add(self, block):
		self.verts.append(block)

	def collect(self, id, val, addr, size, ctx):
		if ctx == self.ctx:
			for b in self.verts:
				b.collect(id, val, addr, size)

	def gen(self, out, decorator = NULL_DECORATOR, with_source = False):
		decorator.start_cfg(self)

		out.write("digraph %s {\n" % self.id)
		for b in self.verts:
			out.write("\t%s [" % norm(b.id))
			if b.type == BLOCK_ENTRY:
				out.write("label=\"entry\"")
			elif b.type == BLOCK_EXIT:
				out.write("label=\"exit\"")
			elif b.type == BLOCK_CALL:
				out.write("URL=\"%s\",label=\"call %s\",shape=\"box\"" % (b.callee.id, b.callee.label))
			else:
				num = b.id[b.id.find("-") + 1:]
				out.write("margin=0,shape=\"box\",label=<<table border='0' cellpadding='8px'><tr><td>BB %s (%x:%s)</td></tr><hr/><tr><td align='left'>" % (num, b.base, b.size))
				if with_source:
					decorator.bb_source(b, out)
					out.write("</td></tr><hr/><tr><td>")
				decorator.bb_label(b, out)
				out.write("</td></tr></table>>")
			decorator.bb_attrs(b, out)
			out.write("];\n")
		for b in self.verts:
			for e in b.next:
				out.write("\t%s -> %s;\n" % (norm(e.src.id), norm(e.snk.id)))

		decorator.cfg_label(self, out)
		out.write("\n}\n")
		decorator.end_cfg(self)
		

class Task:
	"""Represents a task of the application."""
	
	def __init__(self, name, path):
		self.name = name
		self.path = path
		self.entry = None
		self.cfgs = []
		self.data = { }
		self.read()
	
	def add(self, cfg):
		"""Add a a CFG to the task."""
		if self.entry == None:
			self.entry = cfg
		self.cfgs.append(cfg)
	
	def collect(self, id, val, addr, size, ctx):
		"""Collect statistic item in the CFG."""
		for g in self.cfgs:
			g.collect(id, val, addr, size, ctx)

	def read(self):
		"""Read the task from the file."""
		cfg_path = os.path.join(self.path, "stats/cfg.xml")
		try:

			# open the file
			doc = ET.parse(cfg_path)
			root = doc.getroot()
			if root.tag != "cfg-collection":
				raise IOError("bad XML type")

			# prepare CFGS
			cfg_map = {}
			for n in root.iter("cfg"):
				id = n.attrib["id"]
				
				# look for context
				try:
					ctx = n.attrib["context"]
				except KeyError:
					ctx = ""
					for p in n.iter("property"):
						try:
							if p.attrib["identifier"] == "otawa::CONTEXT":
								ctx = p.text
								break
						except KeyError:
							pass
				
				# build the CFG
				cfg = CFG(id, n.attrib["label"], ctx)
				self.cfgs.append(cfg)
				cfg_map[id] = cfg
				cfg.node = n
			
			# initialize the content of CFGs
			for cfg in self.cfgs:
				block_map = {}

				# fill the vertices of CFG
				for n in cfg.node:
					try:
						id = n.attrib["id"]
					except KeyError:
						continue
					if n.tag == "entry":
						b = Block(BLOCK_ENTRY, id)
						cfg.entry = b
					elif n.tag == "exit":
						b = Block(BLOCK_EXIT, id)
						cfg.exit = b
					elif n.tag == "bb":
						try:
							b = CallBlock(id, cfg_map[n.attrib["call"]])
						except KeyError:
							lines = []
							for l in n.iter("line"):
								lines.append((l.attrib["file"], int(l.attrib["line"])))
							b = BasicBlock(id, int(n.attrib["address"], 16), int(n.attrib["size"]), lines)
							b.lines = lines
					else:
						continue  
					cfg.add(b)
					block_map[id] = b
				
				# fill the edges of CFG
				for n in cfg.node.iter("edge"):
					Edge(block_map[n.attrib["source"]], block_map[n.attrib["target"]])

				cfg.node = None

		except ET.ParseError as e:
			raise IOError("error during CFG read: %s" % e)
		except KeyError:
			raise IOError("malformed CFG XML file")


########## Statistics ########

class Statistic:
	"""Record information about statistics."""
	name = None
	map = None
	max = None

	def __init__(self, name):
		self.name = name

	def load(self, dir, task):
		try:
			inp = open(os.path.join(dir, "stats", self.name + ".csv"))
			for l in inp.readlines():
				fs = l[:-1].split("\t")
				assert len(fs) == 4
				task.collect(self.name, int(fs[0]), int(fs[1], 16), int(fs[2]), "[%s]" % fs[3][1:-1])
		except OSError as e:
			fatal("cannot open statistics %s: %s." % (self.stat, e))

	def init(self):
		self.map = {}
		self.max = 0
		for g in TASK.cfgs:
			for b in g.verts:
				if b.type == BLOCK_CODE:
					for (f, l) in b.lines:

						# get file
						try:
							file = self.map[f]
						except KeyError:
							file = []
							self.map[f] = file

						# get line
						try:
							file[l] = file[l] + b.get_val(self.name)
						except IndexError:
							file += [0] * (l + 1 - len(file))
							file[l] = b.get_val(self.name)

						# compute max
						self.max = max(self.max, file[l])

	def get_max(self):
		if self.map == None:
			self.init()
		return self.max

	def get_line(self, file, line):
		"""Get the statistics for the given line."""
		if self.map == None:
			self.init()
		try:
			return self.map[file][line]
		except (IndexError, KeyError):
			return 0

	def get_file(self, file):
		"""Get the statistics for the give file."""
		if self.map == None:
			self.init()
		try:
			return self.map[file]
		except KeyError:
			return []



######### To integrate ########


######### Template preprocessing #########

EXPAND_VAR = re.compile("([^\$]*)\$\{([^\}]*)\}(.*)")

def preprocess(path, map):
	"""Preprocess the given path containing string of the form ${ID}
	and getting the ID from the map. Return the preprocessed file
	as a string."""
	out = ""
	for l in open(path, "r"):
		while l:
			m = EXPAND_VAR.search(l)
			if not m:
				out = out + l
				break
			else:
				print(l, "\n", m.group(1), m.group(2), m.group(3))
				r = map[m.group(2)]()
				out = out + m.group(1) + r
				l = m.group(3)
	return out

		
def get_functions():
	"""Generate HTML to access functions."""
	out = StringBuffer()
	n = 0
	for f in TASK.cfgs:
		out.write(
			'<div><a href="javascript:show_function(%s, \'%s\');">%s</a></div>' \
			% (n, f.label, f.label)
		)
		n = n + 1
	return out.to_str()


def get_sources():
	"""Generate HTML to access the sources of the current task."""

	# build the list of sources
	map = {}
	for g in TASK.cfgs:
		for v in g.verts:
			if v.type == BLOCK_CODE:
				for l in v.lines:
					src = l[0]
					if src not in map:
						path = SOURCE_MANAGER.find_actual_path(src)
						if path:
							map[src] = path

	# generate the HTML
	out = ""
	srcs = list(map.keys())
	srcs.sort()
	for src in srcs:
		out = out + """<div><a href="javascript:show_source('%s')">%s</a></div>""" % (map[src], src)
	return out


def get_stats():
	out = '<option selected>No stat.</option>';
	for s in STATS:
		out = out + "<option>%s</option>" % s.name
	return out


def get_stat_colors():
	out = StringBuffer()
	out.write("var COLORS = new Array(")
	out.write('"%s"' % str(COLORS[0]))
	for i in range(1, len(COLORS)):
		out.write(', "%s"' % COLORS[i])
	out.write(");\n")
	return out.to_str();

def get_application():
	return APPLICATION

def get_task():
	return TASK.name

def get_host():
	return HOST

INDEX_MAP = {
	"functions":	get_functions,
	"sources":		get_sources,
	"stats":		get_stats,
	"stat-colors":	get_stat_colors,
	"application":	lambda: APPLICATION,
	"task":			lambda: TASK.name,
	"host":			lambda: HOST,
	"port":			lambda: str(PORT)
}


######### Server management #########

def do_stop(comps, query = {}):
	"""Stop the application."""
	return 666, {}, "".encode('utf-8')


def do_source(comps, query = {}):
	path = "/".join(comps)
	try:
		stat = query["stat"]
	except KeyError:
		stat = None
	source = SOURCE_MANAGER.find(path)
	if source == None:
		return 500, {"content-Type": "text/plain"}, b"source not available"
	else:
		return \
			200, \
			{'Content-type':"text/html; charset=utf-8"}, \
			source.gen(stat)


def do_source_stat(comps, query):
	stat = STATS[int(query["stat"]) - 1]
	out = StringBuffer();
	out.write("0 %d" % stat.get_max())
	lines = stat.get_file(query["src"])
	for i in range(0, len(lines)):
		if lines[i] != 0:
			out.write(" %d %d" % (i, lines[i]))
	return 200, {"content-Type": "text/plain"}, out.make()


def do_function(comps, query):
	g = TASK.cfgs[int(comps[0])]

	# generate the dot
	(handle, path)  = tempfile.mkstemp(suffix=".dot", text=True)
	#print(path)
	out = os.fdopen(handle, "w")
	g.gen(out, with_source = True)
	out.close()

	# generate the SVG
	r = subprocess.run([DOT_PATH, path, "-Tsvg"], capture_output = True)
	if r.returncode != 0:
		return (
			500,
			{},
			StringBuffer("Cannot generate the CFG: %s" % str(r.returncode)).to_utf8()
		)

	# clean up
	os.remove(path)

	# send the SVG
	return 200, {}, r.stdout


DO_MAP = {
	"stop": 		do_stop,
	"source":		do_source,
	"source-stat":	do_source_stat,
	"function":		do_function
}

def router(path='', query={}):
	"""Process a request and return the anwer."""

	comps = path.split('/', 2)
	try:
		return DO_MAP[comps[1]](comps[2:], query)
	except KeyError:
		if comps[1] == "":
			comps[1] = "index.html"
		path = os.path.join(DATA_DIR, "/".join(comps[1:]))
		if comps[1] == "index.html":
			return 200, \
				{}, \
				preprocess(path, INDEX_MAP).encode('utf-8')
		else:
			r = mimetypes.guess_type(path)
			print("DEBUG:", path, r)
			return 200, \
				{"Content-Type": r[0]}, \
				open(path, 'rb').read()


class Handler(BaseHTTPRequestHandler):
	"""Handle HTTP requests."""

	def do_GET(self):
	
		# parse URL
		urlP = urllib.parse.urlparse(self.path)
		query = {t[0] : t[1] for t in [p.split('=') if '=' in p else [p,''] for p in urlP.query.split('&')]}

		# manage the request
		quit = False
		#try:
		response_code , headers, data = router(urlP.path, query)
		if response_code == 666:
			quit = True
			response_code = 204
		#except Exception as err:
		#	print(err)
		#	response_code = 500
		#	headers = {}
		#	data = str(err).encode('utf-8')

		# build the answer
		if type(response_code) is tuple:
			code = response_code[0]
			message = response_code[1]
		else:
			code = response_code
			message = None
		self.send_response(code, message)
		for key in headers:
			self.send_header(key, headers[key])
		self.send_header('Access-Control-Allow-Origin', '*')
		self.end_headers()
		self.wfile.write(data)
		if quit:
			sys.exit(0)

	do_POST = do_GET


class StartServer(Thread):
	def __init__(self):
		super().__init__()
		self.server = None

	def run(self):
		print("run server at HOST: " + HOST + " and PORT: " + str(PORT))
		with HTTPServer((HOST, PORT), handler) as self.server:
			self.server.serve_forever()

	def stop(self):
		if (self.server is not None):
			self.server.shutdown()
			self.server.server_close()
			self.server = None


######### Start-up #########

def open_browser(port):
	"""Open the connection into a browser."""
	time.sleep(.5)
	webbrowser.open("http://localhost:%d" % port)

def main():
	global APPLICATION
	global DATA_DIR
	global DOT_PATH
	global HOST
	global PORT
	global SOURCE_MANAGER
	global STATS
	global TASK

	# check for dot
	DOT_PATH = shutil.which("dot")
	if DOT_PATH == None:
		fatal("dot command (from GraphViz package) must be available!")

	# parse arguments
	parser = argparse.ArgumentParser(description = "WCET viewer for OTAWA")
	parser.add_argument('executable', type=str,
		help="Select the exacutable to get statistics from.")
	parser.add_argument('task', nargs="?", type=str,
		help="Select which task to display (default main function).")
	parser.add_argument('-p', '--port', type=int,
		help="Port for the browser to display these pages.")
	args = parser.parse_args()
	if args.port is not None:
		PORT = args.port

	# find resources
	otawa_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
	DATA_DIR = None
	for path in [
		os.path.join(otawa_path, "data/obviews"),
		os.path.join(otawa_path, "share/Otawa/obviews")
	]:
		if os.path.exists(path):
			DATA_DIR = path
			break
	if DATA_DIR == None:
		fatal("cannot find internal data!\n")

	# load task information
	exe_dir = os.path.dirname(os.path.splitext(args.executable)[0])
	APPLICATION = os.path.basename(os.path.splitext(args.executable)[0])
	if not args.task:
		task_name = "main"
	else:
		task_name = args.task
	task_path = os.path.join(exe_dir, task_name + "-otawa")
	TASK = Task(task_name, task_path)
	STATS = []
	for s in glob.glob(os.path.join(task_path, "stats/*.csv")):
			stat = Statistic(os.path.basename(s)[:-4])
			STATS.append(stat)
			stat.load(task_path, TASK)
	SOURCE_MANAGER = SourceManager([exe_dir])

	# start browser and server
	Thread(target=partial(open_browser, PORT)).start()
	with HTTPServer((HOST, PORT), Handler) as server:
		server.serve_forever()

if __name__ == "__main__":
	main()
