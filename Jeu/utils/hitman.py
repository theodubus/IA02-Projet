__author__ = "Sylvain Lagrue, and Hénoïk Willot"
__copyright__ = "Copyright 2023, Université de technologie de Compiègne"
__license__ = "LGPL-3.0"
__version__ = "0.6.2"
__maintainer__ = "Sylvain Lagrue"
__email__ = "sylvain.lagrue@utc.fr"
__status__ = "dev"

from enum import Enum
from itertools import product
from typing import List, Tuple, Dict
import sys

print(f"Hitman Referee v{__version__}", file=sys.stderr)
print(f"Please make sure you are using the latest version.", file=sys.stderr)

ASCII_ART = '''
                        .-""""-.
                       / j      \\
                      :.d;       ;
                      $$P        :
           .m._       $$         :
          dSMMSSSss.__$$b.    __ :
         :MMSMMSSSMMMSS$$$b  $$P ;
         SMMMSMMSMMMSSS$$$$     :b
        dSMMMSMMMMMMSSMM$$$b.dP SSb.
       dSMMMMMMMMMMSSMMPT$$=-. /TSSSS.
      :SMMMSMMMMMMMSMMP  `$b_.'  MMMMSS.
      SMMMMMSMMMMMMMMM \\  .'\\    :SMMMSSS.
     dSMSSMMMSMMMMMMMM  \\/\\_/; .'SSMMMMSSSm
    dSMMMMSMMSMMMMMMMM    :.;'" :SSMMMMSSMM;
  .MMSSSSSMSSMMMMMMMM;    :.;   MMSMMMMSMMM;
 dMSSMMSSSSSSSMMMMMMM;    ;.;   MMMMMMMSMMM
:MMMSSSSMMMSSP^TMMMMM     ;.;   MMMMMMMMMMM
MMMSMMMMSSSSP   `MMMM     ;.;   :MMMMMMMMM;
"TMMMMMMMMMM      TM;    :`.:    MMMMMMMMM;
   )MMMMMMM;     _/\\\\    :`.:    :MMMMMMMM
  d$SS$$$MMMb.  |._\\\\\\   :`.:     MMMMMMMM
  T$$S$$$$$$$$$$m;O\\\\\\\\"-;`.:_.-  MMMMMMM;
 :$$$$$$$$$$$$$$$b_l./\\\\ ;`.:    mMMSSMMM;
 :$$$$$$$$$$$$$$$$$$$./\\\\;`.:  .$$MSMMMMMM
  $$$$$$$$$$$$$$$$$$$$. \\\\`.:.$$$$SMSSSMMM;
  $$$$$$$$$$$$$$$$$$$$$. \\\\.:$$$$$SSMMMMMMM
  :$$$$$$$$$$$$$$$$$$$$$.//.:$$$$SSSSSSSMM;
  :$$$$$$$$$$$$$$$$$$$$$$.`.:$$SSSSSSSMMMP
   $$$$$$$$$;"^$J "^$$$$;.`.$$P  `SSSMMMM
   :$$$$$$$$$       :$$$;.`.P'..   TMMM$$b
   :$$$$$$$$$;      $$$$;.`/ c^'   d$$$$$S;
   $$$$$S$$$$;      '^^^:_d$g:___.$$$$$$SSS
   $$$$SS$$$$;            $$$$$$$$$$$$$$SSS;
  :$$$SSSS$$$$            : $$$$$$$$$$$$$SSS
  :$P"TSSSS$$$            ; $$$$$$$$$$$$$SSS;
  j    `SSSSS$           :  :$$$$$$$$$$$$$SS$
 :       "^S^'           :   $$$$$$$$$$$$$S$;
 ;.____.-;"               "--^$$$$$$$$$$$$$P
 '-....-"                       ""^^T$$$$P"
'''


# Hitman constants
class HC(Enum):
    EMPTY = 1
    WALL = 2
    GUARD_N = 3
    GUARD_E = 4
    GUARD_S = 5
    GUARD_W = 6
    CIVIL_N = 7
    CIVIL_E = 8
    CIVIL_S = 9
    CIVIL_W = 10
    TARGET = 11
    SUIT = 12
    PIANO_WIRE = 13
    N = 14
    E = 15
    S = 16
    W = 17


