#!/usr/bin/env python3
 
import argparse
from cmd import Cmd
import datetime
import io
import json
import os
import re
import signal
import subprocess
import sys
import urllib.parse
import webbrowser
import xml.etree.ElementTree as ET
from http import server
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

HOST, PORT = '127.0.0.1', 8000

###############################################################################
#                                                                             #
#                              Setter                                         #
#                                                                             #
###############################################################################

def set_path_otawa(path_otawa, save_config=False):
    globals()['path_dir_otawa'] = path_otawa
    if save_config:
        update_data_config({'otawa-path':globals()['path_dir_otawa']})

def set_path_workdir(path_workdir):
    globals()['path_dir_workspace'] = path_workdir


###############################################################################
#                                                                             #
#                           Generation stats                                  #
#                                                                             #
###############################################################################

def run_owcet(path_executable, script, target=None, path_flowfacts=None):
    prog = os.path.join(globals()['path_dir_otawa_bin'], 'owcet')
    commande = prog+ " " + path_executable
    
    if path_flowfacts is not None:
        commande += " -f " + path_flowfacts

    if target is not None:
        commande += " " + target

    commande += " -s " + script + " --stats"

    return subprocess.call(commande.split())

def get_list_scripts(path_otawa):
    path = os.path.join(path_otawa, "share/Otawa/scripts")
    list_script = []
    with os.scandir(path) as it:
        for entry in it:
            if entry.is_file() and entry.name.endswith(".osx"):
                list_script.append(os.path.splitext(entry.name)[0])
    
    return list_script

def output_list_scripts(list_script):
    return json.dumps(list_script).encode("utf-8")


###############################################################################
#                                                                             #
#                       Generation affichage stats                            #
#                                                                             #
###############################################################################

BLOCK_ENTRY = 0
BLOCK_EXIT = 1
BLOCK_CODE = 2
BLOCK_CALL = 3

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


def background(ratio):
    return COLORS[round(ratio * (len(COLORS) - 1))]

def foreground(ratio):
    if ratio * (len(COLORS) - 1) < COLOR_TH:
        return BLACK
    else:
        return WHITE


def error(msg):
    sys.stderr.write("ERROR: %s\n" % msg)

def fatal(msg):
    error(msg)
    exit(1)


class SourceManager:
	"""The source manager manges sources of the processed program."""
	
	def __init__(self, paths = ["."]):
		self.paths = paths
		self.sources = {}
	
	def load_source(self, path, alias = None):
		"""Try to load the source from the file system."""
		try:
			return list(open(path, "r"))
		except OSError:
			return None
	
	def find_source(self, path):
		"""Lookup for a source file. If not already loaded, lookup
		for the source using the lookup paths."""
		try:
			return self.sources[path]
		except KeyError:
			lines = None
			if os.path.isabs(path):
				lines = self.load_source(path)
			else:
				for p in self.paths:
					p = os.path.join(p, path)
					lines = self.load_source(p, path)
					if lines != None:
						self.sources[p] = lines
						break
			self.sources[path] = lines
			return lines

	def get_line(self, path, line):
		"""Get the line corresponding to the given source path and line.
		If not found, return None."""
		lines = self.find_source(path)
		if lines == None:
			return None
		else:
			try:
				return lines[line - 1]
			except IndexError:
				return None


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
        

class Task:
    
    def __init__(self, name):
        self.name = name
        self.entry = None
        self.cfgs = []
        self.data = { }
    
    def add(self, cfg):
        if self.entry == None:
            self.entry = cfg
        self.cfgs.append(cfg)
    
    def collect(self, id, val, addr, size, ctx):
        for g in self.cfgs:
            g.collect(id, val, addr, size, ctx)


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


