"""





CE FICHIER EST OBSOLETE
LA PHASE 2 EST DANS game.py
faites-moi savoir si tu veux que je mette la phase 2 dans un autre fichier








"""
from typing import FrozenSet
from collections import namedtuple
from utils.hitman import HC, HitmanReferee
from queue import PriorityQueue

Action = namedtuple("Action", ("name"))
actions = {
    "avancer" : {Action("avancer")},
    "tourner_horaire" : {Action("tourner_horaire")},
    "tourner_antihoraire" : {Action("tourner_antihoraire")},
    "tuer_cible" : {Action("tuer_cible")},
    "neutraliser_garde" : {Action("neutraliser_garde")},
    "prendre_costume" : {Action("prendre_costume")},
    "prendre_arme" : {Action("prendre_arme")},
} 

# Pour l'instant: classe etat pas utilisable, a faire la methode __hash__
# class Etat:
#     def __init__(self, pos, dir, avoirCorde, avoirCostume, cibleTuee):
#         self.position = pos
#         self.direction = dir
#         self.avoir_corde = avoirCorde
#         self.avoir_costume = avoirCostume
#         self.cible_tuee = cibleTuee

#     def avancer(self):
#         i, j = self.position
#         new_position =  {"droite": (i+1, j), "gauche": (i-1, j), "haut": (i, j+1), "bas": (i, j-1)}[self.direction]
#         if free(new_position, map_rules):
#             self.position = new_position
#     def tourner_horaire(self):
#         if self.direction == "gauche":
#             return "haut"
#         elif self.direction == "haut":
#             return "droite"
#         elif self.direction == "droite":
#             return "bas"
#         elif self.direction == "bas":
#             return "gauche"
#     def tourner_antihoraire(self):
#         if self.direction == "gauche":
#             return "bas"
#         elif self.direction == "haut":
#             return "gauche"
#         elif self.direction == "droite":
#             return "haut"
#         elif self.direction == "bas":
#             return "droite"
#     def tuer_cible(self):
#         self.cible_tuee = True
#     def prendre_costume(self):
#         self.avoir_costume = True
#     def prendre_arme(self):
#         self.avoir_arme = True

Etat = namedtuple("Etat", ("position", "direction", "avoir_corde", "avoir_costume", "cible_tuee")) 
etat_s0 = Etat((1, 0), "haut", False, False, False)

world_example = [
    [HC.EMPTY, HC.EMPTY, HC.EMPTY, HC.SUIT, HC.GUARD_S, HC.WALL, HC.WALL],
    [HC.EMPTY, HC.WALL, HC.EMPTY, HC.EMPTY, HC.EMPTY, HC.EMPTY, HC.EMPTY],
    [HC.TARGET, HC.WALL, HC.EMPTY, HC.EMPTY, HC.EMPTY, HC.CIVIL_N, HC.EMPTY],
    [HC.WALL, HC.WALL, HC.EMPTY, HC.GUARD_E, HC.EMPTY, HC.CIVIL_W, HC.CIVIL_E],
    [HC.EMPTY, HC.EMPTY, HC.EMPTY, HC.EMPTY, HC.EMPTY, HC.EMPTY, HC.EMPTY],
    [HC.EMPTY, HC.EMPTY, HC.WALL, HC.WALL, HC.EMPTY, HC.PIANO_WIRE, HC.EMPTY],
]

# les fonctions:
def avancer(position, direction):
    i, j = position
    return {"droite": (i+1, j), "gauche": (i-1, j), "haut": (i, j+1), "bas": (i, j-1)}[direction]

def tourner_horaire(direction):
    if direction == "gauche":
        return "haut"
    elif direction == "haut":
        return "droite"
    elif direction == "droite":
        return "bas"
    elif direction == "bas":
        return "gauche"
    
def tourner_antihoraire(direction):
    if direction == "gauche":
        return "bas"
    elif direction == "haut":
        return "gauche"
    elif direction == "droite":
        return "haut"
    elif direction == "bas":
        return "droite"
    
def est_garde_presente(position, gardes):
    for ensemble_gardes in gardes.values():
        for garde in ensemble_gardes:
            if garde.position == position:
                return True
    return False

