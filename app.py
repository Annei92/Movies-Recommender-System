import streamlit as st
import pickle
import pandas as pd
import requests
from dotenv import load_dotenv
import os
import gdown
import os

def download_file(file_id, output):
    url = f"https://drive.google.com/uc?id={file_id}"
    if not os.path.exists(output):
        gdown.download(url, output, quiet=False)

# Use your IDs here
download_file("1DwzwzVJ_rwpNt-IN92ymqYRbWsREpivZ", "movie_dic.pkl")
download_file("1wOIEQa6K6aVwklVrgH8-RyxrbocFr-GT", "similarity.pkl")


# .env file
load_dotenv()

API_KEY = os.getenv("TMDB_API_KEY")


def fetch_poster(movie_id):
    """Fetch poster image URL from TMDB API"""
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US"
    data = requests.get(url).json()
    poster_path = data.get('poster_path')
    if poster_path:
        return "https://image.tmdb.org/t/p/w500" + poster_path
    return "https://via.placeholder.com/500x750?text=No+Image"   # fallback if no poster


# Load data

movies = pickle.load(open('movie_dic.pkl', 'rb'))
similarity = pickle.load(open('similarity.pkl', 'rb'))


# Recommend function

def recommend(movie):
    movie = movie.lower()
    matches = movies[movies['title'].str.lower() == movie]

    if matches.empty:
        return [], []

    movie_index = matches.index[0]
    distances = similarity[movie_index]
    movie_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    recommended_movies = []
    recommended_posters = []
    for i in movie_list:
        movie_id = movies.iloc[i[0]].movie_id   # 👈 make sure your movies df has movie_id column
        recommended_movies.append(movies.iloc[i[0]].title)
        recommended_posters.append(fetch_poster(movie_id))

    return recommended_movies, recommended_posters


# Streamlit UI

st.title("🎬 Movie Recommender System")

selected_movie = st.selectbox(
    "Search for a movie:",
    movies['title'].values
)

if st.button("Recommend"):
    names, posters = recommend(selected_movie)

    if not names:   # if no movie found
        st.write("❌ Movie not found in database")
    else:
        st.write("### Top 5 Recommendations:")
        cols = st.columns(5)   # show posters in small boxes
        for idx, col in enumerate(cols):
            with col:
                st.image(posters[idx], use_column_width=True)
                st.caption(names[idx])
