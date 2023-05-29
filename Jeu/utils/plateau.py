from .case import Case

class Plateau:
    """
    Classe qui represente le plateau de jeu

    Un plateau est caracterise par :
        - sa taille : nombre de lignes et de colonnes
        - son contenu : liste de listes de cases

    Les methodes utiles sont :
        - case_existe : verifie si la case (i, j) existe
        - distance_manhattan : renvoie la distance de Manhattan entre deux cases
        - set_case : modifie le contenu de la case (i, j)
        - get_case : renvoie le contenu de la case (i, j)
        - verif_init : verifie si les coordonnees d'initialisation sont valides
        - infos_plateau : renvoie la taille du plateau
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

        :param m: nombre de colonnes
        :param n: nombre de lignes
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
        m, n = self.infos_plateau()
        return 0 <= i < m and 0 <= j < n
    
    def distance_manhattan(self, i1, j1, i2, j2):
        """
        Renvoie la distance de Manhattan entre deux cases
        """
        if not self.case_existe(i1, j1) or not self.case_existe(i2, j2):
            raise ValueError("La case n'existe pas")

        return abs(i1 - i2) + abs(j1 - j2)
    
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

        m, n = self.infos_plateau()
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
        m, n = self.infos_plateau()
        if var <= m * n:
            type = "invite"
            var -= 1
        else:
            type = "garde"
            var -= (m * n + 1)

        i = var // n
        j = var % n

        return i, j, type
        
    def set_case(self, i, j, contenu):
        """
        Modifie le contenu de la case (i, j)
        """
        if not self.case_existe(i, j):
            raise ValueError("La case n'existe pas")
        self._plateau[i][j].contenu = contenu

    def get_case(self, i, j):
        """
        Renvoie le contenu de la case (i, j)
        """
        if not self.case_existe(i, j):
            raise ValueError("La case n'existe pas")
        return self._plateau[i][j]

    def verif_init(self, m, n):
        """
        Verifie si les coordonnees d'initialisation sont valides
        """
        if type(m) is not int or type(n) is not int:
            raise ValueError("Les coordonnees doivent etre des entiers")
        if m <= 0 or n <= 0:
            raise ValueError("Les coordonnees doivent etre positives")
        return True
    
    def infos_plateau(self):
        """
        Renvoie la taille du plateau
        """
        return self._m, self._n

    def __str__(self):
        """
        Affiche le plateau

        :return: chaine de caracteres representant le plateau
        """
        m, n = self.infos_plateau()
        plateau_str = "    "
        plateau_str += "+-----" * m + "+\n"


        for i in range(n-1, -1, -1):
            plateau_str += f" {i}  |"
            for j in range(m):
                plateau_str += f"{str(self._plateau[j][i]):^5}|"
            plateau_str += "\n    "
            plateau_str += "+-----" * m + "+\n"

        plateau_str += "    "
        for j in range(m):
            plateau_str += f"   {j}  "
        plateau_str += "\n"

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
            candidates = [(i-1, j), (i-2, j), (i-3, j)]
        elif direction == "droite":
            candidates = [(i+1, j), (i+2, j), (i+3, j)]
        elif direction == "haut":
            candidates = [(i, j+1), (i, j+2), (i, j+3)]
        else: # (direction == "bas")
            candidates = [(i, j-1), (i, j-2), (i, j-3)]

        voisins = [c for c in candidates if self.case_existe(c[0], c[1])]

        return voisins