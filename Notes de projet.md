

```python
[[Case11, Case12, ... Case1K],
 [Case21, Case21, ... Case2K],
 ...,
 [CaseN1, CaseN2, ... CaseNK]]
```

```python
Class Case:
	contenu : enum{possibilités}
	vu_garde : [n_min, n_max]
	vu_tot : [n_min, n_max]
```

Choix de déplacement :
```python
[0, 2] vs [1, 3]
```

Faire la liste des cases depuis lesquels il peut être vu, on peut ici se servir de sat et faire des requetes, par ex avec la case 21, on vérifie si il existe un modèle avec `G21` et un modèle avec `-G21`. On fait ensuie la même pour toutes les cases. Penser à aussi considérer la direction pour le minimum (pour le minimum on se sert également du tableau python que l'on connaît)


```
+---+---+---+---+---+---+---+---+---+
|  ? |  ? |  ? | ?  | ? |  ? |  ? |  ? |  ? | 
+---+---+---+---+---+---+---+---+---+
|  ? | Ĝ | <I |G?| ? |  ? |  ? |  ? |  ? | 
+---+---+---+---+---+---+---+---+---+
|  █ |G>|     | ?  | ? |  ? |  ? |  ? |  ? | 
+---+---+---+---+---+---+---+---+---+
|      |    |     | P?| ? |  ? |  ? |  ? |  ? | 
+---+---+---+---+---+---+---+---+---+
```


Penser à touner sur soi même sur une nouvelles case pour voir des nouvelles cases ineplorées

penser à ajouter un attribut pour ne pas boucler sur les cases déjà explorées (un attribu "déjà connu"), ou encore une méthode

Ne pas que considérer les cases voisines mais toutes les cases accessibles (on peut rebrousser chemin pour aller ailleurs), si on rebrousse chemin, évaluer le cout de revenir en arrière et tenter une autre case par rapport au fait de simplement essayer une case 


## Sat
On connait le nombre de garde et d'invités. On ne peut pas déduire les objets.

Pour chaque case on aura donc soit un garde, soit un invité soit aucun des deux.

Pour N gardes et M invités, on fera un at_least(X) et at_most(X) pour les N gardes et M invités.

On fera également une clause permettant de vérifier qu'il n'y a pas d'invité et de garde sur la même case (avec un at_mot_one ntre I et G).

Si côté python on remarque qu'une case `[i, j]` est vide, a un mur ou un objet, on ne peut pas le mettre directement en sat mais on peut mettre une clause `-I[i, j]` et une clause `-G[i, j]`, ce qui apportera de l'information dans les déductions (par exemple si on entent 6+ personnes autour de soi, on fait les combinaisons mais si le fichier cnf continent que telle ou telle case ne contient personne, il pourra faire des déductions supplémentaires.)

Ce sera à python de gérer les voisin d'une case et de les donner au fichier CNF.



## Modélisation des cases

deux options :

+ case `[2, 1]` -> 21
+ Convertir chaque coordonnée en entiers qui se suivent et faire une fonction de translation dans les deux sens.


todo :
clauses