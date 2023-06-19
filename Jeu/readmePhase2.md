Modélisation STRIPS :

**Fluents :**
- Position(objet, x, y) : Indique la position (x, y) d'un objet sur la carte.
- Orientation(objet, o) : Indique l'orientation d'un personnage (Hitman, cible, garde) ; o peut prendre les valeurs "haut", "bas", "gauche", "droite"
- Clear(x, y): Indique qu'à la position (x, y), il y a pas d'objet, ou un invite, ou une garde neutralisée
    * Equivaut Position(vide, x, y) ∨ Position(invite, x, y) ∨ Position(garde_neutralisee, x, y)
- Possede(objet) : Indique que le personnage possède l'objet.
- CibleMorte : Indique que la cible est morte.
- CostumeMis : Indique que Hitman est en costume.

**Etat initiale :**
- Position(Hitman, 0, 0)
- Orientation(Hitman, "haut")
- ¬CibleMorte
- ¬CostumeMis
- Position(Cible, x, y) avec x et y étant les coordonnées de la cible
- Position(Garde, _, _) pour chaque garde
- Orientation(Garde, _)
- Position(Civil, _, _) pour chaque civil 
- Orientation(Civil, _)
- Position(Costume, _, _) avec x et y étant les coordonnées du costume
- Position(Arme, _, _) avec x et y étant les coordonnées du corde de piano

**Actions :**
- TournerHoraire : Change l'orientation du personnage en tournant de 90° dans le sens horaire.
```
Action(TournerHoraire(),
PRECOND: Orientation(Hitman, "haut")
EFFECT : Orientation(Hitman, "droite") ∧ ¬Orientation(Hitman, "haut")

PRECOND: Orientation(Hitman, "droite")
EFFECT : Orientation(Hitman, "bas") ∧ ¬Orientation(Hitman, "droite")

PRECOND: Orientation(Hitman, "bas")
EFFECT : Orientation(Hitman, "gauche") ∧ ¬Orientation(Hitman, "bas")

PRECOND: Orientation(Hitman, "gauche")
EFFECT : Orientation(Hitman, "haut") ∧ ¬Orientation(Hitman, "gauche"))
```

