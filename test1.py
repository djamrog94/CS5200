import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px
from mydb import Database
import helpers
import dash_table
import plotly.io as plt_io

app = dash.Dash(external_stylesheets=[dbc.themes.FLATLY])
dg = Database()

def empty_graph():
    df = pd.DataFrame([0])
    fig = px.line(df)
    return fig

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
            id="example-password",
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


@app.callback(
    Output("modal", "is_open"),
    [Input("open", "n_clicks"), Input("user_submit", "n_clicks")],
    [State("modal", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

app.layout = html.Div([
    dbc.Row(dbc.Col(user_modal), style={'float': 'right'}),
    html.H1('WELCOME TO PAPER TRADER'),
    dbc.Row(dbc.Col(
        [dbc.Label('Add Asset Pair:'),
        dbc.Select(
            id="select",
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
        ),
        dbc.Col(
        dcc.Graph(
            id='example-graph1',
            figure=empty_graph())
    )    
    ]),
    dbc.Row([dbc.Col([
        dbc.Label('Place Order:'),
        html.Div([dbc.InputGroup(dbc.Input(placeholder='Asset Pair')),
        dbc.InputGroup(dbc.Input(placeholder='Open Date')),
        dbc.InputGroup(dbc.Input(placeholder='Close Date')),
        dbc.InputGroup(dbc.Input(placeholder='Quantity'))
        ], style={'width': '49%'}),
        dbc.Button(id='place_order', n_clicks=0, children='Place Order')

    ]), dbc.Col([
        dbc.Label('Trade History'),
        html.Div(create_order_table())
    ],  width={"size": 5, "order": 2, "offset": 1})])
]) 

if __name__ == "__main__":
    app.run_server(debug=True)