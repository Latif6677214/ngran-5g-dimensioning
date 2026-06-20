"""
Module : propagation_3gpp.py
Implémentation du modèle de path loss 3GPP TR 38.901
pour le dimensionnement NG-RAN 5G.

Référence cours : Chap.3 Réseaux Mobiles (Prof. I. Dioum), slide 39
Référence externe : 3GPP TR 38.901 v16.1.0 (2019)

Formule générale :
    L[dB] = 32.4 + 20*log10(fc_GHz) + 10*gamma*log10(d_m) + X_sigma

avec :
    gamma ≈ 2      en LOS (Line-Of-Sight)
    gamma ∈ [3, 4]  en NLOS (Non-Line-Of-Sight)
    sigma ≈ 4 à 8 dB (masquage log-normal)
"""

import math

# Plages de validité du modèle 3GPP 38.901 (usage indicatif)
FREQ_MIN_GHZ = 0.5
FREQ_MAX_GHZ = 100.0
DIST_MIN_M = 1.0
DIST_MAX_M = 10000.0

# Valeurs par défaut de l'exposant de path loss (gamma)
GAMMA_LOS = 2.0
GAMMA_NLOS_MIN = 3.0
GAMMA_NLOS_MAX = 4.0
GAMMA_NLOS_DEFAULT = 3.5

# Écart-type du masquage log-normal (sigma), valeurs typiques 3GPP
SIGMA_LOS_DB = 4.0
SIGMA_NLOS_DB = 8.0


def valider_parametres(fc_ghz: float, d_m: float) -> None:
    """
    Vérifie que la fréquence et la distance sont dans les plages
    de validité du modèle 3GPP 38.901.
    Lève une ValueError si les paramètres sont hors plage.
    """
    if not (FREQ_MIN_GHZ <= fc_ghz <= FREQ_MAX_GHZ):
        raise ValueError(
            f"Fréquence {fc_ghz} GHz hors plage de validité "
            f"[{FREQ_MIN_GHZ}, {FREQ_MAX_GHZ}] GHz"
        )
    if not (DIST_MIN_M <= d_m <= DIST_MAX_M):
        raise ValueError(
            f"Distance {d_m} m hors plage de validité "
            f"[{DIST_MIN_M}, {DIST_MAX_M}] m"
        )


def path_loss_3gpp(fc_ghz: float, d_m: float, gamma: float,
                    sigma_db: float = 0.0) -> float:
    """
    Calcule le path loss selon le modèle 3GPP TR 38.901.

    Paramètres
    ----------
    fc_ghz : fréquence porteuse en GHz
    d_m    : distance émetteur-récepteur en mètres
    gamma  : exposant de path loss (2 en LOS, 3-4 en NLOS)
    sigma_db : écart-type du masquage log-normal en dB (0 = non inclus)

    Retour
    ------
    Path loss L en dB (float)
    """
    valider_parametres(fc_ghz, d_m)

    L = 32.4 + 20 * math.log10(fc_ghz) + 10 * gamma * math.log10(d_m) + sigma_db
    return L


def path_loss_los(fc_ghz: float, d_m: float, sigma_db: float = SIGMA_LOS_DB) -> float:
    """
    Path loss en condition LOS (Line-Of-Sight), gamma = 2.
    """
    return path_loss_3gpp(fc_ghz, d_m, gamma=GAMMA_LOS, sigma_db=sigma_db)


def path_loss_nlos(fc_ghz: float, d_m: float, gamma: float = GAMMA_NLOS_DEFAULT,
                    sigma_db: float = SIGMA_NLOS_DB) -> float:
    """
    Path loss en condition NLOS (Non-Line-Of-Sight), gamma entre 3 et 4.
    """
    if not (GAMMA_NLOS_MIN <= gamma <= GAMMA_NLOS_MAX):
        raise ValueError(
            f"Gamma NLOS {gamma} hors plage typique "
            f"[{GAMMA_NLOS_MIN}, {GAMMA_NLOS_MAX}]"
        )
    return path_loss_3gpp(fc_ghz, d_m, gamma=gamma, sigma_db=sigma_db)


def distance_max(fc_ghz: float, path_loss_admissible_db: float,
                  gamma: float, sigma_db: float = 0.0) -> float:
    """
    Calcule la distance maximale (rayon de cellule) pour un path loss
    admissible donné, en inversant la formule 3GPP 38.901.

    L = 32.4 + 20*log10(fc) + 10*gamma*log10(d) + sigma
    => d = 10 ** ((L - 32.4 - 20*log10(fc) - sigma) / (10*gamma))

    Paramètres
    ----------
    fc_ghz : fréquence porteuse en GHz
    path_loss_admissible_db : path loss maximal toléré (bilan de liaison)
    gamma  : exposant de path loss
    sigma_db : marge de masquage à soustraire (dB)

    Retour
    ------
    Distance maximale d en mètres (float)
    """
    exposant = (path_loss_admissible_db - 32.4 - 20 * math.log10(fc_ghz) - sigma_db) / (10 * gamma)
    d_m = 10 ** exposant
    return d_m


# Test rapide du module si exécuté directement
if __name__ == "__main__":
    fc = 3.5       # GHz (bande 5G typique n78)
    d = 200        # mètres

    pl_los = path_loss_los(fc, d)
    pl_nlos = path_loss_nlos(fc, d)

    print(f"Path loss LOS  à {d} m, {fc} GHz : {pl_los:.2f} dB")
    print(f"Path loss NLOS à {d} m, {fc} GHz : {pl_nlos:.2f} dB")

    # Exemple : distance max pour un bilan de liaison de 140 dB
    bilan = 140
    R_los = distance_max(fc, bilan, gamma=GAMMA_LOS, sigma_db=SIGMA_LOS_DB)
    print(f"Rayon de cellule max (LOS, bilan {bilan} dB) : {R_los:.1f} m")