def free(position, map_rules):  
    return (position not in map_rules.murs and not est_garde_presente(position, map_rules.gardes))

def do_fn(action, etat, rules):
    if action.name == "avancer":
        new_position = avancer(etat.position, etat.direction)
        if free(new_position, map_rules):
            return Etat(new_position, etat.direction, etat.avoir_corde, etat.avoir_costume, etat.cible_tuee)
    elif action.name == "tourner_horaire":
        new_direction = tourner_horaire(etat.direction)
        return Etat(etat.position, new_direction, etat.avoir_corde, etat.avoir_costume, etat.cible_tuee)
    elif action.name == "tourner_antihoraire":
        new_direction = tourner_antihoraire(etat.direction)
        return Etat(etat.position, new_direction, etat.avoir_corde, etat.avoir_costume, etat.cible_tuee)
    elif action.name == "tuer_cible":
        if etat.avoir_corde and etat.position == rules.cible:
            return Etat(etat.position, etat.direction, etat.avoir_corde, etat.avoir_costume, True)
    # elif action.name == "neutraliser_garde":
    #  à implémenter
    #     return
    elif action.name == "prendre_costume" :
        if not etat.avoir_costume and etat.position == rules.costume:
            return Etat(etat.position, etat.direction, etat.avoir_corde, True, etat.cible_tuee)
    elif action.name == "prendre_arme" :
        if not etat.avoir_corde and etat.position == rules.corde:
            return Etat(etat.position, etat.direction, True, etat.avoir_costume, etat.cible_tuee)
    return None

#================ do_fn pour version de classe hashable========
# def do_fn(action, etat, rules):
#     if action.name == "avancer":
#         etat.avancer()    
#         return etat
#     elif action.name == "tourner_horaire":
#         etat.tourner_horaire()
#         return etat
#     elif action.name == "tourner_antihoraire":
#         etat.tourner_antihoraire()
#         return etat
#     elif action.name == "tuer_cible":
#         if etat.avoir_corde and etat.position == rules.cible:
#             etat.tuer_cible()
#             return etat
#     elif action.name == "prendre_costume" :
#         if not etat.avoir_costume and etat.position == rules.costume:
#             etat.prendre_costume()
#             return etat
#     elif action.name == "prendre_arme" :
#         if not etat.avoir_corde and etat.position == rules.corde:
#             etat.prendre_arme()
#             return etat
#     return None
#=========================================================

def succ(etat, rules):
    dic = {}  # Crée un dictionnaire vide pour stocker les états successeurs
    for nom_action in rules.actions:
        # Pour chaque nom d'action défini dans les règles
        for action in rules.actions[nom_action]:
            # Pour chaque action correspondant à ce nom d'action dans les règles

            # Vérifie si l'application de l'action sur l'état génère un nouvel état valide
            if do_fn(action, etat, rules) is not None:
                dic[do_fn(action, etat, rules)] = nom_action
                # Ajoute le nouvel état à la clé et associe le nom de l'action au dictionnaire
                
    return dic  # Renvoie le dictionnaire des états successeurs avec les noms d'actions correspondants


def goals(etat, rules):
    return etat.position == (0, 0) and etat.cible_tuee == True

# ===========================
# Code pour la recherche non informe
def insert_tail(etat, liste):
    liste.append(etat)
    return liste
def remove_head(liste):
    return liste.pop(0), liste
def remove_tail(liste):
    return liste.pop(), liste
def recherche_non_informe(etat_s0, goals, succ, remove_head, insert_tail):
    liste_etats = [etat_s0]
    save = {etat_s0: None} # le dictionnaire pour enregistrer les etats visites et leurs predecesseurs
    while liste_etats:
        etat, liste_etats = remove_head(liste_etats)
        # Retire l'état en tête de liste et met à jour la liste
        for etat_suivant, nom_action in succ(etat, map_rules).items():
        # Pour chaque etat successeur et nom d'action correspondant
            if etat_suivant not in save:
            # Si l'etat successeur n'a pas encore ete visite
                save[etat_suivant] = (etat, nom_action)
                # Enregistre l'etat successeur et son predecesseur
                if goals(etat_suivant, map_rules): # Si l'etat successeur correspond au but recherche
                    return etat_suivant, save # Renvoie l'etat successeur et le dictionnaire save
                insert_tail(etat_suivant, liste_etats)
    return None, save