def read_cfg(path):
	cfg_path = os.path.join(path, "stats/cfg.xml")
	try:

		# open the file
		doc = ET.parse(cfg_path)
		root = doc.getroot()
		if root.tag != "cfg-collection":
			raise IOError("bad XML type")

		# prepare CFGS
		task = Task(path)
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
			task.cfgs.append(cfg)
			cfg_map[id] = cfg
			cfg.node = n
        
        # initialize the content of CFGs
		for cfg in task.cfgs:
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

		return task
	except ET.ParseError as e:
		error("error during CFG read: %s" % e)
	except KeyError:
		error("malformed CFG XML file")

def norm(name):
    return name.replace("-", "_")

def read_stat(dir, task, stat):
	try:
		inp = open(os.path.join(dir, "stats", stat + ".csv"))
		for l in inp.readlines():
			fs = l[:-1].split("\t")
			assert len(fs) == 4
			task.collect(stat, int(fs[0]), int(fs[1], 16), int(fs[2]), "[%s]" % fs[3][1:-1])
	except OSError as e:
		fatal("cannot open statistics %s: %s." % (stat, e))


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
    
	def bb_source(self, bb, out):
		if bb.lines != []:
			for (f, l) in bb.lines:
				t = self.sman.get_line(f, l)
				if t == None:
					t = ""
				out.write("%s:%d: %s<br align='left'/>" % (f, l, escape_html(t)))
    
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


def get_all_stats(dir):
    stats = []
    for f in os.listdir(dir):
        if f.endswith(".csv"):
            stats.append(f[:-4])
    return stats

class SyntaxColorizer:
    
    def colorize(self, line, out):
        out.write(line)

SYNTAX_COLS = { }

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
                

for ext in ['.c', '.h', '.cpp', '.hpp', '.cc', '.hh']:
    SYNTAX_COLS[ext] = CColorizer

def output_html_sign(out):
    out.write("    <center><i>Generated by otawa-stat.py (%s).<br/><a href=\"http://www.otawa.fr\">OTAWA</a> framework - copyright (c) 2019, University of Toulouse.<i></center>\n"
        % datetime.datetime.today())


class StrWrite():
    def __init__(self):
        self.str = ""
    
    def write(self, value):
        self.str += value
    
    def getBinarie(self):
        return self.str.encode("utf-8")

def output_CFG(task, decorator, with_source = False, cfg_id = None):

    # output each CFG
    if cfg_id == None:
        cfg = task.cfgs[0]
    else:
        l_cfg = [x for x in task.cfgs if x.id == cfg_id]
        if len(l_cfg) == 0:
            raise IndexError("cfg %s not found in task" % cfg_id)
        else:
            cfg = l_cfg[0]


    out = StrWrite()
    decorator.start_cfg(cfg)

    # generate file
    out.write("digraph %s {\n" % cfg.id)
    for b in cfg.verts:
        out.write("\t%s [" % norm(b.id))
        if b.type == BLOCK_ENTRY:
            out.write("label=\"entry\"")
        elif b.type == BLOCK_EXIT:
            out.write("label=\"exit\"")
        elif b.type == BLOCK_CALL:
            out.write("URL=\"%s\",label=\"call %s\",shape=\"box\"" % (b.callee.id, b.callee.label))
        else:
            num = b.id[b.id.find("-") + 1:]
            out.write("margin=0,shape=\"box\",label=<<table border='0' cellpadding='8px'><tr><td>BB %s (%s:%s)</td></tr><hr/><tr><td align='left'>" % (num, b.base, b.size))
            if with_source:
                decorator.bb_source(b, out)
                out.write("</td></tr><hr/><tr><td>")
            decorator.bb_label(b, out)
            out.write("</td></tr></table>>")
        decorator.bb_attrs(b, out)
        out.write("];\n")
    for b in cfg.verts:
        for e in b.next:
            out.write("\t%s -> %s;\n" % (norm(e.src.id), norm(e.snk.id)))
    out.write("label=<CFG: %s %s<br/>colorized by %s<br/>" % (cfg.label, cfg.ctx, decorator.major()))
    decorator.cfg_label(cfg, out)
    out.write("<BR/><I>Generated by otawa-stat.py (%s).</I><BR/><I>OTAWA framework - copyright (c) 2019, University of Toulouse</I>" % datetime.datetime.today())
    out.write(">;\n}")

    # close file
    decorator.end_cfg(cfg)

    return out.getBinarie()

