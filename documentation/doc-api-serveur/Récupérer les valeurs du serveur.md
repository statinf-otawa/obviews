# Récupérer les valeurs du serveur

Retourne les valeurs des paramètres demandé



[TOC]

## Requête

**Méthode** : `Get`

```http
http://127.0.0.1:8000/get
```



## Paramètres

### Query

| Paramètre | Type   | Requis | Description                                      |
| --------- | ------ | ------ | ------------------------------------------------ |
| otawa-dir | String | False  | Chemin vers l'installation d'OTAWA               |
| work-dir  | String | False  | Chemin vers le répertoire de travail à analyser. |



## Réponse 

- Succès

| Code     | Content-Type                      | Body                                |
| -------- | --------------------------------- | ----------------------------------- |
| `200 Ok` | `application/json; charset=utf-8` | Valeur demandé renvoyé dans un json |



## Exemple

### Exemple 1

***Requête***

```http
http://127.0.0.1:8000/set?otawa-dir=/home/sylvain/OTAWA
```

**Résultat**

- Code : `200 OK`
- Content-type : `application/json; charset=utf-8`
- Body :   

```json
{"otawa-dir": "/home/sylvain/Documents/[BE]-OTAWA/OTAWA"}
```



### Exemple 2

***Requête***

```http
http://127.0.0.1:8000/get?work-dir
```

**Résultat**

- Code : `200 OK`
- Content-type : `application/json; charset=utf-8`
- Body :   

```
{"work-dir": "/home/sylvain/Documents/[BE]-OTAWA/labwork1/bs"}
```



### Exemple 3

***Requête***

```http
http://127.0.0.1:8000/get?otawa-dir&work-dir
```

**Résultat**

- Code : `200 OK`
- Content-type : `application/json; charset=utf-8`
- Body :   

```
{"work-dir": "/home/sylvain/Documents/[BE]-OTAWA/labwork1/bs", 
"otawa-dir": "/home/sylvain/Documents/[BE]-OTAWA/OTAWA"}
```

