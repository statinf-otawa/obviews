# Récupérer des fichiers ressources

Retourne un fichier demandé qui est dans le répertoire `resources` du serveur.




[TOC]

## Requête

**Méthode** : `Get`

```http
http://127.0.0.1:8000/resources/{$fichier}
```



## Paramètres

### Path

| Paramètre | Type   | Requis | Description             |
| --------- | ------ | ------ | ----------------------- |
| fichier   | string | True   | Nom du fichier demandé. |



## Réponse 

- Succès

| Code     | Content-Type | Body                                                         |
| -------- | ------------ | ------------------------------------------------------------ |
| `200 Ok` |              | Fichier demandé contenue dans le répertoire `resources`du serveur. |

- Echec

| Code                        | Content-Type | Body                    |
| --------------------------- | ------------ | ----------------------- |
| `500 Internal Server Error` |              | Description de l'erreur |

## Exemple 1 

***Requête***

```http
http://127.0.0.1:8000/resources/index.html
```

**Résultat**

- Code : `200 OK`
- Content-type : `text/html; charset=utf-8 `
- Body :   

```html
<!DOCTYPE HTML>
<html>
    <head>
        <title>Index</title>
        <link rel="icon" href="http://127.0.0.1:8000/resources/logo-small.png" sizes="32x32">
    </head>
    <body>

        <h1> Page Index </h1>
		<p>
            Paragraphe de la page index.html
        </p>
    </body>
</html>
```



## Exemple 2 

***Requête***

```http
http://127.0.0.1:8000/resources/fichierInexistant
```

**Résultat**

- Code : ``500 Internal Server Error``
- Content-type : 
- Body :   

```html
[Errno 2] No such file or directory: '/home/OTAWA/bin/resources/fichierInexistant'
```



