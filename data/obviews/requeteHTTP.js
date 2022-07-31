var SOURCE_NAME;
var STAT;
var STAT_NAME;
var HOST = "127.0.0.1";
var PORT = "8000";


// deprecated
var ID_NOM_FICHIER = "pathRepertory";
var ID_REPONSE_SERVEUR = "server_answer";
var GRAPH_WIDTH = 800;
var GRAPH_HEIGHT = 1000;
var ADDRESSE_IP = "127.0.0.1";
var NUM_PORT = "8000";


//Pour la fonction de coloration
var labels = ['ipet-total_time', 'ipet-total_count', ]; 
var backgrounds = ['#ffffff', '#eae7ff', '#d6cfff', '#c0b7ff', '#ab9eff', '#a194fa', '#9b8ef5', '#8c7ded', '#7b6ce3', '#7162dd']; 
var foregrounds = ['#000000', '#000000', '#000000', '#000000', '#000000', '#ffffff', '#ffffff', '#ffffff', '#ffffff', '#ffffff']; 
var s0 = [ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 2, 2, 2, 5, 9, 9, 0, 0, 0, 0, 6, 0, 0, 0, 3, 0, 0, 1, 1, 0, 0, 1, 1, 1, 1, 0, ]; 
var s1 = [ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 2, 2, 2, 9, 8, 8, 0, 0, 0, 0, 8, 0, 0, 0, 8, 0, 0, 2, 2, 0, 0, 2, 2, 2, 2, 0, ]; 

function displayGraph(graph){
  //clearDisplay()
  var viz = new Viz();

  viz.renderSVGElement(graph)
  .then(function(element) {
    afficherGrapheNouvelleFenetre(element);   
    //testNouvelleFenetre();
    //afficherGrapheMemeFenetre(element);  
  })
  .catch(error => {
  // Create a new Viz instance (@see Caveats page for more info)
  viz = new Viz();

  // Possibly display the error
  console.error(error);
  });
}

function graphToHTML(graph){
  var viz = new Viz();

  viz.renderSVGElement(graph)
  .then(function(element) {
    var newDiv = document.createElement("div");
    newDiv.appendChild(element);
    traitementReponseHTML(newDiv);
    return newDiv;
  })
  .catch(error => {
  // Create a new Viz instance (@see Caveats page for more info)
  viz = new Viz();

  // Possibly display the error
  console.error(error);
  });
}

function afficherGrapheMemeFenetre(element){
  let answerDiv = document.getElementById(ID_REPONSE_SERVEUR);
  answerDiv.append(element);
  traitementReponseHTML(answerDiv);
  traitementGraphHTML(answerDiv);
  answerDiv.style.transform = "scale(0.9, 0.9)"; //Faire en sorte de lire les valeurs de width et height (regex) et de scale pour que ça rentre parfaitement dans le cadre
  answerDiv.addEventListener('wheel', testResize);
  testNouvelleFenetre();
}

function afficherGrapheNouvelleFenetre(element){
  var strWindowFeatures = "";
  let graphHTML = document.createElement("p");
  graphHTML.append(element);
  traitementReponseHTML(graphHTML);
  let graphTitle = obtenirTitreGraphe(graphHTML);
  console.log(graphTitle);
  let colorationHTML = setColorationHTML();
  let windowObjectReference = window.open(`template.html#${graphTitle}`, `testGraph${graphTitle}`, strWindowFeatures);
  let templateHTML = `<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8"><link rel="stylesheet" href="resources/css/style.css"/><title>Template</title></head><body id="graph_body"><header><div id="enTete"> <img src="resources/images/Obviews.jpeg" alt="Obviews" /> </div><nav><ul><li><a href="index.html">Accueil</a></li><li><a href="html/mode-d'emploi.html">mode d'emploi</a></li></ul></nav></header><div id="graph_links">Liens</div>${colorationHTML}<div id="graph_border"><div id="graph_frame"><div id="server_answer"></div></div></div><footer>More information : <br><ul><li><a href="resources/html/about.html">About</a></li></ul></footer><script src="resources/javascript/node_modules/viz.js/viz.js"></script><script src="resources/javascript/node_modules/viz.js/full.render.js"></script><script src="resources/javascript/ajax.js"></script><script src="resources/javascript/requeteHTTP.js"></script><script src="resources/javascript/graphScripts.js"></script></body></html>`;
  windowObjectReference.document.write(templateHTML);
  windowObjectReference.document.close(); //Si il manque le close(), la page n'est pas prévenue de l'arret des modifications et peut ne pas se charger
  let answerDiv = windowObjectReference.document.getElementById(ID_REPONSE_SERVEUR);
  answerDiv.append(element);
  traitementReponseHTML(answerDiv);
  traitementGraphHTML(answerDiv);
  let graphWidth = obtenirLargeurGraphe(answerDiv)*1.33;
  let graphHeight = obtenirHauteurGraphe(answerDiv)*1.33;
  //console.log(graphWidth);
  //console.log(graphHeight);
  let graphWidthScale = GRAPH_WIDTH/graphWidth;
  let graphHeightScale = GRAPH_HEIGHT/graphHeight;
  let newScale = Math.min(graphWidthScale, graphHeightScale);
  answerDiv.style.transform = `scale(${newScale})`;
  let monSVG = windowObjectReference.document.getElementsByTagName("svg")[0];
  let monGraphe = windowObjectReference.document.getElementById("graph0");
  monSVG.offsetLeft = "200px";
  console.log(monSVG.offsetLeft);
  monGraphe.style.left = "400px";
  console.log(monGraphe.style.left);
  //monSVG.style.transform = "translate(0 0)";
  monGraphe.style.transform = "translate(0 0)";
  answerDiv.addEventListener('wheel', testResize);
  
}

