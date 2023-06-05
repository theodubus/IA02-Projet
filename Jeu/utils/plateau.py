from .case import Case
from .hitman import *

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
        - voisins_gardes : renvoie les cases depuis lesquelles on peut etre vu par un garde
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
            self._history = dict() # historique temporaire pour le calcul de la distance minimale
            self._pos_hitman = None # position du hitman

        self._plateau = [[Case() for _ in range(n)] for _ in range(m)]

    @property
    def pos_hitman(self):
        return self._pos_hitman
    
    @pos_hitman.setter
    def pos_hitman(self, pos):
        i, j, direction = pos
        if not self.case_existe(i, j):
            raise ValueError("La case n'existe pas")
        if direction not in {"gauche", "droite", "haut", "bas"}:
            raise ValueError("La direction n'est pas valide")
        self._pos_hitman = (i, j, direction)

    def board_to_map(self):
        """
        Renvoie le plateau sous forme de dictionnaire
        """
        equiv = {
            ("vide", None) : HC.EMPTY,
            ("mur", None) : HC.WALL,
            ("corde", None) : HC.PIANO_WIRE,
            ("costume", None) : HC.SUIT,
            ("garde", "haut") : HC.GUARD_N,
            ("garde", "droite") : HC.GUARD_E,
            ("garde", "bas") : HC.GUARD_S,
            ("garde", "gauche") : HC.GUARD_W,
            ("invite", "haut") : HC.CIVIL_N,
            ("invite", "droite") : HC.CIVIL_E,
            ("invite", "bas") : HC.CIVIL_S,
            ("invite", "gauche") : HC.CIVIL_W,
            ("cible", None) : HC.TARGET
        }
        m, n = self.infos_plateau()
        map = dict()
        for i in range(m):
            for j in range(n):
                if self.get_case(i, j).contenu not in equiv.keys():
                    raise ValueError("Le contenu de la case n'est pas valide")
                map[(i, j)] = equiv[self.get_case(i, j).contenu]
        return map

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
    
    def distance_minimale(self, i1, j1, i2, j2):
        """
        Methode distance minimale utilisee par l'utilisateur
        """
        self._history = dict()
        dist = self._distance_minimale(i1, j1, i2, j2)
        if dist == float("inf"):
            raise ValueError(f"Il n'existe pas de chemin entre les cases ({i1}, {j1}) et ({i2}, {j2})")
        return dist
    
    def _distance_minimale(self, i1, j1, i2, j2, case_appelante=None):
        """
        Renvoie la distance minimale entre deux cases, c'est a dire 
        le nombre minimum de cases a traverser pour aller de (i1, j1) a (i2, j2)

        Le but est d'obtenir une heuristique de "la case la plus proche" en tenant compte
        des murs et des gardes que l'on ne peut pas traverser.

        Cette methode est une methode intermediaire utilisee par la methode distance_minimale.
        L'interet est de remettre a zero l'historique des cases visitees a chaque appel de
        distance_minimale, ce qui ne peut se faire qu'ici car la methode est recursive.

        Si il n'existe pas de chemin direct entre les deux cases, on cherche un chemin direct entre
        ses voisins et l'objectif.
        Dans ce cas, il est pertinent de faire une exploration en largeur des possibilites :
        - on voit s'il existe un chemin direct depuis les cases distantes de 1, puis 2, 3, etc
        """

        if not self.case_existe(i1, j1) or not self.case_existe(i2, j2):
            raise ValueError("La case n'existe pas")
        
        if (i1, j1) in self._history.keys():
            return self._history[(i1, j1)]
        
        if self.chemin_direct(i1, j1, i2, j2):
            self._history[(i1, j1)] = self.distance_manhattan(i1, j1, i2, j2)
            return self._history[(i1, j1)]
        
        self._history[(i1, j1)] = float("inf")
        
        voisins = [v for v in self.voisins(i1, j1) if not self.get_case(v[0], v[1]).case_interdite()]

        if case_appelante is not None:
            voisins = [v for v in voisins if v != case_appelante]

        if voisins == []:
            return float("inf")

        for v in voisins:
            if self.chemin_direct(v[0], v[1], i2, j2):
                return self._distance_minimale(v[0], v[1], i2, j2, (i1, j1)) + 1

        shortest = float("inf")
        for v in voisins:
            distance = self._distance_minimale(v[0], v[1], i2, j2, (i1, j1))
            if distance < shortest:
                shortest = distance

        self._history[(i1, j1)] = shortest + 1
        return self._history[(i1, j1)]

    def chemin_direct(self, i1, j1, i2, j2):
        """
        Permet de savoir s'il existe un chemin simple et direct (sans detour) entre deux cases
        """

        if not self.case_existe(i1, j1) or not self.case_existe(i2, j2):
            raise ValueError("La case n'existe pas")
        
        detour1 = False
        detour2 = False

        # horizontal puis vertical
        for i in range(min(i1, i2), max(i1, i2)+1):
            if self.get_case(i, j1).case_interdite():
                detour1 = True
                break
        if not detour1:
            for j in range(min(j1, j2), max(j1, j2)+1):
                if self.get_case(i2, j).case_interdite():
                    detour1 = True
                    break

        # vertical puis horizontal
        if detour1:
            for j in range(min(j1, j2), max(j1, j2)+1):
                if self.get_case(i1, j).case_interdite():
                    detour2 = True
                    break
            if not detour2:
                for i in range(min(i1, i2), max(i1, i2)+1):
                    if self.get_case(i, j2).case_interdite():
                        detour2 = True
                        break

        return not detour1 or not detour2
    
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
        directions = {"gauche": "←", "droite": "→", "haut": "↑", "bas": "↓"}

        if self.pos_hitman is None:
            i_hitman, j_hitman, direction_hitman = (-1, -1, None)
        else:
            i_hitman, j_hitman, direction_hitman = self.pos_hitman
        
        
        m, n = self.infos_plateau()
        plateau_str = "    "
        plateau_str += "+-----" * m + "+\n"


        for i in range(n-1, -1, -1):
            plateau_str += f" {i}  |"
            for j in range(m):
                if i == j_hitman and j == i_hitman:
                    hitman = f"{'H' + directions[direction_hitman]}"
                    if str(self._plateau[j][i]) != " ":
                        hitman += f" {str(self._plateau[j][i])}"
                    plateau_str += f"{hitman :^5}|"
                else:
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
    
    def voisins_gardes(self, i, j):
        """
        Renvoie les cases depuis lesquelles on peut etre vu par un garde
        """
        if not self.case_existe(i, j):
            raise ValueError(f"La case ({i}, {j}) n'existe pas")
        
        droite = []
        if self.case_existe(i-1, j):
            if self.get_case(i-1, j).contenu[0] == "garde":
                droite.append((i-1, j))
            elif self.get_case(i-1, j).contenu[0] in {"inconnu", "vide"}:
                if self.get_case(i-1, j).contenu[0] == "inconnu":
                    droite.append((i-1, j))
                if self.case_existe(i-2, j) and self.get_case(i-2, j).contenu[0] in {"inconnu", "garde"}:
                    droite.append((i-2, j))

        gauche = []
        if self.case_existe(i+1, j):
            if self.get_case(i+1, j).contenu[0] == "garde":
                gauche.append((i+1, j))
            elif self.get_case(i+1, j).contenu[0] in {"inconnu", "vide"}:
                if self.get_case(i+1, j).contenu[0] == "inconnu":
                    gauche.append((i+1, j))
                if self.case_existe(i+2, j) and self.get_case(i+2, j).contenu[0] in {"inconnu", "garde"}:
                    gauche.append((i+2, j))

        bas = []
        if self.case_existe(i, j+1):
            if self.get_case(i, j+1).contenu[0] == "garde":
                bas.append((i, j+1))
            elif self.get_case(i, j+1).contenu[0] in {"inconnu", "vide"}:
                if self.get_case(i, j+1).contenu[0] == "inconnu":
                    bas.append((i, j+1))
                if self.case_existe(i, j+2) and self.get_case(i, j+2).contenu[0] in {"inconnu", "garde"}:
                    bas.append((i, j+2))

        haut = []
        if self.case_existe(i, j-1):
            if self.get_case(i, j-1).contenu[0] == "garde":
                haut.append((i, j-1))
            elif self.get_case(i, j-1).contenu[0] in {"inconnu", "vide"}:
                if self.get_case(i, j-1).contenu[0] == "inconnu":
                    haut.append((i, j-1))
                if self.case_existe(i, j-2) and self.get_case(i, j-2).contenu[0] in {"inconnu", "garde"}:
                    haut.append((i, j-2))

        voisins = {"gauche": gauche, "droite": droite, "haut": haut, "bas": bas}
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

        # on enleve les cases qui n'existent pas
        voisins = [c for c in candidates if self.case_existe(c[0], c[1])]

        # on enleve les cases qui sont cachees par un objet
        for k, c in enumerate(voisins):
            if self.get_case(c[0], c[1]).contenu[0] not in {"vide", "inconnu"}:
                if self.get_case(c[0], c[1]).contenu[0] in {"mur", "garde"}:
                    voisins = voisins[:k]
                else:
                    voisins = voisins[:k+1]
                break

        return voisins