import { useEffect, useState } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

import {
  MapContainer,
  TileLayer,
  GeoJSON,
} from 'react-leaflet'

import 'leaflet/dist/leaflet.css'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8001'

function App() {
  const [priceData, setPriceData] = useState([])
  const [communes, setCommunes] = useState(null)

  const [loadingPrices, setLoadingPrices] = useState(true)
  const [loadingCommunes, setLoadingCommunes] = useState(true)

  const [errorPrices, setErrorPrices] = useState(null)
  const [errorCommunes, setErrorCommunes] = useState(null)

  useEffect(() => {
    fetch(`${API_URL}/prix-mensuels`)
      .then((response) => {
        if (!response.ok) {
          throw new Error('Erreur lors du chargement des prix')
        }
        return response.json()
      })
      .then((data) => {
        setPriceData(data)
        setLoadingPrices(false)
      })
      .catch((error) => {
        setErrorPrices(error.message)
        setLoadingPrices(false)
      })
  }, [])

  useEffect(() => {
    fetch(`${API_URL}/communes`)
      .then((response) => {
        if (!response.ok) {
          throw new Error('Erreur lors du chargement des communes')
        }
        return response.json()
      })
      .then((data) => {
        setCommunes(data)
        setLoadingCommunes(false)
      })
      .catch((error) => {
        setErrorCommunes(error.message)
        setLoadingCommunes(false)
      })
  }, [])

  const formatMonth = (month) => {
    const months = [
      'Janvier',
      'Février',
      'Mars',
      'Avril',
      'Mai',
      'Juin',
      'Juillet',
      'Août',
      'Septembre',
      'Octobre',
      'Novembre',
      'Décembre',
    ]

    const monthNumber = Number(month.split('-')[1])

    return months[monthNumber - 1]
  }

  const getCommuneColor = (price) => {
    if (price === null || price === undefined) {
      return '#d1d5db'
    }

    if (price < 3723) {
      return '#166534'
    }

    if (price < 4156) {
      return '#65a30d'
    }

    if (price < 5467) {
      return '#eab308'
    }

    if (price < 6500) {
      return '#f97316'
    }

    return '#dc2626'
  }

  const communeStyle = (feature) => {
    const price = feature.properties.prix_median_m2

    return {
      fillColor: getCommuneColor(price),
      weight: 1,
      opacity: 1,
      color: '#ffffff',
      fillOpacity: 0.7,
    }
  }

  const onEachCommune = (feature, layer) => {
    const properties = feature.properties

    const name = properties.nom || 'Commune'
    const price = properties.prix_median_m2
    const transactions = properties.nb_transactions || 0

    const formattedPrice =
      price !== null && price !== undefined
        ? `${Number(price).toLocaleString('fr-FR', {
          maximumFractionDigits: 0,
        })} €/m²`
        : 'Pas de données'

    const formattedTransactions =
      Number(transactions).toLocaleString('fr-FR')

    layer.bindPopup(`
      <div style="font-family: Arial, sans-serif; min-width: 180px;">
        <strong style="font-size: 15px;">
          ${name}
        </strong>

        <div style="margin-top: 10px;">
          <div style="font-size: 12px; color: #66736b;">
            Prix médian au m²
          </div>

          <div style="font-size: 16px; font-weight: 700; color: #166534;">
            ${formattedPrice}
          </div>
        </div>

        <div style="margin-top: 8px;">
          <div style="font-size: 12px; color: #66736b;">
            Transactions
          </div>

          <div style="font-size: 14px; font-weight: 600;">
            ${formattedTransactions}
          </div>
        </div>
      </div>
    `)
  }

  return (
    <div className="app">
      <header className="header">
        <div className="brand">PURE</div>

        <div className="dataset">
          DVF 2025 · Val-de-Marne
        </div>
      </header>

      <main className="main">
        <section className="intro">
          <p className="eyebrow">
            ANALYSE IMMOBILIÈRE
          </p>

          <h1>Val-de-Marne</h1>

          <p className="description">
            Explorez le marché immobilier du Val-de-Marne à partir des transactions DVF 2025. Comparez les prix médians au m² entre les communes et visualisez leur répartition sur la carte.

          </p>
        </section>

        <section className="stats">
          <div className="stat-card">
            <p className="stat-label">
              TRANSACTIONS
            </p>

            <p className="stat-value">
              46 311
            </p>

            <p className="stat-description">
              Transactions DVF en 2025
            </p>
          </div>

          <div className="stat-card">
            <p className="stat-label">
              PRIX MÉDIAN
            </p>

            <p className="stat-value">
              4 156 €/m²
            </p>

            <p className="stat-description">
              Médiane des prix communaux
            </p>
          </div>

          <div className="stat-card">
            <p className="stat-label">
              COMMUNES
            </p>

            <p className="stat-value">
              47
            </p>

            <p className="stat-description">
              Communes analysées
            </p>
          </div>
        </section>

        <section className="dashboard">
          <div className="panel">
            <div className="panel-header">
              <div>
                <p className="panel-label">
                  ÉVOLUTION
                </p>

                <h2>
                  Prix de vente médian au m²
                </h2>
              </div>

              <span className="panel-period">
                2025
              </span>
            </div>

            <div className="chart-container">
              {loadingPrices && (
                <p>Chargement des données...</p>
              )}

              {errorPrices && (
                <p>
                  Impossible de charger les données.
                </p>
              )}

              {!loadingPrices &&
                !errorPrices &&
                priceData.length > 0 && (
                  <ResponsiveContainer
                    width="100%"
                    height="100%"
                  >
                    <LineChart data={priceData}>
                      <CartesianGrid
                        strokeDasharray="3 3"
                        vertical={false}
                      />

                      <XAxis
                        dataKey="mois"
                        tickFormatter={formatMonth}
                      />

                      <YAxis
                        tickFormatter={(value) =>
                          `${value.toLocaleString('fr-FR')} €`
                        }
                      />

                      <Tooltip
                        labelFormatter={formatMonth}
                        formatter={(value) =>
                          `${Number(value).toLocaleString('fr-FR')} €/m²`
                        }
                      />

                      <Line
                        type="monotone"
                        dataKey="prix_median_m2"
                        stroke="#166534"
                        strokeWidth={2}
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                )}
            </div>
          </div>

          <div className="panel">
            <div className="panel-header">
              <div>
                <p className="panel-label">
                  COMPARAISON TERRITORIALE
                </p>

                <h2>
                  Prix médian par commune
                </h2>
              </div>

              <span className="panel-period">
                94
              </span>
            </div>

            <div className="map-container">
              {loadingCommunes && (
                <p>Chargement de la carte...</p>
              )}

              {errorCommunes && (
                <p>
                  Impossible de charger la carte.
                </p>
              )}

              {!loadingCommunes &&
                !errorCommunes &&
                communes && (
                  <MapContainer
                    center={[48.79, 2.45]}
                    zoom={10}
                    scrollWheelZoom={false}
                  >
                    <TileLayer
                      attribution="&copy; OpenStreetMap contributors"
                      url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    />

                    <GeoJSON
                      data={communes}
                      style={communeStyle}
                      onEachFeature={onEachCommune}
                    />
                  </MapContainer>
                )}

              <div className="map-legend">
                <p>Prix médian au m²</p>

                <div>
                  <span className="legend-color very-low"></span>
                  <span>&lt; 3 723 €</span>
                </div>

                <div>
                  <span className="legend-color low"></span>
                  <span>3 723 – 4 155 €</span>
                </div>

                <div>
                  <span className="legend-color medium"></span>
                  <span>4 156 – 5 466 €</span>
                </div>

                <div>
                  <span className="legend-color medium-high"></span>
                  <span>5 467 – 6 499 €</span>
                </div>

                <div>
                  <span className="legend-color high"></span>
                  <span>≥ 6 500 €</span>
                </div>

                <div>
                  <span className="legend-color no-data"></span>
                  <span>Pas de données</span>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}

export default App