#!/usr/bin/env python3
#
# Obviews - OTAWA Binary Viewers
#
# This file is part of OTAWA
# Copyright (c) 2022, IRIT UPS.
# 
# OTAWA is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# OTAWA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OTAWA; if not, write to the Free Software 
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

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
VERBOSE = False
DEBUG = False
HOST = '127.0.0.1'
PORT = 8000
DATA_DIR = None
DOT_PATH = None
TASK = None


######### Convenient functions #########

def error(msg):
	sys.stderr.write("ERROR: %s\n" % msg)

def warn(msg):
	sys.stderr.write("WARNING: %s\n" % msg)

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

	def to_xml(self):
		return ('<?xml version="1.0" encoding="utf8" standalone="yes"?>\n' + self.str).encode("utf-8")


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

	def __init__(self, name, path):
		self.label = os.path.basename(name)
		self.name = name
		self.path = path
		self.lines = None
		self.data = []
		self.colorizer = None

	def init_lines(self):
		self.lines = list(open(self.path, "r"))

	def get_lines(self):
		if self.lines == None:
			self.init_lines()
		return self.lines

	def get_line(self, num):
		if self.lines == None:
			self.init_lines()
		if num >= len(self.lines):
			return ""
		else:
			return self.lines[num]

	def get_colorizer(self):
		if self.colorizer == None:
			try:
				self.colorizer = SYNTAX_COLS[os.path.splitext(self.path)[1]]()
			except KeyError:
				self.colorizer = NULL_COLORIZER
		return self.colorizer

	def collect(self, num, stat, val):
		if num >= len(self.data):
			self.data = self.data + [None] * (num + 1 - len(self.data))
		if self.data[num] == None:
			self.data[num] = Data()
		return self.data[num].add_val(stat, val)

	def get_stat(self, num, stat):
		if num >= len(self.data):
			return 0
		else:
			data = self.data[num]
			if data ==  None:
				return 0
			else:
				return data.get_val(stat)

	def gen(self, stat = None):
		"""Generate a source output."""
		col = self.get_colorizer()

		# generate the table
		out = StringBuffer()
		out.write('<table id="stats">\n')
		out.write(" <tr><th></th><th>source</th><th></th>\n")

		num = 0
		for l in self.get_lines():
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
				col.colorize(l, out)
				out.write("</td><td></td>")

		out.write("</tr>\n")
		out.write("</table>\n")
		r = out.to_utf8()
		return r


class SourceManager:
	"""The source manager manages sources of the processed program."""
	
	def __init__(self, task, paths = ["."]):
		self.task = task
		self.paths = paths
		self.map = {}
		self.sources = []
		self.max = Data()

	def get_sources(self):
		"""Get the sources composing the task."""
		return self.sources

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
	
	def find(self, name):
		"""Lookup for a source file. If not already loaded, lookup
		for the source using the lookup paths."""
		try:
			return self.map[name]
		except KeyError:
			source = None
			path = self.find_actual_path(name)
			if path != None:
				try:
					source = Source(name, path)
					self.sources.append(source)
				except OSError:
					pass
			self.map[name] = source
			return source

	def collect(self, path, num, stat, val):
		source = self.find(path)
		if source != None:
			x = source.collect(num, stat, val)
			self.max.max_val(stat, x)

	def get_lines(self, path):
		"""Get the lines for the given path. Return None if the path
		cannot be found."""
		if source == None:
			return None
		else:
			return source.get_lines()

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

	def get_max(self,stat):
		return self.max.get_val(stat)


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
	
	def __init__(self, task):
		self.sman = task.get_source_manager()
	
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
					t = escape_html(source.get_lines()[l-1])
					source.get_colorizer().colorize(t, out)
					out.write("<br align='left'/>")
				prev_file = f
				prev_line = l

	def bb_label(self, b, out):
		pass


class BaseDecorator(Decorator):
	
	def __init__(self, task):
		Decorator.__init__(self, task)
		self.task = task
	
	def bb_label(self, bb, out):
		for stat in self.task.stats:
			val = bb.get_val(stat)
			percent = val * 100. / self.task.sum.get_val(stat)
			out.write("%s=%d (%3.2f%%)<br/>" % (stat.name, val, percent))


