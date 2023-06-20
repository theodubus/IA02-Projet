from utils.clauses_combin import *
from utils.plateau import Plateau
from utils.hitman import HC, HitmanReferee
from gophersat.dimacs import solve
import heapq
from typing import Tuple, List, Set
from collections import namedtuple
from time import sleep

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
        - _temporisation : booleen qui indique si on utilise la temporisation ou non (pour faire les affichages plus lentement)
        - _dict_cases : dictionnaire qui permet de convertir un contenu de case en un tuple (element, direction)
        - _dict_directions : dictionnaire qui permet de convertir une direction en un chaine de caracteres
        - _sat_mode : chaine de caracteres qui indique le mode de calcul du risque (voir plus bas)
        - _display : booleen qui indique si on affiche le jeu ou non

    
    Les methodes utiles sont :
        Pour la phase 1 :
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

        Pour la phase 2 :
            - avancer, tourner_horaire, tourner_antihoraire : methodes qui renvoient la nouvelle position/direction apres avoir effectue l'action correspondante
            - seen_by_guards, seen_by_civil : methodes qui renvoient le nombre de gardes/invites qui nous voient depuis une case donnee
            - do_fn : methode qui permet de simuler une action, prend un etat en parametre et renvoit le nouvel etat correspondant apres l'action
            - do_fn_for_real : methode qui permet d'effectuer reellement une action
            - succ : methode qui renvoit les etats successeurs d'un etat donne (voir plus bas)
            - test_if_goal_achived : Teste si dans l'objectif a ete atteint pour l'etat donne
            - h_score : Adaptation de penalite_minimale pour calcul de h_score pour A* dans la phase 2 (voir plus bas)
            - calculer_heuristique_a_etoile : methode qui calcule l'heuristique pour A*, g_score + h_score
            - transform_dict_to_namedtuple : initialise l'etat initial (namedtuple)
            - locate_element : localise un element sur le plateau
            - search_with_parent : cherche a atteindre un objectif depuis un etat donne
            - phase_2 : implementation de la phase 2 du jeu (voir plus bas)
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
        self._temporisation = True
        self._sat_mode = "auto"
        self._history_etats = set()
        self._history_positions = set()
        self._display = True
        self.n_invite_inconnu_restants = None
        self.n_garde_inconnu_restants = None
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

    def afficher_plateau(self):
        """
        Affiche le plateau si self._display est True
        """
        if self._display:
            print(self.plateau)

    ##########################################
    ##########################################
    ######## Methodes pour la phase 1 ########
    ##########################################
    ##########################################
    
    @property
    def sat_mode(self):
        return self._sat_mode
    
    @sat_mode.setter
    def sat_mode(self, mode: str):
        if mode not in ("auto", "sat", "no_sat"):
            raise ValueError("Le mode doit etre 'auto', 'sat' ou 'no_sat'")
        self._sat_mode = mode

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
            

    def phase_1(self, temporisation: bool = True, sat_mode: str = "auto", display: bool = True)-> Tuple[int, int]:
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
        print("\nLa phase 1 commence !")
        # Initialisation
        self.status = self.hitman.start_phase1()
        lignes = self.status['m']
        colonnes = self.status['n']
        self.plateau = Plateau(colonnes, lignes)
        self.penalites = [[False for _ in range(lignes)] for _ in range(colonnes)]
        n_invites = self.status['civil_count']
        n_gardes = self.status['guard_count']
        self._temporisation = temporisation
        self.sat_mode = sat_mode
        self._display = display

        # recuperation des dimensions du plateau et des variables cnf
        m, n = self.plateau.infos_plateau()
        variables_invites = [self.plateau.cell_to_var(i, j, "invite") for i in range(m) for j in range(n)]
        variables_gardes = [self.plateau.cell_to_var(i, j, "garde") for i in range(m) for j in range(n)]
        self.nb_variables = len(variables_invites) + len(variables_gardes)

        # On ajoute les clauses initiales
        
        # 1. clauses pour le nombre d'invites et de gardes
        # # Les clauses pour dire qu'il y a n_invites invites et n_gardes gardes sur le plateau sont trop
        # # nombreuses et explosent si on aggrandi la carte, on ne les ajoute pas et on gere le nombre d'invites
        # # et de gardes avec le code
        # # self.clauses += exactly_n(n_invites, variables_invites) # clauses pour avoir n_invites invites
        # # self.clauses += exactly_n(n_gardes, variables_gardes) # clauses pour avoir n_gardes gardes
        self.n_invite_inconnu_restants = n_invites
        self.n_garde_inconnu_restants = n_gardes

        # 2. clauses pour ne pas avoir d'invite et de garde sur la meme case
        ## cette condition produit n * m clauses, ce qui est raisonnable meme pour de grandes cartes
        self.clauses += unique(variables_invites, variables_gardes) # clauses pour ne pas avoir d'invite et de garde sur la meme case

        self.afficher_plateau()
        self.update_knowledge()
        i_act, j_act = self.pos_actuelle()
        self.clauses.append([-self.plateau.cell_to_var(i_act, j_act, "garde")]) # La case de depart est vide
        self.clauses.append([-self.plateau.cell_to_var(i_act, j_act, "invite")])
        self.plateau.set_case(i_act, j_act, ("vide", None))
        self.afficher_plateau()

        # Deroulement
        prochain_objectif = self.prochain_objectif()
        while prochain_objectif:
            i, j = prochain_objectif
            self.explore(i, j)
            prochain_objectif = self.prochain_objectif()

        # Fin
        if self.hitman.send_content(self.plateau.board_to_dict()):
            m, n = self.plateau.infos_plateau()
            calculated_score = 2 * m * n - self.status['penalties']
        else:
            print("Perdu !")

        _, score, _, _ = self.hitman.end_phase1()

        print("Result phase 1 :")
        print(score)

        return calculated_score, -self.status['penalties'], 2*m*n

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
                    self.afficher_plateau()

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
            penalite_min_tableau = self.penalite_minimale(i_target, j_target, cases_target=set(voisins_actuels))
            for i_voisin, j_voisin in voisins_actuels:
                penal = penalite_min_tableau[i_voisin][j_voisin]
                
                if penal < penal_min:
                    penal_min = penal
                    voisin_min = (i_voisin, j_voisin)
                elif penal == penal_min:
                    if self.plateau.distance_minimale(i_act, j_act, i_voisin, j_voisin) < self.plateau.distance_minimale(i_act, j_act, voisin_min[0], voisin_min[1]):
                        voisin_min = (i_voisin, j_voisin)

        return voisin_min
    
    def penalite_minimale(self, i: int, j: int, cases_target: Set[Tuple[int, int]] = set()) -> List[List[int]]:
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
                - On recommence jusqu'a ce que le tas soit vide ou qu'on ait traite toutes les cases que l'on voulait
            III. Fin
                - On renvoie le tableau des penalites minimales

        En procedant de cette maniere, on rajoute a chaque iteration la nieme case de penalite
        minimale pour aller a la case objectif

        cases_target est une liste de coordonnees pour lesquelles veut recuperer les penalites.
        Si cette liste est vide, on recupere les penalites pour tout le plateau, sinon, on s'arrete
        des qu'on a les cases souhaitees. On utilisera SAT pour calculer le risque de ces cases afin
        d'affiner son calcul. Quand cette liste est non vide, elle correspond aux voisins de la case actuelle.

        Utiliser SAT pour calculer le risque de toutes les cases n'est pas utile car la majorite des cases
        traitees sont inconnues et entourees de cases inconnues (et que l'on n'a pas non plus entendues)
        """
        m, n = self.plateau.infos_plateau()
        cases_traitees = set()
        tas_cases_a_traiter = []

        penalites = [[float("inf") for _ in range(n)] for _ in range(m)]

        if (i, j) in cases_target:
            penalites[i][j] = self.risque(i, j, use_sat=True)
        else:
            penalites[i][j] = self.risque(i, j)
        cases_traitees.add((i, j))

        for i_voisin, j_voisin in self.plateau.voisins(i, j):
            if self.plateau.get_case(i_voisin, j_voisin).case_interdite():
                continue
            if (i_voisin, j_voisin) in cases_target:
                penalite = penalites[i][j] + 1 + self.risque(i_voisin, j_voisin, use_sat=True)
            else:
                penalite = penalites[i][j] + 1 + self.risque(i_voisin, j_voisin)
            heapq.heappush(tas_cases_a_traiter, (penalite, i_voisin, j_voisin))

        while tas_cases_a_traiter != [] and (cases_target == set() or not cases_target.issubset(cases_traitees)):
            penalite_act, i_act, j_act = heapq.heappop(tas_cases_a_traiter)
            if (i_act, j_act) in cases_traitees:
                continue
            cases_traitees.add((i_act, j_act))
            penalites[i_act][j_act] = penalite_act

            for i_voisin, j_voisin in self.plateau.voisins(i_act, j_act):
                if self.plateau.get_case(i_voisin, j_voisin).case_interdite():
                    continue
                if (i_voisin, j_voisin) in cases_target:
                    penalite = penalites[i_act][j_act] + 1 + self.risque(i_voisin, j_voisin, use_sat=True)
                else:
                    penalite = penalites[i_act][j_act] + 1 + self.risque(i_voisin, j_voisin)
                heapq.heappush(tas_cases_a_traiter, (penalite, i_voisin, j_voisin))

        return penalites

        
    def risque(self, i: int, j: int, use_sat: bool = False)-> int:
        """
        Determine le risque d'aller sur une case,
        On calcule d'abord un tuple (min, max) correspondant au nombre minimum et maximum de gardes
        par lesquels on peut etre vus en passant par la case (i, j). On peut etre vu par quatre
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

        if self.sat_mode == "no_sat":
            use_sat = False
        elif self.sat_mode == "sat":
            use_sat = True

        if not self.plateau.case_existe(i, j):
            raise ValueError("La case n'existe pas")
        
        # si la case est un invite, on ne sera pas vu
        if self.plateau.get_case(i, j).contenu[0] == "invite":
            return 0
        
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
                                clauses_temp.append([-self.plateau.cell_to_var(i_garde, j_garde, "garde")])
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
        if not self.plateau.get_case(i, j).contenu_connu() and self.n_invite_inconnu_restants > 0:
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
                                self.afficher_plateau()
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
            self.afficher_plateau()
        # sens inverse des aiguilles d'une montre
        elif index == (index_act + 3) % 4:
            self.status = self.hitman.turn_anti_clockwise()
            self.update_knowledge()
            self.afficher_plateau()
        # On tourne 2 fois, on regarde dans quel sens il sera le plus informatif de tourner
        elif index == (index_act + 2) % 4:
            if direction in {"haut", "bas"}:
                nb_cases_inconnues_gauche = len([(i, j) for i, j in self.plateau.cases_voir(i_act, j_act, "gauche") if not self.plateau.get_case(i, j).contenu_connu()])
                nb_cases_inconnues_droite = len([(i, j) for i, j in self.plateau.cases_voir(i_act, j_act, "droite") if not self.plateau.get_case(i, j).contenu_connu()])
                
                if nb_cases_inconnues_gauche > nb_cases_inconnues_droite:
                    if direction == "haut":
                        self.status = self.hitman.turn_clockwise()
                        self.update_knowledge()
                        self.afficher_plateau()
                        self.status = self.hitman.turn_clockwise()
                    else:
                        self.status = self.hitman.turn_anti_clockwise()
                        self.update_knowledge()
                        self.afficher_plateau()
                        self.status = self.hitman.turn_anti_clockwise()
                else: # nb_cases_inconnues_gauche <= nb_cases_inconnues_droite
                    if direction == "haut":
                        self.status = self.hitman.turn_anti_clockwise()
                        self.update_knowledge()
                        self.afficher_plateau()
                        self.status = self.hitman.turn_anti_clockwise()                            
                    else:
                        self.status = self.hitman.turn_clockwise()
                        self.update_knowledge()
                        self.afficher_plateau()
                        self.status = self.hitman.turn_clockwise()
            
            else: # direction in {"gauche", "droite"}
                nb_cases_inconnues_haut = len([(i, j) for i, j in self.plateau.cases_voir(i_act, j_act, "haut") if not self.plateau.get_case(i, j).contenu_connu()])
                nb_cases_inconnues_bas = len([(i, j) for i, j in self.plateau.cases_voir(i_act, j_act, "bas") if not self.plateau.get_case(i, j).contenu_connu()])

                if nb_cases_inconnues_haut > nb_cases_inconnues_bas:
                    if direction == "gauche":
                        self.status = self.hitman.turn_anti_clockwise()
                        self.update_knowledge()
                        self.afficher_plateau()
                        self.status = self.hitman.turn_anti_clockwise()
                    else:
                        self.status = self.hitman.turn_clockwise()
                        self.update_knowledge()
                        self.afficher_plateau()
                        self.status = self.hitman.turn_clockwise()
                else: # nb_cases_inconnues_haut <= nb_cases_inconnues_bas
                    if direction == "gauche":
                        self.status = self.hitman.turn_clockwise()
                        self.update_knowledge()
                        self.afficher_plateau()
                        self.status = self.hitman.turn_clockwise()
                    else:
                        self.status = self.hitman.turn_anti_clockwise()
                        self.update_knowledge()
                        self.afficher_plateau()
                        self.status = self.hitman.turn_anti_clockwise()
            
            self.update_knowledge()
            self.afficher_plateau()
        
        if not self.direction_actuelle() == direction:
            raise ValueError("La direction n'est pas bonne")
        
        return False
        

    def satisfiable(self)-> bool:
        """
        Renvoie True si les clauses sont satisfiables, False sinon
        """
        return solve(self.clauses, nb_var=self.nb_variables)

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

        - premier_passage sert a savoir si on est deja passe par la case actuelle (i_act, j_act),
            et voir s'il utile de proceder au traitement pour les penalites et l'ecoute

        - premiere_fois_etat sert a savoir si on a deja ete dans l'etat (i_act, j_act, direction_act)
            et ainsi savoir s'il est utile de proceder au traitement pour la vue
        """

        # permet de ralentir l'affichage pour mieux voir les etapes si cela va trop vite
        if self._temporisation:
            sleep(0.25)

        if self.status is None:
            raise ValueError("Le jeu n'a pas ete initialise")

        vision = self.status['vision']
        hear = self.status['hear']
        i_act, j_act = self.pos_actuelle()
        direction_act = self.direction_actuelle()

        if (i_act, j_act) in self._history_positions:
            premier_passage = False
            if (i_act, j_act, direction_act) in self._history_etats:
                premiere_fois_etat = False
            else:
                self._history_etats.add((i_act, j_act, direction_act))
                premiere_fois_etat = True
        else:
            self._history_positions.add((i_act, j_act))
            premier_passage = True
            premiere_fois_etat = True

        # penalites
        if premier_passage:
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
                                    self.n_garde_inconnu_restants -= 1
                                    if self.n_garde_inconnu_restants == 0:
                                        m, n = self.plateau.infos_plateau()
                                        for i_prove in range(m):
                                            for j_prove in range(n):
                                                if not self.plateau.get_case(i_prove, j_prove).contenu_connu():
                                                    self.plateau.get_case(i_prove, j_prove).proven_not_guard = True

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
        if premiere_fois_etat:
            for case in vision:
                pos, contenu = case
                i, j = pos
                if not self.plateau.get_case(i, j).contenu_connu():
                    self.plateau.set_case(i, j, self._dict_cases[contenu])
                    if self._dict_cases[contenu][0] == "invite":
                        self.n_invite_inconnu_restants -= 1
                        self.plateau.get_case(i, j).proven_not_guard = True

                    elif self._dict_cases[contenu][0] == "garde":
                        self.n_garde_inconnu_restants -= 1
                        if self.n_garde_inconnu_restants == 0:
                            m, n = self.plateau.infos_plateau()
                            for i_prove in range(m):
                                for j_prove in range(n):
                                    if not self.plateau.get_case(i_prove, j_prove).contenu_connu():
                                        self.plateau.get_case(i_prove, j_prove).proven_not_guard = True

                    else:
                        self.plateau.get_case(i, j).proven_not_guard = True
                    
                    for pair in self.attente:
                        for direction in {"haut", "droite", "bas", "gauche"}:
                            if (i, j, ("garde", direction)) in pair:
                                if self._dict_cases[contenu] != ("garde", direction):
                                    other_item = pair[0] if pair[0] != (i, j, ("garde", direction)) else pair[1]
                                    self.plateau.set_case(other_item[0], other_item[1], other_item[2])
                                    self.n_garde_inconnu_restants -= 1
                                    if self.n_garde_inconnu_restants == 0:
                                        m, n = self.plateau.infos_plateau()
                                        for i_prove in range(m):
                                            for j_prove in range(n):
                                                if not self.plateau.get_case(i_prove, j_prove).contenu_connu():
                                                    self.plateau.get_case(i_prove, j_prove).proven_not_guard = True
                                self.attente.remove(pair)


                    ## clauses
                    if self._dict_cases[contenu][0] in {"invite", "garde"}:
                        self.clauses.append([self.plateau.cell_to_var(i, j, self._dict_cases[contenu][0])])
                    else:
                        self.clauses.append([-self.plateau.cell_to_var(i, j, "invite")])
                        self.clauses.append([-self.plateau.cell_to_var(i, j, "garde")])

        # ouie
        ## clauses
        if premier_passage:
            cases_entendues = self.plateau.cases_entendre(i_act, j_act) # toutes les cases qu'on peut entendre depuis la case actuelle
            cases_inconnues_entendues = []

            # pour alleger les clauses, si on connait le contenu d'une case et que ce n'est pas un invite/garde, on peut le retirer de la clause car on connait sont contenu
            # si on connait son contenu mais que c'est un invite/garde et qu'on est pas en brouhaha, on peut retirer la case de la clause et decrementer le nombre de personnes
            # entendues de 1
            for c in cases_entendues:
                if not self.plateau.get_case(c[0], c[1]).contenu_connu(): # case inconnue
                    cases_inconnues_entendues.append(c)
                elif hear < 5 and self.plateau.get_case(c[0], c[1]).contenu[0] in {"invite", "garde"}: # case connue et decompte de personne precis
                    hear -= 1
                elif hear == 5 and self.plateau.get_case(c[0], c[1]).contenu[0] in {"invite", "garde"}: # case connue mais decompte de personnes non precis
                    cases_inconnues_entendues.append(c)
                # else: # case connue et pas un invite/garde, on ne fait rien
                #    pass

            variables_invites_gardes = [self.plateau.cell_to_var(i, j, "invite") for i, j in cases_inconnues_entendues] + [self.plateau.cell_to_var(i, j, "garde") for i, j in cases_inconnues_entendues]

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
                elif penalite == penalite_min:
                    if self.plateau.distance_minimale(i, j, i2, j2) < self.plateau.distance_minimale(i, j, i_min, j_min):
                        i_min, j_min = i2, j2

        # on renvoie la premiere case qui n'a pas encore ete exploree
        if i_min is not None and j_min is not None:
            return i_min, j_min
            
        # si toutes les cases ont ete explorees, on renvoie False
        return False
    
    ##########################################
    ##########################################
    ######## Methodes pour la phase 2 ########
    ##########################################
    ##########################################
    
    def avancer(self, position: Tuple[int, int], direction: str)-> Tuple[int, int]:
        """
        Renvoit la position de la case devant la case (i, j) en regardant dans la direction
        La case peut ne pas exister
        """
        i, j = position
        return {"droite": (i+1, j), "gauche": (i-1, j), "haut": (i, j+1), "bas": (i, j-1)}[direction]

    def tourner_horaire(self, direction: str)-> str:
        """
        Renvoie la direction dans laquelle on regarde apres avoir tourne dans le sens des aiguilles d'une montre
        """
        if direction == "gauche":
            return "haut"
        elif direction == "haut":
            return "droite"
        elif direction == "droite":
            return "bas"
        elif direction == "bas":
            return "gauche"
        else:
            raise ValueError("La direction n'est pas bonne")

    def tourner_antihoraire(self, direction: str)-> str:
        """
        Renvoie la direction dans laquelle on regarde apres avoir tourne dans le sens inverse des aiguilles d'une montre
        """
        if direction == "gauche":
            return "bas"
        elif direction == "haut":
            return "gauche"
        elif direction == "droite":
            return "haut"
        elif direction == "bas":
            return "droite"
        else:
            raise ValueError("La direction n'est pas bonne")

    def seen_by_guards(self, i: int, j: int, empty: List[Tuple[int, int]] = [])-> int:
        """
        Renvoie le nombre de gardes qui peuvent nous voir depuis la case (i, j)
        empty est la liste des cases qui ont ete videes : invite/garde neutralise,
        objet ramasse
        """

        if not self.plateau.case_existe(i, j):
            raise ValueError("La case n'existe pas")
        
        # si on est sur un invite que l'on n'a pas supprime
        if self.plateau.get_case(i, j).contenu[0] == "invite" and not (i, j) in empty:
            return 0

        nb_garde_vu = 0

        # cases ou un garde peut voir (i, j) en regardant dans une direction
        # la direction est inversee : si un garde nous voit en regardant a gauche, il est sur une case a droite de nous
        vues_direction = {"bas": [(i, j+1), (i, j+2)],
                            "gauche": [(i+1, j), (i+2, j)],
                            "haut": [(i, j-1), (i, j-2)],
                            "droite": [(i-1, j), (i-2, j)]}
        
        for direction in vues_direction:
            case1, case2 = vues_direction[direction]
            if self.plateau.case_existe(case1[0], case1[1]):
                # si la case1 est vide, on regarde la case2
                if case1 in empty or self.plateau.get_case(case1[0], case1[1]).contenu[0] == "vide":
                    if self.plateau.case_existe(case2[0], case2[1]):
                        # On regarde si la case2 contient un garde qui regarde dans la direction et que la case est non vide
                        if self.plateau.get_case(case2[0], case2[1]).contenu[0] == "garde" and self.plateau.get_case(case2[0], case2[1]).contenu[1] == direction and not case2 in empty:
                            nb_garde_vu += 1
                # sinon on regarde si la case1 contient un garde qui regarde dans la direction
                elif self.plateau.get_case(case1[0], case1[1]).contenu[0] == "garde" and self.plateau.get_case(case1[0], case1[1]).contenu[1] == direction:
                    nb_garde_vu += 1
                
        return nb_garde_vu


    def seen_by_civil(self, i: int, j: int, empty: List[Tuple[int, int]] = [])-> int:
        """
        Renvoie le nombre de civils qui peuvent nous voir depuis la case (i, j)
        empty est la liste des cases qui ont ete videes : invite/garde neutralise,
        objet ramasse
        """

        if not self.plateau.case_existe(i, j):
            raise ValueError("La case n'existe pas")
        
        # si on est sur un invite que l'on n'a pas supprime
        if self.plateau.get_case(i, j).contenu[0] == "invite" and not (i, j) in empty:
            return 1 # l'invite sur lequel on n'est nous voit, c'est ce qui a ete defini dans hitman.py

        nb_invite_vu = 0

        # cases ou un garde peut voir (i, j) en regardant dans une direction
        vues_direction = {"bas": (i, j+1),
                            "gauche": (i+1, j),
                            "haut": (i, j-1),
                            "droite": (i-1, j)}
        
        for direction in vues_direction:
            case = vues_direction[direction]
            if self.plateau.case_existe(case[0], case[1]):
                # On regarde si la case est non vide, et contient un invite
                if self.plateau.get_case(case[0], case[1]).contenu[0] == "invite" and self.plateau.get_case(case[0], case[1]).contenu[1] == direction and not case in empty:
                    nb_invite_vu += 1
                
        return nb_invite_vu

    def do_fn(self, action: str, etat: namedtuple)-> namedtuple:
        """
        Cette methode est utilisee dans la phase de planification,
        Elle a pour objectif de simuler une action et de renvoyer le nouvel etat
        que l'on obtient apres avoir fait cette action a partir d'un etat donne
        """

        penalties_actuel = etat.penalties + 1 # +1 car cout de base d'une action
        new_etat = None
        opposite_direction = {"gauche": "droite", "droite": "gauche", "haut": "bas", "bas": "haut"}
        i = etat.position[0]
        j = etat.position[1]

        seen_by_guards = self.seen_by_guards(i, j, list(etat.ensemble_cases_videes))
        seen_by_civil = self.seen_by_civil(i, j, list(etat.ensemble_cases_videes))
        seen_by_total = seen_by_guards + seen_by_civil

        if action == "move":
            new_position = self.avancer(etat.position, etat.orientation)
            if self.plateau.case_existe(new_position[0], new_position[1]):
                # case non interdire (ni mur, ni garde), ou alors neutralise (garde neutralise) 
                if not self.plateau.get_case(new_position[0], new_position[1]).case_interdite() or (new_position[0], new_position[1]) in etat.ensemble_cases_videes:
                    new_etat = etat._replace(position=new_position)

        elif action == "turn_clockwise":
            new_orientation = self.tourner_horaire(etat.orientation)
            new_etat = etat._replace(orientation=new_orientation)

        elif action == "turn_anti_clockwise":
            new_orientation = self.tourner_antihoraire(etat.orientation)
            new_etat = etat._replace(orientation=new_orientation)

        elif action == "kill_target":
            contenu_sur_cette_case = self.plateau.get_case(etat.position[0], etat.position[1]).contenu[0]
            if etat.has_weapon and contenu_sur_cette_case == "cible":
                new_tuple_neutralisee = etat.ensemble_cases_videes + ((etat.position[0], etat.position[1]),)
                new_etat = etat._replace(is_target_down=True, ensemble_cases_videes=new_tuple_neutralisee)
                penalties_actuel += 100 * seen_by_total

        elif action == "neutralize_guard" or action == "neutralize_civil":
            if action == "neutralize_guard":
                type_cible = "garde"
            else:
                type_cible = "invite"

            # position et orientation actuelle
            i = etat.position[0]
            j = etat.position[1]
            orientation_actuelle = etat.orientation

            if orientation_actuelle == "gauche":
                case_devant = (i-1, j)
            elif orientation_actuelle == "droite":
                case_devant = (i+1, j)
            elif orientation_actuelle == "haut":
                case_devant = (i, j+1)
            elif orientation_actuelle == "bas":
                case_devant = (i, j-1)
            else:
                raise ValueError("Orientation incorrecte")
            
            # si la case existe
            if self.plateau.case_existe(case_devant[0], case_devant[1]):
                # si la case est un garde/invite non neutralise
                if self.plateau.get_case(case_devant[0], case_devant[1]).contenu[0] == type_cible and (case_devant[0], case_devant[1]) not in etat.ensemble_cases_videes:
                    # si le garde/invite ne nous voit pas : si son orientation ne correspond pas a l'oppose de la notre
                    if self.plateau.get_case(case_devant[0], case_devant[1]).contenu[1] != opposite_direction[orientation_actuelle]:
                        new_tuple_neutralisee = etat.ensemble_cases_videes + ((case_devant[0], case_devant[1]),)
                        new_etat = etat._replace(ensemble_cases_videes=new_tuple_neutralisee)

                        penalties_actuel += 20
                        penalties_actuel += 100 * seen_by_total

        elif action == "take_suit":
            contenu_sur_cette_case = self.plateau.get_case(etat.position[0], etat.position[1]).contenu[0]
            if not etat.has_suit and contenu_sur_cette_case == "costume":
                new_tuple_neutralisee = etat.ensemble_cases_videes + ((etat.position[0], etat.position[1]),)
                new_etat = etat._replace(has_suit=True, ensemble_cases_videes=new_tuple_neutralisee)

        elif action == "take_weapon" :
            contenu_sur_cette_case = self.plateau.get_case(etat.position[0], etat.position[1]).contenu[0]
            if not etat.has_weapon and contenu_sur_cette_case == "corde":
                new_tuple_neutralisee = etat.ensemble_cases_videes + ((etat.position[0], etat.position[1]),)
                new_etat = etat._replace(has_weapon=True, ensemble_cases_videes=new_tuple_neutralisee)

        elif action == "put_on_suit" :
            if etat.has_suit:
                new_etat = etat._replace(is_suit_on=True)
                penalties_actuel += 100 * seen_by_total

        if new_etat is None:
            return None
        
        # penalites des gardes si on n'a pas de costume
        # on n'utilise pas la variable seen_by_guards initialisee plus haut, on recalcule
        # avec la methode, car la position a pu changer (si on a "move")
        if not new_etat.is_suit_on:
            penalties_actuel += 5 * self.seen_by_guards(new_etat.position[0], new_etat.position[1], list(new_etat.ensemble_cases_videes))
        
        new_historique_actions = etat.historique_actions + (action,)
        etat_result = new_etat._replace(penalties=penalties_actuel, historique_actions=new_historique_actions)
        return etat_result


    def do_fn_for_real(self, nom_action: str):
        """
        Cette methode permet d'effectuer une action sur le plateau reellement
        lors de la phase 2. Elle n'est utilisee que lorsque l'on a trouve la liste
        complete des actions a effectuer.
        """
        position = self.status['position']

        # Faire une action reellement
        if nom_action == "turn_clockwise":
            self.status = self.hitman.turn_clockwise()

        elif nom_action == "turn_anti_clockwise":
            self.status = self.hitman.turn_anti_clockwise()

        elif nom_action == "move":
            self.status = self.hitman.move()

        elif nom_action == "kill_target":
            self.status = self.hitman.kill_target()
            # on indique au plateau que la cible est tuee pour l'affichage
            self.plateau.remove_case(position[0], position[1])

        elif nom_action == "neutralize_guard":
            i_guard, j_guard = self.status['vision'][0][0]
            self.status = self.hitman.neutralize_guard()
            # on indique au plateau que le garde est neutralise pour l'affichage
            self.plateau.remove_case(i_guard, j_guard)

        elif nom_action == "neutralize_civil":
            i_civil, j_civil = self.status['vision'][0][0]
            self.status = self.hitman.neutralize_civil()
            # on indique au plateau que l'invite est neutralise pour l'affichage
            self.plateau.remove_case(i_civil, j_civil)
            
        elif nom_action == "take_suit" :
            self.status = self.hitman.take_suit()
            # on indique au plateau que le costume est pris pour l'affichage
            self.plateau.remove_case(position[0], position[1])
            
        elif nom_action == "take_weapon" :
            self.status = self.hitman.take_weapon()
            # on indique au plateau que l'arme est prise pour l'affichage
            self.plateau.remove_case(position[0], position[1])

        elif nom_action == "put_on_suit":
            self.status = self.hitman.put_on_suit()
            # on indique au plateau que le costume est mis pour l'affichage
            self.plateau.put_suit()
            
        return None

    def succ(self, etat: namedtuple)-> List[namedtuple]:
        """
        Cette methode prend en parametre un etat, et retourne tous ses etats successeurs.

        Un etat est successeur a deux conditions :
            - Il correspond a l'etat dans lequel on se retrouverait en effectuant une seule action
            - Il n'est pas en conflit avec les regles du jeu (ex: tuer la cible sans arme, aller dans un mur, etc)
        """
        actions = [
            "turn_clockwise",
            "turn_anti_clockwise", 
            "move",
            "kill_target",
            "neutralize_guard", 
            "neutralize_civil", 
            "take_suit", 
            "take_weapon", 
            "put_on_suit", 
        ] 
        succ = []
        for action in actions:
            # on calcule pour chaque actions l'etat dans lequel on se retrouverait,
            # cet etat est "None" si il est en conflit avec les regles du jeu
            etat_apres_action = self.do_fn(action, etat)
            if etat_apres_action is not None:
                succ.append(etat_apres_action)
        return succ
    
    def test_if_goal_achived(self, etat, objectif: str)-> bool:
        """
        Teste si dans l'objectif a ete atteint pour l'etat donne
        """
        if objectif == "get_weapon":
            return etat.has_weapon == True
        elif objectif == "kill_target":
            return etat.is_target_down == True
        elif objectif == "return_home":
            return etat.position == (0, 0)
        elif objectif == "get_suit":
            return etat.has_suit == True
        else:
            raise ValueError("objectif invalide")
        
    
    def h_score(self, i: int, j: int, i_start: int, j_start: int, empty: List[Tuple[int, int]] = [], suit_on: bool = False)-> int:
        """
        Adaptation de penalite_minimale pour calcul de h_score pour A* dans la phase 2

        Les modifications sont notamment :
            - On ne compte pas les penalites de la case d'origine car deja comptee dans le g_score
            - On ne compte pas les penalites dues aux gardes si on a un costume
            - On tient compte du fait que certaines cases ont ete videes (invite/garde neutralise, objet ramasse)
            - On ne retourne que la valeur (car une seule case nous interesse, on retourne donc cette valeur), et pas un tableau de valeur (une par case)
            - Remplacement du risque et utilisation du nombre exact de gardes qui nous voient car en phase 2 l'information est complete
            - Possibilite de passer a travers un garde si on le tue (tenir compte du cout de cette action)
        """
        m, n = self.plateau.infos_plateau()
        cases_traitees = set()
        tas_cases_a_traiter = []

        penalites = [[float("inf") for _ in range(n)] for _ in range(m)]
        
        penalites[i][j] = 0 # nombre de gardes qui nous voient sur cette case deja compte dans le g_score
        cases_traitees.add((i, j))

        for i_voisin, j_voisin in self.plateau.voisins(i, j):
            malus_kill = 0
            if self.plateau.get_case(i_voisin, j_voisin).contenu[0] == "mur": # on ne peut pas passer par un mur
                continue
            elif self.plateau.get_case(i_voisin, j_voisin).contenu[0] == "garde" and not (i_voisin, j_voisin) in empty: # on peut passer par un garde encore present mais il faut le neutraliser
                malus_kill = 20
                malus_kill += 100 * (self.seen_by_guards(i, j, empty) + self.seen_by_civil(i, j, empty))
                
            if not suit_on:
                malus_seen = 5 * self.seen_by_guards(i_voisin, j_voisin, empty)
            else:
                malus_seen = 0
            penalite = malus_kill + penalites[i][j] + 1 + malus_seen
            heapq.heappush(tas_cases_a_traiter, (penalite, i_voisin, j_voisin))

        while not (i_start, j_start) in cases_traitees:
            penalite_act, i_act, j_act = heapq.heappop(tas_cases_a_traiter)
            if (i_act, j_act) in cases_traitees:
                continue
            cases_traitees.add((i_act, j_act))
            penalites[i_act][j_act] = penalite_act

            for i_voisin, j_voisin in self.plateau.voisins(i_act, j_act):
                malus_kill = 0
                if self.plateau.get_case(i_voisin, j_voisin).contenu[0] == "mur": # on ne peut pas passer par un mur
                    continue
                elif self.plateau.get_case(i_voisin, j_voisin).contenu[0] == "garde" and not (i_voisin, j_voisin) in empty: # on peut passer par un garde encore present mais il faut le neutraliser
                    malus_kill = 20
                    malus_kill += 100 * (self.seen_by_guards(i_act, j_act, empty) + self.seen_by_civil(i_act, j_act, empty))

                if not suit_on:
                    malus_seen = 5 * self.seen_by_guards(i_voisin, j_voisin, empty)
                else:
                    malus_seen = 0
                penalite = malus_kill + penalites[i_act][j_act] + 1 + malus_seen
                heapq.heappush(tas_cases_a_traiter, (penalite, i_voisin, j_voisin))

        return penalites[i_start][j_start]

    def calculer_heuristique_a_etoile(self, etat: namedtuple, pos_i: int, pos_j: int)-> int:
        """
        Calcul de l'heuristique pour A* dans la phase 2
        """
        g_score = etat.penalties
        h_score = self.h_score(pos_i, pos_j, etat.position[0], etat.position[1], list(etat.ensemble_cases_videes))
        f_score = g_score + h_score

        return f_score

    def transform_dict_to_namedtuple(self, dictionary: dict)-> namedtuple:
        """
        Cette methode permet d'initialiser le premier etat.
        Elle prend en parametre le dictionnaire "status", le transforme
        en enlevant certains champs dont on n'a pas besoin pour representer un etat,
        en ajoute d'autres dont on a besoin, et renvoie un namedtuple "Etat" qui
        represente le premier etat, et qui est base sur les champs que l'on a conserve.

        Les deux champs ajoutes sont :
            - ensemble_cases_videes : un ensemble de cases qui ont ete videes pour cet etat (invite/garde neutralise, objet ramasse)
            - historique_actions : une liste des actions effectuees pour arriver a cet etat
        """

        dictionary['ensemble_cases_videes'] = tuple()
        dictionary['historique_actions'] = tuple()

        fields = list(dictionary.keys())

        fiels_to_remove = ["civil_count", "guard_count", "hear", "is_in_guard_range", "is_in_civil_range", "m", "n", "phase", "status", "vision"]
        for field in fiels_to_remove:
            fields.remove(field)
            del dictionary[field]

        # Convertir "direction"
        if dictionary['orientation'] == HC.E:
            dictionary['orientation'] = "droite"
        elif dictionary['orientation'] == HC.N:
            dictionary['orientation'] = "haut"
        elif dictionary['orientation'] == HC.W:
            dictionary['orientation'] = "gauche"
        else: #if dictionary['orientation'] == HC.S:
            dictionary['orientation'] = "bas"

        # Creation d'un NamedTuple Class
        Etat = namedtuple('Etat', fields)

        # Creation d'une instance de namedtuple
        named_tuple_instance = Etat(**dictionary)

        return named_tuple_instance

    def locate_element(self, element: str)-> Tuple[int, int]:
        """
        Retourne les coordonnees de l'element donne en parametre
        """

        if element not in {"cible", "corde", "costume", "home"}:
            raise ValueError("Element invalide")
        
        if element == "home":
            return (0, 0)

        m, n = self.plateau.infos_plateau()
        for i in range(m):
            for j in range(n):
                if self.plateau.get_case(i, j).contenu[0] == element:
                    return (i, j)
                
        return None

    def search_with_parent(self, etat_init: namedtuple, objectif: str)-> namedtuple:
        """
        Cette methode est celle qui effectue le travail de recherche a proprement parler pour la phase 2.

        Elle prend en parametre un etat initial, et un objectif, et renvoie un etat remplissant
        l'objectif qu'elle a reussi a atteindre en effectuant une serie d'actions.

        Inutile de chercher a stocker ces actions etant donne que chaque etat possede un 
        historique d'actions effectuees pour arriver a cet etat. On stocke en revanche
        Un historique des etats visites (aux penalites et historique d'actions pres).
        Cela permet de ne pas revisiter un etat deja visite, et donc de ne pas boucler.
        A* permet de toute facon de ne pas boucler indefiniment, mais stocker l'historique
        permet de gagner du temps.

        L'objectif peut etre :
            - "get_weapon" : chercher la corde
            - "kill_target" : tuer la cible
            - "return_home" : retourner en (0, 0)
        """

        if etat_init == None:
            raise ValueError("Le jeu n'a pas ete initialise")
        
        etat_actuel = etat_init

        history = set(etat_actuel._replace(historique_actions=None, penalties=None))

        objectif_dict = {"get_weapon": "corde", "kill_target": "cible", "return_home": "home", "get_suit": "costume"}
        coords_objectif = self.locate_element(objectif_dict[objectif])

        successeurs = []

        while not self.test_if_goal_achived(etat_actuel, objectif):
            for etat_suivant in self.succ(etat_actuel):
                if etat_suivant._replace(historique_actions=None, penalties=None) in history:
                    continue
                heuristique = self.calculer_heuristique_a_etoile(etat_suivant, coords_objectif[0], coords_objectif[1])
                heapq.heappush(successeurs, (heuristique, etat_suivant))

            _, etat_actuel = heapq.heappop(successeurs) # Recupere l'etat avec le cout le plus faible
            history.add(etat_actuel._replace(historique_actions=None, penalties=None))
            
        return etat_actuel
    

    def phase_2(self, temporisation: bool = True, costume_combinations: bool = False, display: bool = True)-> int: 
        """
        La phase 2 est decoupee en 3 objectifs:
            I.   Chercher la corde
            II.  Tuer la cible
            III. Retourner en (0, 0)

        Par defaut, on cherche juste a atteindre ces objectifs dans l'ordre. Cela a cependant un
        defaut : le costume ne sera que pris si il est rentable pour la phase en cours, sauf qu'il
        est possible que prendre le costume soit penalisant dans l'immediat, mais rentable a long terme,
        dans les phases suivantes. Avec le parametre "costume_combinations", on compare les scores
        entre :
            - Ne pas specialement chercher a prendre le costume
            - Chercher a prendre le costume avant la corde
            - Chercher a prendre le costume avant la cible
            - Chercher a prendre le costume avant de retourner en (0, 0)

        On choisit la meilleure combinaison de ces 4 possibilites. Cette methode offrira un score soit egal
        soit superieur a la methode par defaut, mais elle est bien plus longue a executer.
        """
        self._temporisation = temporisation
        self._display = display

        print("\nLa phase 2 commence !")

        self.status = self.hitman.start_phase2()
        self.update_hitman()

        # Etapes sans forcer la prise du costume
        etat_s0 = self.transform_dict_to_namedtuple(self.status)
        etat_s1 = self.search_with_parent(etat_s0, "get_weapon") # Chercher la corde
        etat_s2 = self.search_with_parent(etat_s1, "kill_target") # Tuer le cible
        etat_final = self.search_with_parent(etat_s2, "return_home") # Retourner en (0, 0)

        if costume_combinations:
            # Etapes en forcant la prise du costume apres avoir tue la cible, on peut partir de s2 car le debut est le meme
            etat_s3 = self.search_with_parent(etat_s2, "get_suit") # Chercher le costume
            etat_final_bis = self.search_with_parent(etat_s3, "return_home") # Retourner en (0, 0)

            if etat_final_bis.penalties < etat_final.penalties:
                etat_final = etat_final_bis

            # Etapes en forcant la prise du costume apres avoir pris la corde, on peut partir de s1 car le debut est le meme
            etat_s2 = self.search_with_parent(etat_s1, "get_suit") # Chercher le costume
            etat_s3 = self.search_with_parent(etat_s2, "kill_target") # Tuer le cible
            etat_final_bis = self.search_with_parent(etat_s3, "return_home") # Retourner en (0, 0)

            if etat_final_bis.penalties < etat_final.penalties:
                etat_final = etat_final_bis

            # Etapes en forcant la prise du costume au tout debut
            etat_s1 = self.search_with_parent(etat_s0, "get_suit") # Chercher le costume
            etat_s2 = self.search_with_parent(etat_s1, "get_weapon") # Chercher la corde
            etat_s3 = self.search_with_parent(etat_s2, "kill_target") # Tuer le cible
            etat_final_bis = self.search_with_parent(etat_s3, "return_home") # Retourner en (0, 0)

            if etat_final_bis.penalties < etat_final.penalties:
                etat_final = etat_final_bis

        self.afficher_plateau()
        for action in etat_final.historique_actions:
            self.do_fn_for_real(action)
            self.update_hitman()
            self.afficher_plateau()
            if self._temporisation:
                sleep(0.25)

        _, score, _ = self.hitman.end_phase2()

        print("Result phase 2 :")
        print(score, "\n\n")
        
        penalites = -etat_final.penalties

        return penalites
        