"""
Module : capacity_model.py
Dimensionnement par capacité (trafic) pour le réseau NG-RAN 5G.

Référence cours : Chap.3 Réseaux Mobiles (Prof. I. Dioum), workflow slide 41

Principe :
    1. Estimer le débit total demandé dans la zone, en tenant compte
       du taux d'abonnés réellement actifs simultanément (heure de pointe)
    2. Estimer le débit max qu'une cellule peut fournir
       (bande passante x efficacité spectrale x facteur de charge)
    3. En déduire le nombre de sites nécessaires pour absorber le trafic
"""

import math

# Valeurs par défaut (à justifier dans le rapport)
DENSITE_ABONNES_DEFAUT = 2000      # abonnés / km² (zone urbaine dense)
DEBIT_MOYEN_MBPS_DEFAUT = 20.0     # Mbps par abonné actif en heure de pointe (usage data 5G eMBB)
BANDE_PASSANTE_MHZ_DEFAUT = 100.0  # MHz alloués (canal 5G NR typique, bande n78)
EFFICACITE_SPECTRALE_DEFAUT = 4.0  # bps/Hz (moyenne réaliste DL, 5G NR avec MIMO)
FACTEUR_CHARGE_DEFAUT = 0.7        # taux de charge cellule (70%, marge réseau)
NB_SECTEURS_DEFAUT = 3             # secteurs par site (tri-sectoriel, cohérent Partie 2)
TAUX_ACTIVITE_DEFAUT = 0.03        # 3% des abonnés actifs simultanément en heure de pointe


def debit_total_requis(densite_abonnes_km2: float,
                        debit_moyen_mbps: float,
                        surface_zone_km2: float,
                        taux_activite: float = TAUX_ACTIVITE_DEFAUT) -> float:
    """
    Calcule le débit total demandé dans la zone (Mbps), en tenant compte
    du taux d'abonnés réellement actifs simultanément (heure de pointe).

    Débit_total = densité_abonnés x surface x taux_activité x débit_moyen_par_abonné_actif
    """
    nb_abonnes = densite_abonnes_km2 * surface_zone_km2
    nb_abonnes_actifs = nb_abonnes * taux_activite
    debit_total_mbps = nb_abonnes_actifs * debit_moyen_mbps
    return debit_total_mbps


def debit_max_cellule(bande_passante_mhz: float,
                       efficacite_spectrale: float,
                       facteur_charge: float = FACTEUR_CHARGE_DEFAUT,
                       nb_secteurs: int = NB_SECTEURS_DEFAUT) -> float:
    """
    Calcule le débit maximal qu'un site (tous secteurs confondus)
    peut fournir (Mbps).

    Débit_secteur = bande_passante x efficacité_spectrale x facteur_charge
    Débit_site = Débit_secteur x nb_secteurs
    """
    debit_secteur_mbps = bande_passante_mhz * efficacite_spectrale * facteur_charge
    debit_site_mbps = debit_secteur_mbps * nb_secteurs
    return debit_site_mbps


def nombre_sites_capacite(densite_abonnes_km2: float = DENSITE_ABONNES_DEFAUT,
                           debit_moyen_mbps: float = DEBIT_MOYEN_MBPS_DEFAUT,
                           surface_zone_km2: float = 10.0,
                           bande_passante_mhz: float = BANDE_PASSANTE_MHZ_DEFAUT,
                           efficacite_spectrale: float = EFFICACITE_SPECTRALE_DEFAUT,
                           facteur_charge: float = FACTEUR_CHARGE_DEFAUT,
                           nb_secteurs: int = NB_SECTEURS_DEFAUT,
                           taux_activite: float = TAUX_ACTIVITE_DEFAUT) -> dict:
    """
    Calcule le nombre de sites nécessaires pour absorber le trafic
    prévu dans la zone cible.

    Retour
    ------
    dict contenant tous les résultats intermédiaires et le nombre de sites
    """
    debit_total_mbps = debit_total_requis(densite_abonnes_km2, debit_moyen_mbps,
                                            surface_zone_km2, taux_activite)
    debit_site_mbps = debit_max_cellule(bande_passante_mhz, efficacite_spectrale,
                                          facteur_charge, nb_secteurs)

    n_sites = debit_total_mbps / debit_site_mbps

    return {
        "debit_total_requis_Mbps": debit_total_mbps,
        "debit_max_par_site_Mbps": debit_site_mbps,
        "nombre_sites": math.ceil(n_sites),
        "nombre_sites_exact": n_sites,
    }


# Test rapide du module si exécuté directement
if __name__ == "__main__":
    print("=== Dimensionnement par capacité (trafic) ===\n")

    resultats = nombre_sites_capacite(
        densite_abonnes_km2=2000,
        debit_moyen_mbps=20.0,
        surface_zone_km2=10.0,
        bande_passante_mhz=100.0,
        efficacite_spectrale=4.0,
        facteur_charge=0.7,
        nb_secteurs=3,
        taux_activite=0.03,
    )

    for cle, valeur in resultats.items():
        print(f"{cle} : {valeur}")