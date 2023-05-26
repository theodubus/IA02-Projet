from utils.clauses_combin import *
from utils.case import Case
from utils.plateau import Plateau
from utils.hitman import HC, HitmanReferee, complete_map_example
from pprint import pprint
from gophersat.dimacs import solve


class Game:
    def __init__(self, m, n):
        self.plateau = Plateau(m, n)
        self.hitman = HitmanReferee()
        self.clauses = []

    def phase_1(self):
        """
        méthode encore en construction

        pour le moment il n'y a que les clauses des n gardes et m invites à l'entree du jeu
        il reste l'exploration du jeu a faire, ainsi que la mise a jour du plateau avec plateau.set_case()
        et l'ajout de clauses au fur et a mesure
        """

        status = self.hitman.start_phase1()
        n_invites = status['civil_count']
        n_gardes = status['guard_count']

        # recuperation des dimensions du plateau et des variables cnf
        m, n = self.plateau.infos_plateau()
        variables_invites = [self.plateau.cell_to_var(i, j, "invite") for i in range(m) for j in range(n)]
        variables_gardes = [self.plateau.cell_to_var(i, j, "garde") for i in range(m) for j in range(n)]
        nb_variables = len(variables_invites) + len(variables_gardes)

        # On ajoute les clauses initiales
        self.clauses += exactly_n(n_invites, variables_invites) # clauses pour avoir n_invites invites
        self.clauses += exactly_n(n_gardes, variables_gardes) # clauses pour avoir n_gardes gardes
        self.clauses += unique(variables_invites, variables_gardes) # clauses pour ne pas avoir d'invite et de garde sur la meme case
                
        print("nombre de clauses : ", len(self.clauses))

        # test de resolution des clauses une fois obtenues
        print(solve(self.clauses, nb_var=nb_variables))


        # l'initialisation est faite, il reste a se deplacer et a ajouter les clauses au fur et a mesure

        # on peut essayer de predire si une case contient un garde par exemple en
        # ajoutant une clause "garde à telle case" et vérifier si il existe un modèle qui vérifie cette condition,
        # auquel cas il est possible qu'il y ait un garde à cette case.


g = Game(6, 5)

g.phase_1()