# ============================
def est_vu_par_garde(position, gardes):
    # Vérification du champ de vision des gardes
    i, j = position
    for ensemble_gardes in gardes.values():
        for garde in ensemble_gardes:
            if garde.direction == "haut":
                # Vérification des positions en haut du personnage
                for y in range(j+1, j+3):
                    if est_garde_presente((i, y), gardes):
                        return True

            elif garde.direction == "bas":
                for y in range(j-1, j-3, -1):
                    if est_garde_presente((i, y), gardes):
                        return True

            elif garde.direction == "gauche":
                for x in range(i-1, i-3, -1):
                    if est_garde_presente((x, j), gardes):
                        return True

            elif garde.direction == "droite":
                for x in range(i+1, i+3):
                    if est_garde_presente((x, j), gardes):
                        return True
    return False
# ============================
# Code pour l'implementation d'algo recherche informe

def calculer_heuristique(etat_suivant, nom_action):
    vuParGarde = False
    if est_vu_par_garde(etat_suivant.position, map_rules.gardes):
        vuParGarde = True
    if nom_action == "avancer":
        if vuParGarde: return -6
    elif nom_action == "tourner_horaire":
        if vuParGarde: return -6
    elif nom_action == "tourner_antihoraire":
        if vuParGarde: return -6
    elif nom_action == "neutraliser_garde" :
        if vuParGarde: return -100
        return -20
    elif nom_action == "prendre_costume" :
        if vuParGarde: return -100
    elif nom_action == "tuer_cible":
        if vuParGarde: return -100
    return -1

def recherche_informe(etat_init, goals, succ):
    queue = PriorityQueue()  # Crée une file de priorité
    queue.put((0, etat_init))  # Ajoute l'état initial avec une priorité de 0 à la file
    save = {etat_init: None}  # Dictionnaire pour enregistrer les états visités et leurs prédécesseurs
    
    while not queue.empty():  # Tant que la file de priorité n'est pas vide
        _, etat = queue.get()  # Récupère l'état avec la plus haute priorité de la file
        # on traite alors la meilleure action
        
        if goals(etat, map_rules):
            # Si l'état correspond à un objectif recherché
            return etat, save  
        
        for etat_suivant, nom_action in succ(etat, map_rules).items():
            # Pour chaque état successeur et nom d'action correspondant
            
            if etat_suivant not in save:
                # Si l'état successeur n'a pas encore été visité
                save[etat_suivant] = (etat, nom_action)  # Enregistre l'état successeur et son prédécesseur
                
                cout_action = calculer_heuristique(etat_suivant, nom_action)
                # Calcule le coût heuristique de l'action successeur
                
                queue.put((cout_action, etat_suivant))
                # Ajoute l'état successeur à la file de priorité avec le coût heuristique comme priorité
                
    return None, save  # Aucun objectif trouvé, renvoie None et le dictionnaire save


# ==========================

#  Choisir un algo de recherche:

# dernier_etat, save = recherche_non_informe(etat_s0, goals, succ, remove_head, insert_tail)
dernier_etat, save = recherche_informe(etat_s0, goals, succ)

def dict2path(etat, dic):
    liste = [(etat, None)]  # Liste représentant l'état initial
    while dic[etat] is not None:
        # Tant que le prédécesseur de l'état actuel n'est pas None dans le dictionnaire
        parent, action = dic[etat]  # Récupère le prédécesseur et l'action menant à l'état actuel
        liste.append((parent, action))  
        etat = parent  # Met à jour l'état actuel avec le prédécesseur pour continuer la remontée
    liste.reverse()  # Inverse l'ordre des éléments de la liste pour obtenir le chemin complet du début à l'état
    return liste  # Renvoie la liste représentant le chemin complet


plan = "->".join([action for etat, action in dict2path(dernier_etat, save) if action])

print(plan)