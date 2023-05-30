from utils.hitman import HC, HitmanReferee, complete_map_example
from pprint import pprint

class Game:
    def __init__(self, m, n):
        self.hitman = HitmanReferee()
        self.__avoir_corde = False
        self.__avoir_costume = False

    def tourner_horaire(self):
        return self.hitman.turn_clockwise()
    def tourner_antihoraire(self):
        return self.hitman.turn_anti_clockwise()
    def avancer(self):
        return self.hitman.move()
    def getMap(self):
        return complete_map_example
    def tuer_cible(self, map, positionActuelle):
        if map[positionActuelle] == HC.TARGET and self.__avoir_corde == True:
            # code pour tuer..
            return 
    def passer_costume(self, map, positionActuelle):
        if self.__avoir_costume == True:
            if map[positionActuelle] == HC.EMPTY:
                map[positionActuelle] = HC.SUIT
                self.__avoir_costume = False
        return 
    def prendre_costume(self, map, positionActuelle):
        if self.__avoir_costume == False:
            if map[positionActuelle] == HC.SUIT:
                self.__avoir_costume = True
                map[positionActuelle] = HC.EMPTY
        return 
            
    def prendre_arme(self, map, positionActuelle):
        if self.__avoir_corde == False:
            if map[positionActuelle] == HC.PIANO_WIRE:
                self.__avoir_corde = True
                map[positionActuelle] = HC.EMPTY
        return 
            
    def phase_2(self):
        status = self.hitman.start_phase1()
        n_invites = status['civil_count']
        n_gardes = status['guard_count']
        map = self.getMap()
        positionActuelle = status['position']
        orientationActuelle = status['orientation']

        print("first pos: ", positionActuelle)
        print("ori: ", orientationActuelle)
        print("avoir costume: ", self.__avoir_costume)
        self.tourner_horaire()
        self.avancer()
        self.tourner_antihoraire()
        self.avancer()
        self.tourner_horaire()
        self.avancer()
        self.tourner_antihoraire()
        self.avancer()
        self.avancer()
        self.avancer()
        self.avancer()
        self.avancer()
        self.tourner_horaire()
        status = self.avancer()
        positionActuelle = status['position']
        orientationActuelle = status['orientation']
        self.prendre_costume(map, positionActuelle)
        
        print("second pos: ", positionActuelle)
        print("ori: ", orientationActuelle)
        print("avoir costume: ", self.__avoir_costume)


g = Game(6, 5)

g.phase_2()