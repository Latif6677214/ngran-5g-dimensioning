"""
Module : gui/app.py
Interface graphique Tkinter pour l'application de dimensionnement NG-RAN 5G.

Structure : 3 onglets
    1. Paramètres : saisie des paramètres radio, propagation et trafic
    2. Résultats  : bilan de liaison, rayon de cellule, trafic, nb sites
    3. Graphes    : visualisation (rayon vs fréquence, comparaison sites)

Référence cours : Chap.3 Réseaux Mobiles (Prof. I. Dioum)
"""

import tkinter as tk
from tkinter import ttk

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from core.coverage_model import rayon_cellule, nombre_sites_couverture
from core.capacity_model import (
    nombre_sites_capacite,
    DENSITE_ABONNES_DEFAUT,
    DEBIT_MOYEN_MBPS_DEFAUT,
    EFFICACITE_SPECTRALE_DEFAUT,
    FACTEUR_CHARGE_DEFAUT,
    TAUX_ACTIVITE_DEFAUT,
    NB_SECTEURS_DEFAUT,
)
from models.propagation_3gpp import GAMMA_NLOS_MIN, GAMMA_NLOS_MAX, GAMMA_NLOS_DEFAULT


# ----------------------------------------------------------------------
# Palette et style
# ----------------------------------------------------------------------
COULEUR_FOND = "#1e2530"
COULEUR_PANNEAU = "#262e3d"
COULEUR_ACCENT = "#4fa3e3"
COULEUR_TEXTE = "#e8edf4"
COULEUR_TEXTE_SECONDAIRE = "#9aa7ba"
COULEUR_OK = "#4fd18b"
COULEUR_ALERTE = "#e3a64f"
POLICE_TITRE = ("Segoe UI", 14, "bold")
POLICE_LABEL = ("Segoe UI", 10)
POLICE_VALEUR = ("Segoe UI", 12, "bold")


