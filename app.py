import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input, State
import dash_table
import plotly.express as px
import pandas as pd
import helpers
from mydb import Database
import plotly.graph_objects as go
from plotly.subplots import make_subplots

dg = Database()

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
df = pd.DataFrame([0])
fig = px.line(df)
asset_pairs = dg.get_asset_pairs()
dropdown_options = [{'label': x, 'value': x} for x in asset_pairs]
sql_stmt = f'SELECT * FROM Assets'
opts = dg.send_query(sql_stmt, helpers.ResponseType.ALL)
selected_options = [{'label': x['name'], 'value': x['name']} for x in opts]
selected_ticker = ''

clicks = 0

def create_order_table():
    order_df = dg.get_order_details()
    order_details = dash_table.DataTable(
        data=order_df.to_dict('records'),
        columns=[{'id': c, 'name': c} for c in order_df.columns],
        style_cell_conditional=[
        {
            'if': {'column_id': c},
            'textAlign': 'left'
        } for c in ['Date', 'Region']
    ],
    style_table={'height': 330, 'overflowY': 'auto'},

    style_as_list_view=True,)
    return order_details

app.layout = html.Div(children=[
    html.H1(children='Hello David'),

    html.Div(children='''
        Welcome to paperTrader. Here you can track all of your orders!
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
    ], style={'width': '49%'}),

    html.Div([
        html.Div([
            html.Label('Asset Pair'),
            dcc.Dropdown(
                id='select_pair',
                options=selected_options,
                value = ''
            ),

        ]),
    ], style={'width': '49%'}),
            dcc.Graph(
                id='example-graph',
                figure=fig,
            ),

    html.Div([
        html.Div([
            html.Label('Asset Pair'),
            dcc.Input(id='asset_to_buy', type='text', value='')], style={'width': '49%', 'float': 'left'}),
        html.Div([
             html.Label('Trade History'),
             dcc.Dropdown(
            id='trade_history',
            options = dropdown_options,
            value=''),
            html.Div(id='order_details', children=create_order_table())
        ], style={'width': '49%', 'float': 'right'}),

            html.Label('Open Date | Format YYYY-MM-DD'),
            dcc.Input(id='open_date', type='text', value=''),
            html.Label('Close Date'),
            dcc.Input(id='close_date', type='text', value=''),
            html.Label('Dollar Value'),
            dcc.Input(id='quantity', type='text', value=''),
            html.Button(id='buy', n_clicks=0, children='Place Trade'),
            html.Div(id='output-state1'),
         

    ])
])


@app.callback([Output('example-graph', 'figure'),
               Output('asset_to_buy', 'value'),
               Output('output-state1', 'children'),
               Output('open_date', 'value'),
               Output('close_date', 'value'),
               Output('quantity', 'value'),
               Output('order_details', 'children')],
              [Input('select_pair', 'value'),
               Input('buy', 'n_clicks'),
                ],
              [State('asset_to_buy', 'value'),
               State('open_date', 'value'),
               State('close_date', 'value'),
               State('quantity', 'value')],
               )

def update_output_graph(asset_pair_drop, n_clicks, asset_pair_text, open, close, quantity):
    # drop down trigger
    global clicks
    if n_clicks == clicks:
        fig = create_graph(asset_pair_drop)
        return fig, asset_pair_drop, '', '', '', '', create_order_table()

    # button press trigger
    else:
        
        clicks += 1
        ans = ''
        try:
            dg.create_order(asset_pair_text, open, close, quantity)
            ans = f'Order placed to buy ${quantity} of {asset_pair_text} completed!'
            
        except:
            ans = 'Order couldnt be placed!'
        fig = create_graph(asset_pair_drop)
        return fig, asset_pair_drop, ans, '', '', '', create_order_table()

def create_graph(asset):
    port_title = 'Portfolio Balance'
    if asset == '':
        pl = dg.calc_profit('port')
        fig = make_subplots(rows=1, cols=2, subplot_titles=('No Asset Selected', port_title))
        fig.add_trace(go.Scatter(x=[0],y=[0],mode='lines'), row=1, col=1)
        fig.add_trace(go.Scatter(x=pl['Time'],y=pl['Balance'],mode='lines'), row=1, col=2)
        fig.update_yaxes(tickformat = '$', row=1, col=1)
        fig.update_yaxes(tickformat = '$', row=1, col=2)
        return fig
    
    # asset graph
    print(asset)
    df = dg.get_history(asset)
    open, close = dg.get_orders(asset)

    # personal graph
    pl = dg.calc_profit('port')

    if open is None:
        fig = make_subplots(rows=1, cols=2, subplot_titles=(f'{asset} History', port_title))
        fig.add_trace(go.Scatter(x=df['Time'],y=df['Close'],mode='lines'), row=1, col=1)
        fig.add_trace(go.Scatter(x=pl['Time'],y=pl['Balance'],mode='lines'), row=1, col=2)
        fig.update_yaxes(tickformat = '$', row=1, col=1)
        fig.update_yaxes(tickformat = '$', row=1, col=2)
        return fig

    fig = make_subplots(rows=1, cols=2, subplot_titles=(f'{asset} History', port_title))
    
    fig.add_trace(go.Scatter(x=df['Time'],y=df['Close'],mode='lines'), row=1, col=1)
    fig.add_trace(go.Scatter(x=open['Time'],y=open['Close'], mode='markers', marker_size=10, marker_symbol=5, marker_color="green"), row=1, col=1)
    fig.add_trace(go.Scatter(x=close['Time'],y=close['Close'], mode='markers', marker_size=10, marker_symbol=6, marker_color="red"), row=1, col=1)
    fig.add_trace(go.Scatter(x=pl['Time'],y=pl['Balance'], mode='lines'), row=1, col=2)
    fig.update_traces(marker=dict(size=12,
                            line=dict(width=2,
                                        color='DarkSlateGrey')),
                selector=dict(mode='markers'))
    fig.update_yaxes(tickformat = '$', row=1, col=1)
    fig.update_yaxes(tickformat = '$', row=1, col=2)
    return fig


@app.callback([Output('output-state', 'children'),
              Output('select_pair', 'options'),
              Output('pair', 'value')],
              [Input('add', 'n_clicks')],
              State('pair', 'value'),
               )

def update_assets(n_clicks, input1):
    if n_clicks != 0:
        if input1 == None:
            return 'Select an asset pair(s), then click "ADD"', selected_options, None
        opt = [{'label': x, 'value': x} for x in input1]
        for i in opt:
            if i not in selected_options:
                dg.create_asset(dg.get_asset_id(i['label']), i['label'])
                dg.collect_data(i['label'])
                selected_options.append(i)
        return f'Asset pair(s) added: {", ".join(input1)}', selected_options, None
    else:
        return 'Select an asset pair(s), then click "ADD"', selected_options, None

if __name__ == '__main__':
    # app.run_server()
    app.run_server(debug=True)
    