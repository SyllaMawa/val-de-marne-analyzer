
import json

import pandas as pd
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from database import engine


app = FastAPI(
    title="Val-de-Marne Analyzer",
    description=(
        "API d'analyse des transactions immobilières "
        "et des parcelles cadastrales du Val-de-Marne."
    ),
    version="1.0.0"
)


frontend_url = os.getenv(
    "FRONTEND_URL",
    "http://localhost:5173"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        frontend_url,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "API Val-de-Marne",
        "status": "ok"
    }


@app.get("/test-db")
def test_db():
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT COUNT(*) FROM parcelles_finales")
        )
        value = result.scalar()

    return {
        "database": "connected",
        "result": value
    }


@app.get("/parcelles")
def get_parcelles():
    query = text("""
        SELECT
            parcelle_key,
            commune_code,
            section,
            numero,
            nb_transactions,
            prix_median,
            prix_m2_median,
            surface_batie_mediane,
            statut_matching,
            ST_AsGeoJSON(geometry) AS geometry
        FROM parcelles_finales
        WHERE statut_matching = 'MATCHED'
    """)

    with engine.connect() as connection:
        result = connection.execute(query)

        features = []

        for row in result.mappings():
            features.append({
                "type": "Feature",
                "geometry": json.loads(row["geometry"]),
                "properties": {
                    "parcelle_key": row["parcelle_key"],
                    "commune_code": row["commune_code"],
                    "section": row["section"],
                    "numero": row["numero"],
                    "nb_transactions": row["nb_transactions"],
                    "prix_median": row["prix_median"],
                    "prix_m2_median": row["prix_m2_median"],
                    "surface_batie_mediane": row["surface_batie_mediane"],
                    "statut_matching": row["statut_matching"]
                }
            })

    return {
        "type": "FeatureCollection",
        "features": features
    }


@app.get("/prix-mensuels")
def get_prix_mensuels():
    df = pd.read_csv("../data/prix_mensuels.csv")

    return df.to_dict(orient="records")


@app.get("/communes")
def get_communes():

    # Lecture des limites géographiques des communes
    with open(
        "../data/limites_communes.geojson",
        encoding="utf-8"
    ) as file:
        communes_geojson = json.load(file)


    # Calcul du prix médian au m² pour chaque commune
    query = text("""
        SELECT
            commune_code,
            SUM(nb_transactions) AS nb_transactions,
            PERCENTILE_CONT(0.5)
                WITHIN GROUP (ORDER BY prix_m2_median)
                AS prix_median_m2
        FROM parcelles_finales
        WHERE
            statut_matching = 'MATCHED'
            AND prix_m2_median IS NOT NULL
            AND prix_m2_median > 0
        GROUP BY commune_code
    """)


    with engine.connect() as connection:
        result = connection.execute(query)

        prix_communes = {}

        for row in result.mappings():
            code_commune = str(row["commune_code"])

            prix_communes[code_commune] = {
                "prix_median_m2": row["prix_median_m2"],
                "nb_transactions": row["nb_transactions"]
            }


    # Ajout des données immobilières aux communes
    communes_94 = []

    for feature in communes_geojson["features"]:

        properties = feature.get("properties", {})

        code_commune = properties.get("code")

        departement = properties.get("departement")

        if departement != "94":
            continue


        code_commune = str(code_commune)

        if code_commune in prix_communes:

            feature["properties"]["prix_median_m2"] = (
                prix_communes[code_commune]["prix_median_m2"]
            )

            feature["properties"]["nb_transactions"] = (
                prix_communes[code_commune]["nb_transactions"]
            )

        else:

            feature["properties"]["prix_median_m2"] = None
            feature["properties"]["nb_transactions"] = 0


        communes_94.append(feature)


    return {
        "type": "FeatureCollection",
        "features": communes_94
    }


@app.get("/stats-prix-communes")
def stats_prix_communes():

    query = text("""
        SELECT
            MIN(prix_median_m2) AS minimum,
            PERCENTILE_CONT(0.25)
                WITHIN GROUP (ORDER BY prix_median_m2) AS q1,
            PERCENTILE_CONT(0.50)
                WITHIN GROUP (ORDER BY prix_median_m2) AS mediane,
            PERCENTILE_CONT(0.75)
                WITHIN GROUP (ORDER BY prix_median_m2) AS q3,
            MAX(prix_median_m2) AS maximum
        FROM (
            SELECT
                commune_code,
                PERCENTILE_CONT(0.5)
                    WITHIN GROUP (ORDER BY prix_m2_median) AS prix_median_m2
            FROM parcelles_finales
            WHERE
                statut_matching = 'MATCHED'
                AND prix_m2_median IS NOT NULL
                AND prix_m2_median > 0
            GROUP BY commune_code
        ) communes
    """)

    with engine.connect() as connection:
        result = connection.execute(query).mappings().first()

    return {
        "minimum": result["minimum"],
        "q1": result["q1"],
        "mediane": result["mediane"],
        "q3": result["q3"],
        "maximum": result["maximum"]
    }