function setColorationHTML(){
  let colorationHTML = "<br><br><div class='invisible'><label for='coloration'>Type de coloration : </label>";
  var radios = document.getElementsByName('coloration');

  for (var i = 0, length = radios.length; i < length; i++) {
    if (radios[i].checked) {
      colorationHTML += `<input type="radio" name="coloration" value="${radios[i].value}" checked="checked">${radios[i].value}</input>`;
    }else{
      colorationHTML += `<input type="radio" name="coloration" value="${radios[i].value}">${radios[i].value}</input>`;
    }
  }
  colorationHTML += "</div>";

  return colorationHTML;
}

function findColorationValue(){
  let colorationValue = "";
  var radios = document.getElementsByName('coloration');
  var i = 0;

  for (i, length = radios.length; i < length; i++) {
    if (radios[i].checked) {
      colorationValue = `${radios[i].value}`;
    }
  }

  return [i, colorationValue];
}

/*
function testNouvelleFenetre(){
  var strWindowFeatures = "";
  let rand = Math.floor(Math.random() * 1000); //Test de fenêtres avec un nom différent pour que la deuxième n'écrase pas la première
  let windowObjectReference = window.open(`template.html#${rand}`, `testGraph${rand}`, strWindowFeatures);
  let templateHTML = '<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8"><meta http-equiv="X-UA-Compatible" content="IE=edge"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Template</title></head><body><div id="graph_links" onload="chargerLiensGraphe();"></div><div id="server_answer"><p>tout</p></div><script src="./javascript/node_modules/viz.js/viz.js"></script><script src="./javascript/node_modules/viz.js/full.render.js"></script><script src="./javascript/ajax.js"></script><script src="./javascript/requeteHTTP.js"></script></body></html>';
  windowObjectReference.document.write(templateHTML);
  windowObjectReference.document.close(); //Si il manque le close(), la page n'est pas prévenue de l'arret des modifications et peut ne pas se charger
}
*/

function arbreLiens(html){
  let listeLiens = trouverLiens(traitementReponseHTML(html));
  let nouveauxLiens = new Array();

  listeLiens.forEach(function(myLink){
    let linkTarget = trouverCibleLien(myLink);
    let newHTML = graphToHTML()
  });
}

function obtenirLargeurGraphe(answerDiv){
  var str = answerDiv.innerHTML.toString();
  return (str.match(/width="([^\#]*?)"/)[1]).replace(/pt/g, '');
}

