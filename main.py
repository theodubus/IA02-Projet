from game import Game
import argparse

def str_bool(s):
    if s.lower() == 'false':
        return False
    return True

def main():
    g = Game()
    parser = argparse.ArgumentParser(description='Hitman')
    parser.add_argument('--sat', type=str, default="auto", help='sat mode, can be "auto", "no_sat" or "sat", default is "auto"')
    parser.add_argument('--temp', type=str, default="True", help='Wait a bit between each action, default is True. Is set to false if display is False')
    parser.add_argument('--costume_combinaisons', type=str, default="True", help='Use costume combinations, default is True')
    parser.add_argument('--display', type=str, default="True", help='Display the game, default is True')
    args = parser.parse_args()

    if args.display == "False":
        args.temp = "False"

    score_1, penalites_1, points_positifs = g.phase_1(temporisation=str_bool(args.temp), sat_mode=args.sat, display=str_bool(args.display))
    score_2 = g.phase_2(temporisation=str_bool(args.temp), costume_combinations=str_bool(args.costume_combinaisons), display=str_bool(args.display))


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