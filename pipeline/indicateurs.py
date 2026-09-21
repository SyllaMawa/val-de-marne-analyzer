import pandas as pd

DVF_PATH = "../data/dvf/ValeursFoncieres-2025.txt"
PARCELLES_PATH = "../data/parcelles_dvf.csv"
OUTPUT_PATH = "../data/parcelles_indicateurs.csv"
PRIX_MENSUELS_PATH = "../data/prix_mensuels.csv"


print("Chargement du DVF...")

dvf = pd.read_csv(
    DVF_PATH,
    sep="|",
    encoding="utf-8",
    low_memory=False,
    usecols=[
        "Code departement",
        "Code commune",
        "Section",
        "No plan",
        "Date mutation",
        "Nature mutation",
        "Valeur fonciere",
        "Surface reelle bati"
    ]
)


# ============================================================
# 1. Filtrer le Val-de-Marne
# ============================================================

dvf = dvf[
    dvf["Code departement"]
    .astype(str)
    .str.strip()
    == "94"
].copy()


# ============================================================
# 2. Normaliser les identifiants de parcelles
# ============================================================

dvf["commune_code"] = (
    "94"
    + dvf["Code commune"]
    .astype(str)
    .str.strip()
    .str.zfill(3)
)

dvf["section_normalisee"] = (
    dvf["Section"]
    .astype(str)
    .str.strip()
    .str.upper()
    .str.zfill(2)
)

dvf["numero_normalise"] = (
    dvf["No plan"]
    .astype(str)
    .str.strip()
    .str.zfill(4)
)

dvf["parcelle_key"] = (
    dvf["commune_code"]
    + "_"
    + dvf["section_normalisee"]
    + "_"
    + dvf["numero_normalise"]
)


# ============================================================
# 3. Nettoyer les dates
# ============================================================

dvf["Date mutation"] = pd.to_datetime(
    dvf["Date mutation"],
    dayfirst=True,
    errors="coerce"
)


# ============================================================
# 4. Nettoyer les valeurs foncières
# ============================================================

dvf["Valeur fonciere"] = (
    dvf["Valeur fonciere"]
    .astype(str)
    .str.replace(",", ".", regex=False)
)

dvf["Valeur fonciere"] = pd.to_numeric(
    dvf["Valeur fonciere"],
    errors="coerce"
)


# ============================================================
# 5. Nettoyer les surfaces bâties
# ============================================================

dvf["Surface reelle bati"] = pd.to_numeric(
    dvf["Surface reelle bati"],
    errors="coerce"
)

dvf["Surface reelle bati"] = (
    dvf["Surface reelle bati"]
    .replace(0, pd.NA)
)


# ============================================================
# 6. Calculer le prix au m²
# ============================================================

dvf["prix_m2"] = (
    dvf["Valeur fonciere"]
    / dvf["Surface reelle bati"]
)


# ============================================================
# 7. Transactions exploitables
# ============================================================

dvf_exploitable = dvf[
    dvf["Valeur fonciere"].notna()
    & (dvf["Valeur fonciere"] > 0)
].copy()

print(
    "Nombre de transactions exploitables :",
    len(dvf_exploitable)
)


# ============================================================
# 8. Calculer les indicateurs par parcelle
# ============================================================

indicateurs = (
    dvf_exploitable
    .groupby("parcelle_key")
    .agg(
        nb_transactions=("Valeur fonciere", "count"),
        prix_median=("Valeur fonciere", "median"),
        surface_batie_mediane=("Surface reelle bati", "median"),
        prix_m2_median=("prix_m2", "median")
    )
    .reset_index()
)

print(
    "Nombre de parcelles avec au moins une transaction exploitable :",
    len(indicateurs)
)


# ============================================================
# 9. Calculer l'évolution mensuelle du prix de vente au m²
# ============================================================

dvf_prix_m2 = dvf_exploitable[
    (dvf_exploitable["Nature mutation"] == "Vente")
    & dvf_exploitable["prix_m2"].notna()
    & (dvf_exploitable["prix_m2"] > 0)
    & dvf_exploitable["Date mutation"].notna()
].copy()


dvf_prix_m2["mois"] = (
    dvf_prix_m2["Date mutation"]
    .dt.to_period("M")
    .astype(str)
)


prix_mensuels = (
    dvf_prix_m2
    .groupby("mois")
    .agg(
        prix_median_m2=("prix_m2", "median"),
        nb_ventes=("prix_m2", "count")
    )
    .reset_index()
)


prix_mensuels["prix_median_m2"] = (
    prix_mensuels["prix_median_m2"]
    .round(2)
)


print("\nÉvolution mensuelle du prix de vente médian au m² :")
print(prix_mensuels)


prix_mensuels.to_csv(
    PRIX_MENSUELS_PATH,
    index=False
)

print(
    "\nFichier sauvegardé :",
    PRIX_MENSUELS_PATH
)


# ============================================================
# 10. Ajouter les indicateurs aux parcelles
# ============================================================

parcelles = pd.read_csv(
    PARCELLES_PATH,
    dtype={
        "commune_code": str,
        "section_normalisee": str,
        "numero_normalise": str,
        "parcelle_key": str,
        "statut_matching": str
    }
)


indicateurs = parcelles.merge(
    indicateurs,
    on="parcelle_key",
    how="left"
)


# ============================================================
# 11. Sauvegarder les indicateurs par parcelle
# ============================================================

indicateurs.to_csv(
    OUTPUT_PATH,
    index=False
)


print(
    "\nDataset sauvegardé :",
    OUTPUT_PATH
)

print("\nAffichage du dataframe :")
print(indicateurs.head(10))