class ColorDecorator(BaseDecorator):

	def __init__(self, task, stat):
		BaseDecorator.__init__(self, task)
		self.stat = stat

	def bb_attrs(self, bb, out):
		if bb.type == BLOCK_CALL:
			val = bb.callee.max.get_val(self.stat)
		else:
			val = bb.get_val(self.stat)
		ratio = float(val) / self.task.get_max(self.stat)
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
	
	def max_val(self, id, val):
		if val == 0:
			return 0
		try:
			self.data[id] = max(self.data[id], val)
		except KeyError:
			self.data[id] = val
		return self.data[id]

	def add_val(self, id, val):
		if val == 0:
			return 0
		try:
			self.data[id] = self.data[id] + val
		except KeyError:
			self.data[id] = val
		return self.data[id]


class Block(Data):
	
	def __init__(self, type, id):
		Data.__init__(self)
		self.type = type
		self.id = id
		self.next = []
		self.pred = []
		self.lines = []
	
	def collect(self, id, val, addr, size, task):
		return 0
	

class BasicBlock(Block):
	
	def __init__(self, id, base, size, lines = []):
		Block.__init__(self, BLOCK_CODE, id)
		self.base = base
		self.size = size
		self.lines = lines

	def collect(self, id, val, addr, size, task):
		if self.base <= addr and addr < self.base + self.size:
			self.add_val(id, val)
			for (f, l) in self.lines:
				task.sman.collect(f, l, id, val)


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
		self.max = Data()
		self.sum = Data()
	
	def add(self, block):
		block.number = len(self.verts)
		self.verts.append(block)

	def begin_stat(self, id):
		self.max.set_val(id, 0)
		self.sum.set_val(id, 0)

	def collect(self, id, val, addr, size, ctx, task):
		if ctx == self.ctx:
			for b in self.verts:
				b.collect(id, val, addr, size, task)

	def end_stat(self, id):
		for v in self.verts:
			x = v.get_val(id)
			self.max.max_val(id, x)
			self.sum.add_val(id, x)

	def gen(self, out, decorator, with_source = False):
		decorator.start_cfg(self)

		out.write("digraph %s {\n" % self.id)
		for b in self.verts:
			out.write("\t%s [" % norm(b.id))
			if b.type == BLOCK_ENTRY:
				out.write("label=\"entry\"")
			elif b.type == BLOCK_EXIT:
				out.write("label=\"exit\"")
			elif b.type == BLOCK_CALL:
				out.write("URL=\"javascript:show_function(%d, '%s')\",label=\"call %s\",shape=\"box\"" \
					% (b.callee.number, b.callee.label, b.callee.label))
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
	
	def __init__(self, exec, name, path):
		self.exec = exec
		self.name = name
		self.path = path
		self.entry = None
		self.cfgs = []
		self.max = Data()
		self.sum = Data()
		self.stats = []
		self.sman = SourceManager([os.path.dirname("exec")])
		self.read()

	def get_max(self, stat):
		return self.max.get_val(stat)

	def get_sum(self, stat):
		return self.sum.get_val(stat)

	def get_source_manager(self):
		return self.sman

	def get_sources(self):
		return self.sman.get_sources()

	def find_source(self, name):
		return self.sman.find(name)
	
	def add(self, cfg):
		"""Add a a CFG to the task."""
		if self.entry == None:
			self.entry = cfg
		self.cfgs.append(cfg)

	def begin_stat(self, id):
		self.max.set_val(id, 0)
		self.sum.set_val(id, 0)
		for g in self.cfgs:
			g.begin_stat(id)

	def collect(self, id, val, addr, size, ctx):
		"""Collect statistic item in the CFG."""
		for g in self.cfgs:
			g.collect(id, val, addr, size, ctx, self)

	def end_stat(self, id):
		for g in self.cfgs:
			g.end_stat(id)
			self.max.max_val(id, g.max.get_val(id))
			self.sum.add_val(id, g.sum.get_val(id))
	
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
				cfg.number = len(self.cfgs)
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
								file = l.attrib["file"]
								lines.append((file, int(l.attrib["line"])))
								self.sman.find(file)
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

DEF_RE = re.compile("#\s*(\S+):\s*(.*)")
OP_MAX = lambda d, s, x: d.max_val(s, x)
OP_SUM = lambda d, s, x: d.add_val(s, x)
OP_MAP = {
	"sum":	OP_SUM,
	"max":	OP_MAX
}

