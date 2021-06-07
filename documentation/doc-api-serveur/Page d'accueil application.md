# Page d'accueil

La page d'accueil est la première page affiché par l'application Obviews.

![Accueil](images\Accueil.png)



[TOC]

## Requête

**Méthode** : `Get`

```http
http://127.0.0.1:8000/
```

Demande la page d'accueil de l'application Obviews. Cette page d'accueil est le fichier index.html du répertoire `resources`.

```
Obvious
   |-- serv.py
   |-- config.json
   |-- resources
          |-- index.html
```



## Réponse

***Code Retour***

- Succès

  | Code     | Content-Type                | Body                           |
  | -------- | --------------------------- | ------------------------------ |
  | `200 Ok` | ``tetx/html; charset=utf-8` | Fichier `resources/index.html` |



## Exemple

***Requête\***

```http
http://127.0.0.1:8000/
```

**Résultat**

- Code : `200 OK`
- Content-type : `text/html; charset=utf-8`
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



