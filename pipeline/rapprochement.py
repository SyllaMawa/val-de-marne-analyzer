
import pandas as pd

from preparation_donnees import dvf, cadastre


# ------------------------------------------------------
# CLÉS CADASTRALES
# ------------------------------------------------------

cadastre_keys = set(
    cadastre["parcelle_key"]
)


# ------------------------------------------------------
# CORRESPONDANCE EXACTE
# ------------------------------------------------------

dvf["parcelle_trouvee"] = (
    dvf["parcelle_key"]
    .isin(cadastre_keys)
)


# ------------------------------------------------------
# RECHERCHE D'UN MÊME NUMÉRO DANS LA COMMUNE
# ------------------------------------------------------

numeros_commune = set(
    zip(
        cadastre["commune_normalisee"],
        cadastre["numero_normalise"]
    )
)


def determiner_statut(row):
    """
    Détermine le statut de rapprochement
    d'une ligne DVF.
    """

    # Correspondance exacte :
    # commune + section + numéro
    if row["parcelle_trouvee"]:
        return "MATCHED"

    # Le numéro existe dans la commune,
    # mais pas avec cette section.
    numero_existe = (
        row["commune_code"],
        row["numero_normalise"]
    ) in numeros_commune

    if numero_existe:
        return "SECTION_MISMATCH"

    # Le numéro n'existe pas dans la commune.
    return "NOT_FOUND"


# ------------------------------------------------------
# CHERCHE  DU STATUT
# ------------------------------------------------------

dvf["statut_matching"] = dvf.apply(
    determiner_statut,
    axis=1
)


# ------------------------------------------------------
# RESULTATS
# ------------------------------------------------------

print("\n==============================================")
print("RÉSULTATS DU RAPPROCHEMENT")
print("==============================================")

print(
    dvf["statut_matching"]
    .value_counts()
)


taux_correspondance = (
    dvf["parcelle_trouvee"].mean()
    * 100
)

print(
    "\nTaux de correspondance exacte :",
    round(taux_correspondance, 2),
    "%"
)


# ------------------------------------------------------
# UNE LIGNE PAR PARCELLE DVF
# ------------------------------------------------------

parcelles = (
    dvf[
        [
            "commune_code",
            "section_normalisee",
            "numero_normalise",
            "parcelle_key",
            "statut_matching"
        ]
    ]
    .drop_duplicates(
        "parcelle_key"
    )
    .copy()
)


print(
    "\nParcelles DVF distinctes :",
    len(parcelles)
)

print(
    "Parcelles MATCHED :",
    (
        parcelles["statut_matching"]
        == "MATCHED"
    ).sum()
)

print(
    "Parcelles SECTION_MISMATCH :",
    (
        parcelles["statut_matching"]
        == "SECTION_MISMATCH"
    ).sum()
)

print(
    "Parcelles NOT_FOUND :",
    (
        parcelles["statut_matching"]
        == "NOT_FOUND"
    ).sum()
)


# ------------------------------------------------------
# SAUVEGARDE
# ------------------------------------------------------

output_path = "../data/parcelles_dvf.csv"

parcelles.to_csv(
    output_path,
    index=False
)

print(
    "\nDataset sauvegardé :",
    output_path
)