# Provisoire...
world_example = [
    [HC.EMPTY, HC.EMPTY, HC.EMPTY, HC.SUIT, HC.GUARD_S, HC.WALL, HC.WALL],
    [HC.EMPTY, HC.WALL, HC.EMPTY, HC.EMPTY, HC.EMPTY, HC.EMPTY, HC.EMPTY],
    [HC.TARGET, HC.WALL, HC.EMPTY, HC.EMPTY, HC.EMPTY, HC.CIVIL_N, HC.EMPTY],
    [HC.WALL, HC.WALL, HC.EMPTY, HC.GUARD_E, HC.EMPTY, HC.CIVIL_E, HC.CIVIL_W],
    [HC.EMPTY, HC.EMPTY, HC.EMPTY, HC.EMPTY, HC.EMPTY, HC.EMPTY, HC.EMPTY],
    [HC.EMPTY, HC.EMPTY, HC.WALL, HC.WALL, HC.EMPTY, HC.PIANO_WIRE, HC.EMPTY],
]

complete_map_example = {
    (0, 5): HC.EMPTY,
    (1, 5): HC.EMPTY,
    (2, 5): HC.EMPTY,
    (3, 5): HC.SUIT,
    (4, 5): HC.GUARD_S,
    (5, 5): HC.WALL,
    (6, 5): HC.WALL,
    (0, 4): HC.EMPTY,
    (1, 4): HC.WALL,
    (2, 4): HC.EMPTY,
    (3, 4): HC.EMPTY,
    (4, 4): HC.EMPTY,
    (5, 4): HC.EMPTY,
    (6, 4): HC.EMPTY,
    (0, 3): HC.TARGET,
    (1, 3): HC.WALL,
    (2, 3): HC.EMPTY,
    (3, 3): HC.EMPTY,
    (4, 3): HC.EMPTY,
    (5, 3): HC.CIVIL_N,
    (6, 3): HC.EMPTY,
    (0, 2): HC.WALL,
    (1, 2): HC.WALL,
    (2, 2): HC.EMPTY,
    (3, 2): HC.GUARD_E,
    (4, 2): HC.EMPTY,
    (5, 2): HC.CIVIL_E,
    (6, 2): HC.CIVIL_W,
    (0, 1): HC.EMPTY,
    (1, 1): HC.EMPTY,
    (2, 1): HC.EMPTY,
    (3, 1): HC.EMPTY,
    (4, 1): HC.EMPTY,
    (5, 1): HC.EMPTY,
    (6, 1): HC.EMPTY,
    (0, 0): HC.EMPTY,
    (1, 0): HC.EMPTY,
    (2, 0): HC.WALL,
    (3, 0): HC.WALL,
    (4, 0): HC.EMPTY,
    (5, 0): HC.PIANO_WIRE,
    (6, 0): HC.EMPTY,
}


