from typing import List, Tuple
import subprocess
import os

def clauses_to_dimacs(clauses, nb_var):
    nb_clause = len(clauses)
    chaine = f"p cnf {nb_var} {nb_clause}\n"
    for clause in clauses:
        chaine += " ".join([str(i) for i in clause]) + " 0\n"
    return chaine

def write_dimacs_file(dimacs: str, filename: str):
    with open(filename, "w", newline="") as cnf:
        cnf.write(dimacs)

def exec_gophersat(
    filename: str, cmd: str = "./gophersat", encoding: str = "utf8"
) -> Tuple[bool, List[int]]:
    result = subprocess.run(
        [cmd, filename], capture_output=True, check=True, encoding=encoding
    )
    string = str(result.stdout)
    lines = string.splitlines()

    if lines[1] != "s SATISFIABLE":
        return False, []

    model = lines[2][2:-2].split(" ")

    return True, [int(x) for x in model]


def solve(clauses, nb_var):
    file_directory = os.path.dirname(os.path.realpath(__file__))
    os.chdir(file_directory)
    dimacs = clauses_to_dimacs(clauses, nb_var)
    write_dimacs_file(dimacs, "hitman.cnf")

    satisfiable, _ = exec_gophersat("hitman.cnf")

    return satisfiable