
import pandas as pd
import geopandas as gpd


DVF_PATH = "../data/dvf/ValeursFoncieres-2025.txt"
CADASTRE_PATH = "../data/cadastre/cadastre_94_val_de_marne.geojson"


def preparer_cadastre(cadastre):
    """
    Normalise les identifiants cadastraux
    et construit la clé de rapprochement.
    """

    cadastre = cadastre.copy()

    cadastre["commune_normalisee"] = (
        cadastre["commune"]
        .astype(str)
        .str.strip()
    )

    cadastre["section_normalisee"] = (
        cadastre["section"]
        .astype(str)
        .str.strip()
        .str.upper()
        .str.zfill(2)
    )

    cadastre["numero_normalise"] = (
        cadastre["numero"]
        .astype(str)
        .str.strip()
        .str.zfill(4)
    )

    cadastre["parcelle_key"] = (
        cadastre["commune_normalisee"]
        + "_"
        + cadastre["section_normalisee"]
        + "_"
        + cadastre["numero_normalise"]
    )

    return cadastre


def charger_donnees():
    """
    Charge et prépare les données DVF et cadastrales.
    """

    print("Chargement du DVF...")

    dvf = pd.read_csv(
        DVF_PATH,
        sep="|",
        encoding="utf-8",
        low_memory=False,
        usecols=[
            "Code departement",
            "Code commune",
            "Prefixe de section",
            "Section",
            "No plan",
            "Valeur fonciere",
            "Surface reelle bati"
        ]
    )

    print(
        "DVF chargé :",
        len(dvf),
        "lignes"
    )

    print("\nChargement du cadastre...")

    cadastre = gpd.read_file(
        CADASTRE_PATH
    )

    print(
        "Cadastre chargé :",
        len(cadastre),
        "parcelles"
    )

    # Filtre Val-de-Marne
    dvf = dvf[
        dvf["Code departement"]
        .astype(str)
        .str.strip()
        == "94"
    ].copy()

    print(
        "DVF Val-de-Marne :",
        len(dvf),
        "lignes"
    )

    # Normalisation DVF
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

    # Normalisation cadastre
    cadastre = preparer_cadastre(
        cadastre
    )

    # Vérifications
    print("\n--- VÉRIFICATIONS ---")

    print(
        "Parcelles cadastrales :",
        len(cadastre)
    )

    print(
        "Clés cadastrales distinctes :",
        cadastre["parcelle_key"].nunique()
    )

    print(
        "Clés DVF distinctes :",
        dvf["parcelle_key"].nunique()
    )

    return dvf, cadastre


dvf, cadastre = charger_donnees()


if __name__ == "__main__":
    print("\nPréparation terminée.")