class HitmanReferee:
    def __init__(self, filename: str = ""):
        self.__filename = filename
        if filename == "":
            self.__world = world_example
            self.__m = len(self.__world)
            self.__n = len(self.__world[0])
        else:
            raise NotImplementedError("TODO")

        self.__civil_count = self.__compute_civil_count()
        self.__guard_count = self.__compute_guard_count()
        self.__civils = self.__compute_civils()
        self.__guards = self.__compute_guards()
        self.__phase = 0
        self.__phase1_penalties = 0
        self.__phase1_guess_score = 0
        self.__phase2_penalties = 0
        self.__pos = (0, 0)
        self.__orientation = HC.N
        self.__has_guessed = False
        self.__is_in_guard_range = False
        self.__is_in_civil_range = False
        self.__phase1_history: List[str] = []
        self.__phase2_history: List[str] = []
        self.__has_suit = False
        self.__suit_on = False
        self.__has_weapon = False
        self.__is_target_down = False

    def start_phase1(self):
        self.__phase = 1
        return self.__get_status_phase_1()

    def __get_status_phase_1(self, err: str = "OK"):
        return {
            "status": err,
            "phase": self.__phase,
            "guard_count": self.__guard_count,
            "civil_count": self.__civil_count,
            "m": self.__m,
            "n": self.__n,
            "position": self.__pos,
            "orientation": self.__orientation,
            "vision": self.__get_vision(),
            "hear": self.__get_listening(),
            "penalties": self.__phase1_penalties,
            "is_in_guard_range": self.__is_in_guard_range,
        }

    def send_content(self, map_info: Dict[Tuple[int, int], HC]) -> bool:
        if not self.__has_guessed:
            self.__has_guessed = True
            guess_is_right = True
            for (x, y), content in map_info.items():
                if (
                    x >= self.__n
                    or y >= self.__m
                    or x < 0
                    or y < 0
                    or content != self.__get_world_content(x, y)
                ):
                    guess_is_right = False
                else:
                    self.__phase1_guess_score += 2
            all_tiles = list(product(range(self.__n), range(self.__m)))
            unobserved_tiles = [
                (x, y) for (x, y) in all_tiles if (x, y) not in map_info.keys()
            ]
            return len(unobserved_tiles) == 0 and guess_is_right
        else:
            raise ValueError("Err: cand only send content once")

    def end_phase1(self) -> Tuple[bool, str, List, Dict]:
        if not self.__has_guessed:
            return False, "Err: Cannot end phase1 without guessing the map", [], {}
        self.__phase = 0
        all_tiles = list(product(range(self.__n), range(self.__m)))
        map_content = {(x, y): self.__get_world_content(x, y) for (x, y) in all_tiles}
        return (
            True,
            f"Your score is {self.__phase1_guess_score-self.__phase1_penalties}",
            self.__phase1_history,
            map_content,
        )

    def __get_world_content(self, x: int, y: int):
        # provisoire
        return self.__world[self.__m - y - 1][x]

    def __update_world_content(self, x: int, y: int, new_content: HC):
        self.__world[self.__m - y - 1][x] = new_content
        # comme un objet bloquant la vue peut être retiré, il faut update les visions
        self.__civils = self.__compute_civils()
        self.__guards = self.__compute_guards()

    def __get_listening(self, dist=2):
        count = 0
        possible_offset = range(-dist, dist + 1)
        offsets = product(possible_offset, repeat=2)
        x, y = self.__pos
        for i, j in offsets:
            pos_x, pos_y = x + i, y + j
            if pos_x >= self.__n or pos_y >= self.__m or pos_x < 0 or pos_y < 0:
                continue
            if self.__get_world_content(pos_x, pos_y) in [
                HC.CIVIL_N,
                HC.CIVIL_E,
                HC.CIVIL_S,
                HC.CIVIL_W,
                HC.GUARD_N,
                HC.GUARD_E,
                HC.GUARD_S,
                HC.GUARD_W,
            ]:
                count += 1
            if count == 5:
                break

        return count

    def __get_offset(self):
        if self.__orientation == HC.N:
            offset = 0, 1
        elif self.__orientation == HC.E:
            offset = 1, 0
        elif self.__orientation == HC.S:
            offset = 0, -1
        elif self.__orientation == HC.W:
            offset = -1, 0

        return offset

    def __get_vision(self, dist=3):
        offset_x, offset_y = self.__get_offset()
        pos = self.__pos
        x, y = pos
        vision = []
        for _ in range(0, dist):
            pos = x + offset_x, y + offset_y
            x, y = pos
            if x >= self.__n or y >= self.__m or x < 0 or y < 0:
                break
            vision.append((pos, self.__get_world_content(x, y)))
            if vision[-1][1] != HC.EMPTY:
                break
        return vision

    def move(self):
        offset_x, offset_y = self.__get_offset()
        x, y = self.__pos

        if self.__phase == 1:
            self.__phase1_penalties += 1
        elif self.__phase == 2:
            self.__phase2_penalties += 1
        else:
            raise ValueError("Err: invalid phase")

        self.__add_history("Move")

        if self.__get_world_content(x + offset_x, y + offset_y) not in [
            HC.EMPTY,
            HC.PIANO_WIRE,
            HC.CIVIL_N,
            HC.CIVIL_E,
            HC.CIVIL_S,
            HC.CIVIL_W,
            HC.SUIT,
            HC.TARGET,
        ]:
            if self.__phase == 1:
                self.__phase1_penalties += 5 * self.__seen_by_guard_num()
                return self.__get_status_phase_1("Err: invalid move")
            else:
                self.__phase2_penalties += (
                    0 if self.__suit_on else 5 * self.__seen_by_guard_num()
                )
                return self.__get_status_phase_2("Err: invalid move")

        self.__pos = x + offset_x, y + offset_y

        if self.__phase == 1:
            self.__phase1_penalties += 5 * self.__seen_by_guard_num()
            return self.__get_status_phase_1()
        else:
            self.__seen_by_civil_num()
            self.__phase2_penalties += (
                0 if self.__suit_on else 5 * self.__seen_by_guard_num()
            )
            return self.__get_status_phase_2()

    def turn_clockwise(self):
        if self.__phase == 1:
            self.__phase1_penalties += 1
            self.__phase1_penalties += 5 * self.__seen_by_guard_num()
        elif self.__phase == 2:
            self.__phase2_penalties += 1
            self.__phase2_penalties += (
                0 if self.__suit_on else 5 * self.__seen_by_guard_num()
            )
        else:
            raise ValueError("Err: invalid phase")

        self.__add_history("Turn Clockwise")

        if self.__orientation == HC.N:
            self.__orientation = HC.E
        elif self.__orientation == HC.E:
            self.__orientation = HC.S
        elif self.__orientation == HC.S:
            self.__orientation = HC.W
        elif self.__orientation == HC.W:
            self.__orientation = HC.N

        return (
            self.__get_status_phase_1()
            if self.__phase == 1
            else self.__get_status_phase_2()
        )

    def turn_anti_clockwise(self):
        if self.__phase == 1:
            self.__phase1_penalties += 1
            self.__phase1_penalties += 5 * self.__seen_by_guard_num()
        elif self.__phase == 2:
            self.__phase2_penalties += 1
            self.__phase2_penalties += (
                0 if self.__suit_on else 5 * self.__seen_by_guard_num()
            )
        else:
            raise ValueError("Err: invalid phase")

        self.__add_history("Turn Anti-Clockwise")

        if self.__orientation == HC.N:
            self.__orientation = HC.W
        elif self.__orientation == HC.E:
            self.__orientation = HC.N
        elif self.__orientation == HC.S:
            self.__orientation = HC.E
        elif self.__orientation == HC.W:
            self.__orientation = HC.S
        return (
            self.__get_status_phase_1()
            if self.__phase == 1
            else self.__get_status_phase_2()
        )

    def start_phase2(self):
        self.__phase = 2
        self.__pos = (0, 0)
        self.__orientation = HC.N
        self.__seen_by_guard_num()
        self.__seen_by_civil_num()
        return self.__get_status_phase_2()

    def __get_status_phase_2(self, err: str = "OK"):
        return {
            "status": err,
            "phase": self.__phase,
            "guard_count": self.__guard_count,
            "civil_count": self.__civil_count,
            "m": self.__m,
            "n": self.__n,
            "position": self.__pos,
            "orientation": self.__orientation,
            "vision": self.__get_vision(),
            "hear": self.__get_listening(),
            "penalties": self.__phase2_penalties,
            "is_in_guard_range": self.__is_in_guard_range,
            "is_in_civil_range": self.__is_in_civil_range,
            "has_suit": self.__has_suit,
            "is_suit_on": self.__suit_on,
            "has_weapon": self.__has_weapon,
            "is_target_down": self.__is_target_down,
        }

    def end_phase2(self):
        if not self.__is_target_down or not self.__pos == (0, 0):
            return False, "Err: finish the mission and go back to (0,0)", []
        self.__phase = 0
        return True, f"Your score is {- self.__phase2_penalties}", self.__phase2_history

    def kill_target(self):
        if self.__phase != 2:
            raise ValueError("Err: invalid phase")

        self.__add_history("Kill Target")
        self.__phase2_penalties += 1
        self.__phase2_penalties += (
            0 if self.__suit_on else 5 * self.__seen_by_guard_num()
        )
        x, y = self.__pos
        if self.__get_world_content(x, y) != HC.TARGET or not self.__has_weapon:
            return self.__get_status_phase_2("Err: invalid move")

        self.__update_world_content(x, y, HC.EMPTY)
        self.__is_target_down = True

        self.__phase2_penalties += 100 * (
            self.__seen_by_guard_num() + self.__seen_by_civil_num()
        )
        return self.__get_status_phase_2()

    def neutralize_guard(self):
        if self.__phase != 2:
            raise ValueError("Err: invalid phase")

        self.__add_history("Neutralize Guard")
        self.__phase2_penalties += 1
        self.__phase2_penalties += 5 * self.__seen_by_guard_num()

        offset_x, offset_y = self.__get_offset()
        x, y = self.__pos

        if self.__get_world_content(x + offset_x, y + offset_y) not in [
            HC.GUARD_N,
            HC.GUARD_E,
            HC.GUARD_S,
            HC.GUARD_W,
        ] or (x, y) in [
            pos for (pos, _) in self.__guards[(x + offset_x, y + offset_y)]
        ]:
            return self.__get_status_phase_2("Err: invalid move")

        self.__phase2_penalties += 20
        self.__update_world_content(x + offset_x, y + offset_y, HC.EMPTY)
        self.__guard_count -= 1
        self.__phase2_penalties += 100 * (
            self.__seen_by_guard_num() + self.__seen_by_civil_num()
        )

        return self.__get_status_phase_2()

    def neutralize_civil(self):
        if self.__phase != 2:
            raise ValueError("Err: invalid phase")

        self.__add_history("Neutralize Civil")
        self.__phase2_penalties += 1
        self.__phase2_penalties += 5 * self.__seen_by_guard_num()

        offset_x, offset_y = self.__get_offset()
        x, y = self.__pos
        if self.__get_world_content(x + offset_x, y + offset_y) not in [
            HC.CIVIL_N,
            HC.CIVIL_E,
            HC.CIVIL_S,
            HC.CIVIL_W,
        ] or (x, y) in [
            pos for (pos, _) in self.__civils[(x + offset_x, y + offset_y)]
        ]:
            return self.__get_status_phase_2("Err: invalid move")

        self.__phase2_penalties += 20
        self.__update_world_content(x + offset_x, y + offset_y, HC.EMPTY)
        self.__civil_count -= 1
        self.__phase2_penalties += 100 * (
            self.__seen_by_guard_num() + self.__seen_by_civil_num()
        )

        return self.__get_status_phase_2()

    def take_suit(self):
        if self.__phase != 2:
            raise ValueError("Err: invalid phase")

        self.__add_history("Take Suit")
        self.__phase2_penalties += 1
        self.__phase2_penalties += 5 * self.__seen_by_guard_num()

        x, y = self.__pos
        if self.__get_world_content(x, y) != HC.SUIT:
            return self.__get_status_phase_2("Err: invalid move")

        self.__has_suit = True
        self.__update_world_content(x, y, HC.EMPTY)

        return self.__get_status_phase_2()

    def take_weapon(self):
        if self.__phase != 2:
            raise ValueError("Err: invalid phase")

        self.__add_history("Take Weapon")
        self.__phase2_penalties += 1
        self.__phase2_penalties += 5 * self.__seen_by_guard_num()
        x, y = self.__pos
        if self.__get_world_content(x, y) != HC.PIANO_WIRE:
            return self.__get_status_phase_2("Err: invalid move")

        self.__has_weapon = True
        self.__update_world_content(x, y, HC.EMPTY)

        return self.__get_status_phase_2()

    def put_on_suit(self):
        if self.__phase != 2:
            raise ValueError("Err: invalid phase")

        self.__add_history("Put on Suit")
        self.__phase2_penalties += 1
        self.__phase2_penalties += 5 * self.__seen_by_guard_num()

        if not self.__has_suit:
            return self.__get_status_phase_2("Err: invalid move")

        self.__suit_on = True
        self.__phase2_penalties += 100 * (
            self.__seen_by_guard_num() + self.__seen_by_civil_num()
        )
        return self.__get_status_phase_2()

    def __repr__(self) -> str:
        return f"HitmanReferee({self.__filename})"

    def __str__(self) -> str:
        return ASCII_ART

    def __compute_civil_count(self) -> int:
        count = 0
        for l in self.__world:
            for c in l:
                if (
                    c == HC.CIVIL_N
                    or c == HC.CIVIL_E
                    or c == HC.CIVIL_S
                    or c == HC.CIVIL_W
                ):
                    count += 1
        return count

    def __compute_guard_count(self) -> int:
        count = 0
        for l in self.__world:
            for c in l:
                if (
                    c == HC.GUARD_N
                    or c == HC.GUARD_E
                    or c == HC.GUARD_S
                    or c == HC.GUARD_W
                ):
                    count += 1
        return count

    def __compute_civils(
        self,
    ) -> Dict[Tuple[int, int], List[Tuple[Tuple[int, int], HC]]]:
        locations = {}
        for l_index, l in enumerate(self.__world):
            for c_index, c in enumerate(l):
                if (
                    c == HC.CIVIL_N
                    or c == HC.CIVIL_E
                    or c == HC.CIVIL_S
                    or c == HC.CIVIL_W
                ):
                    civil_x, civil_y = (c_index, self.__m - l_index - 1)
                    locations[(civil_x, civil_y)] = self.__get_civil_vision(
                        civil_x, civil_y
                    )
        return locations

    def __get_civil_offset(self, civil):
        if civil == HC.CIVIL_N:
            offset = 0, 1
        elif civil == HC.CIVIL_E:
            offset = 1, 0
        elif civil == HC.CIVIL_S:
            offset = 0, -1
        elif civil == HC.CIVIL_W:
            offset = -1, 0

        return offset

    def __get_civil_vision(self, civil_x, civil_y):
        civil = self.__get_world_content(civil_x, civil_y)
        offset_x, offset_y = self.__get_civil_offset(civil)
        pos = (civil_x, civil_y)
        x, y = pos
        vision = [(pos, self.__get_world_content(x, y))]

        pos = x + offset_x, y + offset_y
        x, y = pos
        if self.__n > x >= 0 and self.__m > y >= 0:
            vision.append((pos, self.__get_world_content(x, y)))
        return vision

    def __seen_by_civil_num(self) -> int:
        count = 0
        x, y = self.__pos
        for civil in self.__civils.keys():
            count += (
                1
                if len([0 for ((l, c), _) in self.__civils[civil] if l == x and c == y])
                > 0
                else 0
            )
        self.__is_in_civil_range = count > 0
        return count

    def __compute_guards(
        self,
    ) -> Dict[Tuple[int, int], List[Tuple[Tuple[int, int], HC]]]:
        locations = {}
        for l_index, l in enumerate(self.__world):
            for c_index, c in enumerate(l):
                if (
                    c == HC.GUARD_N
                    or c == HC.GUARD_E
                    or c == HC.GUARD_S
                    or c == HC.GUARD_W
                ):
                    guard_x, guard_y = (c_index, self.__m - l_index - 1)
                    locations[(guard_x, guard_y)] = self.__get_guard_vision(
                        guard_x, guard_y
                    )
        return locations

    def __get_guard_offset(self, guard):
        if guard == HC.GUARD_N:
            offset = 0, 1
        elif guard == HC.GUARD_E:
            offset = 1, 0
        elif guard == HC.GUARD_S:
            offset = 0, -1
        elif guard == HC.GUARD_W:
            offset = -1, 0

        return offset

    def __get_guard_vision(self, guard_x, guard_y, dist=2):
        guard = self.__get_world_content(guard_x, guard_y)
        offset_x, offset_y = self.__get_guard_offset(guard)
        pos = (guard_x, guard_y)
        x, y = pos
        vision = []
        for _ in range(0, dist):
            pos = x + offset_x, y + offset_y
            x, y = pos
            if x >= self.__n or y >= self.__m or x < 0 or y < 0:
                break
            vision.append((pos, self.__get_world_content(x, y)))
            if vision[-1][1] != HC.EMPTY:
                break
        return vision

    def __seen_by_guard_num(self) -> int:
        count = 0
        x, y = self.__pos
        if self.__get_world_content(x, y) not in [
            HC.CIVIL_N,
            HC.CIVIL_E,
            HC.CIVIL_S,
            HC.CIVIL_W,
        ]:
            for guard in self.__guards.keys():
                # Note : un garde ne peut pas voir au dela d'un objet
                # mais si Hitman est sur l'objet alors il voit Hitman
                count += (
                    1
                    if len(
                        [0 for ((l, c), _) in self.__guards[guard] if l == x and c == y]
                    )
                    > 0
                    else 0
                )
        self.__is_in_guard_range = count > 0
        return count

    def __add_history(self, action):
        if self.__phase == 1:
            self.__phase1_history.append(action)
        elif self.__phase == 2:
            self.__phase2_history.append(action)
        else:
            raise ValueError("Err: invalid phase")
