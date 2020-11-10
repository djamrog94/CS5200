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
dg = DataGatherer()
try:
    dg.first_time()
except:
    print('Database already exists')

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
df = pd.DataFrame([0])
fig = px.line(df)
asset_pairs = dg.get_asset_pairs()
dropdown_options = [{'label': x, 'value': x} for x in asset_pairs]
dg.connect_to_db()
dg.cur.execute(f'SELECT * FROM public.Assets')
opts = list(dg.cur.fetchall())
print(opts)
selected_options = [{'label': x[0], 'value': x[0]} for x in opts]
selected_ticker = 'portfolio'
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
            value = selected_ticker
        ),

        dcc.Graph(
            id='example-graph',
            figure=fig
        ),
    ])

])

@app.callback(
    Output(component_id='example-graph', component_property='figure'),
    [Input(component_id='select_pair', component_property='value')]
)
def update_output_div(input_value):
    if input_value == 'portfolio':
        df = pd.DataFrame({'Time':[1,2,3,4], 'Balance': [10000,12000,11000,15000]})
        return px.line(df, x='Time', y='Balance')
    dg.connect_to_db()
    dg.cur.execute(f"SELECT * FROM public.History WHERE assetID='{input_value}';")
    data = dg.cur.fetchall()
    df = pd.DataFrame(data, columns=dg.columns)
    fig = px.line(df, x="Time", y="Close")
    return fig

@app.callback([Output('output-state', 'children'),
              Output('select_pair', 'options'),
              Output('pair', 'value')],
              [Input('add', 'n_clicks')],
              State('pair', 'value'),
               )
def update_output(n_clicks, input1):
    if n_clicks != 0:
        if input1 == None:
            return 'Select an asset pair(s), then click "ADD"', selected_options, None
        opt = [{'label': x, 'value': x} for x in input1]
        dg.create_table()
        for i in opt:
            if i not in selected_options:
                dg.engine = dg.create_db_engine()
                dg.connect_to_db()
                insert_st = f"INSERT INTO public.Assets VALUES ('{i['label']}')"
                dg.cur.execute(insert_st)
                dg.cur.close()
                dg.conn.commit()
                dg.conn.close()

                selected_options.append(i)
                add_history(i['label'])
        return f'Asset pair(s) added: {", ".join(input1)}', selected_options, None
    else:
        return 'Select an asset pair(s), then click "ADD"', selected_options, None

def add_history(ticker):
    df = dg.collect_data(ticker)
    dg.insert_data_to_db(df)
if __name__ == '__main__':
    app.run_server(debug=True)
    