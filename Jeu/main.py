from game import Game

def main():
    g = Game()
    score_1, penalites_1, points_positifs = g.phase_1(temporisation=False, sat_mode="no_sat")
    score_2 = g.phase_2(temporisation=False, costume_combinations=True)


    print("==============================================")
    print("resultat final:\n")
    print(f"Points positifs phase 1: {points_positifs}")
    print(f"Penalites phase 1: {penalites_1}")
    print(f"Score phase 1: {score_1}\n")
    print(f"Penalites phase 2: {score_2}\n")
    print(f"Score total: {score_1 + score_2}")
    print("==============================================")

if __name__ == "__main__":
    main()