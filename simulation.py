# Transport_type = PRIV_MOT_TRANSP
# Transport_mean = CAR_DRIV, CAR_PASS, TAXI, TAXI_LIKE
# Travel_Reason = ALL_REAS
# Socio_DEMO_Variable_Type = ??
# Socio_demo_variable = ??
# UNIT_MEAS = KM (Tagesdistanz in km), MIN (Mittlere Zeit unterwegs = reduzieren)

# Verteilung der Fahrzeuge Benzin (60.4%), Diesel (25.2%), Hybrid (7.5%), Plug-in-Hybrid (2.1%), Elektrisch (4.2%)
# Nutzfahrzeuge und Lieferwagen wurden vernachlässigt

import pandas as pd
import matplotlib.pyplot as plt
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import dash
import numpy as np

vh_file_path = "./verkehrsverhalten.csv"
vh_data = pd.read_csv(vh_file_path, delimiter=';')

# Motorisierter Individualverkehr, gefahrene Kilometer und Jahr 2021
pkw_2023 = vh_data[
    (vh_data['TRANSPORT_TYPE'] == 'PRIV_MOT_TRANSP') &  # Motorisierter Individualverkehr
    (vh_data['UNIT_MEAS'] == 'KM') &  # Einheit Kilometer
    (vh_data['PERIOD_REF'] == 2021)  # Jahr 2023
]
gesamt_kilometer = pkw_2023['VALUE'].mean()
print(gesamt_kilometer)

# Initialdaten
gesamtfahrleistung = 22_577_600_000  # Nationalstrassenfahrleistung (Pkw)
gesamt_autofahrer = 8_738_791 * 0.832  # Geschätzte Autofahrende in der Schweiz
emissionen_pro_km_g = 112.7  # g CO₂/km (durchschnittliche Emission) ############################## pro Fahrzeug
emissionen_pro_km = emissionen_pro_km_g / 1_000_000
fahrzeugverteilung = {"benzin": 0.604, "diesel": 0.252, "hybrid": 0.075, "plug-in hybrid": 0.021, "elektro": 0.042}  
autobahn_anteil = 0.40  # 40% der Fahrleistung findet auf Nationalstraßen statt
fahrleistung = 12580 # Durchschnittliche Fahrleistung pro Jahr
d_fahrleistung_nstrasse = fahrleistung * autobahn_anteil # Fahrleistung pro Jahr auf Autobahn

# Carpooling zusammengezählt muss man auf die gesamten Fahrzeugkilometer der Autobahn kommen
# Knopf für Anreize (Carpooling ab 3+)
# Autobeladung aufzeigen

# Monte-Carlo-Simulation
def simulation_carpooling_verhalten(n_runs):
    np.random.seed(42)  # Reproduzierbarkeit

    # Simulation von Carpooling-Adoption pro Person (normalverteilt)
    carpooling_werte = np.clip(np.random.normal(loc=0.3, scale=0.15, size=n_runs), 0.05, 0.9)

    emissions_ergebnisse = []
    fahrzeuge_eingespart = []

    for carpooling_anteil in carpooling_werte:
        # Fahrzeugauslastung durchschnittswert + errechneter anteil
        auslastung_vorher = 1.2
        auslastung_nachher = 1.2 + (6.8 * (1 - np.exp(-3 * carpooling_anteil)))

        # Reduzierte Fahrleistung
        reduzierte_fahrleistung = gesamtfahrleistung * (auslastung_vorher / auslastung_nachher) * (1 - carpooling_anteil)

        # Anzahl der eingesparten Fahrzeuge (neue Berechnung!)
        eingesparte_fahrleistung = gesamtfahrleistung - reduzierte_fahrleistung
        fahrzeuge_reduziert = eingesparte_fahrleistung / d_fahrleistung_nstrasse

        # Berechnung der Emissionen nach Carpooling
        emissionen = sum(
            reduzierte_fahrleistung * emissionen_pro_km * fahrzeugverteilung[typ] / 1_000
            for typ in fahrzeugverteilung
        )

        emissions_ergebnisse.append(emissionen * 10000)  # CO2 in Millionen Tonnen
        fahrzeuge_eingespart.append(fahrzeuge_reduziert)

    return carpooling_werte, emissions_ergebnisse, fahrzeuge_eingespart

# Dash-App erstellen
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("CO₂-Einsparung durch dynamische Carpooling-Adoption"),
    dcc.Slider(
        id='simulation-slider',
        min=100,
        max=5000,
        step=100,
        value=1000,
        marks={i: f'{i}' for i in range(1000, 5001, 1000)}
    ),
    dcc.Graph(id='simulation-plot'),
])

# Callback für die Simulation
@app.callback(
    Output('simulation-plot', 'figure'),
    [Input('simulation-slider', 'value')]
)
def update_simulation(n_runs):
    # Simulation wird nun mit n_runs ausgeführt!
    carpooling_werte, emissions_ergebnisse, fahrzeuge_eingespart = simulation_carpooling_verhalten(n_runs)

    fig = go.Figure()

    # Scatter-Plot für Emissionen
    fig.add_trace(go.Scatter(
        x=carpooling_werte,
        y=emissions_ergebnisse,
        mode='markers',
        name="CO₂-Emissionen",
        marker=dict(color='green', opacity=0.5)
    ))

    fig.add_trace(go.Scatter(
        x=carpooling_werte,
        y=emissions_ergebnisse,
        mode='markers',
        name="CO₂-Einsparung (Mt)",  # Millionen Tonnen CO₂
        marker=dict(color='green', opacity=0.5),
        yaxis='y1'  # Verwendet die erste Y-Achse
    ))

    fig.add_trace(go.Scatter(
        x=carpooling_werte,
        y=fahrzeuge_eingespart,
        mode='markers',
        name="Eingesparte Fahrzeuge (Mio.)",  # Millionen Fahrzeuge
        marker=dict(color='blue', opacity=0.5),
        yaxis='y2'  # Verwendet die zweite Y-Achse
    ))

    fig.update_layout(
        yaxis=dict(title="CO₂-Einsparung (Tonnen)"),
        yaxis2=dict(title="Eingesparte Fahrzeuge (Millionen)", overlaying='y', side='right')
    )
    return fig

# App starten
if __name__ == '__main__':
    app.run_server(debug=True)