def output_sources(path, main, task, stats, source_id = None):
    
    # collect sources and statistics
    sources = []
    lines = { }
    maxv = { s: 0 for s in stats }
    maxl = { }

    for g in task.cfgs:
        for b in g.verts:
            if b.type == BLOCK_CODE:
                for (f, l) in b.lines:
                    if f not in sources and os.path.isfile(os.path.join(globals()['path_dir_workspace'], f)):
                        sources.append(f)
                        maxl[f] = 0
                    if f in sources:
                        for s in stats:
                            try:
                                v  = lines[(s, f, l)] + b.get_val(s)
                            except KeyError:
                                v = b.get_val(s)

                            lines[(s, f, l)] = v
                            maxv[s] = max(v, maxv[s])
                            maxl[f] = max(maxl[f], l)

    # output index
    out = StrWrite()
    
    if source_id == None:
        out.write("<html><head><title>Task %s colored by %s</title></head><body>" % (task.name, main))
        out.write("<h1>Task %s colored by %s</h1>" % (task.name, main))
        out.write("<p>List of sources:</p><ul>")
        for f in sources:
            out.write("<li><a href=\"%s\">%s</a></li>" % (f, f))
        out.write("</ul>")
        output_html_sign(out)
        out.write("</body></html>")
        
        return out.getBinarie()

    # output each file
    elif source_id in sources:
        f = source_id
        
        # select colorizer
        try:
            col = SYNTAX_COLS[os.path.splitext(f)[1]]()
        except KeyError:
            col = SyntaxColorizer()
        
        # begin of header
        out.write("<html><head><title>%s colored for %s</title>" % (f, main))
        
        # output styles
        out.write("""
    <style>
        td {
            text-align: right;
            padding-left: 8pt;
            padding-right: 8pt;
        }
        td.source {
            text-align: left;
        }
        table {
            margin-top: 1em;
        }
    </style>

        """)
    
        # output script
        out.write("""
    <script type="text/javascript">
    """)
        out.write("        var labels = [")
        for s in stats:
            out.write("'%s', " % s)
        out.write("];\n")
        out.write("        var backgrounds = ['%s'" % WHITE)
        for c in COLORS:
            out.write(", '%s'" % c)
        out.write("];\n")
        out.write("        var foregrounds = ['%s'" % BLACK)
        for i in range(COLOR_TH):
            out.write(", '%s'" % BLACK)
        for i in range(len(COLORS) - COLOR_TH):
            out.write(", '%s'" % WHITE)
        out.write("];\n")
        out.write("""
        function colorize(backs, label) {
            document.getElementById("label").textContent = label;
            trs = document.getElementById("stats").getElementsByTagName("tr");
            for(i = 0; i < trs.length; i++) {
                trs[i].style.backgroundColor = backgrounds[backs[i]];
                trs[i].style.color = foregrounds[backs[i]];
            }
        }

        """)
        for s in stats:
            out.write("        var s%d = [\n            0,\n" % stats.index(s))
            for l in range(maxl[f] + 1):
                try:
                    v = lines[(s, f, l + 1)]
                    if v == 0:
                        c = 0
                    else:
                        c = round(float(v) * (len(COLORS) - 1) / maxv[s]) + 1
                except KeyError:
                    c = 0
                out.write("            %d,\n" % c)
            out.write("        ];\n")
        out.write("""
    </script>
            """)
    
        # end of head
        out.write("</head><body>\n")
        
        # output details
        out.write("    <h1>%s</h1>\n" % f)
        out.write("""
    <p><a href=\".\">Top</a><br/>
    <b>Task:</b> %s<br/>
    <b>Colored by:</b> <span id='label'>%s</span>
    """ % (task.name, main))
        
        # output table begin
        out.write("    <table id=\"stats\">\n")
        out.write("    <tr><th>num.</th><th>source</th>")
        for s in stats:
            i = stats.index(s)
            out.write("<th><a href=\"javascript:colorize(s%d, '%s')\">%s</a></th>" % (i, s, s))
        out.write("</tr>\n")

        # read the source file
        inp = open(os.path.join(globals()['path_dir_workspace'], f))
        num = 0
        for l in inp.readlines():
            num = num + 1

            # prepare row
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
            out.write("    <tr><td>%d</td><td class=\"source\"" % num)
            if style:
                out.write(" style=\"%s\"" % style)
            out.write(">")
            col.colorize(l, out)
            out.write("</td>")

            for s in stats:
                try:
                    v = lines[(s, f, num)]
                    out.write("<td>%d</td>" % v)
                except KeyError:
                    out.write("<td></td>")
            out.write("</tr>\n")
        
        # close source file
        inp.close()
        
        # generate tail
        out.write("    </table>\n")
        output_html_sign(out)
        out.write("    <script type='text/javascript'>colorize(s%d, '%s');</Script>\n" % (stats.index(main), main))
        out.write("<body></html>\n")

        return out.getBinarie()

