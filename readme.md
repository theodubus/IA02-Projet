# Hitman
Projet de l'UV IA02 pour le semestre P23

## Projet
Dans ce projet, le but est de controler un personnage, "hitman", afin de l'aider à tuer une cible.
Le jeu se déroule en deux phases, une d'exploration ou le but est d'explorer la carte en se faisant le moins voir possible, et une phase d'execution ou le but est de planifier une série d'actions afin de tuer la cible tout en restant le plus discret possible.

Ce readme n'est qu'une description générale et brève du fonctionnement des différents concepts que nous avons mis en place. Pour plus de détails, vous pouvez consulter le code, qui est très commenté et explicite.

## Utilisation

```bash
python3 main.py
```

Différentes options sont disponibles :
```
usage: main.py [-h] [--sat SAT] [--temp TEMP] [--costume-combinaisons COSTUME_COMBINAISONS] [--display DISPLAY]

Hitman

options:
  -h, --help            show this help message and exit
  --sat SAT             sat mode, can be "auto", "no_sat" or "sat", default is "auto"
  --temp TEMP           Wait a bit between each action, default is True. Is set to false if display is False
  --costume-combinaisons COSTUME_COMBINAISONS
                        Use costume combinations, default is True
  --display DISPLAY     Display the game, default is True
```

Voir plus bas pour l'explication de `costume-combinaisons` et `sat`. `temp` est un paramètre qui permet de marquer une petite pause entre chaque action lors des affichage du jeu, ce qui permet de mieux voir ce qu'il se passe. Ce paramètre est automatiquement mis à `False` si `display` est mis à `False`, c'est à dire si on n'affiche pas le jeu.

Pour l'affichage, un tableau est affiché après chaque action, on peut facilement voir les coordonnées de chaque case.
Le contenu des cases est affiché de la manière suivante :
+ `?` : Contenu de la case inconnu
+ `_` : Case vide
+ `G` : Garde
+ `I` : Invité
+ `C` : Cible
+ `H` : Hitman
+ `CS` : Costume
+ `CD` : Corde de piano (arme)
+ `███` : Mur
+ `h` : Hitman en costume (phase 2)
+ `←`/`↑`/`→`/`↓` : Orientation du personnage (pour les gardes, invités et hitman)
+ Hitman peut être sur la même case qu'un objet ou invité, une case pourra donc être affiché comme `H↑ I→` ou `H↓ CS` par exemple.

Les paramètres par défaut devraient offrir de bonnes performaneces, tout en étant capables de gérer des cartes assez grandes. Pour les cartes très très grandes, envisager `--sat no_sat` et `--costume-combinaisons False` pour des délais d'exécution plus courts.

