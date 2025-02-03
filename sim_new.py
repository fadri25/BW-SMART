import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import numpy as np

# Initialdaten
gesamtfahrleistung = 22_577_600_000  # Nationalstrassenfahrleistung (Pkw)
gesamt_autofahrer = 8_738_791 * 0.832  # Geschätzte Autofahrende in der Schweiz
emissionen_pro_km_g = 112.7  # g CO₂/km (durchschnittliche Emission)
emissionen_pro_km = emissionen_pro_km_g / 1_000_000  # Umrechnung in Tonnen/km
fahrzeugverteilung = {"benzin": 0.604, "diesel": 0.252, "hybrid": 0.075, "plug-in hybrid": 0.021, "elektro": 0.042}  
autobahn_anteil = 0.40  # 40% der Fahrleistung auf Nationalstrassen
fahrleistung = 12580  # Durchschnittliche Fahrleistung pro Jahr
d_fahrleistung_nstrasse = fahrleistung * autobahn_anteil  # Fahrleistung pro Jahr auf Autobahnen

# Kilometerpreis und einsparung errechnen 0.76 pro Kilometer
# Knopf für Anreize
# Skalierung dezimal, Jahr 2021, Pro Jahr erwähnen, nur auf Autobahnen

# Monte-Carlo-Simulation
def simulation_carpooling_verhalten(n_runs):
    np.random.seed(42)  # Reproduzierbarkeit (Seed)
    
    # Simulation von Carpooling-Adoption pro Person (normalverteilt)
    carpooling_werte = np.clip(np.random.normal(loc=0.3, scale=0.15, size=n_runs), 0.05, 0.9)

    emissions_ergebnisse = []
    fahrzeuge_eingespart = []
    belegung_verteilung = {i: [] for i in range(1, 8)}  # Für Belegung 1 bis 7 Personen

    for carpooling_anteil in carpooling_werte:
        # Fahrzeugauslastung: Carpooling erst ab 3 Personen
        auslastung_vorher = 1.2
        auslastung_nachher = 1.2 + (6.8 * (1 - np.exp(-3 * carpooling_anteil))) #auslastung_nachher = max(3, 3 + (3.8 * (1 - np.exp(-3 * carpooling_anteil)))) ##########################################################################

        # Reduzierte Fahrleistung
        reduzierte_fahrleistung = gesamtfahrleistung * (auslastung_vorher / auslastung_nachher) * (1 - carpooling_anteil)

        # Anzahl der eingesparten Fahrzeuge
        eingesparte_fahrleistung = gesamtfahrleistung - reduzierte_fahrleistung
        fahrzeuge_reduziert = eingesparte_fahrleistung / fahrleistung

        # Berechnung der CO₂-Emissionen nach Carpooling
        emissionen = sum(
            reduzierte_fahrleistung * emissionen_pro_km * fahrzeugverteilung[typ] / 1_000
            for typ in fahrzeugverteilung
        )

        # Verteilung der Fahrzeuge nach Belegung
        total_fahrzeuge = reduzierte_fahrleistung / d_fahrleistung_nstrasse
        for belegung in range(1, 8):  # Belegung von 1 bis 7 Personen
            if belegung <= auslastung_nachher:
                wahrscheinlichkeit = 1 / belegung  # Vereinfachte Wahrscheinlichkeit
                belegung_verteilung[belegung].append(total_fahrzeuge * wahrscheinlichkeit)
            else:
                belegung_verteilung[belegung].append(0)

        emissions_ergebnisse.append(emissionen * 10000)  # CO2 in Millionen Tonnen
        fahrzeuge_eingespart.append(fahrzeuge_reduziert)
    
        # Berechnung der tatsächlich gefahrenen Kilometer unter Berücksichtigung der Belegung
    gesamt_fahrleistung_simuliert = sum(
        sum(belegung_verteilung[belegung]) * belegung for belegung in range(1, 8)
        )

    # Berücksichtigung der Fahrzeuge, die nicht am Carpooling teilnehmen (1 und 2 Personen)
    nicht_carpooling_fahrleistung = sum(belegung_verteilung[1]) + sum(belegung_verteilung[2])  # 1- und 2-Personen-Fahrzeuge
    gesamt_fahrleistung_simuliert += nicht_carpooling_fahrleistung
    skalierungsfaktor = gesamtfahrleistung / gesamt_fahrleistung_simuliert
    gesamt_fahrleistung_simuliert *= skalierungsfaktor

    # Differenz kilometer
    eingesparte_kilometer = gesamtfahrleistung - gesamt_fahrleistung_simuliert

    return carpooling_werte, emissions_ergebnisse, fahrzeuge_eingespart, belegung_verteilung, gesamt_fahrleistung_simuliert, eingesparte_kilometer