def get_list_cfgs(path):
    cfg_path = os.path.join(path, "stats/cfg.xml")
    try:
		# open the file
        doc = ET.parse(cfg_path)
        root = doc.getroot()
        if root.tag != "cfg-collection":
            raise IOError("bad XML type")

        list_cfg = []

        for n in root.iter("cfg"):
            id_cfg = n.attrib["id"]
            label_cfg = n.attrib["label"]
            list_cfg.append({"id":id_cfg, "label":label_cfg})

        return list_cfg

    except ET.ParseError as e:
        error("error during CFG read: %s" % e)
    except KeyError:
        error("malformed CFG XML file")        

def output_list_cfgs(list_cfg):
    return json.dumps(list_cfg).encode("utf-8")

###############################################################################
#                                                                             #
#                              Serveur                                        #
#                                                                             #
###############################################################################

def router(path='', query={}):
    """
    Renvoi le fichier adapter en fonction du path et des query indiqué

    Args:
        path (str, optional): LiChemin vers le fichier. Defaults to ''.
        query ([type], optional): Dictionnaire des query envoyé aprés ? dans une url. Defaults to None.

    Returns:
        bytes : fichier à envoyer
    """

    lien = path.split('/',2)
    # lien[0] = '/' car path commence par /
    p = lien[2] if len(lien)>=3 else ""
    if lien[1] == "wcet":                        # /wcet
        return routerWcet(p, query)

    elif lien[1] == "stats":                     # /stats
        return routerStats(p, query)

    elif lien[1] == "set":                       # /set
        return routerSet(p, query)

    elif lien[1] == "get":                       # /get
        return routerGet(p, query)

    elif lien[1] == "resources":                 # /resources
        if len(lien) >= 3:
            return 200, {}, open(os.path.join(globals()['path_dir_serveur_resources'], lien[2]), 'rb').read()

    elif lien[1] == "stop":
        os.kill(os.getpid(), signal.SIGINT)
        return 204, {}, "".encode('utf-8')

    else:                                        # /
        return 200, {'Content-type':'text/html'}, open(os.path.join(globals()['path_dir_serveur_resources'],'index.html'), 'rb').read()

