import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.express as px
import pandas as pd
import krakenex
from datetime import datetime
from main import DataGatherer

k = krakenex.API()
params = {'pair': 'ETHUSD', 'interval': 1440}
data = k.query_public('OHLC', params)
df = pd.DataFrame(data['result']['XETHZUSD'])
df = df[[0,4]]

START_DATE = '2015-01-01'
END_DATE = '2020-08-19'

dg = DataGatherer()
try:
    dg.first_time()
except:
    'DB already exists'

def convert_timestamp_to_date(r):
    return datetime.utcfromtimestamp(r[0])

df['Time'] = df.apply(convert_timestamp_to_date, axis=1)
df = df[['Time', 4]]
df.columns = ['Time', 'Close']
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

fig = px.line(df, x="Time", y="Close")
asset_pairs = dg.get_asset_pairs()
dropdown_options = [{'label': x, 'value': x} for x in asset_pairs]
selected_options = []
app.layout = html.Div(children=[
    html.H1(children='Hello David'),

    html.Div(children='''
        Dash: A web application framework for Python.
    '''),

    
    
    html.Div([
        html.Label('Add Asset Pair'),
        dcc.Dropdown(
            id='pair',
            options = dropdown_options,
            value=[],
            multi=True),

        html.Button(id='add', n_clicks=0, children='Add'),
        html.Div(id='output-state')
    ]),

    html.Div([
        html.Label('Asset Pair'),
        dcc.Dropdown(
            id='select_pair',
            options=selected_options,
            value = None
        ),

        dcc.Graph(
            id='example-graph',
            figure=fig
        ),
    ])

])

@app.callback([Output('output-state', 'children'),
              Output('select_pair', 'options')],
              [Input('add', 'n_clicks')],
              State('pair', 'value'),
               )
def update_output(n_clicks, input1):
    if n_clicks != 0:
        opt = [{'label': x, 'value': x} for x in input1]
        selected_options.extend(opt)
        return f'Asset pair(s) added: {", ".join(input1)}', selected_options
    else:
        return 'Select an asset pair(s), then click "ADD"', selected_options


if __name__ == '__main__':
    app.run_server(debug=True)
    