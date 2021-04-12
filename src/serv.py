from http.server import BaseHTTPRequestHandler, HTTPServer
import webbrowser
from threading import Thread
import urllib.parse
import os

params = '127.0.0.1', 8000

def controler(path='', query=None):
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

    if(lien[1] == "stats"):
        if(len(lien) < 3  or lien[2].split('/',1)[0]==""):    # /stats/
            return open('main-otawa/src/index.html', 'rb').read()
        else:                                                 # /stats/...
            return open('main-otawa/src/'+lien[2], 'rb').read()

    else:                                                     # /
        return open('index.html', 'rb').read()
        


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        print("\n")
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        urlP = urllib.parse.urlparse(self.path)
        print(urlP)

        f = controler(urlP.path)

        self.wfile.write(f)

    do_POST = do_GET

class StartServer(Thread):
    def __init__(self):
        super().__init__()
        self.server = None

    def run(self):
        print("run server")
        with HTTPServer(params, handler) as self.server:
            self.server.serve_forever()

    def stop(self):
        if (self.server is not None):
            self.server.shutdown()

# Lance le server d'écoute de requette Http
t = StartServer()
t.start()

# Ouvre le navigateur par defaut
webbrowser.open("http://"+params[0]+':'+str(params[1]))

# Attend que l'utilisateur veuille arreter le serveur
text = ''
while(text!="stop"):

    text = input("> ")

if t.is_alive() :
    t.stop()

os._exit(0)




