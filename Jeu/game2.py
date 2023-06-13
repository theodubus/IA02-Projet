from re import search
from utils.hitman import HC
from collections import namedtuple
from queue import PriorityQueue
from time import sleep
from typing import Tuple, List

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
        #Renvoie le nombre de gardes qui peuvent nous voir depuis la case (i, j)
        #empty est la liste des cases qui ont été vidées (inite/garde) neutralise,
        #objet ramasse

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
        #Renvoie le nombre de civils qui peuvent nous voir depuis la case (i, j)
        #empty est la liste des cases qui ont été vidées (inite/garde) neutralise,
        #objet ramasse

        if not self.plateau.case_existe(i, j):
            raise ValueError("La case n'existe pas")
    
        # si on est sur un invite que l'on n'a pas supprime
        if self.plateau.get_case(i, j).contenu[0] == "invite" and not (i, j) in empty:
            return 0

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
        # "Simuler" une action, utilisée dans la phase de planification

        penalties_actuel = etat.penalties + 1 # +1 car cout de base d'une action
        new_etat = None

        if action == "move":
            new_position = self.avancer(etat.position, etat.orientation)
            if self.plateau.case_existe(new_position[0], new_position[1]):
                new_contenu_sur_case = self.plateau.get_case(new_position[0], new_position[1]).contenu[0]
                # pour savoir le contenu de cette cas, genre "guard" ou "mur" etc.
                if (new_contenu_sur_case!= "garde" or (new_position[0], new_position[1]) in etat.ensemble_neutralise) and new_contenu_sur_case!= "mur":
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
                    
                penalties_actuel += 100 * (self.seen_by_guards(new_etat.position[0], new_etat.position[1], list(new_etat.ensemble_neutralise)) \
                                            + self.seen_by_civil(new_etat.position[0], new_etat.position[1], list(new_etat.ensemble_neutralise)))
                # seen_by_guards retourne le nombre exact de gardes par lesquels on est vu pour chaque case
                # si c'est == 0 alors on subit pas de penalites supplémentaires
                # dans le cas contraire, c'est égal à 100 * (nb de guards + civils qui voit le hitman)

        elif action == "neutralize_guard":
            # obtenir le contenu des cases adjacentes
            i = etat.position[0]
            j = etat.position[1]
            #candidates = [(i-1, j), (i+1, j), (i, j-1), (i, j+1), (i-1, j-1), (i+1, j+1), (i-1, j+1), (i+1, j-1)]
            candidates = [(i-1, j), (i+1, j), (i, j-1), (i, j+1)]
            adjacentes = [c for c in candidates if self.plateau.case_existe(c[0], c[1])]

            contenu_sur_cases_adjacentes = {}
            for position in adjacentes:
                contenu_sur_cases_adjacentes[(position[0], position[1])] = self.plateau.get_case(position[0], position[1]).contenu[0]
                
            # coordinate_garde est la position de garde
            for coordinate_garde, contenu in contenu_sur_cases_adjacentes.items():
                if contenu == "garde" and (coordinate_garde[0], coordinate_garde[1]) not in etat.ensemble_neutralise:
                    nb_guard = etat.guard_count
                    transition_etat = etat._replace(guard_count=nb_guard-1) #transition_etat : maj guard_count
                    #maj ensemble_neutralise:
                    new_tuple_neutralisee = transition_etat.ensemble_neutralise + ((coordinate_garde[0], coordinate_garde[1]),)
                    new_etat = transition_etat._replace(ensemble_neutralise=new_tuple_neutralisee)

                    penalties_actuel += 20 # 20 car on vient de neutraliser une personne
                    penalties_actuel += 100 * (self.seen_by_guards(new_etat.position[0], new_etat.position[1], list(new_etat.ensemble_neutralise)) \
                                                + self.seen_by_civil(new_etat.position[0], new_etat.position[1], list(new_etat.ensemble_neutralise)))
                    # seen_by_guards retourne le nombre exact de gardes par lesquels on est vu pour chaque case
                    # si c'est == 0 alors on subit pas de penalites supplémentaires
                    # dans le cas contraire, c'est égal à 100 * (nb de guards + civils qui voit le hitman)


        elif action == "neutralize_civil":
            # obtenir le contenu des cases adjacentes
            i = etat.position[0]
            j = etat.position[1]
            #candidates = [(i-1, j), (i+1, j), (i, j-1), (i, j+1), (i-1, j-1), (i+1, j+1), (i-1, j+1), (i+1, j-1)]
            candidates = [(i-1, j), (i+1, j), (i, j-1), (i, j+1)]
            adjacentes = [c for c in candidates if self.plateau.case_existe(c[0], c[1])]

            contenu_sur_cases_adjacentes = {}
            for position in adjacentes:
                contenu_sur_cases_adjacentes[(position[0], position[1])] = self.plateau.get_case(position[0], position[1]).contenu[0]

            for coordinate_civil, contenu in contenu_sur_cases_adjacentes.items():
                if contenu == "invite" and (coordinate_civil[0], coordinate_civil[1]) not in etat.ensemble_neutralise:
                    nb_civil = etat.civil_count
                    transition_etat = etat._replace(civil_count=nb_civil-1) #transition_etat : maj civil_count
                    #maj ensemble_neutralise:
                    new_tuple_neutralisee = transition_etat.ensemble_neutralise + ((coordinate_civil[0], coordinate_civil[1]),)
                    new_etat = transition_etat._replace(ensemble_neutralise=new_tuple_neutralisee)

                    penalties_actuel += 20 # 20 car on vient de neutraliser une personne
                    penalties_actuel += 100 * (self.seen_by_guards(new_etat.position[0], new_etat.position[1], list(new_etat.ensemble_neutralise)) \
                                                + self.seen_by_civil(new_etat.position[0], new_etat.position[1], list(new_etat.ensemble_neutralise)))
                    # seen_by_guards retourne le nombre exact de gardes par lesquels on est vu pour chaque case
                    # si c'est == 0 alors on subit pas de penalites supplémentaires
                    # dans le cas contraire, c'est égal à 100 * (nb de guards + civils qui voit le hitman)

        elif action == "take_suit" :
            contenu_sur_cette_case = self.plateau.get_case(etat.position[0], etat.position[1]).contenu[0]
            if not etat.has_suit and contenu_sur_cette_case == "costume":
                new_etat = etat._replace(has_suit=True)

        elif action == "take_weapon" :
            contenu_sur_cette_case = self.plateau.get_case(etat.position[0], etat.position[1]).contenu[0]
            if not etat.has_weapon and contenu_sur_cette_case == "corde":
                new_etat = etat._replace(has_weapon=True)

        elif action == "put_on_suit" :
            if etat.has_suit:
                new_etat = etat._replace(is_suit_on=True)
                penalties_actuel += 100 * (self.seen_by_guards(new_etat.position[0], new_etat.position[1], list(new_etat.ensemble_neutralise)) \
                                            + self.seen_by_civil(new_etat.position[0], new_etat.position[1], list(new_etat.ensemble_neutralise)))
                # seen_by_guards retourne le nombre exact de gardes par lesquels on est vu pour chaque case
                # si c'est == 0 alors on subit pas de penalites supplémentaires
                # dans le cas contraire, c'est égal à 100 * (nb de guards + civils qui voit le hitman)

        etat_result = None
        if new_etat is not None:
            # update penalites
            if new_etat.is_suit_on:
                pass
            else:
                penalties_actuel += 5 * self.seen_by_guards(new_etat.position[0], new_etat.position[1], list(new_etat.ensemble_neutralise))
                # seen_by_guards retourne le nombre exact de gardes par lesquels on est vu pour cette case
                # si c'est == 0 alors on subit pas de penalites supplémentaires
                # dans le cas contraire, c'est égal à 5 * nb de guards qui voit le hitman
            etat_result = new_etat._replace(penalties=penalties_actuel)
        
        #print(etat_result)
        return etat_result


    def do_fn_for_real(self, nom_action):
        # Faire une action réellement
        if nom_action == "turn_clockwise":
            self.status = self.hitman.turn_clockwise()
        elif nom_action == "turn_anti_clockwise":
            self.status = self.hitman.turn_anti_clockwise()
        elif nom_action == "move":
            self.status = self.hitman.move()
        elif nom_action == "kill_target":
            self.status = self.hitman.kill_target()
        elif nom_action == "neutralize_guard":
            self.status = self.hitman.neutralize_guard()
        elif nom_action == "neutralize_civil":
            self.status = self.hitman.neutralize_civil()
        elif nom_action == "take_suit" :
            self.status = self.hitman.take_suit()
        elif nom_action == "take_weapon" :
            self.status = self.hitman.take_weapon()
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
        dic = {}  # Crée un dictionnaire vide pour stocker les états successeurs
        for action in actions:
            # Pour chaque nom d'action défini dans les règles
            # Vérifie si l'application de l'action sur l'état génère un nouvel état valide
            if self.do_fn(action, etat) is not None:
                dic[self.do_fn(action, etat)] = action
                # Ajoute le nouvel état à la clé et associe le nom de l'action au dictionnaire
                
        return dic  # Renvoie le dictionnaire des états successeurs avec les noms d'actions correspondants

    def testIfGoalAchived(self, etat, objectif):
        if objectif == "get_weapon":
        # tester si le hitman a un arme, a un etat donne
            return etat.has_weapon == True
        elif objectif == "kill_target":
        # tester si le jeu peut se terminer, a un etat donne
            return etat.is_target_down == True
        elif objectif == "return_home":
        # tester si le jeu peut se terminer, a un etat donne
            return etat.position == (0, 0)

    def calculer_heuristique_a_etoile(self, etat, pos_i, pos_j):
        # calculer g_score et h_score
        # g_score: distance de (0, 0) a cet etat
        # h_score: distance de cet etat a (pos_i, pos_j)
        
        g_score = self.plateau.distance_minimale(0, 0, etat.position[0],etat.position[1])
        h_score = self.plateau.distance_minimale(etat.position[0],etat.position[1], pos_i, pos_j)
        f_score = g_score + h_score
        return f_score

    def transform_dict_to_namedtuple(self, dictionary):
        # Le but est d'avoir un hashable namedtuple
        fields = list(dictionary.keys())

        # On a pas besoin de 'vision' pour la phase 2
        dictionary['vision'] = tuple()

        # Convertir "direction"
        if dictionary['orientation'] == HC.E:
            dictionary['orientation'] = "gauche"
        if dictionary['orientation'] == HC.N:
            dictionary['orientation'] = "haut"
        if dictionary['orientation'] == HC.W:
            dictionary['orientation'] = "droite"
        if dictionary['orientation'] == HC.E:
            dictionary['orientation'] = "bas"

        # Créer une liste contenant la position des cases sur lesquelles se trouvent des guards / civils neutralisées
        dictionary['ensemble_neutralise'] = tuple()
        fields.append('ensemble_neutralise')


        # Création d'un NamedTuple Class
        Etat = namedtuple('Etat', fields)

        # Création d'une instance de namedtuple
        named_tuple_instance = Etat(**dictionary)
        return named_tuple_instance

      
    def search_with_parent(self, etat_init, objectif, search_mode):
        # objectif: "get_weapon" ou "kill_target" ou "return_home
        # search_mode: "a_etoile" ou "phase_2_heuristic"

        if etat_init == None:
            raise ValueError("Le jeu n'a pas ete initialise")

        # Chercher la postion de l'objectif, par exemple la position de l'arme, du cible...
        if search_mode == "a_etoile":
            # C'est utile uniquement si on utilise algo A*
            m, n = self.plateau.infos_plateau()
            if objectif == "get_weapon":
            # recuperer la position de l'arme
                for i in range(m):
                    for j in range(n):
                        if self.plateau.get_case(i, j).contenu[0] == "corde":
                            pos_objectif_i = i
                            pos_objectif_j = j
            elif objectif == "kill_target":
             # recuperer la position du cible
               for i in range(m):
                    for j in range(n):
                        if self.plateau.get_case(i, j).contenu[0] == "cible":
                            pos_objectif_i = i
                            pos_objectif_j = j
            elif objectif == "return_home":
                pos_objectif_i = 0
                pos_objectif_j = 0
            else: raise ValueError("objectif pas connu")


        
        queue = PriorityQueue()  # Crée une file de priorité
        queue.put((0, etat_init))  # Ajoute l'état initial avec une priorité de 0 à la file
        save = {etat_init: None}  # Dictionnaire pour enregistrer les états visités et l'action prédécesseur

        while not queue.empty():  # Tant que la file de priorité n'est pas vide
            score, etat = queue.get()  # Récupère l'état avec le score de pénalité le plus bas
            # on traite alors la meilleure action

            #print(score, " ",etat)
            #print("            etat pred: ", save[etat])
            #print()

            if self.testIfGoalAchived(etat, objectif):
            # Si l'état correspond à l'objectif recherché
                return etat, save  
        
            for etat_suivant, nom_action in self.succ(etat).items():
            # Pour chaque état successeur et nom d'action correspondant
                if etat_suivant not in save:
                # Si l'état successeur n'a pas encore été visité
                    save[etat_suivant] = (etat, nom_action)  # Enregistre l'état successeur et le nom d'action prédécesseur

                    # Choisir entre 2 type d'algo de recherche: 2 etoile ou heuristique phase 2
                    if search_mode == "a_etoile":  #heuristique a_etoile
                        cout_action = self.calculer_heuristique_a_etoile(etat_suivant, pos_objectif_i, pos_objectif_j)
                    else:
                        cout_action = etat_suivant.penalties # heurisitique de l'enonce de phase 2
                  
                    # Calcule le coût heuristique de l'action successeur
                    queue.put((cout_action, etat_suivant))
                    # Ajoute l'état successeur à la file de priorité avec le coût heuristique comme priorité

                
        return None, save  # Aucun objectif trouvé, renvoie None et le dictionnaire save

    def dict2path(self, etat, dic):

        liste = [(etat, None)]  # Liste représentant l'état initial
        while dic[etat] is not None:
            # Tant que le prédécesseur de l'état actuel n'est pas None dans le dictionnaire
            parent, action = dic[etat]  # Récupère le prédécesseur et l'action menant à l'état actuel
            liste.append((parent, action))  
            etat = parent  # Met à jour l'état actuel avec le prédécesseur pour continuer la remontée
        liste.reverse()  # Inverse l'ordre des éléments de la liste pour obtenir le chemin complet du début à l'état
        return liste  # Renvoie la liste représentant le chemin complet

    def phase_2(self, temporisation_phase2):
        print("La phase 2 a commence !")
        print("Veuillez patienter, Hitman est en train de reflechir ...")
        
        #Dans cette phase, il y a 3 objectifs principals:
            #I.  Chercher le corde
            #II. Tuer le cible
            #III.Retourner à (0, 0) 

        self.status = self.hitman.start_phase2()
        self.update_hitman()

        etat_s0 = self.transform_dict_to_namedtuple(self.status)

        #etat_objectif_1, save = self.search_with_parent(etat_s0, "get_weapon", "a_etoile")
        etat_objectif_1, save = self.search_with_parent(etat_s0, "get_weapon", "phase_2_heuristic")
        actions_obj1 = [action for etat, action in self.dict2path(etat_objectif_1, save) if action]
        print("Hitman a trouve un arme !")

        etat_objectif_2, save = self.search_with_parent(etat_objectif_1, "kill_target", "phase_2_heuristic")
        actions_obj2 = [action for etat, action in self.dict2path(etat_objectif_2, save) if action]
        print("Hitman a trouve un chemin pour aller au cible !")

        etat_objectif_3, save = self.search_with_parent(etat_objectif_2, "return_home", "phase_2_heuristic")
        actions_obj3 = [action for etat, action in self.dict2path(etat_objectif_3, save) if action]
        print("Hitman a trouve un chemin pour retourner !")

        print("Liste de ses actions:")
        print("Objectif 1: trouver un arme")
        print(actions_obj1)
        print("Objectif 2: tuer le cible")
        print(actions_obj2)
        print("Objectif 3: retourner")
        print(actions_obj3)

        for action in actions_obj1:
            self.do_fn_for_real(action)
            self.update_hitman()
            print(self.plateau)
            if temporisation_phase2:
                sleep(0.25)
        for action in actions_obj2:
            self.do_fn_for_real(action)
            self.update_hitman()
            print(self.plateau)
            if temporisation_phase2:
                sleep(0.25)
        for action in actions_obj3:
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