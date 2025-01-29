# Transport_type = PRIV_MOT_TRANSP
# Transport_mean = CAR_DRIV, CAR_PASS, TAXI, TAXI_LIKE
# Travel_Reason = ALL_REAS
# Socio_DEMO_Variable_Type = ??
# Socio_demo_variable = ??
# UNIT_MEAS = KM (Tagesdistanz in km), MIN (Mittlere Zeit unterwegs = reduzieren)

# Verteilung der Fahrzeuge Benzin (60.4%), Diesel (25.2%), Hybrid (7.5%), Plug-in-Hybrid (2.1%), Elektrisch (4.2%)

import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go

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

# Daten und Parameter
gesamtfahrleistung = 22_577_600_000  #Nationalstrassen 27.4 Mrd KM (2021) -> 17.6% von Nutzfahrzeugen und Lieferwagen
emissionen_pro_km = {"benzin": 150, "diesel": 120, "elektro": 50}  # g CO₂/km
fahrzeugverteilung = {"benzin": 0.6, "diesel": 0.3, "elektro": 0.1}  # Verteilung der Fahrzeugtypen

# CO2
def berechne_emissionen(carpooling_anteil):
    auslastung_vorher = 1.2
    auslastung_nachher = 3.0
    reduzierte_fahrleistung = gesamtfahrleistung * (auslastung_vorher / auslastung_nachher) * (1 - carpooling_anteil)
    emissionen = sum(
        reduzierte_fahrleistung * emissionen_pro_km[typ] * fahrzeugverteilung[typ] / 1_000
        for typ in emissionen_pro_km
    )
    return emissionen

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("CO2-Emissionen in Abhängigkeit vom Carpooling-Anteil"),
    dcc.Slider(
        id='carpooling-slider',
        min=0,
        max=1,
        step=0.01,
        value=0.5,
        marks={i/10: f'{i*10}%' for i in range(0, 11)}
    ),
    dcc.Graph(id='emissionen-plot'),
])

@app.callback(
    Output('emissionen-plot', 'figure'),
    [Input('carpooling-slider', 'value')]
)
def update_plot(carpooling_anteil):
    emissionen = berechne_emissionen(carpooling_anteil)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=["Nach Carpooling"],
        y=[emissionen],
        name="CO2-Emissionen",
        marker_color='green'
    ))
    fig.update_layout(
        title=f"CO2-Emissionen bei Carpooling-Anteil: {carpooling_anteil*100:.0f}%",
        xaxis_title="Carpooling-Szenario",
        yaxis_title="CO2-Emissionen (Tonnen)",
        template="plotly_white"
    )
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)



