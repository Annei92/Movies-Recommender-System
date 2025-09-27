# Movie Recommender (Streamlit)

Type a movie title , get similar films with poster art and quick star cues (stars = similarity, not IMDb rating).
Built with Python, Streamlit, pandas, precomputed similarity, and TMDB posters.

# Demo

Live app: add your Streamlit Cloud (https://movies-recommender-system-e5ugcnuw3cmuxdbpl3sjnb.streamlit.app/)


## How it works (ranking)

Uses a precomputed similarity matrix (similarity.pkl) over movies (movie_dic.pkl).
When you pick a movie, we sort by its row in that matrix (highest first).
The gold stars are a min-max remap of similarity to 0–5 for the displayed set (not IMDb ratings).
TMDB is used only to fetch posters.
