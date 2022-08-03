// main widget management
const MODE_NOTHING = 0;
const MODE_FUNCTION = 1;
const MODE_SOURCE = 2;
var MAIN = {
	mode:		MODE_NOTHING,
	id: 		null,
	name:		"",
	stat:		0,
	stat_name:	""
};


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

var CFG = {
	scale: 		1.,
	step: 		.1,
	panning: 	false,
	pos:		{ x: 0, y: 0 },
	prev:		{ x: 0, y: 0 },
	cont:		null
};

function cfg_reset(cont) {
	CFG.scale = 1.;
	CFG.panning = false;
	CFG.pos.x = 0;
	CFG.pos.y = 0;
	CFG.prev.x = 0;
	CFG.prev.y = 0;
	CFG.cont = cont;
}

function cfg_transform() {
	var t =
		`scale(${CFG.scale}, ${CFG.scale}) translate(${CFG.pos.x}px, ${CFG.pos.y}px)`;
	CFG.cont.style.transform = t;
	//console.log("CFG transform: " + t);
}


function cfg_onmousedown(e) {
	if(e.button == 0) {
		//console.log("down: " + e.x + ", " + e.y + ", " + e.button);
		CFG.panning = true;
		CFG.prev.x = e.x;
		CFG.prev.y = e.y;
	}
}


function cfg_onmousemove(e) {
	if(CFG.panning) {
		var dx = e.x - CFG.prev.x;
		var dy = e.y - CFG.prev.y;
		CFG.prev.x = e.x;
		CFG.prev.y = e.y;
		//console.log("move: " + dx + ", " + dy);
		CFG.pos.x = CFG.pos.x + dx / CFG.scale;
		CFG.pos.y = CFG.pos.y + dy / CFG.scale;
		cfg_transform();
	}
}

function cfg_onmouseup(e) {
	if(e.button == 0) {
		//console.log("up: : " + e.x + ", " + e.y + ", " + e.button);
		CFG.panning = false;
	}
}

function cfg_onwheel(e) {
	//console.log("wheel: " + e.timeStemp + ", " + e. deltaMode + ", " + e.wheelDelta);
	if(e.wheelDelta > 0) {
		if(CFG.scale > CFG.step)
			CFG.scale = CFG.scale - CFG.step;
	}
	else
		CFG.scale = CFG.scale + CFG.step;
	cfg_transform();
}


function display_in_code(msg) {
	var code = document.getElementById("code");
	code.innerHTML = `<div class="hint">${msg}</div>`;
	MAIN.mode = MODE_NOTHING;
}


/****** Function display ******/

function display_function(answer) {
	var code = document.getElementById("code");
	code.style.overflow = "clip";
	code.innerHTML = answer;
	var name = document.getElementById("main-name");
	name.innerHTML = MAIN.name;
	MAIN.mode = MODE_FUNCTION;

	cfg_reset(code.children[0]);
	code.onmousedown = cfg_onmousedown;
	code.onmousemove = cfg_onmousemove;
	code.onmouseup = cfg_onmouseup;
	code.addEventListener("wheel", cfg_onwheel);
}

function show_function(num, name, stat) {
	MAIN.id = num;
	MAIN.name = name;
	display_in_code(`Loading function ${name}`);
	ajaxGet(
		`http://${HOST}:${PORT}/function/${num}?stat=${stat}`,
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
}

function show_source(path) {
	display_in_code(`Loading ${path}.`);
	MAIN.id = path;
	MAIN.name = path;
	let url = `http://${HOST}:${PORT}/source/${path}`;
	ajaxGet(url, display_source);
}


/****** Statistics display ******/

function display_stat(answer) {

	// Source case
	if(MAIN.mode == MODE_SOURCE) {
		var t = document.getElementById("stats");
		t = t.children[0]
		//console.log(answer);
		let a = answer.split(" ");
		t.children[0].children[2].innerHTML = MAIN.name;
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
		display_function(answer);
	}
}

function show_stat(stat, name) {
	MAIN.stat = stat;
	MAIN.stat_name = name;

	// Source case
	if(MAIN.mode == MODE_SOURCE) {
		if(stat == 0)
			clear_source_stat();
		else {
			url = new URL(`http://${HOST}:${PORT}/source-stat`);
			url.searchParams.append("stat", stat);
			url.searchParams.append("src", MAIN.id);
			ajaxGet(url, display_stat);
		}		
	}

	// Function case
	else if(MAIN.mode == MODE_FUNCTION) {
		display_in_code(`Loading ${stat} for function ${name}`);
		ajaxGet(
			new URL(`http://${HOST}:${PORT}/function/${MAIN.id}?stat=${stat}`),
			display_function
		)
	}
}


/****** Menu management ******/

function quit() {
	window.close();
}

function logOut(){
  let url = `http://${HOST}:${PORT}/stop`;
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

