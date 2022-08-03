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

