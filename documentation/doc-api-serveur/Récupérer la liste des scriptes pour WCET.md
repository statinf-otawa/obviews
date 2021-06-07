# Récupérer la liste des scriptes pour WCET

Retourne la liste des scripts pouvant être exécuté par wcet




[TOC]

## Requête

**Méthode** : `Get`

```http
http://127.0.0.1:8000/wcet/list_scripts
```



## Réponse 

- Succès

| Code     | Content-Type                      | Body                                                 |
| -------- | --------------------------------- | ---------------------------------------------------- |
| `200 Ok` | `application/json; charset=utf-8` | Json avec la liste des scriptes utilisable pour wcet |



## Exemple

***Requête***

```http
http://127.0.0.1:8000/wcet/list_scripts
```

**Résultat**

- Code : `200 OK`
- Content-type : `application/json; charset=utf-8`
- Body :   

```json
["generic", "lpc2138", "trivial"]
```

