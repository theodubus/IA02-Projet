from utils.clauses_combin import *
from utils.case import Case
from utils.plateau import Plateau
from utils.hitman import HC, HitmanReferee, complete_map_example
from pprint import pprint
from gophersat.dimacs import solve
import time
import heapq


class Game:
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
        self.dict_cases = {
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
        self.dict_directions = {
            HC.N : "haut",
            HC.E : "droite",
            HC.S : "bas",
            HC.W : "gauche"
        }


    def pos_actuelle(self):
        """
        Renvoit la position actuelle du hitman
        """
        if self.status is None:
            raise ValueError("Le jeu n'a pas ete initialise")

        return self.status['position']
    
    def direction_actuelle(self):
        """
        Renvoit la direction actuelle du hitman
        """
        if self.status is None:
            raise ValueError("Le jeu n'a pas ete initialise")

        return self.dict_directions[self.status['orientation']]
            

    def phase_1(self, temporisation=True, no_sat=False):
        """
        méthode encore en construction

        pour le moment il n'y a que les clauses des n gardes et m invites à l'entree du jeu
        il reste l'exploration du jeu a faire, ainsi que la mise a jour du plateau avec plateau.set_case()
        et l'ajout de clauses au fur et a mesure
        """

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
        self.clauses.append([-self.plateau.cell_to_var(i_act, j_act, "garde")])
        print(self.plateau)


        while self.prochain_objectif():
            i, j = self.prochain_objectif()
            self.explore(i, j)

        if self.hitman.send_content(self.plateau.board_to_map()):
            print(f"Gagné ! trouve avec {self.status['penalties']} penalites")
        else:
            print("Perdu !")



    def explore(self, i_objectif, j_objectif):
        """
        fonction d'exploration qui a pour but d'effectuer une serie d'actions pour determiner
        le contenu de la case (i_objectif, j_objectif).

        Pour se faire, on fait dans un premier temps la liste des cases depuis lesquelles on peut (a priori)
        voir la case (i_objectif, j_objectif). Cette liste n'est pas absolue car il peut par exemple y avoir
        un mur entre la case (i, j) et la case (i_objectif, j_objectif) mais on ne le sait pas encore.

        Une fois la liste obtenue, on effectue les actions suivantes :
            - Tant qu'on est pas sur une case depuis laquelle on peut voir la case (i_objectif, j_objectif) :
                - Calculer la distance entre chacune de nos cases voisines et la cases pour laquelle on peut voir la plus proche
                - Se deplacer sur la case voisine la plus proche
                - (Mettre a jour notre connaissance du plateau et l'afficher)
            - Si la case objectif est visible, on a termine
            - Sinon, on retire la case actuelle de la liste des cases depuis lesquelles on peut voir la case objectif et on reprend la boucle
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
            while (i_act, j_act) not in targets and not self.plateau.get_case(i_objectif, j_objectif).contenu_connu():
                voisin_min = self.prochaine_case(i_act, j_act, targets)
                
                if voisin_min is None:
                    raise ValueError("Aucun voisin n'est accessible")
                
                # A ce stade, soit on tourne 1 fois ou 2 pour se retrouver dans la bonne direction et voir si la case est visitable
                # soit on est directement devant, et on avance
                reflexe_survie = self.tourner(voisin_min[0], voisin_min[1])

                if self.plateau.get_case(i_objectif, j_objectif).contenu_connu():
                    break

                if not self.plateau.get_case(voisin_min[0], voisin_min[1]).case_interdite() and not reflexe_survie:
                    self.status = self.hitman.move()
                    self.update_knowledge()
                    print(self.plateau)

                i_act, j_act = self.pos_actuelle()

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
                    targets += self.plateau.cases_voir(i_objectif, j_objectif, direction)

        if targets == []:
            raise ValueError(f"La case ({i_objectif}, {j_objectif}) n'est pas accessible")
        
    def prochaine_case(self, i_act, j_act, targets, voisins_actuels=None):
        """
        Détermine la prochaine case à explorer pour aller de (i_act, j_act) à (i_objectif, j_objectif)
        """
        if voisins_actuels is None:
            voisins_actuels = [v for v in self.plateau.voisins(i_act, j_act) if not self.plateau.get_case(v[0], v[1]).case_interdite()]
        dist_min = float("inf")
        voisin_min = None

        # voisin le plus proche
        for i_target, j_target in targets:
            penalite_min = self.penalite_minimale(i_target, j_target, sat_coordinates=voisins_actuels)
            for i_voisin, j_voisin in voisins_actuels:
                dist = penalite_min[i_voisin][j_voisin]
                
                if dist < dist_min:
                    dist_min = dist
                    voisin_min = (i_voisin, j_voisin)

        return voisin_min
    
    def penalite_minimale(self, i, j, sat_coordinates=()):
        """
        Renvoie la penalite minimale pour atteindre la case (i, j)
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

        
    def risque(self, i, j, use_sat=False):
        """
        Determine le risque d'aller sur une case,
        le resulat est un tuple du nombre minimum et maximum de gardes par lesquels ont peut etre vus
        en passant par la case (i, j). On peut etre vu dans quatre directions differentes, donc
        le nombre de gardes peut varier entre 0 et 4. (si deux gardes regardent dans la meme direction
        et sont a cote, le premier bloque la vue du second)
        """

        if not self.plateau.case_existe(i, j):
            raise ValueError("La case n'existe pas")
        
        if self.plateau.get_case(i, j).contenu[0] == "invite":
            return 0
        
        if self.no_sat:
            use_sat = False
        
        if self.penalites[i][j] is not False:
            m = self.penalites[i][j]
            # return (1 + m)**2 + (m)
            return (4 * m) + m

        gardes_potentiels = self.plateau.voisins_gardes(i, j)
        visible_depuis = {"gauche": [0, 0], "droite": [0, 0], "haut": [0, 0], "bas": [0, 0]}

        for direction in ['gauche', 'droite', 'haut', 'bas']:
            voisins_direction = gardes_potentiels[direction]
            for i_garde, j_garde in voisins_direction:

                # cas "on est sur" qu'un garde nous voit
                if self.plateau.get_case(i_garde, j_garde).contenu[0] == "garde" and self.plateau.get_case(i_garde, j_garde).contenu[1] == direction:
                    visible_depuis[direction][0] = 1
                    visible_depuis[direction][1] = 1
                    break

                # cas "il est possible" qu'un garde nous voit
                if not self.plateau.get_case(i_garde, j_garde).proven_not_guard:
                    if self.plateau.get_case(i_garde, j_garde).contenu[0] == "inconnu":
                        if use_sat:
                            clauses_temp = self.clauses.copy()
                            self.clauses.append([self.plateau.cell_to_var(i_garde, j_garde, "garde")])
                            if self.satisfiable():
                                visible_depuis[direction][1] = 1
                            else:
                                self.plateau.get_case(i_garde, j_garde).proven_not_guard = True
                            self.clauses = clauses_temp.copy()
                        else:
                            visible_depuis[direction][1] = 1

        min = sum([visible_depuis[direction][0] for direction in visible_depuis])
        max = sum([visible_depuis[direction][1] for direction in visible_depuis])

        if self.plateau.get_case(i, j).contenu[0] == "inconnu": # si la case est un invite, on ne sera pas vu
            min = 0

        # return (1 + min)**2 + (max)
        return (4 * min) + max


    def update_hitman(self):
        """
        Met a jour la position et direction de hitman sur la carte
        """
        i_act, j_act = self.pos_actuelle()
        direction_act = self.direction_actuelle()

        self.plateau.pos_hitman = (i_act, j_act, direction_act)

    def tourner(self, i_objectif, j_objectif):
        """
        Tourne jusqu'a ce que la case (i_objectif, j_objectif) soit visible
        Si la case est deja en face, ne fait rien
        """

        if not self.plateau.case_existe(i_objectif, j_objectif):
            raise ValueError("La case n'existe pas")

        i_act, j_act = self.pos_actuelle()
        if len(self.status['vision']) > 0:
            case_devant = self.status['vision'][0][0]
            if not self.plateau.get_case(case_devant[0], case_devant[1]).case_interdite():
                if self.penalites[i_act][j_act] > 0:
                    autres_pdv = []
                    directions = ("haut", "droite", "bas", "gauche")
                    for direction in directions:
                        autres_pdv += self.plateau.cases_voir(i_objectif, j_objectif, direction)
                    
                    if self.risque(case_devant[0], case_devant[1], use_sat=True) < self.risque(i_act, j_act, use_sat=True):
                        for i, j in autres_pdv:
                            if self.penalites[i][j] == 0 or self.penalites[i][j] is False:
                                self.status = self.hitman.move()
                                self.update_knowledge()
                                print(self.plateau)
                                return True

        directions = ("haut", "droite", "bas", "gauche")
        if self.plateau.distance_manhattan(i_act, j_act, i_objectif, j_objectif) > 3:
            raise ValueError("La case est trop loin")

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

        if index == (index_act + 1) % 4:
            self.status = self.hitman.turn_clockwise()
            self.update_knowledge()
            print(self.plateau)
        elif index == (index_act + 3) % 4:
            self.status = self.hitman.turn_anti_clockwise()
            self.update_knowledge()
            print(self.plateau)
        elif index == (index_act + 2) % 4:
            # On tourne 2 fois, on regarde dans quel sens
            # il sera le plus informatif de tourner
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
        

    def satisfiable(self):
        """
        Renvoie True si les clauses sont satisfiables, False sinon
        """
        solve(self.clauses, nb_var=self.nb_variables)

    def update_knowledge(self):
        """
        Met a jour le plateau et la base de clauses avec les informations obtenues

        Pour la vue, on met a jour notre modele de plateau et on ajoute des clauses.
        
        Pour l'ecoute, on ajoute simplement des clauses. Il y a "hear" cases qui contiennent
        un garde ou un invite le fait qu'un garde et un invite ne soient pas
        sur la meme case est deja pris en compte dans les clauses d'initialisation

        On met egalement a jour la position et la direction de hitman sur la carte
        """

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
                                case1, case2 = voisins_gardes_dict[direction]
                                self.attente.append(((case1[0], case1[1], ("garde", direction)), (case2[0], case2[1], ("garde", direction))))



        self.old_penalty = self.status['penalties']    

        # vision
        ## plateau
        for case in vision:
            pos, contenu = case
            i, j = pos
            if not self.plateau.get_case(i, j).contenu_connu():
                self.plateau.set_case(i, j, self.dict_cases[contenu])
                
                for pair in self.attente:
                    for direction in {"haut", "droite", "bas", "gauche"}:
                        if (i, j, ("garde", direction)) in pair:
                            if self.dict_cases[contenu] != ("garde", direction):
                                other_item = pair[0] if pair[0] != (i, j, ("garde", direction)) else pair[1]
                                self.plateau.set_case(other_item[0], other_item[1], other_item[2])
                            self.attente.remove(pair)


                ## clauses
                if self.dict_cases[contenu][0] in {"invite", "garde"}:
                    self.clauses.append([self.plateau.cell_to_var(i, j, self.dict_cases[contenu][0])])
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
        Renvoie les coordonnees de la prochaine case a explorer, c'est a dire la case la plus proche
        qui n'a pas encore ete exploree
        """
        if self.plateau is None:
            raise ValueError("Le jeu n'a pas ete initialise")
        
        # on recupere les coordonnees de la case actuelle et les dimensions du plateau
        i, j = self.pos_actuelle()
        m, n = self.plateau.infos_plateau()

        penalites_min = self.penalite_minimale(i, j)

        # on recupere les cases candidates
        cases_candidates = []
        for i2 in range(m):
            for j2 in range(n):
                if i2 == i and j2 == j:
                    continue
                if self.plateau.get_case(i2, j2).contenu_connu():
                    continue
                # distance = self.plateau.distance_minimale(i, j, i2, j2)#completer
                distance = penalites_min[i2][j2]
                cases_candidates.append((i2, j2, distance))
        
        # on trie les cases candidates par distance
        cases_candidates.sort(key=lambda x: x[2])

        # on renvoie la premiere case qui n'a pas encore ete exploree
        if cases_candidates != []:
            return cases_candidates[0][0], cases_candidates[0][1]
            
        # si toutes les cases ont ete explorees, on renvoie False
        return False




g = Game()

g.phase_1(no_sat=True, temporisation=True)