def routerWcet(path='', query={}):
    lien = path.split('/',1)

    if lien[0] == "list_scripts":                # /wcet/list_scripts
        list_scripts = get_list_scripts(globals()['path_dir_otawa'])
        return 200, {'Content-type':"text/json; charset=utf-8"}, output_list_scripts(list_scripts)

    elif lien[0] == "run":                       # /wcet/run
        script = query['script'] if 'script' in query else 'generic'

        args = {'path_executable':query['executable'], 'script':script}

        if 'flowfacts' in query:
            args['path_flowfacts'] = query['flowfacts']

        if 'target' in query:
            args['target'] = query['target']
        
        retcode = run_owcet(**args)

        if retcode == 0:
            return 200, {'Content-type':"text/plain; charset=utf-8"}, "succes".encode("utf-8")
        else:
            return 400, {'Content-type':"text/plain; charset=utf-8"}, "error".encode("utf-8")

def routerStats(path='', query={}):
    cfg = True
    stats = ["ipet-total_time","ipet-total_count"]
    stat = stats[0]
    doc_id = None
    f = "main"
    dir = os.path.join(globals()['path_dir_workspace'], f + "-otawa")
            
    if path!="":                                 # /stats/
        lien = path.split('/',1)

        if lien[0]=="list_cfgs":                 # /stats/list_cfgs
            l = get_list_cfgs(dir)
            return 200, {'Content-type':"text/json; charset=utf-8"}, output_list_cfgs(l)
        elif lien[0]=="cfg":                     # /stats/cfg
            cfg = True
        elif lien[0]=="code":                    # /stats/code
            cfg = False                      

        if len(lien) == 2 and lien[1]!="":       # /stats/.../doc_id
                doc_id = lien[1]

        if "colored_by" in query:
            if query["colored_by"]=="time":      # /stats/.../?colored_by=time
                stat = "ipet-total_time"
            elif query["colored_by"]=="count":   # /stats/.../?colored_by=count
                stat = "ipet-total_count"
                    
    
    # read the CFG
    task = read_cfg(dir)
    
    for s in stats:
            read_stat(dir, task, s)

    if cfg:
        decorator = ColorDecorator
        out = output_CFG(task, decorator(stat, task, stats), True, doc_id)
        return 200, {'Content-type':"text/dot; charset=utf-8"}, out

    else :
        out = output_sources(dir, stat, task, stats, doc_id)
        return 200, {'Content-type':"text/html; charset=utf-8"}, out

def routerSet(path='', query={}):
    save_config = 'save_config' in query and query['save_config']=="True"

    if 'work-dir' in query:
        set_path_workdir(query['work-dir'])
    if 'otawa-dir' in query:
        set_path_otawa(query['otawa-dir'], save_config)
    
    return 200, {'Content-type':'text/plain; charset=utf-8'}, ("work-dir : %s \notawa-dir : %s"%(globals()['path_dir_workspace'],globals()['path_dir_otawa'])).encode("utf-8")

def routerGet(path='',query={}):
    get_value = {}

    if 'work-dir' in  query:
        get_value['work-dir'] = globals()['path_dir_workspace']
    if 'otawa-dir' in query: 
        get_value['otawa-dir'] = globals()['path_dir_otawa']

    return 200, {'Content-type':"text/json; charset=utf-8"}, json.dumps(get_value).encode('utf-8')

class handler(BaseHTTPRequestHandler):

    def do_GET(self):
    
        urlP = urllib.parse.urlparse(self.path)
        query = {t[0] : t[1] for t in [p.split('=') if '=' in p else [p,''] for p in urlP.query.split('&')]}

        print("\n")

        try:
            response_code , headers, data = router(urlP.path, query)
        except Exception as err:
            response_code = 500
            headers = {}
            data = str(err).encode('utf-8')

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



###############################################################################
#                                                                             #
#                               Config                                        #
#                                                                             #
###############################################################################

def default_config():
    data = {}
    data['server']={}
    data['server']['PORT'] = 8000
    data['server']['HOST'] = "127.0.0.1"
    data['otawa-path'] = os.path.dirname(os.path.dirname(sys.argv[0]))
    return data

def existing_config():
    return os.path.isfile(os.path.join(globals()['path_dir_serveur'],"config.json"))

