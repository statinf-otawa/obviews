# BE-affichage-statistique-otawa
Projet du bureau d'étude affichage statistique potable par serveur HTTP+HTML/javascript Tlse UT3 2021

## Instalation

> Python 3 est requis.

> ⚠ [Otawa](http://www.tracesgroup.net/otawa/?page_id=419) doit être installé avant de passer à la suite.

- Téléchargé le contenue du répertoire src de ce projet
- Déplacer son contenue dans le répertoire bin du répertoire d'installation d'OTAWA.
    + Si vous placer le contenue de src dans un autre répertoire, modifier dans le fichier `config.json` le champ `otawa-path` avec le chemin vers le répertoire d'installation d'OTAWA
    + Pour générer le fichier de configuration, exécuté l'application avec le paramètre `--config` : `serv.py --config`. Le fichier `config.json` est généré avec des valeurs par défaut. ⚠ si le fichier `config.json` existe déjà, il sera remplacer.

## Exécution

- Lancer un invite de commande.
- Placer vous dans le répertoire avec l'exécutable à analyser.
- Lancer le fichier serv.py que vous avez extrait de `src`
- Un navigateur se lance avec l'application Obviews dedans.

## Paramètre de serv.py


| Paramètre           | Description                                                  |
| ------------------- | ------------------------------------------------------------ |
| --config            | Génère un fichier de configuration par default. Attention si le fichier config.json existe déjà, il sera remplacé. |
| -p/--port NUM       | Numéro de port (NUM) pour ce connecter à l'affichage à partir du navigateur |
| -w/--work-dir PATH  | Chemin du répertoire à analyser                              |
| -o/--otawa-dir PATH | Chemin de l'installation d'Otawa                             |

## List Commande
| Commande                                           | Paramètre                          | Sortie | Description                                                  | Exemple                                                      |
| -------------------------------------------------- | ---------------------------------- | ------ | ------------------------------------------------------------ | ------------------------------------------------------------ |
| http://127.0.0.1:8000/                             |                                    | html   | Page d'accueil de l'application                              | http://127.0.0.1:8000/                                       |
| http://127.0.0.1:8000/stats/code/{$fichier_source} | colored_by                         | html   | Retourne un html du code source indiqué par `$fichier_source` avec les stats du nombre de passages et du temps passé par instruction. Avec le paramètre color_by, on peut indiquer si on veut que les lignes de code soit colorié selon le nombre de passages (`count`, valeur par défaut) ou le temps passé (`time`). | http://127.0.0.1:8000/stats/code/bs.c                        |
| http://127.0.0.1:8000/stats/list_cfgs              |                                    | json   | Retourne la liste des nom des cfg associé à leur identifiant | http://127.0.0.1:8000/stats/list_cfgs                        |
| http://127.0.0.1:8000/stats/cfg/{$id_cfg}          | colored_by                         | .dot   | Retourne le cfg en fichier `.dot` de {$id_cfg} correspondant à une fonction. Si non  indiqué, renvoi celui du `main`. Avec le paramètre color_by, on peut indiquer si on veut que le cfg soit colorié selon le nombre de passages (`count`, valeur par défaut) ou le temps passé (`time`). | http://127.0.0.1:8000/stats/cfg/_0 http://127.0.0.1:8000/stats/cfg/_1 |
| http://127.0.0.1:8000/set                          | otawa-dir work-dir save_config     |        | Permet de paramétré des valeur du serveur. Les paramètre peuvent être envoyé simultanément en les séparant par un `&`. `otawa-dir` indique le chemin d'installation et `work-dir` indique ou est l'espace de travail du serveur, c'est à dire ou sont enregistrées puis les stats sont lue. Si le paramètre `save_config=True` est envoyé, les paramètre envoyé qui peuvent être stocké dans le fichier de configuration seront enregistré dedans et pourront être réutilisé par le serveur au prochain redémarrage également. | http://127.0.0.1:8000/set?otawa-dir=/home/dd/OTAWA  http://127.0.0.1:8000/set?otawa-dir=/home/dd/OTAWA&work-dir=/home/dd/work&svae_config |
| http://127.0.0.1:8000/get                          | otawa-dir work-dir                 | json   | Retourne les valeurs des paramètres demandé                  | http://127.0.0.1:8000/get?otawa-dir http://127.0.0.1:8000/get?work-dir http://127.0.0.1:8000/get?otawa-dir&work-dir |
| http://127.0.0.1:8000/wcet/list_scripts            |                                    | json   | Retourne la liste des scripts pouvant être exécuté par wcet  | http://127.0.0.1:8000/wcet/list_scripts                      |
| http://127.0.0.1:8000/wcet/run                     | executable flowfacts script target |        | Lance l'analyse par wcet de l'exécutable indiqué par le champs obligatoire `executable` avec la possibilité d'indiqué le fichier `flowfacts` associé. Possibilité de choisir avec quel `script` sera analysé le programme parmi ceux renvoyé par http://127.0.0.1:8000/wcet/list_scripts et avec la possibilité de choisir la fonction de départ (default : main). | http://127.0.0.1:8000/wcet/run?executable=/home/labwork1/bs/bs.elf&script=lpc2138&flowfacts=/home/labwork1/bs/bs.ff |
| http://127.0.0.1:8000/stop                         |                                    |        | Arrête le serveur                                            | http://127.0.0.1:8000/stop                                   |

## Contributeur
- Hermès Desgrez Dautet
- Jean-Baptiste Ragues
- Sylvain Roelants
- Hugues Cassé
