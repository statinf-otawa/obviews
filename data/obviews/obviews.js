/*
 *	Obviews JS script
 *
 *	This file is part of OTAWA
 *	Copyright (c) 2022, IRIT UPS.
 *
 *	OTAWA is free software; you can redistribute it and/or modify
 *	it under the terms of the GNU General Public License as published by
 *	the Free Software Foundation; either version 2 of the License, or
 *	(at your option) any later version.
 *
 *	OTAWA is distributed in the hope that it will be useful,
 *	but WITHOUT ANY WARRANTY; without even the implied warranty of
 *	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *	GNU General Public License for more details.
 *
 *	You should have received a copy of the GNU General Public License
 *	along with OTAWA; if not, write to the Free Software
 *	Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 */


/****** Application state ******/
const MODE_NOTHING = 0;
const MODE_FUNCTION = 1;
const MODE_SOURCE = 2;
var MAIN = {
	mode:		MODE_NOTHING,
	id: 		null,
	name:		"",
	stat:		0,
	stat_name:	"",
	vmask:		0,
	ovmask:		0,
	stack:		[],
	code: 		null
};
var HOST = window.location.host;


/****** Convenient functions ******/

function ajaxGet(url, callback) {
    var req = new XMLHttpRequest();
    req.open("GET", url);
    req.addEventListener("load", function(){
        if(req.status >= 200 && req.status < 400)
            callback(req.responseText);
        else
            console.error("req.status: " + req.status + " " + req.statusText + " " + url);
    });
    req.addEventListener("error", function(){
        console.error("Error with URL " + url);
    });
    req.send(null);
}

function clear_display(id){
	let answerDiv = document.getElementById(id);
	answerDiv.innerText = '';
}


/****** Main utilities ******/

function make_CFG(cont) {
	return {
		scale: 		1.,
		default_x: 0.,
		default_y: 0.,
		default_scale: 1.,
		step: 		.15,
		panning: 	false,
		bb_focus: 	false,
		pos:		{ x: 0, y: 0 },
		cont:		cont
	};
}

var CFG = null;
var CFG_MAP = new Map();

function cfg_transform() {
	var t =
		`translate(${CFG.pos.x}px, ${CFG.pos.y}px) scale(${CFG.scale}, ${CFG.scale})`;
	CFG.cont.style.transform = t;
}

function cfg_onmousedown(e) {
	CFG.bb_focus = true;
	if(e.button == 0) {
		elt = document.elementFromPoint(e.clientX, e.clientY)
		// if(elt.localName == "text") {
		// 	return;
		// }
		CFG.panning = true;
		return false;
	}
}


function cfg_onmousemove(e) {
	CFG.bb_focus = false;
	CFG.cont.style.transition = null;
	if(CFG.panning) {
		CFG.pos.x = CFG.pos.x + e.movementX;
		CFG.pos.y = CFG.pos.y + e.movementY;
		cfg_transform();
	}
}

function cfg_onmouseup(e) {
	if(e.button == 0) {
		CFG.panning = false;
	}
}



// CFG.pos refers to the position of the top left corner of the graph BEFORE any scaling takes place
// and changing the transform origin would mean we lose track of these values, 
// which are necessary for other functions. 
function cfg_zoom(isZoomingIn=true, mouseEvt) {
	CFG.cont.style.transition = `null`;
	var zoom = (isZoomingIn) ? 1+CFG.step : 1-CFG.step;

	if (
		(isZoomingIn == true && CFG.scale >= 10) ||
		(isZoomingIn == false && CFG.scale <= 0.1)
	) { 
		return; //don't scale if we're too far in or out
	}

	var srect = code.children[0].getBoundingClientRect();
	var viewport = document.getElementById("viewport").getBoundingClientRect();

	// set viewport centerpoint coordinates
	if (typeof mouseEvt === "undefined") { //from zoom buttons
		var scalecenter = { 
			x: viewport.width/2, 
			y: viewport.height/2
		}
	}
	else { //from mousewheel
		var scalecenter = { 
			x: mouseEvt.pageX - viewport.x, 
			y: mouseEvt.pageY - viewport.y
		}; 
	}

	var graphcenter = { // graph centerpoint coordinates
		x: CFG.pos.x + (srect.width / CFG.scale / 2), 
		y: CFG.pos.y + (srect.height / CFG.scale /2)
	}; 

	var centerdist = { // vector of viewport center -> graph center
		x: graphcenter.x - scalecenter.x, 
		y: graphcenter.y - scalecenter.y
	};

	var newdist = { // distance from viewport to graph center after scaling
		x: centerdist.x * zoom,
		y: centerdist.y * zoom
	};

	var newgraphcenter = { //new graph centerpoint after scaling
		x: scalecenter.x + newdist.x, 
		y: scalecenter.y + newdist.y
	};

	var newpos = { // new position of the top left corner of the graph
		x: newgraphcenter.x - (srect.width / CFG.scale /2),
		y: newgraphcenter.y - (srect.height / CFG.scale /2)
	};


	CFG.scale = CFG.scale * zoom;
	CFG.pos.x = newpos.x;
	CFG.pos.y = newpos.y;
	cfg_transform();
}

