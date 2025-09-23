import streamlit as st
import pickle
import pandas as pd
import requests
import gdown
import os

MOVIE_DIC_ID = "1DwzwzVJ_rwpNt-IN92ymqYRbWsREpivZ"   
SIMILARITY_ID = "1wOIEQa6K6aVwklVrgH8-RyxrbocFr-GT"  
API_KEY = os.getenv("TMDB_API_KEY")  # from .env file
def download_file(file_id, output):
    """Download file from Google Drive if not exists"""
    if not os.path.exists(output):
        url = f"https://drive.google.com/uc?id={file_id}"
        gdown.download(url, output, quiet=False)

def fetch_poster(movie_id):
    """Fetch poster from TMDB API"""
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US"
    response = requests.get(url)
    data = response.json()
    if "poster_path" in data and data["poster_path"]:
        return "https://image.tmdb.org/t/p/w500" + data["poster_path"]
    else:
        return "https://via.placeholder.com/500x750?text=No+Image"

def recommend(movie):
    """Return top 5 similar movies"""
    movie = movie.lower()
    matches = movies[movies['title'].str.lower() == movie]

    if matches.empty:
        return []

    movie_index = matches.index[0]
    distances = similarity[movie_index]
    movie_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    recommended_movies = []
    recommended_posters = []

    for i in movie_list:
        movie_id = movies.iloc[i[0]].movie_id
        recommended_movies.append(movies.iloc[i[0]].title)
        recommended_posters.append(fetch_poster(movie_id))

    return recommended_movies, recommended_posters


download_file(MOVIE_DIC_ID, "movie_dic.pkl")
download_file(SIMILARITY_ID, "similarity.pkl")
movies = pickle.load(open("movie_dic.pkl", "rb"))
similarity = pickle.load(open("similarity.pkl", "rb"))
st.title("Movie Recommender System")
selected_movie = st.selectbox(
    "Search for a movie:",
    movies['title'].values
)
if st.button("Recommend"):
    names, posters = recommend(selected_movie)

    if not names:
        st.error(" Movie not found in database")
    else:
        st.write("### Top 5 Recommendations:")
        cols = st.columns(5)  # 5 small boxes
        for idx, col in enumerate(cols):
            with col:
                st.image(posters[idx], caption=names[idx], width=150)