class Statistic:
	"""Record information about statistics."""
	name = None
	map = None
	max = None

	def __init__(self, task, name, path):
		self.task = task
		self.name = name
		self.path = path
		self.label = name
		self.line_op = OP_SUM
		self.concat_op = OP_SUM
		self.context_op = OP_MAX
		self.unit = None
		self.defs = {}
		self.number = len(task.stats)
		self.total = 0
		self.description = ""
		task.stats.append(self)
		self.loaded = False
		self.pre_loaded = False

	def get_def(self, id, d):
		if id not in self.defs:
			return d
		x = self.defs[id]
		del self.defs[id]
		return x

	def get_op(self, id, d):
		op = self.get_def(id, None)
		if op == None:
			return d
		else:
			try:
				return OP_MAP[op]
			except KeyError:
				warn("unknown line-op operator (%s) for %s"
					% (self.defs["LineOperation"], self.name))
				return d

	def preload(self):
		"""Load definitions from the statistics."""

		# read the file
		try:
			inp = open(self.path)
			for l in inp.readlines():
				if l and l[0] == "#":
					m = DEF_RE.match(l)
					if m:
						self.defs[m.group(1)] = m.group(2).strip(" \t\n")
		except OSError as e:
			fatal("cannot open statistics %s: %s." % (self.name, e))

		# consume useful defs
		self.label = self.get_def("Label", self.name)
		self.unit = self.get_def("Unit", self.unit)
		self.total = self.get_def("Total", self.unit)
		self.description = self.get_def("Description", self.unit)
		self.line_op = self.get_op("LineOp", OP_SUM)
		self.concat_op = self.get_op("ConcatOp", OP_SUM)
		self.context_op = self.get_op("ContextOp", OP_SUM)

	def ensure_preload(self):
		if not self.pre_loaded:
			self.preload()
			self.pre_loaded = True

	def load(self):
		"""Load statistics data from the file."""
		try:
			inp = open(self.path)
			self.task.begin_stat(self)
			for l in inp.readlines():
				if l and l[0] == "#":
					continue
				else:
					fs = l[:-1].split("\t")
					assert len(fs) == 4
					self.task.collect(self,
						int(fs[0]),
						int(fs[1], 16),
						int(fs[2]),
						"[%s]" % fs[3][1:-1])
			self.task.end_stat(self)
		except OSError as e:
			fatal("cannot open statistics %s: %s." % (self.name, e))

	def ensure_load(self):
		"""Ensure that statistics data has been loaded."""
		if not self.loaded:
			self.load()
			self.loaded = True

	def record_source(self, source):
		"""Record data in the given source."""
		self.ensure_load()
		for g in self.task.cfgs:
			for b in g.verts:
				if b.type == BLOCK_CODE:
					for (f, l) in b.lines:
						if f == source.name:
							if source.data[l-1] == None:
								source.data[l-1] = Data()
							source.data[l-1].add_val(self, b.get_val(self))

	def get_max(self):
		self.ensure_load()
		return self.task.max.get_val(self)

	def get_sum(self):
		self.ensure_load()
		return self.task.sum.get_val(self)


######### Template preprocessing #########

EXPAND_VAR = re.compile("([^\$]*)\$\{([^\}]*)\}(.*)")

def preprocess(path, map):
	"""Preprocess the given path containing string of the form ${ID}
	and getting the ID from the map. Return the preprocessed file
	as a string."""
	out = StringBuffer()
	for l in open(path, "r"):
		while l:
			m = EXPAND_VAR.search(l)
			if not m:
				out.write(l)
				break
			else:
				#print(l, "\n", m.group(1), m.group(2), m.group(3))
				r = map[m.group(2)]()
				out.write(m.group(1))
				out.write(r)
				l = m.group(3)
	return out.to_utf8()

		
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
	out = StringBuffer()
	srcs = list(TASK.get_sources())
	srcs.sort()
	for src in srcs:
		out.write("""<div><a href="javascript:show_source('%s')">%s</a></div>""" \
			% (src.name, src.name))
	return out.to_str()


def get_stats():
	for s in TASK.stats:
		s.ensure_preload()
	out = StringBuffer()
	out.write('<option selected>No stat.</option>')
	for s in TASK.stats:
		out.write("<option>%s</option>" % s.label)
	return out.to_str()


def get_stat_colors():
	out = StringBuffer()
	out.write("var COLORS = new Array(")
	out.write('"%s"' % str(COLORS[0]))
	for i in range(1, len(COLORS)):
		out.write(', "%s"' % COLORS[i])
	out.write(");\n")
	return out.to_str();