- TournerAntihoraire : Change l'orientation du personnage en tournant de 90° dans le sens anti-horaire.
```
Action(TournerAntihoraire(),
PRECOND: Orientation(Hitman, "haut")
EFFECT : Orientation(Hitman, "gauche") ∧ ¬Orientation(Hitman, "haut")

PRECOND: Orientation(Hitman, "droite")
EFFECT : Orientation(Hitman, "haut") ∧ ¬Orientation(Hitman, "droite")

PRECOND: Orientation(Hitman, "bas")
EFFECT : Orientation(Hitman, "droite") ∧ ¬Orientation(Hitman, "bas")

PRECOND: Orientation(Hitman, "gauche")
EFFECT : Orientation(Hitman, "bas") ∧ ¬Orientation(Hitman, "gauche"))
```
- Avancer() : Déplace le personnage d'une case vers l'orientation actuelle s'il est possible de s'y déplacer.
```
Action(Avancer(),
PRECOND: Position(Hitman, x, y) ∧ Orientation(Hitman, "haut") ∧ Clear(x+1, y)
EFFECT : Position(Hitman, x+1, y)

PRECOND: Position(Hitman, x, y) ∧ Orientation(Hitman, "droite") ∧ Clear(x, y+1)
EFFECT : Position(Hitman, x, y+1)

PRECOND: Position(Hitman, x, y) ∧ Orientation(Hitman, "bas") ∧ Clear(x-1, y)
EFFECT : Position(Hitman, x-1, y)

PRECOND: Position(Hitman, x, y) ∧ Orientation(Hitman, "gauche") ∧ Clear(x, y-1)
EFFECT : Position(Hitman, x, y-1))

```
- TuerCible : Tue la cible si le personnage a la corde de piano et se trouve sur la même case que la cible.
```
Action(TuerCible(),
PRECOND: Position(Hitman, x, y) ∧ Position(cible, x, y) ∧ Possede(corde)
EFFECT : CibleMorte)

```
- NeutraliserGarde() : Neutralise le garde si le personnage le regarde, est sur une case adjacente et le garde ne le regarde pas.
```
Action(NeutraliserGarde(),
PRECOND: Position(Hitman, x, y) ∧ Orientation(Hitman, "haut") ∧ Position(garde, x+1, y) ∧ ¬Orientation(garde, "bas") 
EFFECT : Position(garde_neutralisee, x+1, y) ∧ ¬Position(garde, x+1, y)

PRECOND: Position(Hitman, x, y) ∧ Orientation(Hitman, "droite") ∧ Position(garde, x, y+1) ∧ ¬Orientation(garde, "gauche") 
EFFECT : Position(garde_neutralisee, x, y+1) ∧ ¬Position(garde, x, y+1)

PRECOND: Position(Hitman, x, y) ∧ Orientation(Hitman, "bas") ∧ Position(garde, x-1, y) ∧ ¬Orientation(garde, "haut") 
EFFECT : Position(garde_neutralisee, x-1, y) ∧ ¬Position(garde, x-1, y)

PRECOND: Position(Hitman, x, y) ∧ Orientation(Hitman, "gauche") ∧ Position(garde, x, y-1) ∧ ¬Orientation(garde, "droite")
EFFECT : Position(garde_neutralisee, x, y-1) ∧ ¬Position(garde, x, y-1))

```
- NeutraliserCivil() : Neutralise le civil si le personnage le regarde, est sur une case adjacente et le civil ne le regarde pas.
```
Action(NeutraliserCivil(),
PRECOND: Position(Hitman, x, y) ∧ Orientation(Hitman, "haut") ∧ Position(invite, x+1, y) ∧ ¬Orientation(invite, "bas") 
EFFECT : Position(invite_neutralise, x+1, y) ∧ ¬Position(invite, x+1, y)

PRECOND: Position(Hitman, x, y) ∧ Orientation(Hitman, "droite") ∧ Position(invite, x, y+1) ∧ ¬Orientation(invite, "gauche") 
EFFECT : Position(invite_neutralise, x, y+1) ∧ ¬Position(invite, x, y+1)

PRECOND: Position(Hitman, x, y) ∧ Orientation(Hitman, "bas") ∧ Position(invite, x-1, y) ∧ ¬Orientation(invite, "haut") 
EFFECT : Position(invite_neutralise, x-1, y) ∧ ¬Position(invite, x-1, y)

PRECOND: Position(Hitman, x, y) ∧ Orientation(Hitman, "gauche") ∧ Position(invite, x, y-1) ∧ ¬Orientation(invite, "droite")
EFFECT : Position(invite_neutralise, x, y-1) ∧ ¬Position(invite, x, y-1))
```
- PasserCostume() : Mettre le costume si Hitman l'a en possession. 
```
Action(PasserCostume(),
PRECOND: Possede(costume) ∧ ¬CostumeMis
EFFECT : CostumeMis)
```
- PrendreCostume : Ajoute l'objet "costume" à la possession du personnage s'il est sur la case actuelle.
```
Action(PrendreCostume(),
PRECOND: Position(Hitman, x, y) ∧ Position(costume, x, y) ∧ ¬Possede(costume)
EFFECT : Possede(costume))
```
- PrendreArme : Ajoute l'objet "corde de piano" à la possession du personnage s'il est sur la case actuelle.
```
Action(PrendreArme(),
PRECOND: Position(Hitman, x, y) ∧ Position(corde, x, y) ∧ ¬Possede(corde)
EFFECT : Possede(corde))
```



**But :**
- Position(Hitman, 0, 0)
- CibleMorte
