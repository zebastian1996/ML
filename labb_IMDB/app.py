from dash import Dash, dcc, html, Input, Output, callback
from dash.exceptions import PreventUpdate
import pandas as pd
import numpy as np
import os #kommer snart fix med os


movie_data = pd.read_csv(r'skriv in din väg till "movies.csv" här')
rating_data = pd.read_csv('skriv in din väg till "ratings.csv" här')

app = Dash(__name__)

app.layout = html.Div([
    html.H1("My recommendation app"),
    dcc.Dropdown(
        id='movie-dropdown',
        searchable=True,
        options=[],
        placeholder="sök efter film här",
    ),
    html.Div(id='recommendation-output')
])

@callback(
    Output("movie-dropdown", "options"),
    Input("movie-dropdown", "search_value")
)
def update_options(search_value):
    if not search_value:
        raise PreventUpdate
    
    search = movie_data[movie_data["title"].str.contains(search_value, case=False)].head(30)
    
    return [{"label": row["title"], "value": row["movieId"]} for _, row in search.iterrows()]

@callback(
    Output('recommendation-output', 'children'),
    Input('movie-dropdown', 'value')
)
def update_output(movie_id):
    if not movie_id:
        return "Välj en film först"
    top5 = rekomend(movie_id)
    return html.Ul([html.Li(title) for title in top5])

def rekomend(movie_ID):

    liking_film_A = rating_data[
        (rating_data["movieId"] == movie_ID) & 
        (rating_data["rating"] >= 4.0)
    ].sort_values("userId")

    users = liking_film_A["userId"].unique()

    rekommend = rating_data[
        (rating_data["userId"].isin(users)) & 
        (rating_data["movieId"] != movie_ID) & 
        (rating_data["rating"] >= 4)
    ].groupby("movieId").size()

    rating_count = rating_data.groupby("movieId").size()

    rekommend = rekommend / len(users)
    rekommend = rekommend / np.sqrt(rating_count)

    top30 = (rekommend.sort_values(ascending=False).head(25))

    top30 = top30.reset_index()
    top30.columns = ["movieId", "score"]

    top = top30.merge(movie_data, on="movieId")


    genrer = movie_data[movie_data["movieId"] == movie_ID]["genres"].iloc[0].split("|")

    for i, genres in enumerate(top["genres"]):
        genre_list = genres.split("|")
        matches = 0
        for g in genre_list:
            if g in genrer:
                matches += 1
        if matches > 0:
            similarity = matches / len(genrer)
            top.loc[i, "score"] += similarity

    return top.sort_values("score", ascending=False).head(5)["title"].tolist()

if __name__ == "__main__":
    app.run(debug=True)