from clauses_combin import *

class Plateau:
    """
    Classe qui represente le plateau de jeu

    Un plateau est caracterise par :
        - sa taille : nombre de lignes et de colonnes
        - son contenu : liste de listes de cases

    Les methodes utiles sont :
        - case_existe : verifie si la case (i, j) existe
        - set_case : modifie le contenu de la case (i, j)
        - verif_init : verifie si les coordonnees d'initialisation sont valides
        - _infos_plateau : renvoie la taille du plateau
        - __str__ : sert a afficher le plateau
        - cell_to_var : converti les coordonnees et le typed'une case en variable cnf
        - var_to_cell : converti une variable cnf en coordonnees de case et le type
        - voisins : renvoie les cases voisines de la case (haut, bas, gauche, droite)
        - voisins_2_cases : renvoie les cases eloignees de deux cases dans la meme direction
        - cases_entendre : renvoie les cases autour de la case dans un rayon de 2, plus la case actuelle elle-meme
        - cases_voir : renvoie les trois cases dans la direction donnee
        
        Les méthodes qui calculent les voisins veillent bien entendu à ne pas renvoyer des cases qui ne sont pas sur le plateau.

        Pour les variables CNF, nous n'utilisons que deux variables par case, pour déduire
        si une case contient un garde, un invité ou ni l'un ni l'autre.
    """

    def __init__(self, m, n):
        """
        Initialise le plateau avec sa taille

        :param m: nombre de lignes
        :param n: nombre de colonnes
        """
        
        if self.verif_init(m, n):
            self._m = m
            self._n = n
            self.clauses = set()
    
        self._plateau = [[Case() for _ in range(n)] for _ in range(m)]

    def case_existe(self, i, j):
        """
        Verifie si la case (i, j) existe
        """
        m, n = self._infos_plateau()
        return 0 <= i < m and 0 <= j < n
    
    def cell_to_var(self, i, j, type):
        """
        converti les coordonnees d'une case et le type en variable cnf

        Exemple avec 2 colonnes et 2 lignes :
        (0, 0, "invite") -> 1, (0, 1, "invite") -> 2, (1, 0, "invite") -> 3, (1, 1, "invite") -> 4
        (0, 0, "garde") -> 5, (0, 1, "garde") -> 6, (1, 0, "garde") -> 7, (1, 1, "garde") -> 8.
        """

        if type not in {"invite", "garde"}:
            raise ValueError("Le type n'est pas valide")

        if not self.case_existe(i, j):
            raise ValueError("La case n'existe pas")

        m, n = self._infos_plateau()
        var = i * n + j + 1

        if type == "garde":
            var += m * n

        return var
    
    def var_to_cell(self, var):
        """
        converti une variable cnf en coordonnees de case et le type

        Exemple avec 2 colonnes et 2 lignes :
        1 -> (0, 0, "invite"), 2 -> (0, 1, "invite"), 3 -> (1, 0, "invite"), 4 -> (1, 1, "invite")
        5 -> (0, 0, "garde"), 6 -> (0, 1, "garde"), 7 -> (1, 0, "garde"), 8 -> (1, 1, "garde").
        """
        m, n = self._infos_plateau()
        if var <= m * n:
            type = "invite"
            var -= 1
        else:
            type = "garde"
            var -= (m * n + 1)

        i = var // n
        j = var % n

        return i, j, type

    def clauses_invites_gardes(self, n_gardes, n_invites):
        """
        Renvoie les clauses permettant de modeliser le nombre de gardes et d'invites
        """
        m, n = self._infos_plateau()

        variables_invites = [self.cell_to_var(i, j, "invite") for i in range(m) for j in range(n)]
        variables_gardes = [self.cell_to_var(i, j, "garde") for i in range(m) for j in range(n)]

        clauses = []
        clauses.append(at_most_k(variables_invites, n_invites))
        clauses.append(at_most_k(variables_gardes, n_gardes))

        

    def set_case(self, i, j, contenu):
        """
        Modifie le contenu de la case (i, j)
        """
        if not self.case_existe(i, j):
            raise ValueError("La case n'existe pas")
        self._plateau[i][j].contenu = contenu


    def verif_init(self, m, n):
        """
        Verifie si les coordonnees d'initialisation sont valides
        """
        if type(m) is not int or type(n) is not int:
            raise ValueError("Les coordonnees doivent etre des entiers")
        if m <= 0 or n <= 0:
            raise ValueError("Les coordonnees doivent etre positives")
        return True
    
    def _infos_plateau(self):
        """
        Renvoie la taille du plateau
        """
        return self._m, self._n

    def __str__(self):
        """
        Affiche le plateau

        :return: chaine de caracteres representant le plateau
        """
        m, n = self._infos_plateau()
        plateau_str = "    "
        for j in range(n):
            plateau_str += f"   {j}  "
        plateau_str += "\n    "
        plateau_str += "+-----" * n + "+\n"

        for i in range(m):
            plateau_str += f" {i}  |"
            for j in range(n):
                plateau_str += f"{str(self._plateau[i][j]):^5}|"
            plateau_str += "\n    "
            plateau_str += "+-----" * n + "+\n"

        return plateau_str
    
    def voisins(self, i, j):
        """
        Renvoie les cases voisines de la case
        Une case a 4 voisins : haut, bas, gauche, droite
        Cette méthode est utile pour se déplacer et aussi pour savoir si on est visible par un garde ou invite.
        """
        if not self.case_existe(i, j):
            raise ValueError(f"La case ({i}, {j}) n'existe pas")

        candidates = [(i-1, j), (i+1, j), (i, j-1), (i, j+1)]
        voisins = [c for c in candidates if self.case_existe(c[0], c[1])]
        return voisins
    
    def voisins_2_cases(self, i, j):
        """
        Renvoie les cases eloignees de deux cases dans la meme direction
        Exemple : haut-haut, bas-bas, gauche-gauche, droite-droite
        Cette méthode est utile pour savoir si on est visible par un garde
        """
        if not self.case_existe(i, j):
            raise ValueError(f"La case ({i}, {j}) n'existe pas")

        candidates = [(i-2, j), (i+2, j), (i, j-2), (i, j+2)]
        voisins = [c for c in candidates if self.case_existe(c[0], c[1])]
        return voisins
    
    def cases_entendre(self, i, j):
        """
        Renvoie les cases autour de la case dans un rayon de 2, plus la case actuelle elle-meme
        Cette methode est utile lorsque le joueur veut "entendre"
        """
        if not self.case_existe(i, j):
            raise ValueError(f"La case ({i}, {j}) n'existe pas")

        candidates = [(x, y) for x in range(i-2, i+3) for y in range(j-2, j+3)]
        voisins = [c for c in candidates if self.case_existe(c[0], c[1])]
                
        return voisins
    

    def cases_voir(self, i, j, direction):
        """
        Renvoie les trois cases dans la direction donnee par rapport a la case (i, j)

        Cette methode est utile lorsque le joueur veut "voir"
        """
        if not self.case_existe(i, j):
            raise ValueError(f"La case ({i}, {j}) n'existe pas")

        if direction not in {"gauche", "droite", "haut", "bas"}:
            raise ValueError("La direction n'est pas valide")
        
        if direction == "gauche":
            candidates = [(i, j-1), (i, j-2), (i, j-3)]
        elif direction == "droite":
            candidates = [(i, j+1), (i, j+2), (i, j+3)]
        elif direction == "haut":
            candidates = [(i-1, j), (i-2, j), (i-3, j)]
        else: # (direction == "bas")
            candidates = [(i+1, j), (i+2, j), (i+3, j)]

        voisins = [c for c in candidates if self.case_existe(c[0], c[1])]

        return voisins

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
                - "mur", "corde", "costume", "personne", "invite", "garde"

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
        if contenu not in {"mur", "corde", "costume", "personne", "invite", "garde"}:
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



p = Plateau(2, 2)
# p.set_case(2, 4, ("mur", None))
# p.set_case(2, 3, ("corde", None))
# p.set_case(2, 2, ("costume", None))

# p.set_case(1, 1, ("invite", "gauche"))
# p.set_case(2, 5, ("garde", "droite"))



# print(p)


