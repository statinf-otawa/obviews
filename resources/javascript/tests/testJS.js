var ID_REPONSE_SERVEUR = "server_answer";
var ID_IFRAME = "inlineFrameExample";
var wild;

//Se renseigner sur les <iframe>

function testNouvelleFenetre3(){
    wild = window.open("testTemplate.html", "mywin", '');
    wild[wild.addEventListener ? 'addEventListener' : 'attachEvent'](
    (wild.attachEvent ? 'on' : '') + 'load', function (e) {
        alert("loaded")
    }, false);
}

function testNouvelleFenetre(){
    var strWindowFeatures = "";
    let rand = Math.floor(Math.random() * 1000); //Test de fenêtres avec un nom différent pour que la deuxième n'écrase pas la première
    let windowObjectReference = window.open(`testTemplate.html#${rand}`, `testGraph${rand}`, strWindowFeatures);
    let templateHTML = '<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8"><meta http-equiv="X-UA-Compatible" content="IE=edge"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Template</title><link rel="stylesheet" href="../../BE-partiehtml/style.css"></head><body><div id="server_answer"></div></body></html>';
    windowObjectReference.document.write(templateHTML);
    windowObjectReference.document.close(); //Si il manque le close(), la page n'est pas prévenue de l'arret des modifications et peut ne pas se charger
    let answerDiv = windowObjectReference.document.getElementById(ID_REPONSE_SERVEUR);
    //console.log(answerDiv);
    answerDiv.append("prout");
}

/*
window.addEventListener('DOMContentLoaded', function(e) {
    wild = window.open("testTemplate.html", "mywin", '');
    wild[wild.addEventListener ? 'addEventListener' : 'attachEvent'](
        (wild.attachEvent ? 'on' : '') + 'load', function (e) {
        alert("loaded")
        }, false);
});
*/
/*
document.addEventListener('click', function(e) {
    try {
        alert(document.body.innerHTML);
    } catch(err) {
        alert(err);
    }
}, false);
*/

function testNouvelleFenetre2(){
    var strWindowFeatures = "";
    //let rand = Math.floor(Math.random() * 1000); //Test de fenêtres avec un nom différent pour que la deuxième n'écrase pas la première
    let nouvelleFenetre = window.open(`./testTemplate.html`, `testGraph`, strWindowFeatures);
    //nouvelleFenetre.document.write("bonjour");
    //nouvelleFenetre.document.close(); //Si il manque le close(), la page n'est pas prévenue de l'arret des modifications et peut ne pas se charger
    //let answerDiv = nouvelleFenetre.document.getElementById(ID_REPONSE_SERVEUR);
    /*
    nouvelleFenetre.onload = function() {
        nouvelleFenetre.document.body.innerHTML="<p>Hey you!!</p>";
        console.log("ok");
    }
    */
    nouvelleFenetre.addEventListener('load', ()=> console.log('hi'), false);
    nouvelleFenetre.document.title = "test";
    //console.log(nouvelleFenetre.document.body.innerHTML);
    /*
    console.log(nouvelleFenetre.document.location.toString());
    nouvelleFenetre.document.location.replace("file:///home/jb/Bureau/Otawa/labwork1/OtawaTests/javascript/tests/testTemplate.html");
    console.log(nouvelleFenetre.document.location.toString());
    console.log(nouvelleFenetre.document.body.innerHTML);
    */
}

function testAfficherHTML(){
    let answerDiv = nouvelleFenetre.document.getElementById(ID_REPONSE_SERVEUR);
    console.log(answerDiv);
}

function testAfficherIframe(){
    let iframeDiv = document.getElementById(ID_IFRAME);
    console.log(iframeDiv.contentWindow.document.body.innerHTML);
}

function testOnLoad(){
    console.log("on load !");
    console.log(document.body.innerHTML);
}