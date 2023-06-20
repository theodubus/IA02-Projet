from typing import Tuple

class Case:
    """
    Classe qui represente une case du plateau

    Une case est caracterisee par :
        - son contenu : tuple (element, direction), avec direction = None si l'element n'est pas une personne
        - proven_not_guard : booleen qui indique si la case a deja ete prouvee comme n'etant pas un garde par gophersat

    Les methodes utiles sont :
        - contenu : getter et setter pour le contenu de la case, permettant de verifier la validite du contenu
        - __str__ : permet d'afficher le contenu de la case avec print() pour pouvoir etre affichee dans le plateau
        - proven_not_guard : getter et setter pour proven_not_guard, permettant de verifier la validite de la valeur 
        - case_interdite : renvoie False si hitman a le droit d'etre sur cette case, True sinon ou si le contenu de la case est inconnu
        - contenu_connu : renvoie True si le contenu de la case est connu, False sinon (voir plus bas)
    """

    def __init__(self):
        self._contenu = ("inconnu", None)
        self._proven_not_guard = False

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
            else: # self.contenu[0] == "garde":
                chaine += "G"

            if self.contenu[1] == "gauche":
                chaine += "←"
            elif self.contenu[1] == "droite":
                chaine += "→"
            elif self.contenu[1] == "haut":
                chaine += "↑"
            else: # self.contenu[1] == "bas":
                chaine += "↓"
        return chaine
    
    @property
    def proven_not_guard(self) -> bool:
        return self._proven_not_guard
    
    @proven_not_guard.setter
    def proven_not_guard(self, value: bool):
        if value is not True:
            raise ValueError("La valeur ne peut que passer de False a True")
        self._proven_not_guard = value

    def erase_contenu(self):
        """
        supprime le contenu de la case
        """
        self._contenu = ("vide", None)
        
    @property
    def contenu(self) -> Tuple[str, str]:
        return self._contenu

    @contenu.setter
    def contenu(self, nouveau_contenu : Tuple[str, str]):
        """
        Modifie le contenu de la case
        :param nouveau_contenu:
            tuple de deux elements
            - le premier element est le contenu de la case et peut prendre les valeurs suivantes :
                - "mur", "corde", "costume", "invite", "garde", "vide", "cible"

            - le deuxieme element est la direction de la personne et peut prendre les valeurs suivantes :
                - "gauche", "droite", "haut", "bas", None

            Pour les objets et les murs, on laisse la direction a None. None est donc pour les objets uniquement,
            une personne doit avoir une direction.
        """
        if self.contenu_connu():
            raise ValueError("Le contenu de la case est deja connu")

        if type(nouveau_contenu) is not tuple or len(nouveau_contenu) != 2:
            raise ValueError("Le contenu doit etre un tuple de deux elements")

        contenu, direction = nouveau_contenu

        # Verification de la validite du contenu
        if contenu not in {"mur", "corde", "costume", "invite", "garde", "vide", "cible"}:
            raise ValueError("Le contenu n'est pas valide")
        if direction is not None:
            if contenu not in {"garde", "invite"}:
                raise ValueError("Un objet n'a pas de direction")
            if direction not in {"gauche", "droite", "haut", "bas"}:
                raise ValueError("La direction n'est pas valide")
        else:
            if contenu in {"garde", "invite"}:
                raise ValueError("Une personne doit avoir une direction : \n- gauche \n- droite \n- haut \n- bas")

        self._contenu = (contenu, direction)

    def case_interdite(self) -> bool:
        """
        Renvoie False si hitman a le droit d'etre sur cette case
        Renvoie True sinon ou si le contenu de la case est inconnu
        """
        return self.contenu[0] in {"mur", "garde"}
    
    def contenu_connu(self) -> bool:
        """
        Renvoie True si le contenu de la case est connu, False sinon
        """
        return self.contenu[0] != "inconnu"