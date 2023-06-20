from itertools import combinations

def at_least_n(n, liste):
    """
    Renvoie les clauses permettant de modeliser au moins n elements de la liste
    """
    if n < 0 or n > len(liste):
        raise ValueError("n doit etre compris entre 0 et la taille de la liste")
    
    if n == 0:
        return []

    clauses = []
    for c in combinations(liste, len(liste) -(n-1)):
        clauses.append(list(c))
    return clauses

    
def at_most_n(n, liste):
    """
    Renvoie les clauses permettant de modeliser au plus n elements de la liste
    """
    if n < 0 or n > len(liste):
        raise ValueError("n doit etre compris entre 0 et la taille de la liste")
    
    if n == len(liste):
        return []

    clauses = []
    listeNeg = [-i for i in liste]
    for c in combinations(listeNeg, n+1):
        clauses.append(list(c))
    return clauses

    
def exactly_n(n, liste):
    """
    Renvoie les clauses permettant de modeliser exactement n elements de la liste
    """
    if liste == []:
        return []
    if n==0:
        return at_most_n(0, liste)
    if n==len(liste):
        return at_least_n(n, liste)
    return at_most_n(n, liste) + at_least_n(n, liste)

def unique(liste1, liste2):
    """
    Renvoie les clauses permettant de modeliser qu'on ne peut pas avoir
    liste1[i] et liste2[i] en meme temps
    """
    if len(liste1) != len(liste2):
        raise ValueError("Les deux listes doivent avoir la meme taille")
    
    clauses = []
    for i in range(len(liste1)):
        clauses.append([-liste1[i], -liste2[i]])
    return clauses