class App(tk.Tk):
    """Fenêtre principale de l'application de dimensionnement NG-RAN 5G."""

    def __init__(self):
        super().__init__()
        self.title("Dimensionnement NG-RAN 5G — Outil de planification radio")
        self.geometry("1080x720")
        self.configure(bg=COULEUR_FOND)
        self.minsize(900, 600)

        self._configurer_style()
        self._construire_layout()

    # ------------------------------------------------------------------
    def _configurer_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("TNotebook", background=COULEUR_FOND, borderwidth=0)
        style.configure("TNotebook.Tab", background=COULEUR_PANNEAU,
                         foreground=COULEUR_TEXTE_SECONDAIRE,
                         padding=(16, 10), font=("Segoe UI", 10, "bold"))
        style.map("TNotebook.Tab",
                  background=[("selected", COULEUR_ACCENT)],
                  foreground=[("selected", "#0e1420")])

        style.configure("TFrame", background=COULEUR_FOND)
        style.configure("Panel.TFrame", background=COULEUR_PANNEAU)
        style.configure("TLabel", background=COULEUR_FOND, foreground=COULEUR_TEXTE,
                         font=POLICE_LABEL)
        style.configure("Panel.TLabel", background=COULEUR_PANNEAU, foreground=COULEUR_TEXTE,
                         font=POLICE_LABEL)
        style.configure("Titre.TLabel", background=COULEUR_FOND, foreground=COULEUR_TEXTE,
                         font=POLICE_TITRE)
        style.configure("Valeur.TLabel", background=COULEUR_PANNEAU, foreground=COULEUR_ACCENT,
                         font=POLICE_VALEUR)
        style.configure("Secondaire.TLabel", background=COULEUR_PANNEAU,
                         foreground=COULEUR_TEXTE_SECONDAIRE, font=("Segoe UI", 9))

        style.configure("TEntry", fieldbackground="#ffffff", padding=4)
        style.configure("Accent.TButton", background=COULEUR_ACCENT, foreground="#0e1420",
                         font=("Segoe UI", 11, "bold"), padding=(14, 10), borderwidth=0)
        style.map("Accent.TButton", background=[("active", "#6cb6ec")])

    # ------------------------------------------------------------------
    def _construire_layout(self):
        entete = ttk.Frame(self, style="TFrame")
        entete.pack(fill="x", padx=24, pady=(20, 10))
        ttk.Label(entete, text="Dimensionnement NG-RAN 5G", style="Titre.TLabel").pack(anchor="w")
        ttk.Label(entete, text="Couverture · Capacité · Bande n78 (3.5 GHz) — environnement urbain",
                   style="TLabel").pack(anchor="w")

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        self.onglet_parametres = ttk.Frame(self.notebook, style="TFrame")
        self.onglet_resultats = ttk.Frame(self.notebook, style="TFrame")
        self.onglet_graphes = ttk.Frame(self.notebook, style="TFrame")

        self.notebook.add(self.onglet_parametres, text="  Paramètres  ")
        self.notebook.add(self.onglet_resultats, text="  Résultats  ")
        self.notebook.add(self.onglet_graphes, text="  Graphes  ")

        self._construire_onglet_parametres()
        self._construire_onglet_resultats()
        self._construire_onglet_graphes()

    # ------------------------------------------------------------------
    def _champ(self, parent, label, valeur_defaut, ligne, colonne=0, largeur=12):
        """Crée une paire (label, Entry) et retourne la variable Tk associée."""
        cadre = ttk.Frame(parent, style="Panel.TFrame")
        cadre.grid(row=ligne, column=colonne, sticky="ew", padx=10, pady=6)

        ttk.Label(cadre, text=label, style="Panel.TLabel").pack(anchor="w")
        var = tk.StringVar(value=str(valeur_defaut))
        entry = ttk.Entry(cadre, textvariable=var, width=largeur)
        entry.pack(anchor="w", pady=(2, 0))
        return var

    def _construire_onglet_parametres(self):
        conteneur = ttk.Frame(self.onglet_parametres, style="TFrame")
        conteneur.pack(fill="both", expand=True, pady=10)

        # --- Panneau Radio / Propagation (coverage_model) ---
        panneau_radio = ttk.Frame(conteneur, style="Panel.TFrame")
        panneau_radio.pack(fill="x", pady=(0, 12))
        ttk.Label(panneau_radio, text="Paramètres radio & propagation",
                   style="Panel.TLabel", font=("Segoe UI", 11, "bold")).grid(
            row=0, column=0, columnspan=4, sticky="w", padx=10, pady=(10, 4))

        self.var_fc = self._champ(panneau_radio, "Fréquence porteuse (GHz)", 3.5, 1, 0)
        self.var_pt = self._champ(panneau_radio, "Puissance Tx BS (dBm)", 43.0, 1, 1)
        self.var_gt = self._champ(panneau_radio, "Gain antenne BS (dBi)", 18.0, 1, 2)
        self.var_gr = self._champ(panneau_radio, "Gain antenne UE (dBi)", 0.0, 1, 3)

        self.var_pmin = self._champ(panneau_radio, "Sensibilité récepteur (dBm)", -100.0, 2, 0)
        self.var_pertes = self._champ(panneau_radio, "Pertes diverses (dB)", 4.0, 2, 1)
        self.var_sigma = self._champ(panneau_radio, "Écart-type masquage σ (dB)", 8.0, 2, 2)
        self.var_pout = self._champ(panneau_radio, "Proba. coupure cible (0-1)", 0.05, 2, 3)

        self.var_gamma = self._champ(panneau_radio,
                                      f"Exposant γ NLOS [{GAMMA_NLOS_MIN}-{GAMMA_NLOS_MAX}]",
                                      GAMMA_NLOS_DEFAULT, 3, 0)
        self.var_surface = self._champ(panneau_radio, "Surface de la zone (km²)", 10.0, 3, 1)

        for i in range(4):
            panneau_radio.grid_columnconfigure(i, weight=1)

        # --- Panneau Trafic / Capacité (capacity_model) ---
        panneau_trafic = ttk.Frame(conteneur, style="Panel.TFrame")
        panneau_trafic.pack(fill="x", pady=(0, 12))
        ttk.Label(panneau_trafic, text="Paramètres de trafic & capacité",
                   style="Panel.TLabel", font=("Segoe UI", 11, "bold")).grid(
            row=0, column=0, columnspan=4, sticky="w", padx=10, pady=(10, 4))

        self.var_densite = self._champ(panneau_trafic, "Densité abonnés (/km²)", DENSITE_ABONNES_DEFAUT, 1, 0)
        self.var_debit_moyen = self._champ(panneau_trafic, "Débit moyen/abonné actif (Mbps)", DEBIT_MOYEN_MBPS_DEFAUT, 1, 1)
        self.var_taux_activite = self._champ(panneau_trafic, "Taux d'activité (0-1)", TAUX_ACTIVITE_DEFAUT, 1, 2)
        self.var_bw = self._champ(panneau_trafic, "Bande passante NR (MHz)", 100.0, 1, 3)

        self.var_eff_spec = self._champ(panneau_trafic, "Efficacité spectrale (bps/Hz)", EFFICACITE_SPECTRALE_DEFAUT, 2, 0)
        self.var_charge = self._champ(panneau_trafic, "Facteur de charge cellule (0-1)", FACTEUR_CHARGE_DEFAUT, 2, 1)
        self.var_secteurs = self._champ(panneau_trafic, "Nb secteurs / site", NB_SECTEURS_DEFAUT, 2, 2)

        for i in range(4):
            panneau_trafic.grid_columnconfigure(i, weight=1)

        # --- Bouton calcul ---
        bouton = ttk.Button(conteneur, text="Lancer le dimensionnement",
                             style="Accent.TButton", command=self._lancer_calcul)
        bouton.pack(pady=10)

        self.label_erreur = ttk.Label(conteneur, text="", style="TLabel", foreground=COULEUR_ALERTE)
        self.label_erreur.pack()

    # ------------------------------------------------------------------
    def _lire_floats(self):
        """Lit et convertit tous les champs en float/int, lève ValueError sinon."""
        return {
            "fc_ghz": float(self.var_fc.get()),
            "pt_dbm": float(self.var_pt.get()),
            "gt_dbi": float(self.var_gt.get()),
            "gr_dbi": float(self.var_gr.get()),
            "pmin_dbm": float(self.var_pmin.get()),
            "pertes_db": float(self.var_pertes.get()),
            "sigma_db": float(self.var_sigma.get()),
            "p_out": float(self.var_pout.get()),
            "gamma": float(self.var_gamma.get()),
            "surface_km2": float(self.var_surface.get()),
            "densite": float(self.var_densite.get()),
            "debit_moyen": float(self.var_debit_moyen.get()),
            "taux_activite": float(self.var_taux_activite.get()),
            "bw_mhz": float(self.var_bw.get()),
            "eff_spec": float(self.var_eff_spec.get()),
            "charge": float(self.var_charge.get()),
            "nb_secteurs": int(float(self.var_secteurs.get())),
        }

    def _lancer_calcul(self):
        self.label_erreur.config(text="")
        try:
            p = self._lire_floats()
        except ValueError:
            self.label_erreur.config(text="⚠ Certains champs ne sont pas des nombres valides.")
            return

        try:
            # --- Étape 1 : Couverture (coverage_model) ---
            res_couverture = rayon_cellule(
                fc_ghz=p["fc_ghz"], gamma=p["gamma"], p_out=p["p_out"],
                sigma_db=p["sigma_db"], pt_dbm=p["pt_dbm"], gt_dbi=p["gt_dbi"],
                gr_dbi=p["gr_dbi"], pmin_dbm=p["pmin_dbm"], pertes_db=p["pertes_db"],
            )
            res_sites_couv = nombre_sites_couverture(
                rayon_m=res_couverture["rayon_cellule_m"],
                surface_zone_km2=p["surface_km2"],
            )

            # --- Étape 2 : Capacité (capacity_model) ---
            res_capacite = nombre_sites_capacite(
                densite_abonnes_km2=p["densite"],
                debit_moyen_mbps=p["debit_moyen"],
                surface_zone_km2=p["surface_km2"],
                bande_passante_mhz=p["bw_mhz"],
                efficacite_spectrale=p["eff_spec"],
                facteur_charge=p["charge"],
                nb_secteurs=p["nb_secteurs"],
                taux_activite=p["taux_activite"],
            )

            # --- Étape 3 : Dimensionnement final ---
            n_couv = res_sites_couv["nombre_sites"]
            n_cap = res_capacite["nombre_sites"]
            n_final = max(n_couv, n_cap)
            critere = "Capacité" if n_cap >= n_couv else "Couverture"

        except ValueError as e:
            self.label_erreur.config(text=f"⚠ {e}")
            return
        except ZeroDivisionError:
            self.label_erreur.config(text="⚠ Division par zéro : vérifiez les paramètres saisis.")
            return

        self._dernier_resultat = {
            "params": p,
            "couverture": res_couverture,
            "sites_couverture": res_sites_couv,
            "capacite": res_capacite,
            "n_final": n_final,
            "critere": critere,
        }

        self._afficher_resultats()
        self._tracer_graphes()
        self.notebook.select(self.onglet_resultats)

    # ------------------------------------------------------------------
    def _carte_resultat(self, parent, titre, valeur, sous_texte="", ligne=0, colonne=0):
        cadre = ttk.Frame(parent, style="Panel.TFrame")
        cadre.grid(row=ligne, column=colonne, sticky="nsew", padx=8, pady=8)
        ttk.Label(cadre, text=titre, style="Secondaire.TLabel").pack(anchor="w", padx=14, pady=(12, 0))
        ttk.Label(cadre, text=valeur, style="Valeur.TLabel").pack(anchor="w", padx=14, pady=(2, 0))
        if sous_texte:
            ttk.Label(cadre, text=sous_texte, style="Secondaire.TLabel").pack(
                anchor="w", padx=14, pady=(0, 12))
        else:
            ttk.Label(cadre, text="", style="Secondaire.TLabel").pack(pady=(0, 6))
        return cadre

    def _construire_onglet_resultats(self):
        self.cadre_resultats = ttk.Frame(self.onglet_resultats, style="TFrame")
        self.cadre_resultats.pack(fill="both", expand=True, pady=10)

        ttk.Label(self.cadre_resultats,
                   text="Lancez un calcul depuis l'onglet « Paramètres » pour voir les résultats ici.",
                   style="TLabel").pack(pady=40)

    def _afficher_resultats(self):
        for widget in self.cadre_resultats.winfo_children():
            widget.destroy()

        r = self._dernier_resultat
        cov, sc, cap = r["couverture"], r["sites_couverture"], r["capacite"]

        grille = ttk.Frame(self.cadre_resultats, style="TFrame")
        grille.pack(fill="x")
        for i in range(3):
            grille.grid_columnconfigure(i, weight=1)

        self._carte_resultat(grille, "RAYON DE CELLULE",
                              f"{cov['rayon_cellule_m']:.0f} m",
                              f"PL disponible : {cov['path_loss_disponible_dB']:.1f} dB",
                              0, 0)
        self._carte_resultat(grille, "SITES — COUVERTURE",
                              f"{sc['nombre_sites']}",
                              f"Surface/site : {sc['surface_cellule_km2']:.2f} km²",
                              0, 1)
        self._carte_resultat(grille, "SITES — CAPACITÉ",
                              f"{cap['nombre_sites']}",
                              f"Trafic total : {cap['debit_total_requis_Mbps']:.0f} Mbps",
                              0, 2)

        cadre_final = ttk.Frame(self.cadre_resultats, style="Panel.TFrame")
        cadre_final.pack(fill="x", padx=8, pady=(4, 16))
        ttk.Label(cadre_final, text="NOMBRE DE SITES FINAL", style="Secondaire.TLabel").pack(
            anchor="w", padx=16, pady=(14, 0))
        ttk.Label(cadre_final, text=f"{r['n_final']} sites",
                   style="Panel.TLabel", font=("Segoe UI", 22, "bold"),
                   foreground=COULEUR_OK).pack(anchor="w", padx=16)
        ttk.Label(cadre_final,
                   text=f"Critère dimensionnant : {r['critere']}  "
                        f"(max entre {sc['nombre_sites']} sites couverture et {cap['nombre_sites']} sites capacité)",
                   style="Secondaire.TLabel").pack(anchor="w", padx=16, pady=(0, 14))

        detail = ttk.Frame(self.cadre_resultats, style="Panel.TFrame")
        detail.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        ttk.Label(detail, text="Détail des calculs intermédiaires",
                   style="Panel.TLabel", font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=16, pady=(12, 6))

        lignes = [
            ("Path loss admissible (bilan de liaison)", f"{cov['path_loss_admissible_dB']:.2f} dB"),
            ("Marge de masquage (log-normale)", f"{cov['marge_masquage_dB']:.2f} dB"),
            ("Path loss disponible (après marge)", f"{cov['path_loss_disponible_dB']:.2f} dB"),
            ("Débit total requis (trafic)", f"{cap['debit_total_requis_Mbps']:.1f} Mbps"),
            ("Débit max par site", f"{cap['debit_max_par_site_Mbps']:.1f} Mbps"),
        ]
        for label, valeur in lignes:
            ligne_w = ttk.Frame(detail, style="Panel.TFrame")
            ligne_w.pack(fill="x", padx=16, pady=2)
            ttk.Label(ligne_w, text=label, style="Panel.TLabel").pack(side="left")
            ttk.Label(ligne_w, text=valeur, style="Panel.TLabel",
                       foreground=COULEUR_ACCENT).pack(side="right")
        ttk.Label(detail, text="", style="Panel.TLabel").pack(pady=4)

    # ------------------------------------------------------------------
    def _construire_onglet_graphes(self):
        self.cadre_graphes = ttk.Frame(self.onglet_graphes, style="TFrame")
        self.cadre_graphes.pack(fill="both", expand=True, pady=10)

        ttk.Label(self.cadre_graphes,
                   text="Lancez un calcul depuis l'onglet « Paramètres » pour voir les graphes ici.",
                   style="TLabel").pack(pady=40)

    def _tracer_graphes(self):
        for widget in self.cadre_graphes.winfo_children():
            widget.destroy()

        r = self._dernier_resultat
        p = r["params"]

        fig = Figure(figsize=(10, 4.2), dpi=100, facecolor=COULEUR_FOND)

        # --- Graphe 1 : Rayon de cellule vs fréquence ---
        ax1 = fig.add_subplot(1, 2, 1)
        ax1.set_facecolor(COULEUR_PANNEAU)
        freqs = [f / 10 for f in range(5, 61, 2)]  # 0.5 à 6.0 GHz
        rayons = []
        for f in freqs:
            res = rayon_cellule(fc_ghz=f, gamma=p["gamma"], p_out=p["p_out"],
                                 sigma_db=p["sigma_db"], pt_dbm=p["pt_dbm"],
                                 gt_dbi=p["gt_dbi"], gr_dbi=p["gr_dbi"],
                                 pmin_dbm=p["pmin_dbm"], pertes_db=p["pertes_db"])
            rayons.append(res["rayon_cellule_m"])
        ax1.plot(freqs, rayons, color=COULEUR_ACCENT, linewidth=2)
        ax1.axvline(p["fc_ghz"], color=COULEUR_OK, linestyle="--", linewidth=1,
                    label=f"Fréquence choisie ({p['fc_ghz']} GHz)")
        ax1.set_xlabel("Fréquence (GHz)", color=COULEUR_TEXTE)
        ax1.set_ylabel("Rayon de cellule (m)", color=COULEUR_TEXTE)
        ax1.set_title("Rayon de cellule vs fréquence", color=COULEUR_TEXTE, fontsize=11)
        ax1.tick_params(colors=COULEUR_TEXTE_SECONDAIRE)
        ax1.legend(facecolor=COULEUR_PANNEAU, labelcolor=COULEUR_TEXTE, fontsize=8)
        for spine in ax1.spines.values():
            spine.set_color(COULEUR_TEXTE_SECONDAIRE)

        # --- Graphe 2 : Comparaison nb sites couverture vs capacité ---
        ax2 = fig.add_subplot(1, 2, 2)
        ax2.set_facecolor(COULEUR_PANNEAU)
        categories = ["Couverture", "Capacité", "Final (retenu)"]
        valeurs = [r["sites_couverture"]["nombre_sites"], r["capacite"]["nombre_sites"], r["n_final"]]
        couleurs = [COULEUR_TEXTE_SECONDAIRE, COULEUR_TEXTE_SECONDAIRE, COULEUR_OK]
        barres = ax2.bar(categories, valeurs, color=couleurs)
        for barre, val in zip(barres, valeurs):
            ax2.text(barre.get_x() + barre.get_width() / 2, val + 0.5, str(val),
                      ha="center", color=COULEUR_TEXTE, fontsize=10, fontweight="bold")
        ax2.set_ylabel("Nombre de sites", color=COULEUR_TEXTE)
        ax2.set_title("Nombre de sites par critère", color=COULEUR_TEXTE, fontsize=11)
        ax2.tick_params(colors=COULEUR_TEXTE_SECONDAIRE)
        for spine in ax2.spines.values():
            spine.set_color(COULEUR_TEXTE_SECONDAIRE)

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.cadre_graphes)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)


def lancer_application():
    """Point d'entrée pour lancer l'interface graphique."""
    app = App()
    app.mainloop()