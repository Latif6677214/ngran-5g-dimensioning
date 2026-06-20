"""
Module : coverage_model.py
Dimensionnement par couverture (bilan de liaison / link budget)
pour le réseau NG-RAN 5G.

Référence cours : Chap.3 Réseaux Mobiles (Prof. I. Dioum)
- Bilan de planification cellulaire : slide 31
- Probabilité de coupure : slide 29
- Modèle 3GPP 38.901 : slide 39

Étapes du calcul (workflow slide 41) :
    1. Calculer le path loss admissible (bilan de liaison)
    2. Calculer la marge de masquage (Q^-1(p_out) * sigma)
    3. Soustraire la marge du path loss admissible
    4. En déduire le rayon de cellule via le modèle 3GPP
    5. En déduire le nombre de sites pour couvrir la zone
"""

import math
from models.propagation_3gpp import distance_max, GAMMA_LOS, GAMMA_NLOS_DEFAULT

# Valeurs par défaut (à justifier dans le rapport)
FC_GHZ_DEFAUT = 3.5          # Fréquence porteuse, bande 5G n78
PT_DBM_DEFAUT = 43.0         # Puissance d'émission BS (typique macro 5G)
GT_DBI_DEFAUT = 18.0         # Gain antenne émission (cohérent avec énoncé Partie 2)
GR_DBI_DEFAUT = 0.0          # Gain antenne réception (terminal mobile, antenne isotrope)
PERTES_DIVERSES_DB = 4.0     # Pertes câbles, connecteurs, pénétration bâtiment
SIGMA_DB_DEFAUT = 8.0        # Écart-type masquage log-normal (urbain macro, slide 27)


def q_inverse(p: float) -> float:
    """
    Approximation de l'inverse de la fonction Q (fonction de répartition
    complémentaire de la loi normale centrée réduite).
    Utilise l'inverse de la fonction d'erreur (erf) de la bibliothèque math.

    Q(x) = p  <=>  x = sqrt(2) * erfinv(1 - 2p)
    """
    if not (0 < p < 1):
        raise ValueError("La probabilité p doit être strictement entre 0 et 1")
    return math.sqrt(2) * erfinv(1 - 2 * p)


def erfinv(x: float) -> float:
    """
    Approximation numérique de la fonction erf inverse (Winitzki, 2008).
    Précision suffisante pour le dimensionnement radio (erreur < 1e-4).
    """
    a = 0.147
    ln1mx2 = math.log(1 - x * x)
    term1 = (2 / (math.pi * a)) + (ln1mx2 / 2)
    term2 = ln1mx2 / a
    return math.copysign(math.sqrt(math.sqrt(term1 ** 2 - term2) - term1), x)


def marge_masquage(p_out: float, sigma_db: float = SIGMA_DB_DEFAUT) -> float:
    """
    Calcule la marge de masquage Mψ nécessaire pour garantir
    une probabilité de coupure p_out donnée.

    Mψ = Q^-1(p_out) * sigma_dB

    Paramètres
    ----------
    p_out : probabilité de coupure cible (ex. 0.05 pour 5%)
    sigma_db : écart-type du masquage log-normal (dB)
    """
    return q_inverse(p_out) * sigma_db


def path_loss_admissible(pt_dbm: float = PT_DBM_DEFAUT,
                          gt_dbi: float = GT_DBI_DEFAUT,
                          gr_dbi: float = GR_DBI_DEFAUT,
                          pmin_dbm: float = -100.0,
                          pertes_db: float = PERTES_DIVERSES_DB) -> float:
    """
    Calcule le path loss maximal admissible par le bilan de liaison.

    L_admissible = Pt + Gt + Gr - Pmin - pertes

    Paramètres
    ----------
    pt_dbm : puissance d'émission (dBm)
    gt_dbi : gain antenne émission (dBi)
    gr_dbi : gain antenne réception (dBi)
    pmin_dbm : sensibilité du récepteur (dBm)
    pertes_db : pertes diverses (câbles, pénétration, etc.)
    """
    return pt_dbm + gt_dbi + gr_dbi - pmin_dbm - pertes_db


def rayon_cellule(fc_ghz: float = FC_GHZ_DEFAUT,
                   gamma: float = GAMMA_NLOS_DEFAULT,
                   p_out: float = 0.05,
                   sigma_db: float = SIGMA_DB_DEFAUT,
                   pt_dbm: float = PT_DBM_DEFAUT,
                   gt_dbi: float = GT_DBI_DEFAUT,
                   gr_dbi: float = GR_DBI_DEFAUT,
                   pmin_dbm: float = -100.0,
                   pertes_db: float = PERTES_DIVERSES_DB) -> dict:
    """
    Calcule le rayon de cellule maximal en tenant compte du bilan
    de liaison complet et de la marge de masquage.

    Retour
    ------
    dict contenant tous les résultats intermédiaires et le rayon final (m)
    """
    L_adm = path_loss_admissible(pt_dbm, gt_dbi, gr_dbi, pmin_dbm, pertes_db)
    M_psi = marge_masquage(p_out, sigma_db)
    L_disponible = L_adm - M_psi

    R = distance_max(fc_ghz, L_disponible, gamma, sigma_db=0.0)

    return {
        "path_loss_admissible_dB": L_adm,
        "marge_masquage_dB": M_psi,
        "path_loss_disponible_dB": L_disponible,
        "rayon_cellule_m": R,
    }


def nombre_sites_couverture(rayon_m: float, surface_zone_km2: float,
                             facteur_recouvrement: float = 2.6) -> dict:
    """
    Calcule le nombre de sites nécessaires pour couvrir une zone,
    à partir du rayon de cellule et d'un facteur de recouvrement
    (motif hexagonal trisectoriel typique en planification cellulaire).

    Surface_cellule = facteur_recouvrement * R^2  (approximation hexagonale)
    N_sites = Surface_zone / Surface_cellule

    Paramètres
    ----------
    rayon_m : rayon de cellule (m)
    surface_zone_km2 : surface totale à couvrir (km²)
    facteur_recouvrement : facteur géométrique (2.6 = hexagone trisectoriel standard)
    """
    rayon_km = rayon_m / 1000
    surface_cellule_km2 = facteur_recouvrement * (rayon_km ** 2)
    n_sites = surface_zone_km2 / surface_cellule_km2

    return {
        "surface_cellule_km2": surface_cellule_km2,
        "nombre_sites": math.ceil(n_sites),
        "nombre_sites_exact": n_sites,
    }


# Test rapide du module si exécuté directement
if __name__ == "__main__":
    print("=== Dimensionnement par couverture (NLOS, urbain) ===\n")

    resultats = rayon_cellule(
        fc_ghz=3.5,
        gamma=GAMMA_NLOS_DEFAULT,
        p_out=0.05,
        sigma_db=8.0,
        pt_dbm=43.0,
        gt_dbi=18.0,
        gr_dbi=0.0,
        pmin_dbm=-100.0,
        pertes_db=4.0,
    )

    for cle, valeur in resultats.items():
        print(f"{cle} : {valeur:.2f}")

    print()

    sites = nombre_sites_couverture(
        rayon_m=resultats["rayon_cellule_m"],
        surface_zone_km2=10.0,  # exemple : 10 km² (zone urbaine type)
    )

    for cle, valeur in sites.items():
        print(f"{cle} : {valeur}")