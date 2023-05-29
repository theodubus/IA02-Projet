from utils.clauses_combin import *
from utils.case import Case
from utils.plateau import Plateau
from utils.hitman import HC, HitmanReferee, complete_map_example
from pprint import pprint
from gophersat.dimacs import solve


class Game:
    def __init__(self, m, n):
        self.plateau = None
        self.hitman = HitmanReferee()
        self.clauses = []
        self.pos_actuelle = None
        self.nb_variables = None
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
            

    def phase_1(self):
        """
        méthode encore en construction

        pour le moment il n'y a que les clauses des n gardes et m invites à l'entree du jeu
        il reste l'exploration du jeu a faire, ainsi que la mise a jour du plateau avec plateau.set_case()
        et l'ajout de clauses au fur et a mesure
        """

        status = self.hitman.start_phase1()
        m = status['m'] + 1
        n = status['n'] + 1
        self.plateau = Plateau(m, n)
        n_invites = status['civil_count']
        n_gardes = status['guard_count']
        self.pos_actuelle = status['position']

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
        self.update_knowledge(status)
        print(self.plateau)

        while self.prochaine_case():
            # i, j = self.prochaine_case()
            # exployer et decouvrir i, j
            break

    def explore(self, i, j):
        
        # while i, j non connu
        # determiner et effectuer la prochaine action
        # update connaissance
        # print plateau
        pass

    def satisfiable(self):
        """
        Renvoie True si les clauses sont satisfiables, False sinon
        """
        solve(self.clauses, nb_var=self.nb_variables)

    def update_knowledge(self, status):
        """
        Met a jour le plateau et la base de clauses avec les informations obtenues

        Pour la vue, on met a jour notre modele de plateau et on ajoute des clauses.
        
        Pour l'ecoute, on ajoute simplement des clauses. Il y a "hear" cases qui contiennent
        un garde ou un invite le fait qu'un garde et un invite ne soient pas
        sur la meme case est deja pris en compte dans les clauses d'initialisation
        """

        vision = status['vision']
        hear = status['hear']

        # vision
        ## plateau
        for case in vision:
            pos, contenu = case
            i, j = pos
            if not self.plateau.get_case(i, j).contenu_connu():
                self.plateau.set_case(i, j, self.dict_cases[contenu])

                ## clauses
                if self.dict_cases[contenu][0] in {"invite", "garde"}:
                    self.clauses.append(self.plateau.cell_to_var(i, j, self.dict_cases[contenu][0]))
                else:
                    self.clauses.append(-self.plateau.cell_to_var(i, j, "invite"))
                    self.clauses.append(-self.plateau.cell_to_var(i, j, "garde"))

        # ouie
        ## clauses
        i_act, j_act = self.pos_actuelle
        cases_entendues = self.plateau.cases_entendre(i_act, j_act)
        variables_invites_gardes = [self.plateau.cell_to_var(i, j, "invite") for i, j in cases_entendues] + [self.plateau.cell_to_var(i, j, "garde") for i, j in cases_entendues]

        if hear == 5:
            self.clauses += at_least_n(5, variables_invites_gardes)
        else:
            self.clauses += exactly_n(hear, variables_invites_gardes)


    def prochaine_case(self):
        """
        Renvoie les coordonnees de la prochaine case a explorer, c'est a dire la case la plus proche
        qui n'a pas encore ete exploree
        """
        if self.plateau is None or self.pos_actuelle is None:
            raise ValueError("Le jeu n'a pas ete initialise")
        
        # on recupere les coordonnees de la case actuelle et les dimensions du plateau
        i, j = self.pos_actuelle
        m, n = self.plateau.infos_plateau()

        # on recupere les cases candidates
        cases_candidates = []
        for i2 in range(m):
            for j2 in range(n):
                if i2 == i and j2 == j:
                    continue
                distance = self.plateau.distance_manhattan(i, j, i2, j2)
                cases_candidates.append((i2, j2, distance))
        
        # on trie les cases candidates par distance
        cases_candidates.sort(key=lambda x: x[2])

        # on renvoie la premiere case qui n'a pas encore ete exploree
        for i2, j2, _ in cases_candidates:
            if not self.plateau.get_case(i2, j2).contenu_connu():
                return i2, j2
            
        # si toutes les cases ont ete explorees, on renvoie False
        return False




g = Game(6, 5)

g.phase_1()

