from dash import Dash, dcc, html, Input, Output, callback
from dash.exceptions import PreventUpdate
import pandas as pd
import numpy as np

movie_data = pd.read_csv("movies.csv")
rating_data = pd.read_csv("ratings.csv")
links_data = pd.read_csv("links.csv")

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
    
    search = movie_data[movie_data["title"].str.contains(search_value, case=False, na=False)].head(30)
    
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
    film_A = movie_ID

    liking_film_A = rating_data[
        (rating_data["movieId"] == film_A) & 
        (rating_data["rating"] >= 4.0)
    ].sort_values("userId")

    users = liking_film_A["userId"].unique()

    rekommend = rating_data[
        (rating_data["userId"].isin(users)) & 
        (rating_data["movieId"] != film_A) & 
        (rating_data["rating"] >= 4)
    ].groupby("movieId").size()

    rating_count = rating_data.groupby("movieId").size()

    rekommend = rekommend / len(users)
    rekommend = rekommend / np.sqrt(rating_count)

    try_top15 = (rekommend.sort_values(ascending=False).head(25))

    top15_score = try_top15.reset_index()
    top15_score.columns = ["movieId", "score"]

    top15 = top15_score.merge(movie_data, on="movieId")
    top15_year = top15.merge(movie_data, on=["movieId", "title", "genres"])
    top15_year = top15_year.merge(links_data[["movieId", "imdbId"]], how="left")

    top = top15_year.sort_values("score", ascending=False)

    genrer = movie_data[movie_data["movieId"] == film_A]["genres"].iloc[0].split("|")

    for i, genres in enumerate(top["genres"]):
        genre_list = genres.split("|")
        matches = 0
        for g in genre_list:
            if g in genrer:
                matches += 1
        if matches > 0:
            similarity = matches / len(genrer)
            top.loc[i, "score"] += similarity

    resultat = top.sort_values("score", ascending=False).head(5)
    return resultat["title"].tolist()


if __name__ == "__main__":
    app.run(debug=True)