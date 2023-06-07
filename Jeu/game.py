from utils.clauses_combin import *
from utils.plateau import Plateau
from utils.hitman import HC, HitmanReferee
from gophersat.dimacs import solve
import time
import heapq
from typing import Tuple, List, Dict



class Game:
    """
    Classe qui represente le jeu

    Le jeu est caracterise par :
        - plateau : objet plateau qui represente le plateau du jeu (notre modelisation de nos connaissances)
        - hitman : objet hitman qui permet de communiquer avec le referee
        - clauses : liste de clauses qui represente notre base de clauses
        - penalites : tableau contenant le nombre exact de gardes par lesquels on est vu pour chaque case (si ce nombre est connu, False sinon)
        - old_penalty : nombre de penalites avant la derniere action
        - status : dictionnaire contenant les informations sur l'etat actuel du jeu
        - nb_variables : nombre de variables dans la base de clauses
        - attente : liste de couples ou l'on sait pour chaque couple qu'au moins une des deux cases est un garde (voir plus bas)
        - temporisation : booleen qui indique si on utilise la temporisation ou non (pour faire les affichages plus lentement)
        - no_sat : booleen qui indique si on utilise sat pour calculer le risque ou non (pour faire les affichages plus lentement) #completer
        - _dict_cases : dictionnaire qui permet de convertir un contenu de case en un tuple (element, direction)
        - _dict_directions : dictionnaire qui permet de convertir une direction en un chaine de caracteres

    
    Les methodes utiles sont :
        - pos_actuelle : renvoie la position actuelle du hitman
        - direction_actuelle : renvoie la direction actuelle du hitman
        - phase_1 : methode qui implemente la phase 1 du jeu (voir plus bas)
        - explore : methode qui explore une case pour en determiner le contenu (voir plus bas)
        - prochain_objectif : methode qui determine la prochaine case a explorer (voir plus bas)
        - prochaine_case : methode qui determine la prochaine case a laquelle se deplacer (voir plus bas)
        - penalite_minimale : methode qui determine la penalite minimale pour aller a une case (voir plus bas)
        - risque : methode qui determine le risque d'aller sur une case (voir plus bas)
        - update_knowledge : methode qui met a jour notre modelisation du jeu (voir plus bas)
        - update_hitman : methode qui met a jour la position et la direction du hitman sur le plateau (voir plus bas)
        - tourner : methode qui tourne jusqu'a ce qu'une case soit visible (voir plus bas)
        - satisfiable : methode qui determine si la base de clauses est satisfiable (voir plus bas)
        
    """
    def __init__(self):
        self.plateau = None
        self.hitman = HitmanReferee()
        self.clauses = []
        self.penalites = None
        self.old_penalty = 0
        self.status = None
        self.nb_variables = None
        self.attente = []
        self.temporisation = True
        self.no_sat = False
        self._dict_cases = {
            HC.EMPTY : ("vide", None),
            HC.WALL : ("mur", None),
            HC.PIANO_WIRE : ("corde", None),
            HC.SUIT : ("costume", None),
            HC.GUARD_N : ("garde", "haut"),
            HC.GUARD_E : ("garde", "droite"),
            HC.GUARD_S : ("garde", "bas"),
            HC.GUARD_W : ("garde", "gauche"),
            HC.CIVIL_N : ("invite", "haut"),
            HC.CIVIL_E : ("invite", "droite"),
            HC.CIVIL_S : ("invite", "bas"),
            HC.CIVIL_W : ("invite", "gauche"),
            HC.TARGET : ("cible", None)
        }
        self._dict_directions = {
            HC.N : "haut",
            HC.E : "droite",
            HC.S : "bas",
            HC.W : "gauche"
        }


    def pos_actuelle(self)-> Tuple[int, int]:
        """
        Renvoit la position actuelle du hitman
        """
        if self.status is None:
            raise ValueError("Le jeu n'a pas ete initialise")

        return self.status['position']
    
    def direction_actuelle(self)-> str:
        """
        Renvoit la direction actuelle du hitman
        """
        if self.status is None:
            raise ValueError("Le jeu n'a pas ete initialise")

        return self._dict_directions[self.status['orientation']]
            

    def phase_1(self, temporisation: bool = True, no_sat: bool = False):
        """
        Implementation de la phase 1 du jeu. Le deroule est le suivant :

        I. Initialisation
            1. On initialise le jeu avec start_phase1 et en recuperant les informations de la phase 1
            2. On cree un objet plateau pour faire notre modelisation du jeu
            3. On initialise la base de clauses
        II. Deroulement
            1. Tant qu'il reste des cases dont le contenu est inconnu :
                - On determine la prochaine case a explorer selon l'heuristique "penalite_minimale" grace a "prochain_objectif"
                - On explore la case en question avec "explore"
        III. Fin
            1. On envoie le contenu du plateau a hitman pour verifier si on a correctement rempli le plateau
            2. On affiche le resultat
        """

        # Initialisation
        self.status = self.hitman.start_phase1()
        lignes = self.status['m']
        colonnes = self.status['n']
        self.plateau = Plateau(colonnes, lignes)
        self.penalites = [[False for _ in range(lignes)] for _ in range(colonnes)]
        n_invites = self.status['civil_count']
        n_gardes = self.status['guard_count']
        self.temporisation = temporisation
        self.no_sat = no_sat

        # recuperation des dimensions du plateau et des variables cnf
        m, n = self.plateau.infos_plateau()
        variables_invites = [self.plateau.cell_to_var(i, j, "invite") for i in range(m) for j in range(n)]
        variables_gardes = [self.plateau.cell_to_var(i, j, "garde") for i in range(m) for j in range(n)]
        self.nb_variables = len(variables_invites) + len(variables_gardes)

        # On ajoute les clauses initiales
        self.clauses += exactly_n(n_invites, variables_invites) # clauses pour avoir n_invites invites
        self.clauses += exactly_n(n_gardes, variables_gardes) # clauses pour avoir n_gardes gardes
        self.clauses += unique(variables_invites, variables_gardes) # clauses pour ne pas avoir d'invite et de garde sur la meme case

        print(self.plateau)
        self.update_knowledge()
        i_act, j_act = self.pos_actuelle()
        self.clauses.append([-self.plateau.cell_to_var(i_act, j_act, "garde")]) # On ne peut pas apparaitre sur un garde car le jeu l'interdit
        print(self.plateau)

        # Deroulement
        while self.prochain_objectif():
            i, j = self.prochain_objectif()
            self.explore(i, j)

        # Fin
        if self.hitman.send_content(self.plateau.board_to_dict()):
            print(f"Gagne ! trouve avec {self.status['penalties']} penalites")
        else:
            print("Perdu !")



    def explore(self, i_objectif: int, j_objectif: int):
        """
        methode d'exploration qui a pour but d'effectuer une serie d'actions pour determiner
        le contenu de la case (i_objectif, j_objectif).

        Pour se faire, on fait dans un premier temps la liste des cases depuis lesquelles on peut (a priori)
        voir la case (i_objectif, j_objectif). Cette liste n'est pas absolue car il peut par exemple y avoir
        un mur entre la case (i, j) et la case (i_objectif, j_objectif) mais on ne le sait pas encore.

        Une fois la liste obtenue, on effectue les actions suivantes :
            - Tant qu'on est pas sur une case depuis laquelle on peut voir la case (i_objectif, j_objectif) :
                - Calculer l'heuristique entre chacune de nos cases voisines et les cases pour laquelle on peut voir l'objectif et prendre le minimum
                - Se deplacer sur la meilleure case voisine
                - (Mettre a jour notre connaissance du plateau et l'afficher)
            - Si la case objectif est visible, on a termine
            - Sinon, on retire la case actuelle de la liste des cases depuis lesquelles on peut voir la case objectif et on reprend la boucle
                - Si la liste finit par etre vide, alors la case objectif n'est pas accessible
        """

        if self.status is None:
            raise ValueError("Le jeu n'a pas ete initialise")
        
        # liste des cases depuis lesquelles on peut (a priori) voir la case (i, j)
        targets = []
        directions = ("haut", "droite", "bas", "gauche")
        for direction in directions:
            targets += self.plateau.cases_voir(i_objectif, j_objectif, direction)
        i_act, j_act = self.pos_actuelle()

        while not self.plateau.get_case(i_objectif, j_objectif).contenu_connu() and targets != []:
            # Le contenu peut etre deduit en cours d'exploration sans avoir ete vu si c'est un garde,
            # On rajoute donc la condition contenu inconnu dans le deuxieme while pour eviter d'aller explorer inutilement
            while (i_act, j_act) not in targets and not self.plateau.get_case(i_objectif, j_objectif).contenu_connu():
                voisin_min = self.prochaine_case(i_act, j_act, targets)
                
                if voisin_min is None:
                    raise ValueError("Aucun voisin n'est accessible")
                
                # self.tourner permet de se tourner vers la case voisine voulue et ainsi de se preparer a s'y deplacer
                # Cependant, si on est actuellement visible par un garde, il peut etre desavantageux de tourner et ainsi prendre des penalites
                # Il vaut surement mieux avancer et se retourner plus loin. La methode gere ce cas et renvoie True si elle a fait avancer hitman
                # pour eviter de se faire voir plus longtemps 
                reflexe_survie = self.tourner(voisin_min[0], voisin_min[1])

                # A ce stade, apres tourner, il existe des cas ou le contenu a pu etre deduit, si c'est le cas on casse la boucle
                if self.plateau.get_case(i_objectif, j_objectif).contenu_connu():
                    break

                # On avance vers la case voisine si elle n'est pas interdite et qu'on s'est tourne vers elle (et donc self.tourner a renvoye False)
                if not self.plateau.get_case(voisin_min[0], voisin_min[1]).case_interdite() and not reflexe_survie:
                    self.status = self.hitman.move()
                    self.update_knowledge()
                    print(self.plateau)

                i_act, j_act = self.pos_actuelle()

            # A ce stade, il existe des cas ou le contenu a pu etre deduit, si c'est le cas on casse la boucle
            if self.plateau.get_case(i_objectif, j_objectif).contenu_connu():
                break

            # A ce stade, on est sur une case depuis laquelle on peut voir la case (i_objectif, j_objectif)
            reflexe_survie = self.tourner(i_objectif, j_objectif)
            i_act, j_act = self.pos_actuelle()

            if not self.plateau.get_case(i_objectif, j_objectif).contenu_connu() and not reflexe_survie:
                # il y a un objet entre la case actuelle et la case objectif
                # on recalcule les targets avec case_voir, qui s'occupe d'enlever les cases non pertinentes a cause d'obstacles
                targets = []
                for direction in directions:
                    targets += self.plateau.cases_voir(i_objectif, j_objectif, direction) # cases_voir renverra les cases depuis lesquelles on peut voir la case objectif en fonction de nos nouvelles connaissances

        if targets == []:
            raise ValueError(f"La case ({i_objectif}, {j_objectif}) n'est pas accessible")
        
    def prochaine_case(self, i_act: int, j_act: int, targets: List[Tuple[int, int]]) -> Tuple[int, int]:
        """
        Determine la prochaine case a laquelle se deplacer pour aller de (i_act, j_act) a (i_objectif, j_objectif)

        L'heuristique utilisee est la penalite minimale
        """
        voisins_actuels = [v for v in self.plateau.voisins(i_act, j_act) if not self.plateau.get_case(v[0], v[1]).case_interdite()]
        penal_min = float("inf")
        voisin_min = None

        # voisin le plus proche
        for i_target, j_target in targets:
            penalite_min_tableau = self.penalite_minimale(i_target, j_target, sat_coordinates=voisins_actuels)
            for i_voisin, j_voisin in voisins_actuels:
                penal = penalite_min_tableau[i_voisin][j_voisin]
                
                if penal < penal_min:
                    penal_min = penal
                    voisin_min = (i_voisin, j_voisin)

        return voisin_min
    
    def penalite_minimale(self, i: int, j: int, sat_coordinates: List[Tuple[int, int]] = []) -> List[List[int]]:
        """
        Methode definissant l'heuristique d'exploration pour la phase 1
        Le retourn est un tableau m*n ou contient la penalite du meilleur chemin 
        entre la case correspondante, et la case objectif (i, j)

        Le principe (egalement explique dans le readme) est le suivant :
            I. Debut
                - On initialise toutes les penalites a +infini
                - On fixe la penalite de la case objectif egale a son risque
                - Pour chaque voisin de la case objectif, on ajoute dans un tas la penalite minimale polentielle
                    de chaque voisin pour aller a la case objectif, egale a :
                    la penalite de la case objectif + 1 + le risque du voisin
                    L'element ajoute au tas est un tuple (penalite, i, j)
            II. Deroulement
                - Prendre dans le tas la penalite minimale potentielle
                - Si la case correspondante a cette penalite a deja ete traitee, on passe a la suivante
                - Sinon, on met a jour la penalite de la case correspondante (penalite minimale potentielle devient penalite minimale)
                    - On ajoute dans le tas les voisins de la case correspondante avec leur penalite minimale potentielle, egales a :
                        la penalite minimale de la case correspondante + 1 + le risque du voisin
                - On recommence jusqu'a ce que le tas soit vide
            III. Fin
                - On renvoie le tableau des penalites minimales

        En procedant de cette maniere, on rajoute a chaque iteration la nieme case de penalite
        minimale pour aller a la case objectif

        sat_coordinates est une liste de coordonnees pour lesquelles on utilisera SAT pour calculer le risque.
        Quand cette liste est non vide, elle correspond aux voisins de la case actuelle.

        On ne peut pas se permettre d'utiliser sat pour calculer le risque de toutes les cases car cela prendrait trop de temps.
        """
        m, n = self.plateau.infos_plateau()
        cases_traitees = set()
        cases_a_traiter = []

        penalites = [[float("inf") for _ in range(n)] for _ in range(m)]

        if (i, j) in sat_coordinates:
            penalites[i][j] = self.risque(i, j, use_sat=True)
        else:
            penalites[i][j] = self.risque(i, j)
        cases_traitees.add((i, j))

        for i_voisin, j_voisin in self.plateau.voisins(i, j):
            if self.plateau.get_case(i_voisin, j_voisin).case_interdite():
                continue
            if (i_voisin, j_voisin) in sat_coordinates:
                penalite = penalites[i][j] + 1 + self.risque(i_voisin, j_voisin, use_sat=True)
            else:
                penalite = penalites[i][j] + 1 + self.risque(i_voisin, j_voisin)
            heapq.heappush(cases_a_traiter, (penalite, i_voisin, j_voisin))

        while cases_a_traiter != []:
            penalite_act, i_act, j_act = heapq.heappop(cases_a_traiter)
            if (i_act, j_act) in cases_traitees:
                continue
            cases_traitees.add((i_act, j_act))
            penalites[i_act][j_act] = penalite_act

            for i_voisin, j_voisin in self.plateau.voisins(i_act, j_act):
                if self.plateau.get_case(i_voisin, j_voisin).case_interdite():
                    continue
                if (i_voisin, j_voisin) in sat_coordinates:
                    penalite = penalites[i_act][j_act] + 1 + self.risque(i_voisin, j_voisin, use_sat=True)
                else:
                    penalite = penalites[i_act][j_act] + 1 + self.risque(i_voisin, j_voisin)
                heapq.heappush(cases_a_traiter, (penalite, i_voisin, j_voisin))

        return penalites

        
    def risque(self, i: int, j: int, use_sat: bool = False)-> int:
        """
        Determine le risque d'aller sur une case,
        On calcule d'abord un tuple (min, max) correspondant au nombre minimum et maximum de gardes
        par lesquels on peut etre vus en passant par la case (i, j). On peut etre vu âr quatre
        directions differentes, donc le nombre de gardes peut varier entre 0 et 4.
        (si deux gardes regardent dans la meme direction et sont a cote, le premier bloque la vue du second)

        La valeur renvoyee correspond a (4 * min) + max, ce qui revient lorsqu'on compare le risque de 
        deux cases a se baser sur le min, puis sur le max en cas d'egalite.
        (0, 0) -> 0
        (0, 1) -> 1
        (0, 2) -> 2
        (0, 3) -> 3
        (0, 4) -> 4
        (1, 1) -> 5
        (1, 2) -> 6
        (1, 3) -> 7
        (1, 4) -> 8
        (2, 2) -> 10
        (2, 3) -> 11
        (2, 4) -> 12
        (3, 3) -> 15
        (3, 4) -> 16
        (4, 4) -> 20

        Au debut le nombre de penalite augmente de 1 en 1, puis a la fin cela augmente plus vite lorsque
        min est grand, ce qui permet de rejeter fortement les cases avec un grand min.
        """

        if not self.plateau.case_existe(i, j):
            raise ValueError("La case n'existe pas")
        
        # si la case est un invite, on ne sera pas vu
        if self.plateau.get_case(i, j).contenu[0] == "invite":
            return 0
        
        if self.no_sat:
            use_sat = False
        
        # self.penalites contient le nombre de gardes par lesquels on est vu pour une case donnee
        # si sa valeur n'est pas False, alors on connait deja la valeur, min = max = self.penalites[i][j]
        if self.penalites[i][j] is not False:
            m = self.penalites[i][j]
            return (4 * m) + m

        gardes_potentiels = self.plateau.voisins_gardes(i, j)

        # "direction" : [min, max]
        visible_depuis = {"gauche": [0, 0], "droite": [0, 0], "haut": [0, 0], "bas": [0, 0]}

        for direction in ['gauche', 'droite', 'haut', 'bas']:
            voisins_direction = gardes_potentiels[direction]
            for i_garde, j_garde in voisins_direction:

                # cas "on est sur" qu'un garde nous voit, mettre min et max a 1 pour la direction
                if self.plateau.get_case(i_garde, j_garde).contenu[0] == "garde" and self.plateau.get_case(i_garde, j_garde).contenu[1] == direction:
                    visible_depuis[direction][0] = 1
                    visible_depuis[direction][1] = 1
                    break

                # cas "il est possible" qu'un garde nous voit, mettre max a 1 pour la direction
                if not self.plateau.get_case(i_garde, j_garde).proven_not_guard:
                    if not self.plateau.get_case(i_garde, j_garde).contenu_connu():
                        
                        # avant d'augmenter max, on essaye de prouver que la case n'est pas un garde.
                        # Pour cela on regarde s'il n'existe pas de modele ou la case est un garde
                        if use_sat:
                            clauses_temp = self.clauses.copy()
                            self.clauses.append([self.plateau.cell_to_var(i_garde, j_garde, "garde")])
                            if self.satisfiable():
                                visible_depuis[direction][1] = 1
                            else:
                                self.plateau.get_case(i_garde, j_garde).proven_not_guard = True
                            self.clauses = clauses_temp.copy()
                        # Si on n'utilise pas sat, on ne cherche pas a prouver que la case n'est pas un garde
                        # et on incremente max dans tous les cas
                        else:
                            visible_depuis[direction][1] = 1

        # chaque visible_depuis[direction] est un tableau [min, max], ou min et max sont compris entre 0 et 1
        # car on ne peut etre vu qu'une fois par direction

        min = sum([visible_depuis[direction][0] for direction in visible_depuis])
        max = sum([visible_depuis[direction][1] for direction in visible_depuis])

        # si la case est un invite, on ne sera pas vu, si son contenu est inconnu, on ne peut pas savoir
        if not self.plateau.get_case(i, j).contenu_connu():
            min = 0

        return (4 * min) + max


    def update_hitman(self):
        """
        Met a jour la position et direction de hitman sur le plateau
        """
        i_act, j_act = self.pos_actuelle()
        direction_act = self.direction_actuelle()

        self.plateau.pos_hitman = (i_act, j_act, direction_act)

    def tourner(self, i_objectif: int, j_objectif: int)-> bool:
        """
        Tourne jusqu'a ce que la case (i_objectif, j_objectif) soit visible
        Si la case est deja en face, ne fait rien

        Si hitman est en train d'etre vu par un garde, alors on regarde si on peut avancer et
        s'il existe un point de vue moins risque pour voir la case objectif. Si oui, on avance
        pour eviter de prendre des penalites supplementaires. La fonction return True si on a avance,
        False sinon.

        Si on doit se retourner, et donc tourner deux fois, la methode calcule dans quel sens il
        est le plus interessant de se retourner, en fonction du nombre de cases inconnue de chaque cote
        """

        if not self.plateau.case_existe(i_objectif, j_objectif):
            raise ValueError("La case n'existe pas")

        i_act, j_act = self.pos_actuelle()

        # si la case est hors de portee meme en se tournant
        directions = ("haut", "droite", "bas", "gauche")
        if self.plateau.distance_manhattan(i_act, j_act, i_objectif, j_objectif) > 3:
            raise ValueError("La case est trop loin")

        if len(self.status['vision']) > 0: # s'il y a une case devant
            case_devant = self.status['vision'][0][0]
            if not self.plateau.get_case(case_devant[0], case_devant[1]).case_interdite(): # si la case devant n'est pas interdite
                if self.penalites[i_act][j_act] > 0: # si on est en train d'etre vu par au moins un garde
                    autres_pdv = []
                    directions = ("haut", "droite", "bas", "gauche")
                    for direction in directions: # autres points de vue depuis lesquels on pourrait voir notre objectif
                        autres_pdv += self.plateau.cases_voir(i_objectif, j_objectif, direction)
                    
                    # s'il existe un meilleur point de vue, on avance, cela ne vaut pas le coup de se tourner vers l'objectif
                    if self.risque(case_devant[0], case_devant[1], use_sat=True) < self.risque(i_act, j_act, use_sat=True):
                        for i, j in autres_pdv:
                            if self.penalites[i][j] == 0 or self.penalites[i][j] is False:
                                self.status = self.hitman.move()
                                self.update_knowledge()
                                print(self.plateau)
                                return True

        # on determine dans quel sens on se tourne
        if i_objectif == i_act:
            if j_objectif > j_act:
                direction = "haut"
            else: # j_objectif < j_act
                direction = "bas"
        elif j_objectif == j_act:
            if i_objectif > i_act:
                direction = "droite"
            else: # i_objectif < i_act
                direction = "gauche"
        else:
            raise ValueError("La case ne peut pas etre vue en tournant sur place")
        
        index = directions.index(direction)
        index_act = directions.index(self.direction_actuelle())

        # sens des aiguilles d'une montre
        if index == (index_act + 1) % 4:
            self.status = self.hitman.turn_clockwise()
            self.update_knowledge()
            print(self.plateau)
        # sens inverse des aiguilles d'une montre
        elif index == (index_act + 3) % 4:
            self.status = self.hitman.turn_anti_clockwise()
            self.update_knowledge()
            print(self.plateau)
        # On tourne 2 fois, on regarde dans quel sens il sera le plus informatif de tourner
        elif index == (index_act + 2) % 4:
            if direction in {"haut", "bas"}:
                nb_cases_inconnues_gauche = len([(i, j) for i, j in self.plateau.cases_voir(i_act, j_act, "gauche") if not self.plateau.get_case(i, j).contenu_connu()])
                nb_cases_inconnues_droite = len([(i, j) for i, j in self.plateau.cases_voir(i_act, j_act, "droite") if not self.plateau.get_case(i, j).contenu_connu()])
                
                if nb_cases_inconnues_gauche > nb_cases_inconnues_droite:
                    if direction == "haut":
                        self.status = self.hitman.turn_clockwise()
                        self.update_knowledge()
                        print(self.plateau)
                        self.status = self.hitman.turn_clockwise()
                    else:
                        self.status = self.hitman.turn_anti_clockwise()
                        self.update_knowledge()
                        print(self.plateau)
                        self.status = self.hitman.turn_anti_clockwise()
                else: # nb_cases_inconnues_gauche <= nb_cases_inconnues_droite
                    if direction == "haut":
                        self.status = self.hitman.turn_anti_clockwise()
                        self.update_knowledge()
                        print(self.plateau)
                        self.status = self.hitman.turn_anti_clockwise()                            
                    else:
                        self.status = self.hitman.turn_clockwise()
                        self.update_knowledge()
                        print(self.plateau)
                        self.status = self.hitman.turn_clockwise()
            
            else: # direction in {"gauche", "droite"}
                nb_cases_inconnues_haut = len([(i, j) for i, j in self.plateau.cases_voir(i_act, j_act, "haut") if not self.plateau.get_case(i, j).contenu_connu()])
                nb_cases_inconnues_bas = len([(i, j) for i, j in self.plateau.cases_voir(i_act, j_act, "bas") if not self.plateau.get_case(i, j).contenu_connu()])

                if nb_cases_inconnues_haut > nb_cases_inconnues_bas:
                    if direction == "gauche":
                        self.status = self.hitman.turn_anti_clockwise()
                        self.update_knowledge()
                        print(self.plateau)
                        self.status = self.hitman.turn_anti_clockwise()
                    else:
                        self.status = self.hitman.turn_clockwise()
                        self.update_knowledge()
                        print(self.plateau)
                        self.status = self.hitman.turn_clockwise()
                else: # nb_cases_inconnues_haut <= nb_cases_inconnues_bas
                    if direction == "gauche":
                        self.status = self.hitman.turn_clockwise()
                        self.update_knowledge()
                        print(self.plateau)
                        self.status = self.hitman.turn_clockwise()
                    else:
                        self.status = self.hitman.turn_anti_clockwise()
                        self.update_knowledge()
                        print(self.plateau)
                        self.status = self.hitman.turn_anti_clockwise()
            
            self.update_knowledge()
            print(self.plateau)
        
        if not self.direction_actuelle() == direction:
            raise ValueError("La direction n'est pas bonne")
        
        return False
        

    def satisfiable(self)-> bool:
        """
        Renvoie True si les clauses sont satisfiables, False sinon
        """
        solve(self.clauses, nb_var=self.nb_variables) #completer, return

    def update_knowledge(self):
        """
        Met a jour le plateau et la base de clauses avec les informations obtenues

        Il y a trois facons d'obtenir des informations :

        I. La vue
            - on met a jour notre modele de plateau
            - on ajoute des clauses

        II. l'ecoute
            - on ajoute simplement des clauses. Il y a "hear" cases qui contiennent
                un garde ou un invite le fait qu'un garde et un invite ne soient pas
                sur la meme case est deja pris en compte dans les clauses d'initialisation
        
        III. les penalites
            On peut deduire grace au status actuel de hitman combien de gardes sont en train de nous voir
            pour la case actuelle. En effet on prend 5 penalites par garde qui nous voit, et on connait
            le nombre de penalites que l'on avait avant de faire notre derniere action.
            L'ecart entre les deux devrait etre : 1 + (nb_gardes_vus * 5).
            On connait donc le nombre de gardes qui nous voient pour les cases deja visitees. On extrait
            de ceci deux informations :
                - le nombre de gardes qui nous voient pour la case actuelle, self.penalties[i_act][j_act],
                    ce qui permet d'affiner le calcul du risque
                - si on est vu par n gardes et qu'il y a n cases inconnues ou des gardes peuvent nous voir,
                    on peut deduire que ces cases contiennent des gardes qui regardent vers hitman


        On met egalement a jour la position et la direction de hitman sur la carte
        """

        # permet de ralentir l'affichage pour mieux voir les etapes si cela va trop vite
        if self.temporisation:
            time.sleep(0.25)

        if self.status is None:
            raise ValueError("Le jeu n'a pas ete initialise")

        vision = self.status['vision']
        hear = self.status['hear']

        # penalites
        i_act, j_act = self.pos_actuelle()
        if self.penalites[i_act][j_act] is False:
            n_vu_par = (self.status['penalties'] - self.old_penalty) // 5
            self.penalites[i_act][j_act] = n_vu_par

            if self.plateau.get_case(i_act, j_act).contenu_connu() and self.plateau.get_case(i_act, j_act).contenu[0] != "invite":            
                voisins_gardes_dict = self.plateau.voisins_gardes(i_act, j_act)
                voisins_gardes = []
                list_not_empty = 0
                for direction in voisins_gardes_dict:
                    if voisins_gardes_dict[direction] != []:
                        list_not_empty += 1
                        voisins_gardes += voisins_gardes_dict[direction]
                gardes_potentiels = [self.plateau.cell_to_var(c[0], c[1], "garde") for c in voisins_gardes]
                self.clauses += at_least_n(n_vu_par, gardes_potentiels)

                if list_not_empty == n_vu_par: # on connait les directions depuis lesquelles on est vu
                    for direction in voisins_gardes_dict:
                        if voisins_gardes_dict[direction] != []:
                            voisins_direction = [self.plateau.cell_to_var(v[0], v[1], "garde") for v in voisins_gardes_dict[direction]]
                            self.clauses += at_least_n(1, voisins_direction)

                            if len(voisins_gardes_dict[direction]) == 1:
                                case = voisins_gardes_dict[direction][0]
                                if not self.plateau.get_case(case[0], case[1]).contenu_connu():
                                    self.plateau.set_case(case[0], case[1], ("garde", direction))

                                for pair in self.attente:
                                    if (case[0], case[1], ("garde", direction)) in pair:
                                        self.attente.remove(pair)

                            else: # len(voisins_gardes_dict[direction]) == 2:
                                # si il y a deux cases contenant des cartes ayant pu nous voir dans cette direction,
                                # une des deux est un garde qui nous regarde. Si on en trouve une, on pourra en deduire l'autre 
                                case1, case2 = voisins_gardes_dict[direction]
                                self.attente.append(((case1[0], case1[1], ("garde", direction)), (case2[0], case2[1], ("garde", direction))))

        self.old_penalty = self.status['penalties'] # mise a jour de la penalite actuelle

        # vision
        ## plateau
        for case in vision:
            pos, contenu = case
            i, j = pos
            if not self.plateau.get_case(i, j).contenu_connu():
                self.plateau.set_case(i, j, self._dict_cases[contenu])
                
                for pair in self.attente:
                    for direction in {"haut", "droite", "bas", "gauche"}:
                        if (i, j, ("garde", direction)) in pair:
                            if self._dict_cases[contenu] != ("garde", direction):
                                other_item = pair[0] if pair[0] != (i, j, ("garde", direction)) else pair[1]
                                self.plateau.set_case(other_item[0], other_item[1], other_item[2])
                            self.attente.remove(pair)


                ## clauses
                if self._dict_cases[contenu][0] in {"invite", "garde"}:
                    self.clauses.append([self.plateau.cell_to_var(i, j, self._dict_cases[contenu][0])])
                else:
                    self.clauses.append([-self.plateau.cell_to_var(i, j, "invite")])
                    self.clauses.append([-self.plateau.cell_to_var(i, j, "garde")])

        # ouie
        ## clauses
        cases_entendues = self.plateau.cases_entendre(i_act, j_act)
        variables_invites_gardes = [self.plateau.cell_to_var(i, j, "invite") for i, j in cases_entendues] + [self.plateau.cell_to_var(i, j, "garde") for i, j in cases_entendues]

        if hear == 5:
            self.clauses += at_least_n(5, variables_invites_gardes)
        else:
            self.clauses += exactly_n(hear, variables_invites_gardes)

        # hitman
        self.update_hitman()


    def prochain_objectif(self):
        """
        Renvoie les coordonnees de la prochaine case a explorer en fonction de 
        l'heuristique "penalite minimale", on choisit la case inconnue avec la plus petite penalite
        de deplacement par rapport a nous.
        """
        if self.plateau is None:
            raise ValueError("Le jeu n'a pas ete initialise")
        
        # on recupere les coordonnees de la case actuelle et les dimensions du plateau
        i, j = self.pos_actuelle()
        m, n = self.plateau.infos_plateau()

        i_min, j_min = None, None
        penalite_min = float("inf")

        penalites_min = self.penalite_minimale(i, j)

        # on recupere les cases candidates
        for i2 in range(m):
            for j2 in range(n):
                if i2 == i and j2 == j:
                    continue
                if self.plateau.get_case(i2, j2).contenu_connu():
                    continue
                penalite = penalites_min[i2][j2]
                if penalite < penalite_min:
                    penalite_min = penalite
                    i_min, j_min = i2, j2

        # on renvoie la premiere case qui n'a pas encore ete exploree
        if i_min is not None and j_min is not None:
            return i_min, j_min
            
        # si toutes les cases ont ete explorees, on renvoie False
        return False




g = Game()
methodes = [m for m in dir(g) if callable(getattr(g, m)) and not m.startswith("__")]

for methode in methodes:
    print(methode)
# g.phase_1(no_sat=True, temporisation=False)