// center on a given block by its address of type int (Hex)
function cfg_center_block_qt_event(block_addr) {
	const addrTitleRegex = new RegExp("(?<addr>[0-9a-fA-F]+):");
	// browse all node to find the one with an address equal to the input
	allNode = document.getElementsByClassName("node");
	for (let node of allNode) {
		// extract address from BB title
		var nodeTitle = node.getElementsByTagName('text')[0].innerHTML;
		var found = nodeTitle.match(addrTitleRegex);
		if (found !== null) {
			var nodeAddr = found.groups["addr"];
			// check if node address equal to the input address
			if (block_addr == parseInt(nodeAddr, 16)) {
				block = node;
				break;
			}
		}
	}
	if (!Object.is(block, null)) {
		CFG.bb_focus = true;
		cfg_center_block(block);
	}
}

/**
 * toggle color for visited/unvisited basic blocks (
 * @param {list<int>} adr_list list of unvisited BBs.
 * @param {boolean} toggle add/remove coloring.
*/
function color_unvisited_bb(adr_list, toggle) {
	const addrTitleRegex = new RegExp("(?<addr>[0-9a-fA-F]+):");
	allNode = document.getElementsByClassName("node");
	// browse all node to add/remove coloring
	if (toggle) {
		for (let node of allNode) {
			var nodeTitle = node.getElementsByTagName('text')[0].innerHTML;
			// extract address from BB title
			var found = nodeTitle.match(addrTitleRegex);
			if (found !== null) {
				var nodeAddr = found.groups["addr"];
				// check if node is visited or not and add color
				if (adr_list.includes(parseInt(nodeAddr, 16))) {
					// fill_node(node, "#FF474C"); // unvisited node in red
					node.children[1].setAttribute("stroke", "#FF474C");
					node.children[1].setAttribute("stroke-width", 2);
					node.children[2].setAttribute("fill", "#FF474C");
				}
				else {
					// fill_node(node, "#0EC481"); // visited node in green
					node.children[1].setAttribute("stroke", "#0EC481");
					node.children[1].setAttribute("stroke-width", 2);
					node.children[2].setAttribute("fill", "#0EC481");
				}
				// node.children[1].setAttribute("opacity", 0.5);
			}
		}
	}
	else {
		// remove all nodes color
		for (let node of allNode) {
			// fill_node(node, "white");
			node.children[1].setAttribute("stroke", "#3b90f3");
			node.children[1].setAttribute("stroke-width", 1);
			node.children[2].setAttribute("fill", "#1C69B6");
		}
	}
}

// center on a given block by its ID
function cfg_center_block_mouse_event(blockid) {
	var block = document.getElementById(blockid);
	cfg_center_block(block);
}

// center on a given block container
function cfg_center_block(block_cont) {
	if (CFG.bb_focus) {
		CFG.cont.style.transform = `initial`;
		CFG.cont.style.transition = `transform .5s`;
		CFG.pos.x = CFG.default_x;
		CFG.pos.y = CFG.default_y;
		var viewport_rect = document.getElementById("viewport").getBoundingClientRect();
		var svg_rect = code.children[0].getBoundingClientRect();
		var bb_rect = block_cont.getBoundingClientRect();

		CFG.pos.x += (svg_rect.width - bb_rect.width) / CFG.scale * CFG.default_scale / 2 - (bb_rect.x - svg_rect.x) / CFG.scale * CFG.default_scale;
		
		var height_to_center = bb_rect.height / CFG.scale;
		// check if block height fit in the screen to center on the block or on the header
		if (height_to_center > viewport_rect.height) {
			height_to_center = 50; // height of a block header (BBx)
		}
		CFG.pos.y += (viewport_rect.height - height_to_center * CFG.default_scale) / 2 - (bb_rect.y - svg_rect.y) / CFG.scale * CFG.default_scale;
		CFG.scale = CFG.default_scale;
		cfg_transform();
	}
	
}

// resets zoom and position
function cfg_reset() {
	CFG.cont.style.transform = `initial`;
	CFG.cont.style.transition = `transform .5s`;
	CFG.pos.x = CFG.default_x;
	CFG.pos.y = CFG.default_y;
	CFG.scale = CFG.default_scale;
	cfg_transform();
}

