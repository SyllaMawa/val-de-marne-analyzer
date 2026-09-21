import geopandas as gpd
import pandas as pd


CADASTRE_PATH = "../data/cadastre/cadastre_94_val_de_marne.geojson"
INDICATEURS_PATH = "../data/parcelles_indicateurs.csv"
OUTPUT_PATH = "../data/parcelles_finales.geojson"


def preparer_cadastre(cadastre):
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


print("==============================================")
print("PRÉPARATION DU DATASET FINAL")
print("==============================================")


print("\nChargement du cadastre...")

cadastre = gpd.read_file(CADASTRE_PATH)

print("Parcelles cadastrales :", len(cadastre))


print("\nPréparation du cadastre...")

cadastre = preparer_cadastre(cadastre)

print(
    "Clés cadastrales distinctes :",
    cadastre["parcelle_key"].nunique()
)


print("\nChargement des indicateurs DVF...")

indicateurs = pd.read_csv(
    INDICATEURS_PATH,
    dtype={
        "commune_code": str,
        "section_normalisee": str,
        "numero_normalise": str,
        "parcelle_key": str,
        "statut_matching": str
    }
)

print("Parcelles DVF :", len(indicateurs))


# ============================================================
# ÉVITER LES COLLISIONS DE COLONNES LORS DE LA JOINTURE
# ============================================================

# commune_code existe déjà dans les indicateurs DVF.
# On le renomme temporairement afin de conserver
# le commune_code provenant du cadastre dans le dataset final.

indicateurs = indicateurs.rename(
    columns={
        "commune_code": "commune_code_dvf"
    }
)


# ============================================================
# PRÉPARATION DU CADASTRE
# ============================================================

cadastre = cadastre[
    [
        "parcelle_key",
        "commune_normalisee",
        "section_normalisee",
        "numero_normalise",
        "contenance",
        "geometry"
    ]
].copy()


cadastre = cadastre.rename(
    columns={
        "commune_normalisee": "commune_code",
        "section_normalisee": "section",
        "numero_normalise": "numero"
    }
)


# ============================================================
# CONTRÔLES AVANT JOINTURE
# ============================================================

print("\nContrôle des clés...")

print(
    "Clés DVF distinctes :",
    indicateurs["parcelle_key"].nunique()
)

print(
    "Clés cadastrales distinctes :",
    cadastre["parcelle_key"].nunique()
)

doublons = cadastre["parcelle_key"].duplicated().sum()

print(
    "Clés cadastrales en doublon :",
    doublons
)

if doublons > 0:
    raise ValueError(
        "Des clés cadastrales sont en doublon."
    )


# ============================================================
# JOINTURE DVF + CADASTRE
# ============================================================

print("\nJointure DVF / cadastre...")

parcelles_finales = indicateurs.merge(
    cadastre,
    on="parcelle_key",
    how="left",
    validate="one_to_one"
)


# ============================================================
# DATASET FINAL
# ============================================================

parcelles_finales = parcelles_finales[
    [
        "parcelle_key",
        "commune_code",
        "section",
        "numero",
        "contenance",
        "nb_transactions",
        "prix_median",
        "prix_m2_median",
        "surface_batie_mediane",
        "statut_matching",
        "geometry"
    ]
].copy()


# ============================================================
# CONTRÔLES
# ============================================================

print("\n==============================================")
print("RÉSULTAT DU DATASET FINAL")
print("==============================================")

print(
    "Nombre de parcelles finales :",
    len(parcelles_finales)
)

print("\nColonnes finales :")

for column in parcelles_finales.columns:
    print(" -", column)


print("\nStatuts de matching :")

print(
    parcelles_finales["statut_matching"]
    .value_counts(dropna=False)
)


print("\nGéométries disponibles :")

print(
    "Avec géométrie :",
    parcelles_finales["geometry"].notna().sum()
)

print(
    "Sans géométrie :",
    parcelles_finales["geometry"].isna().sum()
)


print("\nContrôle des statuts et géométries :")

print(
    "MATCHED avec géométrie :",
    (
        (parcelles_finales["statut_matching"] == "MATCHED")
        & parcelles_finales["geometry"].notna()
    ).sum()
)

print(
    "SECTION_MISMATCH sans géométrie :",
    (
        (parcelles_finales["statut_matching"] == "SECTION_MISMATCH")
        & parcelles_finales["geometry"].isna()
    ).sum()
)

print(
    "NOT_FOUND sans géométrie :",
    (
        (parcelles_finales["statut_matching"] == "NOT_FOUND")
        & parcelles_finales["geometry"].isna()
    ).sum()
)




# ============================================================
# CONVERSION EN GEODATAFRAME
# ============================================================

parcelles_finales = gpd.GeoDataFrame(
    parcelles_finales,
    geometry="geometry",
    crs=cadastre.crs
)


# ============================================================
# SAUVEGARDE
# ============================================================

print("\nSauvegarde du GeoJSON...")

parcelles_finales.to_file(
    OUTPUT_PATH,
    driver="GeoJSON"
)


print("\n==============================================")
print("TERMINÉ")
print("==============================================")

print(
    "Fichier sauvegardé :",
    OUTPUT_PATH
)