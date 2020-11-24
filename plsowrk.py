

import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.DropdownMenu(
    [
        dbc.DropdownMenuItem("Item 1", id="item-1"),
        dbc.DropdownMenuItem("Item 2", id="item-2"),
    ],
    label="Item 1",
    id="dropdownmenu",
)


@app.callback(
    Output("dropdownmenu", "label"),
    [Input("item-1", "n_clicks"), Input("item-2", "n_clicks")],
)
def update_label(n1, n2):
    # use a dictionary to map ids back to the desired label
    # makes more sense when there are lots of possible labels
    id_lookup = {"item-1": "Item 1", "item-2": "Item 2"}

    ctx = dash.callback_context

    if (n1 is None and n2 is None) or not ctx.triggered:
        # if neither button has been clicked, return "Not selected"
        return "Not selected"

    # this gets the id of the button that triggered the callback
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    return id_lookup[button_id]


if __name__ == "__main__":
    app.run_server(debug=True)