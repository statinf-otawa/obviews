# Récupérer le code source avec statistique

Retourne la liste des nom des cfgs associé à leur identifiant




[TOC]

## Requête

**Méthode** : `Get`

```http
http://127.0.0.1:8000/stats/list_cfgs
```



## Réponse 

- Succès

| Code     | Content-Type                      | Body                                   |
| -------- | --------------------------------- | -------------------------------------- |
| `200 Ok` | `application/json; charset=utf-8` | Json avec la liste des cfgs disponible |



## Exemple

***Requête***

```http
http://127.0.0.1:8000/stats/list_cfgs
```

**Résultat**

- Code : `200 OK`
- Content-type : `application/json; charset=utf-8`
- Body :   

```json
  [{"id": "_0", "label": "main"}, {"id": "_1", "label": "binary_search"}]
```

