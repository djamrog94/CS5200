from logging import log
import dash
import os
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

# Since we're adding callbacks to elements that don't exist in the app.layout,
# Dash will raise an exception to warn us that we might be
# doing something wrong.
# In this case, we're adding the elements through a callback, so we can ignore
# the exception.
dg = Database()
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)


index_page = html.Div(id='index_page', children = [
    html.H1(children='Welcome to paperTrader. Please Login'),
    html.Label('Username:'),
    dcc.Input(id='username', type='text', value=''),
    html.Label('Password:'),
    dcc.Input(id='password', type='text', value=''),
    html.Label('Starting Balance:'),
    dcc.Input(id='balance', type='text', value=''),
    html.Label('Account Open Date:'),
    dcc.Input(id='openDate', type='text', value=''),
    html.Div([
        html.Button(id='login', n_clicks=0, children='Login'),
    html.Button(id='create', n_clicks=0, children='Create Account')]),
    html.Div(id='login_status'),
    
], style={'display': 'block', 'line-height':'0', 'height': '0', 'overflow': 'hidden'})
log_click = 0
create_click = 0
user = ''

        # create account

buy_clicks = 0
order_clicks = 0
asset_clicks = 0
add_clicks = 0

def empty_graph():
    df = pd.DataFrame([0])
    return px.line(df)

def get_all_pairs():
    asset_pairs = dg.get_asset_pairs()
    return [{'label': x, 'value': x} for x in asset_pairs]

def get_select_options():
    sql_stmt = f'SELECT * FROM Assets'
    opts = dg.send_query(sql_stmt, helpers.ResponseType.ALL)
    return [{'label': x['name'], 'value': x['name']} for x in opts]

MIN_ORDER_HEIGHT = 65
ROW_HEIGHT = 35
MAX_HEIGHT = (10 * ROW_HEIGHT) + MIN_ORDER_HEIGHT

def create_order_table():
    order_df = dg.get_order_details()
    if len(order_df) == 0:
        height = MIN_ORDER_HEIGHT
    elif len(order_df) <= 10:
        height = MIN_ORDER_HEIGHT + (ROW_HEIGHT * len(order_df))
    else:
        height = MAX_HEIGHT
    order_details = dash_table.DataTable(
        data=order_df.to_dict('records'),
        columns=[{'id': c, 'name': c} for c in order_df.columns],
        style_cell_conditional=[
        {
            'if': {'column_id': c},
            'textAlign': 'left'
        } for c in ['Date', 'Region']
    ],
    style_table={'height': height, 'overflowY': 'auto'},

    style_as_list_view=True,
    filter_action="native",
    sort_action="native",
    sort_mode="multi",
    row_selectable='multi',
    selected_rows=[])
    return order_details

page_1_layout = html.Div( id='page_1_layout', children=[
    html.Div(dcc.Link('Logout', href='/index'), style={'float': 'right'}),
    html.H1('HELLO RICH MAN'),
    html.Div(id='title',children=f'''
        Welcome to paperTrader, {user}. Here you can track all of your orders!
    '''),

    
    html.Div([
        html.Label('Add Asset Pair'),
        dcc.Dropdown(
            id='pair',
            options = get_all_pairs(),
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
                options=get_select_options(),
                value = ''
            ),
            html.Button(id='remove_asset', n_clicks=0, children='Remove Asset'),
            html.Div(id='remove_asset_status')

        ]),
    ], style={'width': '49%'}),
            dcc.Graph(
                id='example-graph',
                figure=empty_graph(),
            ),

    html.Div([
        html.Div([
            html.Label('Asset Pair'),
            dcc.Input(id='asset_to_buy', type='text', value='')], style={'width': '49%', 'float': 'left'}),
        html.Div([
             html.Label('Trade History'),
             dcc.Dropdown(
            id='trade_history',
            options = get_all_pairs(),
            value=''),
            html.Div(id='order_details', children=create_order_table()),
            html.Button(id='remove_order', n_clicks=0, children='Remove Order(s)'),
            html.Div(id='order_remove_details')
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
], style={'display': 'block', 'line-height':'0', 'height': '0', 'overflow': 'hidden'})

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content', children=[index_page, page_1_layout])
])


@app.callback([Output('url', 'pathname'),Output('login_status', 'children')],
              [Input('login', 'n_clicks'),
               Input('create', 'n_clicks')
                ],
              [State('username', 'value'),
               State('password', 'value'),
               State('balance', 'value'),
               State('openDate', 'value')]
               )

def login(l_click, c_click, username, password, balance, date):
    global log_click, create_click, user
    if l_click != log_click:
        log_click += 1
        resp = dg.login(username, password)
        if resp:
            user = username
            return '/page-1', 'success'
            # click
        else:
            return '/index', 'fail'

    elif c_click != create_click:
        create_click += 1
        dg.create_account(username, password, balance, date)
        return '/index', f'Created account for {username}'
    else:
        return dash.no_update
    # You could also return a 404 "URL not found" page here

    # Update the index
