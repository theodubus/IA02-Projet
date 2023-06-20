from .case import Case
from .hitman import *
from typing import Tuple, List, Dict

class Plateau:
    """
    Classe qui represente le plateau de jeu

    Un plateau est caracterise par :
        - sa taille : m lignes et n colonnes
        - son contenu : liste de listes de cases
        - pos_hitman : tuple (i, j, direction) qui indique la position du hitman sur le plateau
        - history : dictionnaire qui stocke les distances minimales deja calculees pour la methode distance_minimale
        - suit_on : booleen qui indique si le hitman porte un costume ou non

    Les methodes utiles sont :
        - board_to_dict : converti le plateau au format dictionnaire pour la soumission de la solution phase 1
        - case_existe : verifie si la case (i, j) existe
        - distance_manhattan : renvoie la distance de Manhattan entre deux cases
        - distance_minimale : renvoie la distance minimale possible entre deux cases, en tenant compte des obstacles connus (murs et gardes)
        - chemin_direct : renvoie True si il existe un chemin simple et direct (sans detour) entre deux cases, avec un seul virage maximum
        - cell_to_var : converti les coordonnees d'une case et le type en variable cnf
        - var_to_cell : converti une variable cnf en coordonnees de case et le type
        - set_case : modifie le contenu de la case (i, j)
        - get_case : renvoie le contenu de la case (i, j)
        - verif_init : verifie si les coordonnees d'initialisation sont valides
        - infos_plateau : renvoie la taille du plateau
        - __str__ : permet d'afficher le plateau avec print()
        - voisins : renvoie les cases voisines de la case
        - voisins_gardes : renvoie les cases autour de (i, j) ou un garde pourrait se trouver et voir la case
        - cases_entendre : renvoie les cases autour de la case dans un rayon de 2, plus la case actuelle elle-meme
        - cases_voir : renvoie les trois cases que l'on peut voir et acceder dans la direction donnee par rapport a la case (i, j)
        - put_suit : met le costume sur le hitman

        Les methodes qui calculent les voisins veillent bien entendu a ne pas renvoyer des cases qui ne sont pas sur le plateau.

        Pour les variables CNF, nous n'utilisons que deux variables par case, pour deduire
        si une case contient un garde, un invite ou ni l'un ni l'autre.
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
        self._suit_on = False

    def put_suit(self):
        """
        Met le costume sur le hitman
        """
        self._suit_on = True

    @property
    def pos_hitman(self) -> Tuple[int, int, str]:
        return self._pos_hitman
    
    @pos_hitman.setter
    def pos_hitman(self, pos : Tuple[int, int, str]):
        i, j, direction = pos
        if not self.case_existe(i, j):
            raise ValueError("La case n'existe pas")
        if direction not in {"gauche", "droite", "haut", "bas"}:
            raise ValueError("La direction n'est pas valide")
        self._pos_hitman = (i, j, direction)

    def board_to_dict(self) -> Dict[Tuple[int, int], HC]:
        """
        converti le plateau au format dictionnaire pour la soumission de la solution phase 1
        """
        equivalences = {
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
        plateau_dict = dict()
        for i in range(m):
            for j in range(n):
                if self.get_case(i, j).contenu not in equivalences.keys():
                    if self.get_case(i, j).contenu_connu():
                        raise ValueError("Le contenu de la case n'est pas valide")
                    else:
                        raise ValueError(f"Le contenu de la case ({i}, {j}) n'est pas connu")
                plateau_dict[(i, j)] = equivalences[self.get_case(i, j).contenu]
        return plateau_dict

    def case_existe(self, i: int, j: int) -> bool:
        """
        Verifie si la case (i, j) existe
        """
        m, n = self.infos_plateau()
        return 0 <= i < m and 0 <= j < n
    
    def distance_manhattan(self, i1: int, j1: int, i2: int, j2: int)-> int:
        """
        Renvoie la distance de Manhattan entre deux cases
        """
        if not self.case_existe(i1, j1) or not self.case_existe(i2, j2):
            raise ValueError("La case n'existe pas")

        return abs(i1 - i2) + abs(j1 - j2)
    
    def distance_minimale(self, i1: int, j1: int, i2: int, j2: int)-> int:
        """
        Methode distance minimale utilisee par l'utilisateur

        La methode calcule la distance minimale possible entre (i1, j1) et (i2, j2), en tenant compte
        des obstacles connus (murs et gardes).
        """
        self._history = dict()
        dist = self._distance_minimale(i1, j1, i2, j2)
        if dist == float("inf"):
            raise ValueError(f"Il n'existe pas de chemin entre les cases ({i1}, {j1}) et ({i2}, {j2})")
        return dist
    
    def _distance_minimale(self, i1: int, j1: int, i2: int, j2: int, case_appelante=None)-> int:
        """
        Renvoie la distance minimale entre deux cases, c'est a dire 
        le nombre minimum de cases a traverser pour aller de (i1, j1) a (i2, j2)

        Le but est d'obtenir une heuristique de "la case la plus proche" en tenant compte
        des murs et des gardes que l'on ne peut pas traverser.

        Cette methode est une methode intermediaire utilisee par la methode distance_minimale.
        L'interet est de remettre a zero l'historique des cases visitees a chaque appel de
        distance_minimale, ce qui ne peut se faire qu'ici car la methode est recursive.

        La methode fonctionne de la maniere suivante :
        - si il existe un chemin direct entre les deux cases, on renvoie la distance de Manhattan
        - sinon, on cherche un chemin direct entre ses voisins et l'objectif.
        
        Dans ce cas, il est pertinent de faire une exploration en largeur des possibilites :
        - on voit s'il existe un chemin direct depuis les cases distantes de 1, puis 2, 3, etc

        Une exploration en profondeur amenerait a explorer jusqu'au bout des chemins qui ne
        sont pas optimaux, ce qui est inutile.

        self._history est un dictionnaire permettant de stocker les distances minimales deja calculees
        et ainsi eviter des appels recursifs inutiles.
        """

        if not self.case_existe(i1, j1) or not self.case_existe(i2, j2):
            raise ValueError("La case n'existe pas")
        
        # cas "on a deja calcule la distance minimale entre ces deux cases"
        if (i1, j1) in self._history.keys():
            return self._history[(i1, j1)]
        
        # cas "il existe un chemin direct entre les deux cases"
        if self.chemin_direct(i1, j1, i2, j2):
            self._history[(i1, j1)] = self.distance_manhattan(i1, j1, i2, j2)
            return self._history[(i1, j1)]
        
        self._history[(i1, j1)] = float("inf")
        
        # on ne considere que les voisins qui ne sont pas des murs ou des gardes
        voisins = [v for v in self.voisins(i1, j1) if not self.get_case(v[0], v[1]).case_interdite()]

        # on retire la case appelante pour eviter de tourner en rond
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

    def chemin_direct(self, i1: int, j1: int, i2: int, j2: int)-> bool:
        """
        Permet de savoir s'il existe un chemin simple et direct (sans detour) entre deux cases,
        avec un seul virage maximum. (aller horizontalement puis verticalement ou l'inverse)
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
    
    def cell_to_var(self, i: int, j: int, type: str)-> int:
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
    
    def var_to_cell(self, var: int)-> Tuple[int, int, str]:
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
        
    def set_case(self, i: int, j: int, contenu: Tuple[str, str]):
        """
        Modifie le contenu de la case (i, j)
        """
        if not self.case_existe(i, j):
            raise ValueError("La case n'existe pas")
        self._plateau[i][j].contenu = contenu

    def remove_case(self, i: int, j: int):
        """
        Retire le contenu de la case (i, j)
        """
        if not self.case_existe(i, j):
            raise ValueError("La case n'existe pas")
        self._plateau[i][j].erase_contenu()

    def get_case(self, i: int, j: int)-> Case:
        """
        Renvoie le contenu de la case (i, j)
        """
        if not self.case_existe(i, j):
            raise ValueError("La case n'existe pas")
        return self._plateau[i][j]

    def verif_init(self, m: int, n: int)-> bool:
        """
        Verifie si les coordonnees d'initialisation sont valides
        """
        if type(m) is not int or type(n) is not int:
            raise ValueError("Les coordonnees doivent etre des entiers")
        if m <= 0 or n <= 0:
            raise ValueError("Les coordonnees doivent etre positives")
        return True
    
    def infos_plateau(self)-> Tuple[int, int]:
        """
        Renvoie la taille du plateau
        """
        return self._m, self._n

    def __str__(self):
        """
        Permet d'afficher le plateau avec print()
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
                    if self._suit_on:
                        h_char = "h"
                    else:
                        h_char = "H"
                    hitman = f"{h_char + directions[direction_hitman]}"
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
    
    def voisins(self, i: int, j: int)-> List[Tuple[int, int]]:
        """
        Renvoie les cases voisines de la case
        Une case a 4 voisins : haut, bas, gauche, droite
        Cette methode est utile pour se deplacer.
        """
        if not self.case_existe(i, j):
            raise ValueError(f"La case ({i}, {j}) n'existe pas")

        candidates = [(i-1, j), (i+1, j), (i, j-1), (i, j+1)]
        voisins = [c for c in candidates if self.case_existe(c[0], c[1])]
        return voisins
    
    def voisins_gardes(self, i: int, j: int)-> Dict[str, List[Tuple[int, int]]]:
        """
        Renvoie les cases autour de (i, j) ou un garde
        pourrait se trouver et voir la case.

        Les differentes directions depuis lesquelles ont peut etre vu sont traitees separement
        afin de faciliter le traitement dans le jeu (on se sert du fait qu'on ne peut que etre vu
        une seule fois au maximum par direction)

        Attention : "droite" ne fait pas reference aux cases qui sont a droite de la case (i, j),
        mais aux cases ou un garde pourrait se trouver et voir la case (i, j) en regardant a droite,
        ce qui revient aux cases de gauche de (i, j). Le meme principe s'applique pour les autres
        directions.
        """
        if not self.case_existe(i, j):
            raise ValueError(f"La case ({i}, {j}) n'existe pas")
        
        droite = []
        if self.case_existe(i-1, j):
            # Si la premiere case est un garde, la case d'apres ne peut pas etre un garde qui voit (i, j) car le premier bloque la vue du second
            if self.get_case(i-1, j).contenu[0] == "garde": 
                droite.append((i-1, j))
            # Si la premiere case est vide ou inconnue, on ne peut pas refuter l'hypothese qu'un garde puisse se trouver sur la case d'apres et voir (i, j)
            elif self.get_case(i-1, j).contenu[0] in {"inconnu", "vide"}:
                # Si la premiere case est inconnue, on ne peut pas refuter l'hypothese qu'un garde puisse se trouver sur la premiere case et voir (i, j)
                if self.get_case(i-1, j).contenu[0] == "inconnu":
                    droite.append((i-1, j))
                # Si la deuxieme case est un garde ou inconnue, on ne peut pas refuter l'hypothese qu'un garde puisse se trouver sur la deuxieme case et voir (i, j)
                if self.case_existe(i-2, j) and self.get_case(i-2, j).contenu[0] in {"inconnu", "garde"}:
                    droite.append((i-2, j))
            # Si la premiere case n'est ni un garde, ni vide, ni inconnue, alors elle n'est pas un garde qui voit (i, j) et bloque la vue de la case d'apres
            # (i, j) ne peut donc pas etre vu par un garde dans cette direction

            # La direction contiendra entre 0 et 2 elements, mais dans le cas 2, evidemment seule une case au maximum pourra
            # contenir un garde qui voit (i, j) dans cette direction, on ne connait juste pas encore laquelle

        # meme principe pour les trois autres directions
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
    
    def cases_entendre(self, i: int, j: int)-> List[Tuple[int, int]]:
        """
        Renvoie les cases autour de la case dans un rayon de 2, plus la case actuelle elle-meme
        Cette methode est utile lorsque le joueur veut "entendre"
        """
        if not self.case_existe(i, j):
            raise ValueError(f"La case ({i}, {j}) n'existe pas")

        # carre 5*5 correspondant a la zone d'ecoute
        candidates = [(x, y) for x in range(i-2, i+3) for y in range(j-2, j+3)]

        # on retire les cases qui n'existent pas
        voisins = [c for c in candidates if self.case_existe(c[0], c[1])]
                
        return voisins
    

    def cases_voir(self, i: int, j: int, direction: str)-> List[Tuple[int, int]]:
        """
        Renvoie les trois cases que l'on peut voir et acceder dans la direction donnee par rapport a la case (i, j)

        Cette methode est utile lorsque le joueur veut connaitre les cases depuis lesquelles
        il peut voir une certaine case.
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
                # Si la case est interdite, on n'inclut que les cases devant
                if self.get_case(c[0], c[1]).case_interdite():
                    voisins = voisins[:k]
                # Sinon, on inclut la case devant et la case actuelle
                else:
                    voisins = voisins[:k+1]
                break

        return voisins