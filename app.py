import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Output, Input, State
import dash_table
import helpers
from mydb import Database
import plotly.graph_objects as go
from plotly.subplots import make_subplots

db = Database()

app = dash.Dash(external_stylesheets=[dbc.themes.FLATLY])

buy_clicks = 0
order_clicks = 0
asset_clicks = 0
add_clicks = 0
login_click = 0
open_click = 0
logout_click = 0
nn1 = 0
nn2 = 0
cnn1 = 0
cnn2 = 0
unn1 = 0
unn2= 0
user = ''


def empty_graph():
    data = ['Empty', [0], [0]]
    x = data[1]
    y = data[2]
    fig = go.Figure(data=go.Scatter(name='No Graph',x=x, y=y))
    fig.update_layout(
    title={
        'text': "NO GRAPH",
        'y':0.9,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top'})
    return fig

def get_all_pairs():
    asset_pairs = db.get_asset_pairs()
    return [{'label': x, 'value': x} for x in asset_pairs]

def get_select_options():
    sql_stmt = f"SELECT assetID FROM user_asset_detail where username='{user}'"
    opts = db.send_query(sql_stmt, helpers.ResponseType.ALL)
    opts = [{'label': db.get_asset_name(x['assetID']), 'value': db.get_asset_name(x['assetID'])} for x in opts]
    return dcc.Dropdown(id='asset_dropdown', options = opts, value = '')


def get_all_saved():
    sql_stmt = "SELECT * FROM assets"
    opts = db.send_query(sql_stmt, helpers.ResponseType.ALL)
    return [{'label': x['name'], 'value': x['name']} for x in opts]


MIN_ORDER_HEIGHT = 80
ROW_HEIGHT = 35
MAX_HEIGHT = (10 * ROW_HEIGHT) + MIN_ORDER_HEIGHT

def create_order_table():
    order_df = db.get_order_details(user)
    order_details = dash_table.DataTable(
        data=order_df.to_dict('records'),
        columns=[{'id': c, 'name': c} for c in order_df.columns],
        style_cell_conditional=[
        {
            'if': {'column_id': c},
            'textAlign': 'left'
        } for c in ['Date', 'Region']
    ],

    style_as_list_view=True,
    row_selectable='multi',
    selected_rows=[]
    )

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

create_user_input = dbc.FormGroup(
    [
        dbc.Label("Username", html_for="example-email"),
        dbc.Input(type="text", id="create_username", placeholder="Enter username"),
        dbc.FormText(
            "Please enter your username",
            color="secondary",
        ),
    ]
)

create_password_input = dbc.FormGroup(
    [
        dbc.Label("Password", html_for="example-password"),
        dbc.Input(
            type="password",
            id="create_password",
            placeholder="Enter password",
        ),
        dbc.FormText(
            "A password stops mean people taking your stuff", color="secondary"
        ),
    ]
)

first_input = dbc.FormGroup(
    [
        dbc.Label("First Name", html_for="example-password"),
        dbc.Input(
            id="create_first",
            placeholder="First Name",
        ),
        dbc.FormText(
            "Please enter your first name.", color="secondary"
        ),
    ]
)

last_input = dbc.FormGroup(
    [
        dbc.Label("Last Name", html_for="example-password"),
        dbc.Input(
            id="create_last",
            placeholder="Last Name",
        ),
        dbc.FormText(
            "Please enter your last name.", color="secondary"
        ),
    ]
)

open_input = dbc.FormGroup(
    [
        dbc.Label("Account Created Day", html_for="example-password"),
        dbc.Input(
            id="create_open",
            placeholder="What day did you open your account?",
        ),
        dbc.FormText(
            "Please enter the day you opened your account in YYYY-MM-DD format.", color="secondary"
        ),
    ]
)

balance_input = dbc.FormGroup(
    [
        dbc.Label("Starting Balance", html_for="example-password"),
        dbc.Input(
            id="create_balance",
            placeholder="Starting Balance",
        ),
        dbc.FormText(
            "Please enter the starting balance for your account.", color="secondary"
        ),
    ]
)

account_form = dbc.Form([create_user_input, create_password_input, first_input, last_input, open_input, balance_input])

account_modal = html.Div(
    [
        dbc.Button("Create Account", id="create_account_button"),
        dbc.Modal(
            [
                dbc.ModalHeader("Create Account"),
                dbc.ModalBody(account_form),
                dbc.ModalFooter(
                    dbc.Button("Submit", id="account_submit", className="ml-auto")
                ),
            ],
            id="account_modal",
        ),
    ]
)


update_modal = html.Div(
    [
        dbc.Button("Update Order", id="update"),
        dbc.Modal(
            [
                dbc.ModalHeader("Update Order"),
                dbc.ModalBody([dbc.Label('Pick Order:'),
                    dbc.Form([dbc.FormGroup(dcc.Dropdown(id='id_update')),
                    dbc.FormGroup(html.Div(id='update_asset')),
                    dbc.FormGroup(dbc.Input(id='update_open',placeholder='Open Date: Format YYYY-MM-DD')),
                    dbc.FormGroup(dbc.Input(id='update_close',placeholder='Close Date: Format YYYY-MM-DD')),
                    dbc.FormGroup(dbc.Input(id='update_quantity',placeholder='Quantity ($)'))]),
                ]),
                dbc.ModalFooter(
                    dbc.Button("Update Order", id="update_button", className="ml-auto")
                ),
            ],
            id="update_modal",
        ),
    ]
)


button_bar = dbc.ButtonGroup([user_modal, account_modal, dbc.Button(id='logout', n_clicks=0, children='Logout')])

app.layout = html.Div([
    html.Div(id='alert'),
    html.Div(id='alert1'),
    html.Div(id='alert2'),
    html.Div(id='alert3'),
    html.Div(id='user', style={'display': 'none'}),
    html.Div(id='refresh', style={'display': 'none'}),
    dbc.Row(button_bar, style={'width': '25%','float': 'right'}),
    html.H1(f'WELCOME TO PAPERTRADER', style={'padding': '25px'}),
    html.Div(id='title', style={'padding': '25px'}),
    dbc.Row(dbc.Col(html.Div(
    [dbc.Label('Add Asset Pair:'),
            dcc.Dropdown(
                id="pair",
                options=get_all_pairs(),
            ),
        dbc.Button(id='add', n_clicks=0, children='Add Asset', block=True),
            html.Div(id='output-state')
            ], style={'padding': '25px'}),width=3)),
    dbc.Row(dbc.Col(html.Div(
        [dbc.Label('Asset Pair:'),
        html.Div(id='pair_drop', children=get_select_options())
        # dcc.Dropdown(
        #     id="select_pair",
        #     options=get_select_options(),
        #     value = '')
        ,
        dbc.Button(id='remove_asset', n_clicks=0, children='Remove Asset', block=True),
        html.Div(id='remove_asset_status')
    ], style={'padding': '25px'}),width=3
    )),
    dbc.Row([dbc.Col(
        dcc.Graph(
            id='example-graph',
            figure=empty_graph()), width=12
    )]),
    dbc.Row([dbc.Col([
        dbc.Label('Place Order:'),
        dbc.Form([dbc.FormGroup(dbc.Input(id='asset_to_buy', placeholder='Asset Pair')),
        dbc.FormGroup(dbc.Input(id='open_date',placeholder='Open Date: Format YYYY-MM-DD')),
        dbc.FormGroup(dbc.Input(id='close_date',placeholder='Close Date: Format YYYY-MM-DD')),
        dbc.FormGroup(dbc.Input(id='quantity',placeholder='Quantity ($)'))]),
        dbc.Button(id='place_order', n_clicks=0, children='Place Order', block=True),
        html.Div(id='output-state1')
    ], width={'size': 3, 'offset': 1}),
     dbc.Col([
        dbc.Label('Trade History'),
        html.Div(id='order_details', children=create_order_table()),
        dbc.Button(id='remove_order', n_clicks=0, children='Remove Order'),
        html.Div(children=[update_modal], style={'float': 'right'}),
        html.Div(id='order_remove_details')
    ], width={'size': 5, 'offset': 2})
    ])

   
    ], style={'width': '99%'})


@app.callback(
    [Output("update_asset", "children"), Output("update_open", "placeholder"),
     Output("update_close", "placeholder"), Output("update_quantity", "placeholder")],
    [Input("id_update", "value")]
)
def update_modal1(id):
    if id is not None:
        sql_stmt = f"SELECT * FROM orders WHERE orderID={id}"
        resp = db.send_query(sql_stmt, helpers.ResponseType.ONE)
        name = db.get_asset_name(resp['assetID'])
        open = helpers.convert_timestamp_to_date_single(resp['openDate'])
        close = helpers.convert_timestamp_to_date_single(resp['closeDate'])
        quantity = resp['quantity']
        return f"Asset to Update: {name}", f'Prior open date: {open}', f'Prior close date: {close}', f'Prior quantity: {quantity}'
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update


@app.callback(
    [Output("update_modal", "is_open"),Output("alert", "children"), Output('id_update', 'options'), Output('refresh', 'children')],
    [Input("update", "n_clicks"), Input("update_button", "n_clicks")],
    [State("update_modal", "is_open"), State("id_update", "value"),
     State("update_open", "value"), State("update_close", "value"),
     State("update_quantity", "value")]
)
def toggle_modal(un1, un2, is_open, id, open, close, quantity):
    global unn1, unn2

    if un1 is None and un2 is None:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update

    if un1 != unn1:
        unn1 += 1
        if user == '':
            return dash.no_update, dbc.Alert('Login first', color="danger", duration=4000), dash.no_update, dash.no_update

        ids = db.get_order_ids(user)
        if ids == []:
            return dash.no_update, dbc.Alert('No orders to modify', color="danger", duration=4000), dash.no_update, dash.no_update
        return not is_open, dash.no_update, ids, dash.no_update

    if un2 != unn2:
        unn2 += 1
        test = db.update_order(id, open, close, quantity)

        if test[0]:
            return not is_open, dbc.Alert(test[1], color="success", duration=4000), dash.no_update, 'update'
        else:
            return not is_open, dbc.Alert(test[1], color="danger", duration=4000), dash.no_update, dash.no_update

    return is_open


@app.callback(
    [Output("account_modal", "is_open"),Output("alert3", "children")],
    [Input("create_account_button", "n_clicks"), Input("account_submit", "n_clicks")],
    [State("account_modal", "is_open"), State("create_username", "value"),
     State("create_password", "value"), State("create_first", "value"),
     State("create_last", "value"), State("create_open", "value"), State("create_balance", "value")]
)
def toggle_modal(cn1, cn2, is_open, name, pw, first, last, open, balance):
    global cnn1, cnn2

    if cn1 is None and cn2 is None:
        return dash.no_update, dash.no_update

    if cn1 != cnn1:
        cnn1 += 1
        return not is_open, dash.no_update

    if cn2 != cnn2:
        cnn2 += 1
        test = db.create_account(name, pw, first, last, open, balance)
        if test[0]:
            return not is_open, dbc.Alert(test[1], color="success", duration=4000)
        else:
            return not is_open, dbc.Alert(test[1], color="danger", duration=4000)

    return is_open

@app.callback(
    [Output("modal", "is_open"),
    Output("user", "children"),
     Output("username", "value"),
     Output("password", "value"),
     Output("alert1", "children")],
    [Input("open", "n_clicks"), Input("user_submit", "n_clicks"), Input("logout", "n_clicks")],
    [State("modal", "is_open"), State("username", "value"),
     State("password", "value")],
)
def toggle_modal(n1, n2, log, is_open, name, pw):
    global nn1, nn2, logout_click, user
    if logout_click != None and log != logout_click:
        logout_click += 1
        if user == '':
            message = dbc.Alert("Not logged in!", color="warning", duration=1000)
        else:
            message = dbc.Alert("Successfully logged out!", color="success", duration=1000)

        return dash.no_update, '', '', '', message

    if n1 is None and n2 is None:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    if n1 != nn1:
        nn1 += 1
        return not is_open, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    if n2 != nn2:
        nn2 += 1
        test = db.login(name, pw)
        if test:
            return not is_open, name, '', '', dbc.Alert("Successfully logged in!", color="success", duration=4000)
        else:
            return not is_open, dash.no_update, '', '', dbc.Alert("Incorrect Credentials. Try again!", color="danger", duration=4000)

    return is_open, dash.no_update, dash.no_update, dash.no_update, dash.no_update

# major callback
@app.callback([Output('output-state', 'children'),
               Output('pair_drop', 'children'),
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
               Output('title', 'children'),
               Output('alert2', 'children')
               ],
              [Input('add', 'n_clicks'),
               Input('asset_dropdown', 'value'),
               Input('place_order', 'n_clicks'),
               Input('remove_order', 'n_clicks'),
               Input('remove_asset', 'n_clicks'),
               Input('user', 'children'),
               Input('refresh', 'children')
               
                ],
              [State('pair', 'value'),
               State('asset_to_buy', 'value'),
               State('open_date', 'value'),
               State('close_date', 'value'),
               State('quantity', 'value'),
               State('order_details', 'children')]
)


# update basically everything on the screen
def update_output_graph(a_clicks, asset_pair_drop, b_clicks, o_clicks, ass_clicks, user1, re, a_pair, asset_pair_text, open, close, quantity, order_table):
    global add_clicks, buy_clicks, order_clicks, asset_clicks, logout_click, user
    login_first = dbc.Alert("You must login first!", color="danger", duration=1000)
    if user == '':
        welcome = html.H2('Hello, Please login!')
    else:
        welcome = html.H2(f'Hello, {user.title()}!')

    if user1 is not None and user1 != user:
        user = user1
        if user == '':
            welcome = html.H2('Hello, Please login!')
        else:
            welcome = html.H2(f'Hello, {user.title()}!')
        fig = create_graph(None)
        return '', get_select_options(), '', fig, '', '', \
             '', '', '', create_order_table(), '', '', welcome, None
        
    if a_clicks != add_clicks:
        add_clicks += 1
        if user == '':
            return dash.no_update, get_select_options(), None, dash.no_update, dash.no_update, dash.no_update, \
         dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, welcome, login_first
        if a_pair == None:
            ans = 'Select an asset pair(s), then click "ADD"'
        else:
            asset = {'label': a_pair, 'value': a_pair}
            if asset not in get_all_saved():
                db.create_asset(db.get_asset_id(asset['label']), asset['label'])
                db.collect_data(asset['label'])
            if asset not in get_select_options():
                db.add_hist_user(user, a_pair)
                ans = f'Asset pair(s) added: {a_pair}'
            else:
                ans = f'Asset pair(s) already been added!: {a_pair}'
        return ans, get_select_options(), None, dash.no_update, dash.no_update, dash.no_update, \
         dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, welcome, None

    # buy an asset!
    elif b_clicks !=  buy_clicks:
        buy_clicks += 1
        if user == '':
            return dash.no_update, get_select_options(), None, dash.no_update, dash.no_update, dash.no_update, \
         dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, welcome, login_first
        ans = db.create_order(asset_pair_text, open, close, quantity, user)
        fig = create_graph(asset_pair_drop)
        return '', dash.no_update, dash.no_update, fig, asset_pair_drop, ans, \
             '', '', '', create_order_table(), '', '', welcome, None

    # remove orders
    elif o_clicks != order_clicks:
        order_clicks += 1
        if user == '':
            return dash.no_update, get_select_options(), None, dash.no_update, dash.no_update, dash.no_update, \
         dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, welcome, login_first
        rows = order_table['props']['selected_rows']
        orderIDs = [order_table['props']['data'][x]['Order ID'] for x in rows]
        db.remove_order(orderIDs)
        ans = f'Removed {len(rows)} order(s)!'
        fig = create_graph(asset_pair_drop)
        return '', dash.no_update, dash.no_update, fig, asset_pair_drop, \
             '', '', '', '', create_order_table(), ans, '', welcome, None

    # remove asset from history
    elif ass_clicks != asset_clicks:
        asset_clicks += 1
        if user == '':
            return dash.no_update, get_select_options(), None, dash.no_update, dash.no_update, dash.no_update, \
         dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, welcome, login_first
        ans = db.remove_asset(user, asset_pair_drop)
        fig = create_graph('')
        return '', get_select_options(), None, fig, '', '', \
             '', '', '', create_order_table(), '', ans, welcome, None

    elif re == 'refresh':
        fig = create_graph('')
        return '', get_select_options(), None, fig, '', '', \
             '', '', '', create_order_table(), '', dash.no_update, welcome, None

    # update graph based on drop down selection
    else:
        fig = create_graph(asset_pair_drop)
        return '', dash.no_update, dash.no_update, fig, asset_pair_drop, '', \
             '', '', '', create_order_table(), '', '', welcome, None



def create_graph(asset):
    port_title = 'Portfolio Balance'
    if asset is None or user == '' or asset == '':
        if user == '':
            return empty_graph()
        else:
            pl = db.calc_profit('port', user)
            fig = make_subplots(rows=1, cols=2, subplot_titles=('No Asset Selected', port_title))
            fig.add_trace(go.Scatter(x=[0],y=[0],mode='lines', name='No Graph'), row=1, col=1)
            fig.add_trace(go.Scatter(x=pl['Time'],y=pl['Balance'],mode='lines', name='Portfolio Balance'), row=1, col=2)
            fig.update_yaxes(tickformat = '$', row=1, col=1)
            fig.update_yaxes(tickformat = '$', row=1, col=2)
            return fig
    
    df = db.get_history(asset)
    open, close = db.get_orders(user, asset)

    # personal graph
    pl = db.calc_profit('port', user)

    if open is None:
        fig = make_subplots(rows=1, cols=2, subplot_titles=(f'{asset} History', port_title))
        fig.add_trace(go.Scatter(x=df['Time'],y=df['Close'],mode='lines', name='Asset History'), row=1, col=1)
        fig.add_trace(go.Scatter(x=pl['Time'],y=pl['Balance'],mode='lines', name='Portfolio Balance'), row=1, col=2)
        fig.update_yaxes(tickformat = '$', row=1, col=1)
        fig.update_yaxes(tickformat = '$', row=1, col=2)
        return fig

    fig = make_subplots(rows=1, cols=2, subplot_titles=(f'{asset} History', port_title))
    
    fig.add_trace(go.Scatter(name='Asset History', x=df['Time'],y=df['Close'],mode='lines'), row=1, col=1)
    fig.add_trace(go.Scatter(name='Open Positions', x=open['Time'],y=open['Close'], mode='markers', marker_size=10, marker_symbol=5, marker_color="green"), row=1, col=1)
    fig.add_trace(go.Scatter(name='Close Positions', x=close['Time'],y=close['Close'], mode='markers', marker_size=10, marker_symbol=6, marker_color="red"), row=1, col=1)
    fig.add_trace(go.Scatter(name='Portfolio Balance', x=pl['Time'],y=pl['Balance'], mode='lines'), row=1, col=2)
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
    