# url_filter
Ce logiciel sert a filtrer des pages web. Dans notre travail de comparaison
visuelle de sites internet, nous avons besoin de rapidement détécter les
différences entre 2 sites mais cela peut être problématique si les sites
ont beaucoup de différences récurrantes. Il faudrais alors faire le
travail mental de filtrer ces différences qui ne sont pas intéressantes et
repérer celles qui le sont. Le logiciel fait donc ce travail et le testeur
reçoit les sites filtrées des différences inintéressantes.

# Utilisation
## Récupération du dépôt
On récupère le dépôt avec:
```
git clone git@github.com:epfl-sdf/url_filter.git
```
(cette commande nécessite la présence de `git` sur l'ordinateur)

Pour executer les commandes des sections suivantes, il faut se mettre dans
le dossier du dépôt.

## Installation des outils nécessaires
Simplement avec la commande:
```
./install.sh
```
Pour que cette commande marche, il faut être sous Ubuntu ou une autre
distribution Linux utilisant `apt-get` comme gestionnaire de paquets et qui a les
mêmes noms de packets que sur les dépôts Ubuntu.

## Lancer le parser
Simplement avec la commande:
```
`/.start.sh proxy.sh ram_maximale`
```

`start.sh` est un script générique qui peut prendre n'importe quel script pour le
lancer avec une limite sur la quantité de la RAM utilisé pendant l'execution.

`proxy.sh` est donc un script qui contient une seule commande a la deuxième ligne
du fichier, il faut que ça soit explicitement `proxy.sh` pour lancer notre filtre.

`ram_maximale` est la quantité de RAM utilisé sur la machine à laquelle le script
va s'arrêter et se relancer lui même. Il faut noter que c'est la quantité de RAM
absolue sur le système et non seulement la RAM utilisé par notre programme.

## Configuration du Proxy

Cette commande lance un proxy web qui va filtrer les réponses aux requêtes qu'il
reçoit. Ce proxy va tourner sur le port `8080` de la machine. Pour l'utiliser,
il faut changer les paramètres d'un navigateur WEB si elles le permettent ou
directement les paramètres de proxy du système. Le proxy ne réponds qu'au traffic
HTTP et HTTPS donc il ne faut configurer le proxy que pour ces deux protocoles
dans les 2 cas.

De plus, comme nous avions besoin d'accepter les certificats de sécurité venant
du proxy, le proxy etant utilisé pour le traffic HTTPs également, il nous
faut accepter le certificat du proxy pour que le navigateur WEB accepte les
réponses du proxy aux requêtes HTTPS. Pour cela, il faut aller [ici](http://mitm.it).

### Example Firefox
Pour effectuer la configuration sur Firefox par exemple, on procède ainsi:

Pour configurer le proxy, il faut aller dans les paramètres avancés dans l'onglet "Réseau" 
puis les paramètres de la connexion. Dans la fenêtre qui s'ouvre, il faut choisir 
la configuration manuelle du proxy puis introduire l'adresse du proxy dans le 
champ "HTTP Proxy" et le port 8080 et cocher la case pour utiliser ce serveur 
proxy pour tous les protocoles puis appuyer sur OK.

Ensuite, il faut ajouter le certificat dans le navigateur pour les sites HTTPS.
Pour cela, une fois que le proxy est configuré dans le navigateur, il faut aller 
[ici](http://mitm.it), choisir "Other" puis chosir de confirmer l'AC pour identifier 
les sites web.

# Expliquation du logiciel

Le script qui se trouve dans `filter.py` ne va pas être lancé lui même. On utilise
içi un proxy implémenté en Python qui s'apelle [mitmproxy](https://mitmproxy.org/). 
On lui passe un script (dans notre cas `filter.py`) où on peut définir des comportements
spéciaux pour les évènements qui arrivent au proxy.

Dans notre cas, on ne fait quoi que ce soit seulement au moment d'une réponse que
le proxy effectue suite à une requête. Quand un testeur a demandé un site à tester
et verifier, le proxy va recevoir ce site, mais avant que la réponse soit
renvoyé, le contenu HTML de la réponse sera modifié. On utilise BeautifulSoup pour
effectuer ces modifications. On peut, avec cette librairie, facilement parcourir
un document HTML dans sa hierarchie et effectuer des modifications arbitraires.

On filtre deux types de sites, les sites de l'EPFL en Jahia et ceux en Wordpress.
Les modifications que l'on fait sur les une et les autres ne sont pas forcemment
les mêmes. Si la requête était pour un autre site, on le laisse passer sans
aucune modification.

On effectue les modifications suivantes sur les sites WordPress:
* Les sites WordPress nécessitent une connexion avant qu'elle peuvent être vues.
  On a ainsi fait en sorte que le navigateur se connecte automatiquement grâce
  au proxy. En effet, le proxy remplit les idéntifiants nécessaires pour le
  site sur les pages de connexions des sites WordPress et injecte un
  script pour que le navigateur appuie sur le bouton de connexion par lui même.
* La bare des réseaux sociaux était dupliquée, on a donc enlevé le doublon.
* À droite du site, où normalement se trouvent seulement des éléments du site
  Jahia, un nouveau menu commun aux sites WordPress, nous l'avons donc supprimé.
* De plus, les éléments de la colonne de droite de Jahia étaient dans le
  mauvais ordre. Nous les avons donc retriés dans l'ordre d'origine.
* Les sites WordPress avaient de plus une barre d'administration du site en haut
  de la page à cause de la connexion. Nous l'avons supprimé.
* Nous avons ajouté un filet où le numéro de version du proxy est affiché
  pour qu'on puisse facilement voir si on passe bien par un proxy et savoir
  lequel on utilise.

On effectue les modifications suivantes sur les sites Jahia:
* Les sites Jahia ont parfois une boîte colorée dans la colonne à droite du
  site. Cette boîte n'étant pas colorée sur les sites Wordpress, nous avons donc
  enlevée la coloration de la boîte sur les sites Jahia.

On effectue les modifications suivantes sur les 2 types de sites:
* On enlève la protéction de corss-origin qui empêcherais les sites à être
  ouvertes dans des `iframe` par example. Dans notre console de comparaison
  de site, on charge justement les 2 sites à comparer dans des `iframe`,
  mais si un site contient cette protection, le navigateur va empêcher
  que le site se charge.
* Les footers des deux sites était différents, nous les avons donc supprimé.
* On change les couleurs trouvé sur le site vers la couleur de base rouge des
  sites de l'EPFL. On fait ceci car tous les sites WordPress ont cette couleur
  alors que les sites Jahia ont une couleur spécifique a chaque site.
* Comme nous ouvrons les sites dans des `iframe`s étroites, le mode responsif
  des sites est enlevé.
* Le site envoi des informations à note console de comparaison (qui sera le parent
  de la fenêtre où la page est affichée dans notre console) concernant la taille
  du site pour bien afficher les 2 `iframe` ainsi que l'URL de la page pour qu'elle
  affiche dans un fimet additionel sur quel URL nous sommes à ce moment.
