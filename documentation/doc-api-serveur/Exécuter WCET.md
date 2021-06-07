# Arrêter le serveur

 Lance l'analyse par wcet de l'exécutable indiqué par le champs obligatoire `executable` avec la possibilité d'indiquer le fichier `flowfacts` associé. Possibilité de choisir avec quel `script` sera analysé le programme parmi ceux renvoyé par http://127.0.0.1:8000/wcet/list_scripts (voir [liste des scriptes](Récupérer%20la%20liste%20des%20scriptes%20pour%20WCET.md)) et avec la possibilité de choisir la fonction de départ (default : main).



> ⚠ Pour pouvoir exécuter wcet (owcet), OTAWA doit être installé et son chemin d'installation doit être précisé.
>
> Le chemin d'installation doit être précisé soit dans le fichier de configuration soit juste pour le lancement actuel en changeant les valeur du serveur.
>
> Voir : [Définir les valeurs du serveur](Définir%20les%20valeurs%20du%20serveur.md) et [Récupérer les valeurs du serveur](Récupérer%20les%20valeurs%20du%20serveur.md)



[TOC]

## Requête

**Méthode** : `Get`

```http
http://127.0.0.1:8000/wcet/run
```



## Paramètres

### Query

| Paramètre  | Type   | Requis | Valeurs          | Description                                                  |
| ---------- | ------ | ------ | ---------------- | ------------------------------------------------------------ |
| executable | string | True   |                  | Chemin vers l'exécutable à analyser                          |
| script     | string | False  | generic (defaut) | Script avec lequel sera analysé l'exécutable                 |
| flowfacts  | string | False  |                  | Flowfact généré avec mkff  (.ff) ou oRange (.ffx) qui indique les limite d'exécution des boucles ou des conditions |
| target     | string | False  | main (defaut)    | Nom de la fonction du programme à analyser. Si aucune valeur donné, analyse la fonction main. |



## Réponse 

- Succès

| Code     | Content-Type                | Body   |
| -------- | --------------------------- | ------ |
| `200 Ok` | `text/plain; charset=utf-8` | succes |

- Echec

| Code              | Content-Type                | Body  |
| ----------------- | --------------------------- | ----- |
| `400 Bad Request` | `text/plain; charset=utf-8` | error |



## Exemple

***Requête\***

```http
http://127.0.0.1:8000/wcet/run?executable=/home/labwork1/bs/bs.elf&script=lpc2138&flowfacts=/home/labwork1/bs/bs.ff
```

**Résultat**

- Code : `200 OK`
- Content-type : `text/plain; charset=utf-8`
- Body :   

```
succes
```