function obtenirTitreGraphe(div){
  var str = div.innerHTML.toString();
  return (str.match(/\<title\>([^\#]*?)\<\/title\>/)[1]).replace(/pt/g, '');
}

function obtenirHauteurGraphe(answerDiv){
  var str = answerDiv.innerHTML.toString();
  return (str.match(/height="([^\#]*?)"/)[1]).replace(/pt/g, '');
}

function traitementReponseHTML(answerDiv){
  var str = answerDiv.innerHTML.toString();
  str = JSON.stringify(str);
  str = str.replace(/\\n/g,'');
  str = str.replace(/\\/g,'');
  answerDiv.innerHTML = str;
}

function traitementGraphHTML(graphDiv){
  var str = graphDiv.innerHTML.toString();
  var n1 = trouverLiens(str);
  
  if(n1 != null){
    n1.forEach(function(myLink){
      var linkName = trouverCibleLien(myLink);
      myLink = remplacerLienParAppelFonction(myLink, linkName, 0);
      graphDiv.innerHTML = remplacerLiensDansHTML(graphDiv.innerHTML, myLink);
    });
  }
}

function trouverLiens(str){
  let regex = /<a(.*?)\/a>/g;
  return str.match(regex);
}

function trouverCibleLien(myLink){
  console.log(myLink);
  myLink = myLink.replace(/\.dot/, "");
  console.log(myLink);
  return myLink.match(/xlink:href="([^\#].*?)"/)[1];
}

function remplacerLienParAppelFonction(link, target, numFonction){
  switch (numFonction) {
    case 0:
      return link.replace(/xlink:href="([^\#].*?)"/, 'xlink:href="#" onclick="getGraphData(\'' + target + '\');"');
      break;
  
    default:
      return link.replace(/xlink:href="([^\#].*?)"/, 'xlink:href="#" onclick="getGraphData(\'' + target + '\');"');
      break;
  }
}

function remplacerLiensDansHTML(html, newLink){
  return html.replace(/\<a xlink:href="([^\#].*?)"(.*?)\/a>/g, newLink);
}


function displaySources(reponse){
  clearDisplay("source_code");
  var answerDiv = document.getElementById("source_code");
  var answerHTML = document.createElement("p");
  answerHTML.innerHTML = reponse;
  answerDiv.appendChild(answerHTML);
  //traitementReponseHTML(answerDiv);
  traitementDataHTML(answerDiv);
  console.log(reponse);
}

function displayCode(reponse){
  clearDisplay("source_code");
  console.log("DisplayCode");
  var answerDiv = document.getElementById("source_code");
  var answerHTML = document.createElement("p");
  let [colorIndex, colorationValue] = findColorationValue();
  answerHTML.innerHTML = reponse;
  answerDiv.appendChild(answerHTML);
  //traitementReponseHTML(answerDiv);
  colorize(`s${colorIndex}`, `ipet-total_${colorationValue}`);
  console.log(reponse);
}

function traitementDataHTML(dataDiv){
  var str = dataDiv.innerHTML.toString();

  let regex = /<a(.*?)\/a>/g;
  var n1 = str.match(regex);
  //console.log(n1);
  
  if(n1 != null){
    n1.forEach(function(myLink){
      var linkName = myLink.match(/href="([^\#].*?)"/)[1];
      console.log(linkName);
      myLink = myLink.replace(/href="([^\#].*?)"/, 'href="#" onclick=getCodeData("' + linkName + '")');
      dataDiv.innerHTML = dataDiv.innerHTML.replace(/\<a href="([^\#].*?)"(.*?)\/a>/g, myLink);
    });
  }
}

function testResize(evt){
  console.log("resize !");
  evt.preventDefault();

  let maDiv = evt.currentTarget;
  let oldScale = maDiv.style.transform.toString();
  let scaleValueRegex = /\(([^)]+)\)/;
  let oldScaleValue = parseFloat(oldScale.match(scaleValueRegex)[1]);

  let newScaleValue = oldScaleValue +  evt.deltaY * -0.001;

  // Restrict scale
  newScaleValue = Math.min(Math.max(.125, newScaleValue), 2);

  // Apply scale transform
  maDiv.style.transform = `scale(${newScaleValue})`;
  console.log(oldScaleValue);
  console.log(newScaleValue);
}

function clearDisplay(divName){
  let answerDiv = document.getElementById(divName);
  answerDiv.innerText = '';
}

function testRemplissageDiv(divName){
  clearDisplay(divName);
  let maDiv = document.getElementById(divName);
  var remplissageHTML = document.createElement("p");
  remplissageHTML.innerHTML = "<p>Remplissage</p>";
  maDiv.appendChild(remplissageHTML);
}

function getData(){
  let nomFichier = document.getElementById(ID_NOM_FICHIER).value;
  /*
  if(nomFichier.length > 1){
    getCodeData(nomFichier);
  }else{
    getSources();
  }
  */
  getSources();
}

function getSources(){
  let url = `http://127.0.0.1:8000/stats/code/`;
  ajaxGet(url, displaySources);
}

function getGraphData(graphName){
  let typeColoration = "count";

  var radios = document.getElementsByName('coloration');

  for (var i = 0, length = radios.length; i < length; i++) {
    if (radios[i].checked) {
      typeColoration = radios[i].value;
      break;
    }
  }

  var url = `http://127.0.0.1:8000/stats/cfg/${graphName}?colored_by=${typeColoration}`;
  //var url = `http://127.0.0.1:8000/stats/cfg`;
  ajaxGet(url, displayGraph);
}


function getCodeData(codeName){
  let typeColoration = "count";
  let url = `http://127.0.0.1:8000/stats/code/${codeName}?colored_by=${typeColoration}`;
  ajaxGet(url, displayCode);
}

function testFonction(){
  alert("ça marche !");
}

function chargerLiensGraphe(){
  console.log("chargerLiensGraphes !");
  let url = "http://127.0.0.1:8000/stats/list_cfgs";
  ajaxGet(url, afficherLiensGraphe);
}

function afficherLiensGraphe(reponse){
  let liens = JSON.parse(reponse);
  let divLiens = document.getElementById("graph_links");
  divLiens.innerHTML = "<p>Liens :<br>"

  liens.forEach(function(lien){
    //divLiens.innerHTML = divLiens.innerHTML + `<p>${lien.id}</p>`;
    //divLiens.innerHTML = divLiens.innerHTML + `<a href="#" onclick="getGraphData('${lien.id}');" name="voir_graphe">${lien.label} (${lien.id})</a><br>`;
   divLiens.innerHTML = divLiens.innerHTML + `<a href="javascript:getGraphData('${lien.id}')"  name="voir_graphe">${lien.label} (${lien.id})</a><br>`;

  });
  divLiens.innerHTML = divLiens.innerHTML + "</p>";
}

function colorize(backs, label) { 
  document.getElementById("label").textContent = label; 
  trs = document.getElementById("stats").getElementsByTagName("tr"); 
  for(i = 0; i < trs.length; i++) { 
    trs[i].style.backgroundColor = backgrounds[backs[i]]; 
    trs[i].style.color = foregrounds[backs[i]]; 
  } 
} 

function changeNumPort(){
  let newNumPort = document.getElementById("numPort").value;
  /*
  let url = `http://${ADDRESSE_IP}:${NUM_PORT}/`;
  ajaxGet(url);
  NUM_PORT = newNumPort;
  */
}

function doNothing(){
  console.log("...");
}

function changePathRepertory(){
  let pathRepertory = document.getElementById("pathRepertory").value;
  let url = `http://${ADDRESSE_IP}:${NUM_PORT}/set?work-dir=${pathRepertory}`;
  console.log("change repertory path to : " + pathRepertory);
  ajaxGet(url, updateInfos);
}

function updateInfos(){
  let url = `http://${ADDRESSE_IP}:${NUM_PORT}/get?otawa-dir&work-dir`;
  ajaxGet(url, changePathInfos);
}

function changePathInfos(reponse){
  /*let pathRepertoryDiv = document.getElementById("pathRepertory");
  let infosServeur = document.getElementById("infosServeur");
  let pathValues = JSON.parse(reponse);
  let workdirPath = pathValues["work-dir"];
  let otawadirPath = pathValues["otawa-dir"];
  //pathRepertoryDiv.value = workdirPath;
  infosServeur.innerHTML = `<p>Infos :<br>Chemin de l'installation d'Otawa : ${otawadirPath}<br>Chemin répertoire de travail : ${workdirPath}</p>`;*/
}


// *********************** NEW CODE ************************


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

function clear_display(id){
	let answerDiv = document.getElementById(id);
	answerDiv.innerText = '';
}


function display_source(response) {
	var code = document.getElementById("code");
	code.innerHTML = response;
	var name = document.getElementById("source-name");
	name.innerHTML = SOURCE_PATH;
	var bar = document.getElementById("source-bar");
	bar.style.display = 'flex';
}

function show_source(path) {
	SOURCE_PATH = path;
	let url = `http://${HOST}:${PORT}/source/${SOURCE_PATH}`;
	ajaxGet(url, display_source);
}

function clear_source_stat() {	
	var t = document.getElementById("stats");
	t = t.children[0]
	t.children[0].children[2].innerHTML = "";
	for(let i = 0; i < t.childElementCount; i++) {
		t.children[i].style.backgroundColor = "white";
		t.children[i].children[2].innerHTML = "";
	}
}

function display_stat_source(answer) {
	var t = document.getElementById("stats");
	t = t.children[0]
	let a = answer.split(" ");
	t.children[0].children[2].innerHTML = STAT_NAME;
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

function show_stat_source(stat, name) {
	STAT = stat;
	STAT_NAME = name;
	if(stat == 0)
		clear_source_stat();
	else {
		url = new URL(`http://${HOST}:${PORT}/source-stat`);
		url.searchParams.append("stat", stat);
		url.searchParams.append("src", SOURCE_PATH);
		ajaxGet(url, display_stat_source);
	}
}
