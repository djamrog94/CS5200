import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
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

# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)

# # app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
app = dash.Dash(external_stylesheets=[dbc.themes.FLATLY])
dg = Database()

buy_clicks = 0
order_clicks = 0
asset_clicks = 0
add_clicks = 0
login_click = 0
open_click = 0
user = ''


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
    order_df = dg.get_order_details(user)
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
    style_table={'height': height, 'width': 'auto', 'overflowY': 'auto'},

    style_as_list_view=True,
    filter_action="native",
    sort_action="native",
    sort_mode="multi",
    row_selectable='multi',
    selected_rows=[])
    return order_details

user_input = dbc.FormGroup(
    [
        dbc.Label("Username", html_for="example-email"),
        dbc.Input(type="text", id="username", placeholder="Enter username"),
        dbc.FormText(
            "Please enter your username",
            color="secondary",
        ),
    ]
)

password_input = dbc.FormGroup(
    [
        dbc.Label("Password", html_for="example-password"),
        dbc.Input(
            type="password",
            id="password",
            placeholder="Enter password",
        ),
        dbc.FormText(
            "A password stops mean people taking your stuff", color="secondary"
        ),
    ]
)

user_form = dbc.Form([user_input, password_input])

user_modal = html.Div(
    [
        dbc.Button("Login", id="open"),
        dbc.Modal(
            [
                dbc.ModalHeader("User Login"),
                dbc.ModalBody(user_form),
                dbc.ModalFooter(
                    dbc.Button("Submit", id="user_submit", className="ml-auto")
                ),
            ],
            id="modal",
        ),
    ]
)

app.layout = html.Div([
    html.Div(id='user', style={'display': 'none'}),
    dbc.Row(dbc.Col(user_modal), style={'float': 'right'}),
    html.H1(f'WELCOME TO PAPERTRADER'),
    html.Div(id='title'),
    dbc.Row(dbc.Col(
        [dbc.Label('Add Asset Pair:'),
        dbc.Select(
            id="pair",
            options=get_all_pairs(),
        ),
    dbc.Button(id='add', n_clicks=0, children='Add Asset'),
        html.Div(id='output-state')
        ], width=3
    )),
    dbc.Row(dbc.Col(
        [dbc.Label('Asset Pair:'),
        dbc.Select(
            id="select_pair",
            options=get_select_options(),
        ),
        dbc.Button(id='remove_asset', n_clicks=0, children='Remove Asset'),
        html.Div(id='remove_asset_status')
    ], width=3
    )),
    dbc.Row([dbc.Col(
        dcc.Graph(
            id='example-graph',
            figure=empty_graph()) 
    )]),
    dbc.Row([dbc.Col([
        dbc.Label('Place Order:'),
        html.Div([dbc.InputGroup(dbc.Input(id='asset_to_buy', placeholder='Asset Pair')),
        dbc.InputGroup(dbc.Input(id='open_date',placeholder='Open Date')),
        dbc.InputGroup(dbc.Input(id='close_date',placeholder='Close Date')),
        dbc.InputGroup(dbc.Input(id='quantity',placeholder='Quantity'))
        ], style={'width': '49%'}),
        dbc.Button(id='place_order', n_clicks=0, children='Place Order'),
        html.Div(id='output-state1')

    ]), dbc.Col([
        dbc.Label('Trade History'),
        html.Div(id='order_details', children=create_order_table()),
        dbc.Button(id='remove_order', n_clicks=0, children='Remove Order'),
        html.Div(id='order_remove_details')
    ],  width={"size": 6, "order": 2, "offset": 1})])
]) 

@app.callback(
    [Output("modal", "is_open"),Output("user", "children")],
    [Input("open", "n_clicks"), Input("user_submit", "n_clicks")],
    [State("modal", "is_open"), State("username", "value"),
     State("password", "value")],
)
def toggle_modal(n1, n2, is_open, name, pw):
    if n1 or n2:
        test = dg.login(name, pw)
        if test:
            return not is_open, name
        else:
            return not is_open, dash.no_update
    return is_open, dash.no_update

@app.callback(Output('title', 'children'), Input('user', 'children'))
def get_name(user1):
    global user
    if user1 != None:
        user = user1
        return html.H2(f'Hello, {user1}!')
    return dash.no_update


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
               Input('place_order', 'n_clicks'),
               Input('remove_order', 'n_clicks'),
               Input('remove_asset', 'n_clicks'),
               Input('title', 'children'),
                ],
              [State('pair', 'value'),
               State('asset_to_buy', 'value'),
               State('open_date', 'value'),
               State('close_date', 'value'),
               State('quantity', 'value'),
               State('order_details', 'children')]
)

# update basically everything on the screen
def update_output_graph(a_clicks, asset_pair_drop, b_clicks, o_clicks, ass_clicks, user, a_pair, asset_pair_text, open, close, quantity, order_table):
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
    if asset is None:
        if user == '':
            return empty_graph()
        else:
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
    # app.run_server()
    app.run_server(debug=True)
    