INDEX_MAP = {
	"functions":	get_functions,
	"sources":		get_sources,
	"stats":		get_stats,
	"stat-colors":	get_stat_colors,
	"application":	lambda: os.path.basename(os.path.splitext(TASK.exec)[0]),
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
	source = TASK.find_source(path)
	if source == None:
		return 500, {"content-Type": "text/plain"}, b"source not available"
	else:
		return \
			200, \
			{'Content-type':"text/html; charset=utf-8"}, \
			source.gen(stat)


def do_source_stat(comps, query):
	stat = TASK.stats[int(query["stat"]) - 1]
	stat.ensure_load()
	source = TASK.find_source(query["id"])
	out = StringBuffer();
	out.write("0 %d" % TASK.get_source_manager().get_max(stat))
	for i in range(0, len(source.get_lines())):
		x = source.get_stat(i, stat)
		if x != 0:
			out.write(" %d %d" % (i, x))
	return 200, {"content-Type": "text/plain"}, out.make()


def do_function(comps, query):
	g = TASK.cfgs[int(comps[0])]

	# define decorator
	for s in TASK.stats:
		s.ensure_load()
	col = BaseDecorator(TASK)

	# generate the dot
	(handle, path)  = tempfile.mkstemp(suffix=".dot", text=True)
	out = os.fdopen(handle, "w")
	g.gen(out, with_source = True, decorator = col)
	out.close()

	# generate the SVG
	r = subprocess.run([DOT_PATH, path, "-Tsvg"], capture_output = True)
	if r.returncode != 0:
		print("ERROR: faulty .dot file:", path)
		return (
			200,
			{},
			StringBuffer("<p>Cannot generate the CFG: %s</p>" % r.returncode).to_xml()
		)

	# send the SVG
	os.remove(path)
	return 200, {}, r.stdout


def do_function_stat(comps, query):
	stat = TASK.stats[int(query["stat"]) - 1]
	stat.ensure_load()
	g = TASK.cfgs[int(query["id"])]
	out = StringBuffer()
	out.write(str(TASK.get_max(stat)))
	for v in g.verts:
		if v.type == BLOCK_CALL:
			x = v.callee.max.get_val(stat)
		else:
			x = v.get_val(stat)
		if x != 0:
			out.write(" %d %d" % (v.number, x))
	return 200, {"content-Type": "text/plain"}, out.to_utf8()


def do_stat_info(comps, query):
	stat = TASK.stats[int(query["stat"]) - 1]
	out = StringBuffer()
	out.write("<div>")
	for (k, v) in stat.defs.items():
		out.write("<b>%s:</b> %s<br/>" % (k, v))
	out.write("</div>")
	return 200, {}, out.to_xml()

DO_MAP = {
	"stop": 			do_stop,
	"source":			do_source,
	"source-stat":		do_source_stat,
	"function":			do_function,
	"function-stat":	do_function_stat,
	"stat-info":		do_stat_info
}



class Handler(BaseHTTPRequestHandler):
	"""Handle HTTP requests."""

	def route(self, path='', query={}):
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
					preprocess(path, INDEX_MAP)
			else:
				r = mimetypes.guess_type(path)
				return 200, \
					{"Content-Type": r[0]}, \
					open(path, 'rb').read()

	def do_GET(self):
	
		# parse URL
		urlP = urllib.parse.urlparse(self.path)
		query = {t[0] : t[1] for t in [p.split('=') if '=' in p else [p,''] for p in urlP.query.split('&')]}

		# manage the request
		quit = False
		if not DEBUG:
			response_code , headers, data = self.route(urlP.path, query)
		else:
			try:
				response_code , headers, data = self.route(urlP.path, query)
			except Exception as err:
				print(err)
				response_code = 500
				headers = {}
				data = str(err).encode('utf-8')
		if response_code == 666:
			quit = True
			response_code = 204

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
		if VERBOSE:
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
	if not args.task:
		task_name = "main"
	else:
		task_name = args.task
	task_dir = os.path.join(exe_dir, task_name + "-otawa")
	TASK = Task(args.executable, task_name, task_dir)
	for s in glob.glob(os.path.join(task_dir, "stats/*.csv")):
		stat = Statistic(TASK, os.path.basename(s)[:-4], s)

	# start browser and server
	Thread(target=partial(open_browser, PORT)).start()
	with HTTPServer((HOST, PORT), Handler) as server:
		server.serve_forever()

if __name__ == "__main__":
	main()
