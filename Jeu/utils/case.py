class Case:
    """
    Classe qui represente une case du plateau

    Une case est caracterisee par :
        - son contenu : tuple (element, direction), avec direction = None si l'element n'est pas une personne

    Les methodes utiles sont :
        - contenu : getter et setter pour le contenu de la case, permettant de verifier la validite du contenu
        - contenu_connu : renvoie True si le contenu de la case est connu, False sinon (voir plus bas)
    """

    def __init__(self):
        self._contenu = ("inconnu", None)

    def __str__(self):
        """
        Affiche le contenu de la case pour pouvoir etre affichee dans le plateau
        """
        chaine = ""
        if self.contenu[0] == "inconnu":
            chaine += "?"
        elif self.contenu[0] == "mur":
            chaine += "███" # remplacer par "M" si le bloc ne passe pas
        elif self.contenu[0] == "corde":
            chaine += "CD"
        elif self.contenu[0] == "costume":
            chaine += "CS"
        elif self.contenu[0] == "vide":
            chaine += " "
        elif self.contenu[0] == "cible":
            chaine += "C"
        else:
            if self.contenu[0] == "invite":
                chaine += "I"
            elif self.contenu[0] == "garde":
                chaine += "G"
            else: # self.contenu[0] == "personne"
                chaine += "P"

            if self.contenu[1] == "gauche":
                chaine += "←"
            elif self.contenu[1] == "droite":
                chaine += "→"
            elif self.contenu[1] == "haut":
                chaine += "↑"
            elif self.contenu[1] == "bas":
                chaine += "↓"
            else: # self.contenu[1] == "inconnu"
                chaine += "?"
        return chaine

    @property
    def contenu(self):
        return self._contenu

    @contenu.setter
    def contenu(self, nouveau_contenu):
        """
        Modifie le contenu de la case
        :param nouveau_contenu:
            tuple de deux elements
            - le premier element est le contenu de la case et peut prendre les valeurs suivantes :
                - "mur", "corde", "costume", "personne", "invite", "garde", "vide", "cible"

            - le deuxieme element est la direction de la personne et peut prendre les valeurs suivantes :
                - "gauche", "droite", "haut", "bas", "inconnu", None

            On utilise personne quand on sait qu'il y a une personne mais qu'on ne sait pas si c'est un garde ou un invite.
            "inconnu" pour la direction signifie qu'on ne sait pas la direction de la personne. Pour les objets et les murs,
            on laisse la direction a None. None est donc pour les objets uniquement, une personne doit avoir une direction (qui
            peut etre "inconnu").
        """
        if self.contenu_connu():
            raise ValueError("Le contenu de la case est deja connu")

        if type(nouveau_contenu) is not tuple or len(nouveau_contenu) != 2:
            raise ValueError("Le contenu doit etre un tuple de deux elements")

        contenu, direction = nouveau_contenu

        # Verification de la validite du contenu
        if contenu not in {"mur", "corde", "costume", "personne", "invite", "garde", "vide", "cible"}:
            raise ValueError("Le contenu n'est pas valide")
        if direction is not None:
            if contenu not in {"garde", "invite", "personne"}:
                raise ValueError("Un objet n'a pas de direction")
            if direction not in {"gauche", "droite", "haut", "bas", "inconnu"}:
                raise ValueError("La direction n'est pas valide")
        else:
            if contenu in {"garde", "invite", "personne"}:
                raise ValueError("Une personne doit avoir une direction : \n- gauche \n- droite \n- haut \n- bas \n- inconnu")

        self._contenu = (contenu, direction)
    
    def contenu_connu(self):
        """
        Renvoie True si le contenu de la case est connu, False sinon

        Une case est consideree comme connue si on sait ce qu'il y a dedans et sa direction (si c'est une personne).
        Une case connue est donc une case que l'on a pas besoin d'aller "voir" car on connait déjà tout son contenu.
        """
        return self.contenu[0] not in {"inconnu", "personne"} and self.contenu[1] != "inconnu"