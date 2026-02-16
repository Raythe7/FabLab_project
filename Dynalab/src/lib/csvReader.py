
import csv
from pathlib import Path

chemin = Path(__file__).parent / "mesureTemps.csv"

def getMinAire(tab,ligne):
    return tab[ligne][1]

def getMaxAire(tab,ligne):
    return tab[ligne][2]

def getMinLong(tab,ligne):
    return tab[ligne][3]

def getMaxLong(tab,ligne):
    return tab[ligne][4]

def readAreaCSV():
    with open(chemin,newline='') as f: #Ouverture du fichier CSV
        tableau=[]
        file=csv.reader(f) #chargement des lignes du fichier csv
        for ligne in file: #Pour chaque ligne...
            #print(ligne, end='\n') #...affichage de la ligne dans la console ...
            tableau.append(ligne) #...on ajoute la ligne dans la liste ...

        return [float(getMinAire(tableau,1)),float(getMaxAire(tableau,1))]
    
def readLengthCSV():
    with open(chemin,newline='') as f: #Ouverture du fichier CSV
        tableau=[]
        file=csv.reader(f) #chargement des lignes du fichier csv
        for ligne in file: #Pour chaque ligne...
            #print(ligne, end='\n') #...affichage de la ligne dans la console ...
            tableau.append(ligne) #...on ajoute la ligne dans la liste ...

        return [float(getMinLong(tableau,1)),float(getMaxLong(tableau,1))]