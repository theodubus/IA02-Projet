from re import search
from utils.hitman import HC
from collections import namedtuple
from queue import PriorityQueue
from time import sleep
from typing import Tuple, List
import heapq

from game import Game
# ===================== Code pour la phase 2: ==========================================

class Game2(Game):

    def __init__(self):
        Game.__init__(self)

    def avancer(self, position, direction):
        i, j = position
        return {"droite": (i+1, j), "gauche": (i-1, j), "haut": (i, j+1), "bas": (i, j-1)}[direction]

    def tourner_horaire(self, direction):
        if direction == "gauche":
            return "haut"
        elif direction == "haut":
            return "droite"
        elif direction == "droite":
            return "bas"
        elif direction == "bas":
            return "gauche"

    def tourner_antihoraire(self, direction):
        if direction == "gauche":
            return "bas"
        elif direction == "haut":
            return "gauche"
        elif direction == "droite":
            return "haut"
        elif direction == "bas":
            return "droite"

    def seen_by_guards(self, i: int, j: int, empty: List[Tuple[int, int]] = [])-> int:
        """
        Renvoie le nombre de gardes qui peuvent nous voir depuis la case (i, j)
        empty est la liste des cases qui ont ete videes (inite/garde) neutralise,
        objet ramasse
        """

        if not self.plateau.case_existe(i, j):
            raise ValueError("La case n'existe pas")
        
        # si on est sur un invite que l'on n'a pas supprime
        if self.plateau.get_case(i, j).contenu[0] == "invite" and not (i, j) in empty:
            return 0

        nb_garde_vu = 0

        # cases ou un garde peut voir (i, j) en regardant dans une direction
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
        empty est la liste des cases qui ont ete videes (inite/garde) neutralise,
        objet ramasse
        """

        if not self.plateau.case_existe(i, j):
            raise ValueError("La case n'existe pas")
        
        # si on est sur un invite que l'on n'a pas supprime
        if self.plateau.get_case(i, j).contenu[0] == "invite" and not (i, j) in empty:
            return 1

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

    def do_fn(self, action, etat):
        # "Simuler" une action, utilisee dans la phase de planification

        penalties_actuel = etat.penalties + 1 # +1 car cout de base d'une action
        new_etat = None
        opposite_direction = {"gauche": "droite", "droite": "gauche", "haut": "bas", "bas": "haut"}
        i = etat.position[0]
        j = etat.position[1]

        # On calcule le nombre de guards et de civils qui nous voient, cela permet de rendre le code plus clair
        # On peut calculer ce nombre avant de faire l'action car on s'en servira que si on ne change pas de case
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
                new_etat = etat._replace(is_target_down=True)
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
                # si la case est un garde non neutralise
                if self.plateau.get_case(case_devant[0], case_devant[1]).contenu[0] == type_cible and (case_devant[0], case_devant[1]) not in etat.ensemble_cases_videes:
                    # si le garde ne nous voit pas
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
        
        # update penalites
        if not new_etat.is_suit_on:
            penalties_actuel += 5 * self.seen_by_guards(new_etat.position[0], new_etat.position[1], list(new_etat.ensemble_cases_videes))
        
        new_historique_actions = etat.historique_actions + (action,)
        etat_result = new_etat._replace(penalties=penalties_actuel, historique_actions=new_historique_actions)
        return etat_result


    def do_fn_for_real(self, nom_action):
        position = self.status['position']
        orientation = self.status['orientation']

        # Faire une action reellement
        if nom_action == "turn_clockwise":
            self.status = self.hitman.turn_clockwise()
        elif nom_action == "turn_anti_clockwise":
            self.status = self.hitman.turn_anti_clockwise()
        elif nom_action == "move":
            self.status = self.hitman.move()
        elif nom_action == "kill_target":
            self.status = self.hitman.kill_target()
            self.plateau.remove_case(position[0], position[1])
        elif nom_action == "neutralize_guard":
            i_guard, j_guard = self.status['vision'][0][0]
            self.status = self.hitman.neutralize_guard()
            self.plateau.remove_case(i_guard, j_guard)
        elif nom_action == "neutralize_civil":
            i_civil, j_civil = self.status['vision'][0][0]
            self.status = self.hitman.neutralize_civil()
            self.plateau.remove_case(i_civil, j_civil)
        elif nom_action == "take_suit" :
            self.status = self.hitman.take_suit()
            self.plateau.remove_case(position[0], position[1])
        elif nom_action == "take_weapon" :
            self.status = self.hitman.take_weapon()
            self.plateau.remove_case(position[0], position[1])
        elif nom_action == "put_on_suit":
            self.status = self.hitman.put_on_suit()
        return None

    def succ(self, etat):
        # Traiter l'etat en cours et retourne l'etat suivant:
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
            etat_apres_action = self.do_fn(action, etat)
            if etat_apres_action is not None:
                succ.append(etat_apres_action)
        return succ
    
    def testIfGoalAchived(self, etat, objectif):
        if objectif == "get_weapon":
            return etat.has_weapon == True
        elif objectif == "kill_target":
            return etat.is_target_down == True
        elif objectif == "return_home":
            return etat.position == (0, 0)
        else:
            raise ValueError("objectif invalide")
        
    
    def h_score(self, i: int, j: int, i_start: int, j_start: int, empty: List[Tuple[int, int]] = [])-> int:
        """
        Adaptation de penalite_minimale pour calcul de h_score pour A* dans la phase 2
        """
        m, n = self.plateau.infos_plateau()
        cases_traitees = set()
        tas_cases_a_traiter = []

        penalites = [[float("inf") for _ in range(n)] for _ in range(m)]
        
        penalites[i][j] = 5 * self.seen_by_guards(i, j, empty)
        cases_traitees.add((i, j))

        for i_voisin, j_voisin in self.plateau.voisins(i, j):
            if self.plateau.get_case(i_voisin, j_voisin).case_interdite() and not (i_voisin, j_voisin) in empty:
                continue
            penalite = penalites[i][j] + 1 + 5 * self.seen_by_guards(i_voisin, j_voisin, empty)
            heapq.heappush(tas_cases_a_traiter, (penalite, i_voisin, j_voisin))

        while not (i_start, j_start) in cases_traitees:
            penalite_act, i_act, j_act = heapq.heappop(tas_cases_a_traiter)
            if (i_act, j_act) in cases_traitees:
                continue
            cases_traitees.add((i_act, j_act))
            penalites[i_act][j_act] = penalite_act

            for i_voisin, j_voisin in self.plateau.voisins(i_act, j_act):
                if self.plateau.get_case(i_voisin, j_voisin).case_interdite() and not (i_voisin, j_voisin) in empty:
                    continue
                penalite = penalites[i_act][j_act] + 1 + 5 * self.seen_by_guards(i_voisin, j_voisin, empty)
                heapq.heappush(tas_cases_a_traiter, (penalite, i_voisin, j_voisin))

        return penalites[i_start][j_start]

    def calculer_heuristique_a_etoile(self, etat, pos_i, pos_j):
        # calculer g_score et h_score
        # g_score: penalites pour arriver a cet etat
        # h_score: heuristique des penalites restantes

        # TODO :
        # 2 modes:
        ## mode "g_score only"
        ## mode "h_score penalties_min"

        g_score = etat.penalties
        h_score = self.h_score(pos_i, pos_j, etat.position[0], etat.position[1], list(etat.ensemble_cases_videes))
        #  self.plateau.distance_manhattan(etat.position[0], etat.position[1], pos_i, pos_j)
        f_score = g_score + h_score

        return f_score

    def transform_dict_to_namedtuple(self, dictionary):
        # Creer une liste contenant la position des cases sur lesquelles se trouvent des guards / civils neutralisees, ainsi que les objets ramasses
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
    

    def locate_element(self, element):
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

    def search_with_parent(self, etat_init, objectif):
        # objectif: "get_weapon" ou "kill_target" ou "return_home"
        # search_mode: "a_etoile" ou "phase_2_heuristic"

        if etat_init == None:
            raise ValueError("Le jeu n'a pas ete initialise")
        
        etat_actuel = etat_init

        history = set(etat_actuel._replace(historique_actions=None, penalties=None))

        objectif_dict = {"get_weapon": "corde", "kill_target": "cible", "return_home": "home"}
        coords_objectif = self.locate_element(objectif_dict[objectif])

        successeurs = []

        while not self.testIfGoalAchived(etat_actuel, objectif):
            for etat_suivant in self.succ(etat_actuel):
                if etat_suivant._replace(historique_actions=None, penalties=None) in history:
                    continue
                heuristique = self.calculer_heuristique_a_etoile(etat_suivant, coords_objectif[0], coords_objectif[1])
                heapq.heappush(successeurs, (heuristique, etat_suivant))

            _, etat_actuel = heapq.heappop(successeurs)#[1] # Recupere l'etat avec le cout le plus faible
            history.add(etat_actuel._replace(historique_actions=None, penalties=None))
            
        return etat_actuel


    def dict2path(self, etat, dic):
        liste = [(etat, None)]  # Liste representant l'etat initial
        while dic[etat] is not None:
            # Tant que le predecesseur de l'etat actuel n'est pas None dans le dictionnaire
            parent, action = dic[etat]  # Recupere le predecesseur et l'action menant e l'etat actuel
            liste.append((parent, action))  
            etat = parent  # Met e jour l'etat actuel avec le predecesseur pour continuer la remontee
        liste.reverse()  # Inverse l'ordre des elements de la liste pour obtenir le chemin complet du debut e l'etat
        return liste  # Renvoie la liste representant le chemin complet


    def phase_2(self, temporisation_phase2):
        """
        Dans cette phase, il y a 3 objectifs principaux:
            I.   Chercher la corde
            II.  Tuer la cible
            III. Retourner en (0, 0)

        Un objectif secondaire est de prendre le costume (si cela est benefique).
        On compare donc plusieurs séries d'actions :
        - Parcours avec prise de costume avant I
        - Parcours avec prise de costume entre I et II
        - Parcours avec prise de costume entre II et III
        - Parcours sans prise de costume
        """

        print("La phase 2 a commence !")
        print("Veuillez patienter, Hitman est en train de reflechir ...")

        self.status = self.hitman.start_phase2()
        self.update_hitman()

        etat_s0 = self.transform_dict_to_namedtuple(self.status)

        # Chercher la corde
        etat_s1 = self.search_with_parent(etat_s0, "get_weapon")
        print("Hitman a trouve un arme !")

        # Tuer le cible
        etat_s2 = self.search_with_parent(etat_s1, "kill_target")
        print("Hitman a trouve un chemin pour aller au cible !")

        # Retourner en (0, 0)
        etat_final = self.search_with_parent(etat_s2, "return_home")
        print("Hitman a trouve un chemin pour retourner !")

        print("Liste de ses actions:")
        print(etat_final.historique_actions)


        print(self.plateau)
        for action in etat_final.historique_actions:
            self.do_fn_for_real(action)
            self.update_hitman()
            print(self.plateau)
            if temporisation_phase2:
                sleep(0.25)

        isDone, message, historique = self.hitman.end_phase2()
        print("Le jeu est termine? ", isDone)
        print("Message: ", message)
        print("Historique des actions:", historique)


if __name__ == "__main__":
    # Pour que ces lignes de code ne soient pas executer dans un autre fichier
    g = Game2()
    g.phase_1(temporisation=False, sat_mode="no_sat")
    g.phase_2(temporisation_phase2=True)