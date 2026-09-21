# Val-de-Marne Analyzer

Analyse des transactions immobilières du **Val-de-Marne (94)** à partir des données DVF 2025 et du cadastre.

Le projet couvre l'ensemble du pipeline de données — de la collecte brute au rapprochement cadastral — jusqu'à une interface web interactive avec graphique d'évolution des prix et carte choroplèthe par commune.

---

## Aperçu

| Métrique | Valeur |
|---|---|
| Transactions DVF 2025 | 46 311 |
| Prix médian au m² (médiane des communes) | 4 156 €/m² |
| Communes analysées | 47 |
| Taux de rapprochement DVF ↔ Cadastre | 97,68 % |

---

## Architecture

```
val-de-marne-analyzer/
│
├── pipeline/                   # Scripts de traitement des données
│   ├── preparation_donnees.py  # Chargement et normalisation DVF + cadastre
│   ├── rapprochement.py        # Rapprochement DVF ↔ cadastre (3 statuts)
│   ├── indicateurs.py          # Calcul des indicateurs par parcelle et prix mensuels
│   └── preparation_postgis.py  # Chargement dans PostGIS
│
├── notebook/
│   └── analyse_anomalies.ipynb # Analyse exploratoire et détection d'anomalies
│
├── backend/                    # API REST (FastAPI)
│   ├── main.py                 # Endpoints : prix mensuels, communes, parcelles
│   └── database.py             # Connexion SQLAlchemy → PostGIS
│
├── frontend/                   # Interface web (React + Vite)
│   └── src/
│       ├── App.jsx             # Graphique Recharts + carte Leaflet
│       └── App.css             # Design system
│
├── docker-compose.yml          # Base de données PostGIS (PostgreSQL 16)
└── data/                       # Données générées (non versionnées)
    └── prix_mensuels.csv       # Seul fichier de données versionné
```

---

## Stack technique

| Couche | Technologie |
|---|---|
| Données | Python · Pandas · GeoPandas |
| Base de données | PostgreSQL 16 + PostGIS 3.4 (Docker) |
| API | FastAPI · SQLAlchemy · Uvicorn |
| Frontend | React 19 · Vite · Recharts · React-Leaflet |
| Données sources | DVF (data.gouv.fr) · Cadastre Etalab · IGN communes |

---

## Pipeline de données

### 1. Préparation (`pipeline/preparation_donnees.py`)

- Chargement du fichier DVF national (format `|`)
- Filtrage sur le département **94**
- Normalisation des identifiants : code commune, section (zfill 2), numéro (zfill 4)
- Construction d'une `parcelle_key` commune DVF ↔ cadastre

### 2. Rapprochement (`pipeline/rapprochement.py`)

Le rapprochement classe chaque ligne DVF selon 3 statuts :

| Statut | Signification |
|---|---|
| `MATCHED` | Correspondance exacte commune + section + numéro |
| `SECTION_MISMATCH` | Numéro trouvé dans la commune, section différente |
| `NOT_FOUND` | Parcelle absente du cadastre |

→ Résultat sauvegardé dans `data/parcelles_dvf.csv`

### 3. Indicateurs (`pipeline/indicateurs.py`)

Pour chaque parcelle DVF :
- Nombre de transactions
- Prix de vente médian
- Surface bâtie médiane
- Prix médian au m²

Pour l'ensemble du département, calcul de l'**évolution mensuelle du prix médian au m²** (ventes uniquement) → `data/prix_mensuels.csv`

### 4. Chargement PostGIS (`pipeline/preparation_postgis.py`)

Import des parcelles avec leur géométrie dans une table `parcelles_finales` (PostGIS).

---

## Lancement du projet

### Prérequis

- Docker Desktop
- Python 3.11+
- Node.js 18+

### 1. Base de données

```bash
docker-compose up -d
```

Lance un conteneur **PostgreSQL 16 + PostGIS 3.4** sur le port `5433`.

### 2. Pipeline Python

```bash
cd pipeline
pip install pandas geopandas sqlalchemy psycopg2-binary fastapi uvicorn

python preparation_donnees.py
python rapprochement.py
python indicateurs.py
python preparation_postgis.py
```

> Les fichiers source DVF et cadastre ne sont pas versionnés (trop volumineux).
> Téléchargez-les sur [data.gouv.fr](https://www.data.gouv.fr/fr/datasets/demandes-de-valeurs-foncieres/) et [cadastre.data.gouv.fr](https://cadastre.data.gouv.fr/datasets/cadastre-etalab).

### 3. Backend (API)

```bash
cd backend
uvicorn main:app --host 127.0.0.1 --port 8001 --reload
```

API disponible sur `http://127.0.0.1:8001`

| Endpoint | Description |
|---|---|
| `GET /` | Statut de l'API |
| `GET /prix-mensuels` | Évolution mensuelle du prix médian au m² |
| `GET /communes` | GeoJSON des communes 94 avec indicateurs |
| `GET /stats-prix-communes` | Distribution statistique des prix communaux |
| `GET /parcelles` | GeoJSON des parcelles rapprochées |

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

Interface disponible sur `http://localhost:5173`

---

## Interface web

L'interface propose deux visualisations côte à côte :

- **Graphique linéaire** — Évolution du prix de vente médian au m² par mois en 2025
- **Carte choroplèthe** — Prix médian au m² par commune du Val-de-Marne, avec légende par quintile et popup au survol

---

## Sources de données

| Source | Description | Lien |
|---|---|---|
| DVF 2025 | Demandes de Valeurs Foncières | [data.gouv.fr](https://www.data.gouv.fr/fr/datasets/demandes-de-valeurs-foncieres/) |
| Cadastre Etalab | Parcelles cadastrales vectorielles | [cadastre.data.gouv.fr](https://cadastre.data.gouv.fr) |
| Limites communes IGN | GeoJSON des communes françaises | [github.com/gregoiredavid](https://github.com/gregoiredavid/france-geojson) |

---
