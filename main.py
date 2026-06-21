"""
Module : main.py
Point d'entrée de l'application de dimensionnement NG-RAN 5G.

Lance l'interface graphique Tkinter (gui/app.py), qui orchestre
les modules de calcul :
    - models/propagation_3gpp.py : modèle de path loss 3GPP TR 38.901
    - core/coverage_model.py     : dimensionnement par couverture
    - core/capacity_model.py     : dimensionnement par capacité

Usage :
    python3 main.py
"""

from gui.app import lancer_application


if __name__ == "__main__":
    lancer_application()