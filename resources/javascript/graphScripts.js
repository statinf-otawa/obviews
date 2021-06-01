var mousePosition;
var offset = [0,0];
var isDown = false;
var divGraph = document.getElementById("server_answer");
var divGraphLinks = document.getElementById("graph_links");

divGraph.addEventListener('mousedown', function(e) {
    isDown = true;
    offset = [
        divGraph.offsetLeft - e.clientX,
        divGraph.offsetTop - e.clientY
    ];
}, true);

document.addEventListener('mouseup', function() {
    isDown = false;
}, true);

document.addEventListener('mousemove', function(event) {
    event.preventDefault();
    if (isDown) {
        mousePosition = {

            x : event.clientX,
            y : event.clientY

        };
        divGraph.style.left = (mousePosition.x + offset[0]) + 'px';
        divGraph.style.top  = (mousePosition.y + offset[1]) + 'px';
    }
}, true);

chargerLiensGraphe();