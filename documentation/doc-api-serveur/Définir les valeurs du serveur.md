# Définir les valeurs du serveur

Permet de paramétré des valeur du serveur. Les paramètre peuvent être envoyé simultanément en les séparant par un `&`. `otawa-dir` indique le chemin d'installation et `work-dir` indique ou est l'espace de travail du serveur, c'est à dire ou sont enregistrées puis les stats sont lue. Si le paramètre `save_config=True` est envoyé, les paramètre envoyé qui peuvent être stocké dans le fichier de configuration seront enregistré dedans et pourront être réutilisé par le serveur au prochain redémarrage également.



[TOC]

## Requête

**Méthode** : `Get`

```http
http://127.0.0.1:8000/set
```



## Paramètres

### Query

| Paramètre   | Type    | Requis | Enregistrable dans le fichier de configuration | Description                                                  |
| ----------- | ------- | ------ | ---------------------------------------------- | ------------------------------------------------------------ |
| otawa-dir   | String  | False  | True                                           | Chemin vers l'installation d'OTAWA                           |
| work-dir    | String  | False  | False                                          | Chemin vers le répertoire de travail à analyser.             |
| save_config | Boolean | False  | False                                          | Peut prendre les valeur True ou False (par défaut) pour indiquer si les valeurs enregistrables dans le fichier de configuration seront enregistrées dans le fichier `config.json`qui sauvegarde la configuration du serveur. |



## Réponse 

- Succès

| Code     | Content-Type                | Body                                       |
| -------- | --------------------------- | ------------------------------------------ |
| `200 Ok` | `text/plain; charset=utf-8` | Valeur de work-dir et otawa-dir du serveur |



## Exemple

### Exemple 1

***Requête***

```http
http://127.0.0.1:8000/set?work-dir=/home/sylvain/Documents/[BE]-OTAWA/labwork1/bs
```

**Résultat**

- Code : `200 OK`
- Content-type : `text/plain; charset=utf-8`
- Body :   

```
work-dir : /home/sylvain/Documents/[BE]-OTAWA/labwork1/bs 
otawa-dir : /home/sylvain/Documents/[BE]-OTAWA/OTAWA
```



### Exemple 2

***Requête***

```http
http://127.0.0.1:8000/set?otawa-dir=/home/sylvain/OTAWA
```

**Résultat**

- Code : `200 OK`
- Content-type : `text/plain; charset=utf-8`
- Body :   

```
work-dir : /home/sylvain/Documents/[BE]-OTAWA/labwork1/bs 
otawa-dir : /home/sylvain/OTAWA
```



### Exemple 3

***Requête***

```http
http://127.0.0.1:8000/set?work-dir=/home/sylvain/Documents/[BE]-OTAWA/labwork1/bs &otawa-dir=/home/sylvain/OTAWA&save_config=True
```

**Résultat**

- Code : `200 OK`
- Content-type : `text/plain; charset=utf-8`
- Body :   

```
work-dir : /home/sylvain/Documents/[BE]-OTAWA/labwork1/bs 
otawa-dir : /home/sylvain/OTAWA
```

La valeur de otawa-dir a été enregistré dans le fichier de configuration et sera utilisé par le serveur pour les prochains redémarrages

- *`config.json`*

```json
{
  "server": {
    "PORT": 8000,
    "HOST": "127.0.0.1"
  },
  "otawa-path": "/home/sylvain/OTAWA"
}
```