# Dash-App erstellen
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("CO2-Einsparung durch Carpooling-Adoption"),
    dcc.Slider(
        id='simulation-slider',
        min=100,
        max=5000,
        step=100,
        value=1000,
        marks={i: f'{i}' for i in range(1000, 5001, 1000)}
    ),
    dcc.Graph(id='simulation-plot'),
    html.Div(id="fahrleistung-info")  # Hier wird die Fahrleistung angezeigt
])

@app.callback(
    [Output('simulation-plot', 'figure'), Output('fahrleistung-info', 'children')],
    [Input('simulation-slider', 'value')]
)
def update_simulation(n_runs):
    # Simulation ausführen
    carpooling_werte, emissions_ergebnisse, fahrzeuge_eingespart, belegung_verteilung, gesamt_fahrleistung_simuliert, eingesparte_kilometer = simulation_carpooling_verhalten(n_runs)

    fig = go.Figure()
    
    # Scatter-Plot für Emissionen
    fig.add_trace(go.Scatter(
        x=carpooling_werte,
        y=emissions_ergebnisse,
        mode='markers',
        name="CO2-Emissionen",
        marker=dict(color='green', opacity=0.5)
    ))

    # Scatter-Plot für CO2-Einsparung
    fig.add_trace(go.Scatter(
        x=carpooling_werte,
        y=emissions_ergebnisse,
        mode='markers',
        name="CO2-Emissionen",
        marker=dict(color='green', opacity=0.5)
    ))

    # Scatter-Plot für Fahrzeugeinsparung
    fig.add_trace(go.Scatter(
        x=carpooling_werte,
        y=fahrzeuge_eingespart,
        mode='markers',
        name="Eingesparte Fahrzeuge (Mio.)",
        marker=dict(color='blue', opacity=0.5),
        yaxis="y2"
    ))

    # Linien für Fahrzeugbelegungen
    for belegung, werte in belegung_verteilung.items():
        fig.add_trace(go.Scatter(
            x=carpooling_werte,
            y=werte,
            mode='lines',
            name=f"Belegung: {belegung} Personen",
            line=dict(width=2),
            opacity=0.6
        ))

    fig.update_layout(
        xaxis_title="Simulierter Carpooling-Anteil (%)",
        template="plotly_white",
        yaxis=dict(
            title=dict(
                text="CO2-Einsparung (Tonnen)",
                font=dict(size=14)
            )
        ),
        yaxis2=dict(
            title=dict(
                text="Eingesparte Fahrzeuge (Millionen)",
                font=dict(size=14)
            ),
            overlaying="y",
            side="right",
            showgrid=False
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.5,  # Position unterhalb der Grafik
            xanchor="center",
            x=0.5
        )
    )

    # Fahrleistungsanzeige als Text-Element zurückgeben
    fahrleistung_info = html.Div([
        html.P(f"Gesamte simulierte Fahrleistung: {gesamt_fahrleistung_simuliert:,.0f} km"),
        html.P(f"Differenz: {eingesparte_kilometer:,.0f} km"),
    ], style={"textAlign": "center", "marginTop": "10px", "fontSize": "16px"})

    return fig, fahrleistung_info

# App starten
if __name__ == '__main__':
    app.run_server(debug=True)