def init_config():
    with open(os.path.join(globals()['path_dir_serveur'],"config.json"), "w") as config_file:
        data = default_config()
        json.dump(data, config_file, indent=2)

def read_config():
    with open(os.path.join(globals()['path_dir_serveur'],"config.json"), "r") as config_file:
        data = json.load(config_file)
        return data

def apply_config(config):
    globals()['PORT'] = config['server']['PORT']
    globals()['HOST'] = config['server']['HOST'] 
    globals()['path_dir_otawa'] = config['otawa-path']

def replace_value_config(dict_1, dict_2):
    if type(dict_1) is dict and type(dict_2) is dict:
        for key in dict_2:
            print(key)
            if key in dict_1 and type(dict_1[key]) is dict and type(dict_2[key]) is dict:
                replace_value_config(dict_1[key], dict_2[key])
            else:
                dict_1[key] = dict_2[key]

def update_data_config(data_updated):
    with open(os.path.join(globals()['path_dir_serveur'],"config.json"), "r+") as config_file:
        data = json.load(config_file)
        
        replace_value_config(data, data_updated)
        config_file.seek(0)
        json.dump(data, config_file, indent=2)
        config_file.truncate()


###############################################################################
#                                                                             #
#                                Main                                         #
#                                                                             #
###############################################################################
def dir_path(path):
    if os.path.exists(path):
        if os.path.isdir(path):
            return path
        else:
            raise argparse.ArgumentTypeError("path is not a directory: %r" % path)
    else:
        raise argparse.ArgumentTypeError("path does not exist: %r" % path)

def main():
    # parse arguments
    parser = argparse.ArgumentParser(description = "Display for OTAWA")
    parser.add_argument('-p', '--port', type=int, help="Port pour ce connecter à l'affichage à partir du navigateur")
    parser.add_argument('-w', '--work-dir', metavar="PATH", type=dir_path, default=os.getcwd(), help="Chemin du répertoire à analyser")
    parser.add_argument('-o', '--otawa-dir', metavar="PATH", type=dir_path, help="Chemin de l'installation d'Otawa")
    args = parser.parse_args()


    globals()['path_dir_serveur'] = os.path.dirname(sys.argv[0])

    config = default_config()
    print("existing config : ", existing_config(), flush=True)
    if existing_config == True:
        replace_value_config(config, read_config())
    else:
        init_config()

    apply_config(config)

    if args.port is not None:
        globals()['PORT'] = args.port
    if args.otawa_dir is not None:
        globals()['path_dir_otawa'] = args.otawa_dir

    
    globals()['path_dir_serveur_resources'] = os.path.join(globals()['path_dir_serveur'],'resources') # Chemin vers les ressources de cette application
    globals()['path_dir_otawa_bin'] = os.path.join(globals()['path_dir_otawa'], "bin") # Chemin vers les sources de cette application
    globals()['path_dir_workspace'] = args.work_dir           # Chemin vers le répertoire à annalyser

    print(globals()['path_dir_otawa'], flush=True)
    print(globals()['path_dir_otawa_bin'], flush=True)
    print(globals()['path_dir_serveur_resources'], flush=True)
    print(globals()['path_dir_workspace'], flush=True)
    print("@@@@@@@@@@@@@@@@\n\n", flush=True)


    # Lance le server d'écoute de requette Http
    t = StartServer()
    t.start()

    # Ouvre le navigateur par defaut
    webbrowser.open("http://"+HOST+':'+str(PORT))

    # Attend que l'utilisateur veuille arreter le serveur
    
    def handlerSIGINT(signal, stack_frame):
        if t.is_alive() :
            t.stop()

        os._exit(0)
        
    signal.signal(signal.SIGINT, handlerSIGINT)

    text = ""
    while(text!="stop"):

        text = input("> ")

    if t.is_alive() :
        t.stop()

    os._exit(0)


if __name__ == "__main__":
    main()
