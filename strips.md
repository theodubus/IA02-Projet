Modélisation STRIPS :

**Fluents :**
- libre(x,y) : Hitman peut se déplacer sur la case (x, y).
- Contenu(objet, x, y) : case à la position (x, y) contient objet, avec objet ∈ {Hitman, Cible, Garde, Invite, Costume, Arme, Mur} 
- Orientation(objet, o) : objet est orienté vers o, avec o ∈ {haut, bas, gauche, droite} et objet ∈ {Hitman, Garde, Invite}
- Possede(objet) : Indique que hitman possède l'objet.
- CibleMorte : Indique que la cible est morte.
- CostumeMis : Indique que Hitman est en costume.
- Voisin (x1, y1, x2, y2) : Indique que la case (x1, y1) est voisine de la case (x2, y2).

**Etat initial :**
- Contenu(Hitman, 0, 0)
- Orientation(Hitman, "haut")
- ¬CibleMorte
- ¬CostumeMis
- Contenu(Cible, x, y) avec x et y étant les coordonnées de la cible
- Contenu(Garde, _, _) pour chaque garde
- Orientation(Garde, _) pour chaque garde
- Contenu(Civil, _, _) pour chaque civil 
- Orientation(Civil, _) pour chaque civil
- Contenu(Costume, x, y) avec x et y étant les coordonnées du costume
- Contenu(Arme, x, y) avec x et y étant les coordonnées de la corde de piano
- Contenu(Mur, _, _) pour chaque mur
- libre(x, y) pour chaque case libre
- Voisin(x1, y1, x2, y2) pour chaque case voisine

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
PRECOND: Contenu(Hitman, x, y) ∧ Orientation(Hitman, "haut") ∧ libre(x+1, y)
EFFECT : Contenu(Hitman, x+1, y) ∧ ¬Contenu(Hitman, x, y)

PRECOND: Contenu(Hitman, x, y) ∧ Orientation(Hitman, "droite") ∧ libre(x, y+1)
EFFECT : Contenu(Hitman, x, y+1) ∧ ¬Contenu(Hitman, x, y)

PRECOND: Contenu(Hitman, x, y) ∧ Orientation(Hitman, "bas") ∧ libre(x-1, y)
EFFECT : Contenu(Hitman, x-1, y) ∧ ¬Contenu(Hitman, x, y)

PRECOND: Contenu(Hitman, x, y) ∧ Orientation(Hitman, "gauche") ∧ libre(x, y-1)
EFFECT : Contenu(Hitman, x, y-1)) ∧ ¬Contenu(Hitman, x, y)

```
- TuerCible : Tue la cible si le personnage a la corde de piano et se trouve sur la même case que la cible.
```
Action(TuerCible(),
PRECOND: Contenu(Hitman, x, y) ∧ Contenu(cible, x, y) ∧ Possede(Arme)
EFFECT : CibleMorte ∧ ¬Contenu(cible, x, y))

```
- NeutraliserGarde() : Neutralise le garde si le hitman le regarde, est sur une case adjacente et le garde ne le regarde pas.
```
Action(NeutraliserGarde(),
PRECOND: Contenu(Hitman, x, y) ∧ Orientation(Hitman, "haut") ∧ Contenu(garde, x+1, y) ∧ ¬Orientation(garde, "bas") 
EFFECT : ¬Contenu(garde, x+1, y) ∧ libre(x+1, y)

PRECOND: Contenu(Hitman, x, y) ∧ Orientation(Hitman, "droite") ∧ Contenu(garde, x, y+1) ∧ ¬Orientation(garde, "gauche") 
EFFECT : ¬Contenu(garde, x, y+1) ∧ libre(x, y+1)

PRECOND: Contenu(Hitman, x, y) ∧ Orientation(Hitman, "bas") ∧ Contenu(garde, x-1, y) ∧ ¬Orientation(garde, "haut") 
EFFECT : ¬Contenu(garde, x-1, y) ∧ libre(x-1, y)

PRECOND: Contenu(Hitman, x, y) ∧ Orientation(Hitman, "gauche") ∧ Contenu(garde, x, y-1) ∧ ¬Orientation(garde, "droite")
EFFECT : ¬Contenu(garde, x, y-1) ∧ libre(x, y-1))

```
- NeutraliserCivil() : Neutralise le civil si le personnage le regarde, est sur une case adjacente et le civil ne le regarde pas.
```
Action(NeutraliserCivil(),
PRECOND: Contenu(Hitman, x, y) ∧ Orientation(Hitman, "haut") ∧ Contenu(invite, x+1, y) ∧ ¬Orientation(invite, "bas") 
EFFECT : ¬Contenu(invite, x+1, y)

PRECOND: Contenu(Hitman, x, y) ∧ Orientation(Hitman, "droite") ∧ Contenu(invite, x, y+1) ∧ ¬Orientation(invite, "gauche") 
EFFECT : ¬Contenu(invite, x, y+1)

PRECOND: Contenu(Hitman, x, y) ∧ Orientation(Hitman, "bas") ∧ Contenu(invite, x-1, y) ∧ ¬Orientation(invite, "haut") 
EFFECT : ¬Contenu(invite, x-1, y)

PRECOND: Contenu(Hitman, x, y) ∧ Orientation(Hitman, "gauche") ∧ Contenu(invite, x, y-1) ∧ ¬Orientation(invite, "droite")
EFFECT : ¬Contenu(invite, x, y-1))
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
PRECOND: Contenu(Hitman, x, y) ∧ Contenu(costume, x, y) ∧ ¬Possede(costume)
EFFECT : Possede(costume) ∧ ¬Contenu(costume, x, y))
```
- PrendreArme : Ajoute l'objet "corde de piano" à la possession du personnage s'il est sur la case actuelle.
```
Action(PrendreArme(),
PRECOND: Contenu(Hitman, x, y) ∧ Contenu(corde, x, y) ∧ ¬Possede(corde)
EFFECT : Possede(corde) ∧ ¬Contenu(corde, x, y))
```


**But :**
- Contenu(Hitman, 0, 0)
- CibleMorte
