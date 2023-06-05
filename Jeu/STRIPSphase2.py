from typing import FrozenSet
from collections import namedtuple
from utils.hitman import HC
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
# à faire: fonction pour convertir cette variable "world_example" en "map_rules" en dessous:

Garde = namedtuple("Garde", ("position", "direction"))
gardes = {
    "g1" : frozenset({Garde((4,5), "bas")}),
    "g2" : frozenset({Garde((3,2), "droite")}),
} 

Predicat = namedtuple("Predicat", ("murs", "gardes", "invites", "corde", "costume", "cible", "actions"))  
map_rules = Predicat(
    murs=frozenset(
        { 
            # murs normaux
            (2, 0),
            (3, 0),
            (0, 2),
            (1, 2),
            (1, 3),
            (1, 4),
            # murs en bas
            (0, -1),
            (1, -1),
            (2, -1),
            (3, -1),
            (4, -1),
            (5, -1),
            (6, -1),
            # murs en haut
            (0, 6),
            (1, 6),
            (2, 6),
            (3, 6),
            (4, 6),
            (5, 6),
            (6, 6),
            # murs a droite
            (7, 0),
            (7, 1),
            (7, 2),
            (7, 3),
            (7, 4),
            (7, 5),
            # murs a gauche
            (-1, 0),
            (-1, 1),
            (-1, 2),
            (-1, 3),
            (-1, 4),    
            (-1, 5),
        }
    ),
    gardes=gardes,
    invites=frozenset(
        { 
            (5, 2),
            (5, 3),
            (6, 2),
        }
    ),
    corde=((5,0)),
    costume=((3,5)),
    cible=((0,3)),
    actions=actions,
)


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
    dic = {}
    for nom_action in rules.actions: 
        for action in rules.actions[nom_action]:
            if do_fn(action, etat, rules) != None:
                dic[do_fn(action, etat, rules)] = nom_action
    return dic

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
    save = {etat_s0: None}
    while liste_etats:
        etat, liste_etats = remove_head(liste_etats)
        for etat_suivant, nom_action in succ(etat, map_rules).items():
            if etat_suivant not in save:
                save[etat_suivant] = (etat, nom_action)
                if goals(etat_suivant, map_rules):
                    return etat_suivant, save
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
# Code pour l'implementation de A*

def calculer_heuristique(etat_suivant, nom_action):
    vuParGarde = False
    if est_vu_par_garde(etat_suivant.position, map_rules.gardes):
        vuParGarde = True
    if nom_action == "avancer":
        if vuParGarde: return 6
    elif nom_action == "tourner_horaire":
        if vuParGarde: return 6
    elif nom_action == "tourner_antihoraire":
        if vuParGarde: return 6
    elif nom_action == "neutraliser_garde" :
        if vuParGarde: return 100
        return 20
    elif nom_action == "prendre_costume" :
        if vuParGarde: return 100
    elif nom_action == "tuer_cible":
        if vuParGarde: return 100
    return 1

def recherche_a_etoile(etat_init, goals, succ):
    queue = PriorityQueue()
    queue.put((0, etat_init))
    save = {etat_init: None}
    
		while not queue.empty():
        _, etat = queue.get()
        
        if goals(etat, map_rules):
            return etat, save
        
        for etat_suivant, nom_action in succ(etat, map_rules).items():
            if etat_suivant not in save:
                save[etat_suivant] = (etat, nom_action)
                cout_action = calculer_heuristique(etat_suivant, nom_action)
                queue.put((cout_action, etat_suivant))
    
    return None, save

# ==========================

#  Choisir un algo de recherche:

# dernier_etat, save = recherche_non_informe(etat_s0, goals, succ, remove_head, insert_tail)
dernier_etat, save = recherche_a_etoile(etat_s0, goals, succ)

def dict2path(etat, dic):
    liste = [(etat, None)]
    while dic[etat] is not None:
        parent, action = dic[etat]
        liste.append((parent, action))
        etat = parent
    liste.reverse()
    return liste

plan = "->".join([action for etat, action in dict2path(dernier_etat, save) if action])

print(plan)