function cfg_onwheel(e) {
	if(e.wheelDelta < 0)
		cfg_zoom(false, e);
	else
		cfg_zoom(true, e);
}

function display_in_code(msg) {
	var code = document.getElementById("code");
	code.innerHTML = `<div class="hint">${msg}</div>`;
	MAIN.mode = MODE_NOTHING;
}

function fill_node(node, color) {
	if(node.children[1].tagName == "g")
		node = node.children[1].children[0].children[0];
	else
		node = node.children[1];
	node.setAttribute("fill", color);
}



/****** Statistics display ******/

function display_info(answer) {
	var t = document.getElementById("infos");
	t.innerHTML = answer;
}

function display_stat(answer) {
	let a = answer.split(" ");

	// Source case
	if(MAIN.mode == MODE_SOURCE) {
		var t = document.getElementById("stats");
		t = t.children[0]
		let a = answer.split(" ");
		t.children[0].children[2].innerHTML = MAIN.stat_name;
		let max = parseInt(a[1]);
		let n = COLORS.length;
		for(let i = 2; i < a.length; i += 2) {
			let l = parseInt(a[i]);
			let x = parseInt(a[i + 1]);
			let c = Math.floor((x - 1) * n / max);
			t.children[l].style.backgroundColor = COLORS[c];
			t.children[l].children[2].innerHTML = "" + x;
		}
	}

	// Function case
	else if(MAIN.mode == MODE_FUNCTION) {
		clear_function_stat();
		let max = parseInt(a[0])
		for(let i = 1; i < a.length; i+= 2) {
			let n = parseInt(a[i]);
			let g = document.getElementById("node" + (n + 1));
			let x = parseInt(a[i + 1]);
			let c = Math.floor((x - 1) * COLORS.length / max);
			fill_node(g, COLORS[c]);
		}
	}

	// display info if required
	if(MAIN.stat != 0)
		ajaxGet(
			`http://${HOST}/stat-info?stat=${MAIN.stat}`,
			display_info);
}

function show_stat(stat, name) {
	MAIN.stat = stat;
	MAIN.stat_name = name;
	cmd = null;

	// Source case
	if(MAIN.mode == MODE_SOURCE) {
		if(stat == 0)
			clear_source_stat();
		else
			cmd = "source-stat";
	}

	// Function case
	else if(MAIN.mode == MODE_FUNCTION) {
		if(stat == 0)
			clear_function_stat();
		else
			cmd = "function-stat";
	}
	
	// issue command if required
	if(cmd != null) {
		url  = new URL(`http://${HOST}/${cmd}`);
		url.searchParams.append("stat", stat);
		url.searchParams.append("id", MAIN.id);
		ajaxGet(url, display_stat);
	}
}


/****** Function display ******/

function display_context(answer) {
	var name = document.getElementById("main-name");
	name.innerHTML = answer;
}

function show_context() {
	ajaxGet(
		`http://${HOST}/context?id=${MAIN.id}`,
		display_context
	);
	
}

function clear_function_stat() {
	var g = document.getElementById("graph0");
	for(let c of g.getElementsByTagName("g"))
		if(c.id.startsWith("node"))
			fill_node(c, "white");
}
// compute initial (default) position and scale of CFG
function cfg_initial_position(code) {
	var viewport_rect = document.getElementById("viewport").getBoundingClientRect();
	var svg_rect = code.children[0].getBoundingClientRect();

	if(viewport_rect.width < svg_rect.width) {
		CFG.scale = viewport_rect.width / svg_rect.width;
		CFG.default_scale = CFG.scale;
		CFG.pos.x = -(svg_rect.width - viewport_rect.width) / 2;
		CFG.pos.y = -(svg_rect.height - svg_rect.height * CFG.scale) / 2
		CFG.default_y = CFG.pos.y;
		
	}
	else {
		CFG.pos.x = -(svg_rect.width - viewport_rect.width) / 2 / CFG.scale;
	}
	CFG.default_x = CFG.pos.x;
}

function display_function(answer) {
	
	// setup elements
	var code = document.getElementById("code");
	code.style.overflow = "clip";
	code.innerHTML = answer;
	var name = document.getElementById("main-name");
	name.innerHTML = MAIN.name;
	MAIN.mode = MODE_FUNCTION;
	enable_function();

	// set the configuration
	if(CFG_MAP.has(MAIN.id)) {
		CFG = CFG_MAP.get(MAIN.id);
		CFG.cont = code.children[0];
	}
	else {
		CFG = make_CFG(code.children[0]);
		CFG_MAP.set(MAIN.id, CFG);
	}
	cfg_initial_position(code)
	cfg_transform();

	// update events
	code.onmousedown = cfg_onmousedown;
	code.onmousemove = cfg_onmousemove;
	window.onmouseup = cfg_onmouseup;
	code.addEventListener("wheel", cfg_onwheel);

	// update context and stats
	show_context();
	if(MAIN.stat != 0)
		show_stat(MAIN.stat, MAIN.stat_name);
}