## Modélisation code
Aussi bien pour la phase 1 que la phase 2, nous modélisons nos connaissances sur le jeu de manière interne. Ainsi, nous avons créé la classe Case, et la classe Plateau (contenant un tableau d'objets "Case"), ce qui nous permet de facilement accéder à toutes les informations dont nous avons besoin. Un exemple parmi tant d'autres est la méthode `case_interdite()` de la classe Case, qui permet de savoir s'il est possible de se déplacer sur cette case ou non (si la case ne contient pas de mur ou de garde).

## Heuristiques
Nous utilisons plusieurs heuristiques à différents endroits dans le code, les voici :
+ Distance de Manhattan : assez peu utilisée dans le code car limitée, elle trouve cependant son utilité dans quelques situations
+ Distance minimale : Cette heuristique un peu plus coûteuse à calculer a pour avantage d'être plus précise que la distance de Manhattan, si des cases n'ont qu'une case les séparant mais que cette case est un mur, alors la distance de Manhattan sera de 2, alors que la distance minimale tiendra compte du mur et calculera le chemin de distance minimale entre les deux cases. Il a été mentionné en cours que chaque case était accessible dans le cadre du projet. Cette condition est **impérative**, car sans cela, il existe des cas ou on ne peut pas calculer le chemin de distance minimale entre deux cases, et la fonction lèvera une exception indiquant qu'il n'existe pas de chemin entre les deux cases. Une question qui se pose est "Comment calculer une distance minimale lorsque l'on a encore des cases inconnues ?". Pour cela nous nous inspirons de la technique pour résoudre des labyrinthe utilisée dans les compétitions Micromouse, [voir la vidéo expliquant fonctionnement](https://youtu.be/ZMQbHMgK2rw?t=482) (le timecode est défini intentionnellement sur le passage qui nous intéresse).
+ Pénalité minimale : Cette heuristique est celle dont nous nous servons le plus. Cette méthode ressemple à "Distance minimale", sauf qu'au lieu de simplement estimer les pénalités qu'on aurait en allant d'un point à un autre, on estime les pénalités (distance + être vu par un garde) que nous coûterait le voyage. Cette méthode est utilisée pour la phase 1, et a été ré-adaptée pour la phase 2, sous le nom de "h_score", cette dernière étant utilisée pour calculer le h_score.
+ Risque : Cette heuristique est utilisée pour la phase 1, elle n'est pas une heuristique qui permet d'aller d'un point à un autre comme les précédentes, mais une estimation du "risque" d'aller sur une case donnée. En effet, on ne sait jamais à l'avance par combien de gardes on va être vu en allant sur une case, cette méthode calcule le nombre minimum de garde par lesquels on sera vus (estimation optimiste), ainsi qu'un nombre maximum de garde par lesquels on sera vus (estimation pessimiste). Et retourne un score basée sur ces estimation. Le risque est notamment utilisé pour "pénalité minimale". C'est également pour cette heuristique que SAT est utilisé. En effet, SAT peut être utile pour affiner le nombre de gardes qui nous verraient en allant sur une case, si on arrive par exemple à prouver qu'une case donnée ne contient pas de garde, alors notre estimation pessimiste pourra être réduite, et donc le risque sera plus faible.

## Phase 1

### Modélisation SAT
Nous avons décidé de modéliser uniquement les gardes et les invités en SAT, sans leur orientation. L'intérêt de modélisé les murs, la cible, les objets et l'orientation des gardes et invités en SAT aurait été très limité, car ces informations ne peuvent pas être déduites par SAT. Le seul moyen d'y avoir accès est de voir directement les cases correspondantes. La raison à cela est que la vue ne laisse pas place à plusieurs possibilités. L'ouïe en revanche, laisse place à plusieurs possibilités et ouvre la porte à des déductions, mais ne permet que d'en faire par rapport aux invités et gardes. Nous avons donc deux variables par case, une si la case contient un garde et une si la case contient un invité. Des clauses s'assurent du fait qu'une case contienne soit un garde, soit un invité, soit rien mais pas un garde ET un invité.

### Déductions et prise d'information
Il y a trois manières de faire des déductions :
+ La vue : Après une action, si on voit quelque chose de nouveau on met à jour notre représentation du plateau, et on ajoute les clauses correspondantes (par exemple si on voit un mur, on ajoute les clauses disant que cette case n'est ni un invité ni un garde).
+ L'ouïe : Après une action, si on entend quelque chose de nouveau (sur une case ou l'on n'a jamais été), on rajoute les clauses correspondantes par rapport au nombre de personnes autour de nous, avec un `exactly_n` dans le cas général, et avec un `at_least_n` en cas de brouhaha. L'ajout de ces clauses est fait de manières intelligente, par exemple, si on entend 4 personnes mais qu'autour de nous on sait déjà que 5 cases sont vides et 1 contient un garde, au lieu de faire un `exactly_4` parmis 25 cases (rayon de 2 + notre case), on retire des 25 cases celles dont on sait qui ne contiennent personne, puis on retire 1 au nombre de personnes que l'on entend et on retire la case ou l'on sait que se trouve un garde, puis on fait donc un `exactly_3` parmis les 19 cases restantes. La fonction `exactly_n` faisant des combinaisons, des petites optimisations comme celles-ci permet de réduire drastiquement le nombre de clauses ajoutées (30 fois moins environ), et donc de réduire le temps de calcul de SAT.
+ Les pénalités : Bien que le dictionnaire de status nous prévient quand on est vu par un garde, pour la phase 1 les pénalités apportent une information bien plus précieuse. Si on compare le nombre de pénalités par rapport à l'action précédente, on peut facilement déduire de l'augmentation de pénalités le nombre exact de gardes qui nous voient en étant sur cette case. Cela permet non seulement d'affiner l'heuristique de risque sur les cases déjà visitées, mais cela permet occasionnellement de faire des déductions. Par exemple, si il n'y a qu'une seule case inconnue autour de nous (qui se trouve à gauche par exemple), que l'on connaît toutes les autres et que ces dernières ne contiennent pas de garde, mais que grâce aux pénalités on saut qu'on est en train d'être vu par un garde, dans ce cas non seulement le garde ne peut être qu'au niveau de la case inconnue, mais on connaît en plus de cela son orientation (vers nous), on déduit donc sa position et son orientation sans forcément avoir à l'entendre ni à le voir. Les pénalités servent également à générer certaines clauses.

### Méthode générale
Le principe d'exploration de la phase 1 est la suivante :
```
Tant qu'il existe une case inconnue :
    déterminer "case" la case la plus intéressante à explorer selon pénalité_minimale
    déterminer "cases_target" les cases depuis lesquelles "case" est visible
    se rendre sur la "case_target" la plus intéressante selon pénalité_minimale
    se tourner pour faire face à "case" et ainsi la voir
```

### Optimisations supplémentaires
+ Quand hitman devrait tourner, mais qu'il est en train d'être vu par un garde, ce dernier a un "réflexe de survie", et avance pour ne pas rester plus longtemps sur cette case et se faire voir plus longtemps, ce dernier se retournera plus loin. Ce réflèxe n'est bien évidemment que déclenché lorsqu'il est plus intéressant de se retourner plus loin.
+ Lorsque hitman doit se retourner (tourner deux fois), il calcule le nombre de cases inonnues qu'il a de chaque côté pour savoir s'il serait plus informatif de tourner deux fois dans le sens horaire ou deuc fois dans le sens anti-horaire.
+ L'heuristique "penalité_minimale" utilise une liste de candidats destinée à être ordonnée pour ajouter à la prochaine itération le candidat de pénalité minimale (ce qui fait penser à Dijkstra, à la différence près que la valeur exacte des arcs n'est pas toujours connue à l'avance). Cette liste devant être toujours triée, nous avons optée pour la structure de donnée "tas", avec le module "heapq". Des tas ont également été utilisés pour la phase 2.

### Différents mode SAT
L'utilisation de SAT pour le risque pouvant être coûteuse et parfois non nécessaire, nous avons implémenté plusieurs modes SAT, qui sont les suivants :
+ `no_sat` : Aucune utilisation de SAT pour la phase 1 (exécution très rapide, > 1 seconde sur la carte du sujet)
+ `auto` : Utilisation intelligente de SAT, uniquement quand cela est le plus pertinent (exécution moyenne, ~ 30 secondes sur la carte du sujet)
+ `sat` : Utilisation de SAT dès que possible (exécution lente, > 2 minutes sur la carte du sujet)

`sat` s'accomode assez mal aux grandes cartes, et lance des dizaines de fois SAT entre chaque action (pour calculer le risque de beaucoup de cases pour `penalite_minimale`, dont certaines cases pour lesquelles il n'est pas forcément le plus utile de calculer le risque). `auto` focalise la précision (l'utilisation de SAT) sur les cases autour de hitman, c'est la valeur de l'utilisation de sat par défaut. À noter qu'une utilisation plus forte de SAT ne s'accompagne pas forcément d'une meilleure performance, car SAT utilisé pour estimer le risque, mais même si on affine le risque, la valeur exacte du risque reste souvent approximative avant d'être sur la case en question. Une estimation plus précise du risque peut parfois nous amener à prendre d'autres décisions, alors que par chance, c'était la case qui nous semblait la plus risquée qui s'est avéré être la case ou il faut aller. Pour ces raisons, il arrive qu'un mode qui utilise moins SAT soit plus performant qu'un mode qui utilise plus SAT.


## Phase 2
La phase 2 est une planification d'actions utilisant A*. Nous représentons un état sous forme d'un namedtuple, contenant les informations suivantes :
+ `position` : la position de hitman
+ `orientation` : l'orientation de hitman
+ `penalties` : le nombre de pénalités pour arriver à cet état
+ `has_suit` : un booléen indiquant si hitman a le costume
+ `has_weapon` : un booléen indiquant si hitman a l'arme
+ `is_suit_on` : un booléen indiquant si hitman a mis le costume
+ `is_target_down` : un booléen indiquant si la cible est morte
+ `ensemble_cases_videes` : un ensemble contenant les cases que hitman a vidées
+ `historique_actions` : une liste contenant les actions qui ont été faites pour arriver à cet état

Étant donné que l'on fait de la planification, si on tue un garde dans un état, on ne le tue pas encore pour de vrai, et ce garde n'est pas neutralisé pour tous les états, on ne peut donc pas retirer ce garde du plateau. Il en va de même pour les objets. Le fait que tel ou tel objet ne soit plus sur le plateau est donc propre à un état, et doit donc être stocké dans cet état. `ensemble_cases_videes` stocke cette information. `historique_actions` stocke quant à lui les actions qui ont été faites pour arriver à cet état, ce qui permet de facilement comprendre tous les états candidats pendant le déroulement de l'algorithme, mais surtout d'avoir facilement accès à la liste d'actions à effectuer une fois qu'un état dans notre ensemble de successeurs correspond à notre objectif.

Pour l'heuristique, le `g_score` correspond au nombre de pénalités, et le `h_score` à l'estimation du nombre de pénalité restantes pour arriver à l'objectif. On aurait pu prendre par exemple la distance de Manhattan pour le `h_score`, c'est d'ailleurs ce que nous avions essayé, mais le `h_score` était vraiment trop peu significatif comparé au `g_score`, et la recherche mettait trop de temps à converger.

Pour les successeurs à considérer pour A*, étant donné qu'on doit avoir une liste de successeurs trié en fonction de leur heuristique, on utilise la structure de données "tas".

La recherche en elle-même se déroule en trois étapes :
1. Chercher et prendre l'arme
2. Chercher et tuer la cible
3. Retourner en (0, 0)

Par defaut, on cherche juste a atteindre ces objectifs dans l'ordre. Cela a cependant un
defaut : le costume ne sera que pris si il est rentable pour la phase en cours, sauf qu'il
est possible que prendre le costume soit penalisant dans l'immediat, mais rentable a long terme,
dans les phases suivantes. Pour palier à ce problème, le paramètre `costume-combinaisons` essaye différents enchaînements :
+ Ne pas forcer la prise du costume
+ Forcer la prise du costume avant la prise de l'arme
+ Forcer la prise du costume après la prise de l'arme et avant de tuer la cible
+ Forcer la prise du costume avoir tué la cible et avant de retourner en (0, 0)

Ce paramètre fait donc rajouter une quatrième étape à la recherche, et compare pour déterminer le meilleur enchaînement.
Mettre `costume-combinaisons` à false revient juste à n'essayer que le cas "Ne pas forcer la prise du costume". Ce cas
sera souvent le plus optimal, mais pas toujours, utiliser `costume-combinaisons` est plus long, mais garanti un score soit égal, soit meilleur.

Le code de la phase 2 concernant les actions correspond à la modélisation STRIPS présente dans le fichier `strips.md`.


```
      .____.
   xuu$``$$$uuu.
 . $``$  $$$`$$$
dP*$  $  $$$ $$$
?k $  $  $$$ $$$
 $ $  $  $$$ $$$
 ":$  $  $$$ $$$
  N$  $  $$$ $$$
  $$  $  $$$ $$$
   $  $  $$$ $$$
   $  $  $$$ $$$
   $  $  $$$ $$$
   $  $  $$$ $$$
   $  $  $$$ $$$
   $$#$  $$$ $$$
   $$'$  $$$ $$$
   $$`R  $$$ $$$
   $$$&  $$$ $$$
   $#*$  $$$ $$$
   $  $  $$$ @$$
   $  $  $$$ $$$
   $  $  $$$ $$$
   $  $  $B$ $$&.
   $  $  $D$ $$$$$muL.
   $  $  $Q$ $$$$$  `"**mu..
   $  $  $R$ $$$$$    k  `$$*t
   $  @  $$$ $$$$$    k   $$!4
   $ x$uu@B8u$NB@$uuuu6...$$X?
   $ $(`RF`$`````R$ $$5`"""#"R
   $ $" M$ $     $$ $$$      ?
   $ $  ?$ $     T$ $$$      $
   $ $F H$ $     M$ $$K      $  ..
   $ $L $$ $     $$ $$R.     "d$$$$Ns.
   $ $~ $$ $     N$ $$X      ."    "%2h
   $ 4k f  $     *$ $$&      R       "iN
   $ $$ %uz!     tuuR$$:     Buu      ?`:
   $ $F          $??$8B      | '*Ned*$~L$
   $ $k          $'@$$$      |$.suu+!' !$
   $ ?N          $'$$@$      $*`      d:"
   $ dL..........M.$&$$      5       d"P
 ..$.^"*I$RR*$C""??77*?      "nu...n*L*
'$C"R   ``""!$*@#""` .uor    bu8BUU+!`
'*@m@.       *d"     *$Rouxxd"```$
     R*@mu.           "#$R *$    !
     *%x. "*L               $     %.
        "N  `%.      ...u.d!` ..ue$$$o..
         @    ".    $*"""" .u$$$$$$$$$$$$beu...
        8  .mL %  :R`     x$$$$$$$$$$$$$$$$$$$$$$$$$$WmeemeeWc
       |$e!" "s:k 4      d$N"`"#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$>
       $$      "N @      $?$    F$$$$$$$$$$$$$$$$$$$$$$$$$$$$>
       $@       ^%Uu..   R#8buu$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$>
                  ```""*u$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$>
                         #$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$>
                          "5$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$>
                            `*$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$>
                              ^#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$>
                                 "*$$$$$$$$$$$$$$$$$$$$$$$$$$>
                                   `"*$$$$$$$$$$$$$$$$$$$$$$$>
                                       ^!$$$$$$$$$$$$$$$$$$$$>
                                           `"#+$$$$$$$$$$$$$$>
                                                 ""**$$$$$$$$>
                                                        ```""

```