@app.callback([Output('index_page', 'style'),
               Output('page_1_layout', 'style')],
              Input('url', 'pathname'))

def display_page(pathname):
    return_value = [{'display': 'block', 'line-height': '0', 'height': '0', 'overflow': 'hidden'} for _ in range(2)]
    if pathname == '/page-1':
        return_value[1] = {'height': 'auto', 'display': 'inline-block'}
        return return_value
    else:
        return_value[0] = {'height': 'auto', 'display': 'inline-block'}
        return return_value

# major callback
@app.callback([Output('output-state', 'children'),
               Output('select_pair', 'options'),
               Output('pair', 'value'),
               Output('example-graph', 'figure'),
               Output('asset_to_buy', 'value'),
               Output('output-state1', 'children'),
               Output('open_date', 'value'),
               Output('close_date', 'value'),
               Output('quantity', 'value'),
               Output('order_details', 'children'),
               Output('order_remove_details', 'children'),
               Output('remove_asset_status', 'children'),
               ],
              [Input('add', 'n_clicks'),
               Input('select_pair', 'value'),
               Input('buy', 'n_clicks'),
               Input('remove_order', 'n_clicks'),
               Input('remove_asset', 'n_clicks'),
                ],
              [State('pair', 'value'),
               State('asset_to_buy', 'value'),
               State('open_date', 'value'),
               State('close_date', 'value'),
               State('quantity', 'value'),
               State('order_details', 'children')]
               )

# update basically everything on the screen
def update_output_graph(a_clicks, asset_pair_drop, b_clicks, o_clicks, ass_clicks, a_pair, asset_pair_text, open, close, quantity, order_table):
    global add_clicks, buy_clicks, order_clicks, asset_clicks
    if a_clicks != add_clicks:
        add_clicks += 1
        if a_pair == None:
            ans = 'Select an asset pair(s), then click "ADD"'
        else:
            opt = [{'label': x, 'value': x} for x in a_pair]
            for i in opt:
                if i not in get_select_options():
                    dg.create_asset(dg.get_asset_id(i['label']), i['label'])
                    dg.collect_data(i['label'])
            ans = f'Asset pair(s) added: {", ".join(a_pair)}'
        return ans, get_select_options(), None, dash.no_update, dash.no_update, dash.no_update, \
         dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    # buy an asset!
    elif b_clicks != buy_clicks:
        buy_clicks += 1
        ans = ''
        try:
            dg.create_order(asset_pair_text, open, close, quantity, user)
            ans = f'Order placed to buy ${quantity} of {asset_pair_text} completed!'
            
        except:
            ans = 'Order couldnt be placed!'
        fig = create_graph(asset_pair_drop)
        return '', dash.no_update, dash.no_update, fig, asset_pair_drop, ans, \
             '', '', '', create_order_table(), '', ''

    # remove orders
    elif o_clicks != order_clicks:
        order_clicks += 1
        rows = order_table['props']['selected_rows']
        orderIDs = [order_table['props']['data'][x]['Order ID'] for x in rows]
        dg.remove_order(orderIDs)
        ans = f'Removed {len(rows)} order(s)!'
        fig = create_graph(asset_pair_drop)
        return '', dash.no_update, dash.no_update, fig, asset_pair_drop, \
             '', '', '', '', create_order_table(), ans, ''

    # remove asset from history
    elif ass_clicks != asset_clicks:
        asset_clicks += 1
        ans = dg.remove_asset(asset_pair_drop)
        fig = create_graph('')
        return '', get_select_options(), None, fig, '', '', \
             '', '', '', create_order_table(), '', ans

    # update graph based on drop down selection
    else:
        fig = create_graph(asset_pair_drop)
        return '', dash.no_update, dash.no_update, fig, asset_pair_drop, '', \
             '', '', '', create_order_table(), '', ''



def create_graph(asset):
    port_title = 'Portfolio Balance'
    if asset == '':
        pl = dg.calc_profit('port', user)
        fig = make_subplots(rows=1, cols=2, subplot_titles=('No Asset Selected', port_title))
        fig.add_trace(go.Scatter(x=[0],y=[0],mode='lines'), row=1, col=1)
        fig.add_trace(go.Scatter(x=pl['Time'],y=pl['Balance'],mode='lines'), row=1, col=2)
        fig.update_yaxes(tickformat = '$', row=1, col=1)
        fig.update_yaxes(tickformat = '$', row=1, col=2)
        return fig
    
    df = dg.get_history(asset)
    open, close = dg.get_orders(asset)

    # personal graph
    pl = dg.calc_profit('port', user)

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


if __name__ == '__main__':
    app.run_server(debug=True)