function show_function(num, name) {
	MAIN.id = num;
 	MAIN.name = name;
	display_in_code(`Loading function ${name}`);
	ajaxGet(
		`http://${HOST}/function/${num}?vmask=${MAIN.vmask}`,
		display_function
	);
}


/****** Source display ******/

function clear_source_stat() {	
	var t = document.getElementById("stats");
	t = t.children[0]
	t.children[0].children[2].innerHTML = "";
	for(let i = 0; i < t.childElementCount; i++) {
		t.children[i].style.backgroundColor = "white";
		t.children[i].children[2].innerHTML = "";
	}
}

function display_source(response) {
	var code = document.getElementById("code");
	code.style.overflow = "auto";
	code.innerHTML = response;
	var name = document.getElementById("main-name");
	name.innerHTML = MAIN.name;
	MAIN.mode = MODE_SOURCE;
	MAIN.stack = [];
	disable_function();

	if(MAIN.stat != 0)
		show_stat(MAIN.stat, MAIN.stat_name);
}

function show_source(path) {
	display_in_code(`Loading ${path}.`);
	MAIN.id = path;
	MAIN.name = path;
	let url = `http://${HOST}/source/${path}`;
	ajaxGet(url, display_source);
}


/****** Menu management ******/

function enable_function() {
	var e = document.getElementById("view-button");
	e.disabled = false;
	e.style.color = "#1c69b6ff";
	e.children[0].style.opacity = 1.;		
	e = document.getElementById("back-button");
	if(MAIN.stack.length == 0) {
		e.disabled = true;
		e.children[0].style.opacity = .25;
	}
	else {
		e.disabled = false;
		e.children[0].style.opacity = 1.;		
	}
	e = document.getElementById("zoom-in-button");
	e.disabled = false;
	e.children[0].style.opacity = 1.;		
	e = document.getElementById("zoom-out-button");
	e.disabled = false;
	e.children[0].style.opacity = 1.;
	e = document.getElementById("reset-button");
	e.disabled = false;
	e.children[0].style.opacity = 1.;
}

function disable_function() {
	var e = document.getElementById("view-button");
	e.disabled = true;
	e.style.color = "#1c69b64f";
	e.children[0].style.opacity = .25;		
	e = document.getElementById("back-button");
	e.disabled = true;		
	e.children[0].style.opacity = .25;
	e = document.getElementById("zoom-in-button");
	e.disabled = true;
	e.children[0].style.opacity = .25;
	e = document.getElementById("zoom-out-button");
	e.disabled = true;
	e.children[0].style.opacity = .25;
	e = document.getElementById("reset-button");
	e.disabled = true;
	e.children[0].style.opacity = .25;
}

function quit() {
	window.close();
}

function logOut(){
  let url = `http://${HOST}/stop`;
  ajaxGet(url, quit);
}

function about() {
	window.open("about.html", "obvious-about");
}

function mainWindow() {
	location.assign("index.html");
}

function help() {
	window.open("help.html", "obvious-help");
}

function view_change(e, n) {
	if(e.checked)
		MAIN.vmask |= 1 << n;
	else
		MAIN.vmask &= ~(1 << n);
}

function view_switch() {
	var menu = document.getElementById("view-menu");
	if((menu.style.display == "none") || (menu.style.display.length === 0))
		menu.style.display = "block";
	else {
		menu.style.display = "none";
		if(MAIN.vmask != MAIN.ovmask) {
			MAIN.ovmask = MAIN.vmask;
			//alert("view completed");
			if(MAIN.mode == MODE_FUNCTION)
				show_function(MAIN.id, MAIN.name);
		}
	}
}


function open_function(idx, name) {
	MAIN.stack = []
	show_function(idx, name);
}

function call_function(idx, name) {
	MAIN.stack.push({idx: MAIN.id, name: MAIN.name});
	show_function(idx, name);
}

function return_function() {
	if(MAIN.mode == MODE_FUNCTION && MAIN.stack.length >= 1) {
		let l = MAIN.stack.pop();
		show_function(l.idx, l.name);
	}
}


/***** Initialization ******/
MAIN.vmask = VIEW_MASK;
MAIN.ovmask = VIEW_MASK;
MAIN.code = document.getElementById("code");
disable_function();
