import streamlit as st
import pickle
import pandas as pd
import requests
import os
import gdown
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

# Google Drive file IDs
MOVIE_DIC_ID = "1DwzwzVJ_rwpNt-IN92ymqYRbWsREpivZ"  # replace with your ID
SIMILARITY_ID = "1wOIEQa6K6aVwklVrgH8-RyxrbocFr-GT"  # replace with your ID

# Download files if not already present
def download_file(file_id, output):
    if not os.path.exists(output):
        url = f"https://drive.google.com/uc?id={file_id}"
        gdown.download(url, output, quiet=False)

download_file(MOVIE_DIC_ID, "movie_dic.pkl")
download_file(SIMILARITY_ID, "similarity.pkl")

# Load data
movies = pickle.load(open("movie_dic.pkl", "rb"))
similarity = pickle.load(open("similarity.pkl", "rb"))
movies = pd.DataFrame(movies)

# Fetch poster from TMDB
def fetch_poster(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"
    data = requests.get(url).json()
    if "poster_path" in data and data["poster_path"]:
        return "https://image.tmdb.org/t/p/w500" + data["poster_path"]
    else:
        return "https://via.placeholder.com/500x750.png?text=No+Image"

# Recommend function
def recommend(movie):
    movie = movie.lower()
    matches = movies[movies["title"].str.lower() == movie]

    if matches.empty:
        return []

    movie_index = matches.index[0]
    distances = similarity[movie_index]
    movie_list = sorted(
        list(enumerate(distances)), reverse=True, key=lambda x: x[1]
    )[1:6]

    recommendations = []
    for i in movie_list:
        movie_id = movies.iloc[i[0]].id
        title = movies.iloc[i[0]].title
        recommendations.append((title, fetch_poster(movie_id)))

    return recommendations

# Streamlit UI
st.title("🎬 Movie Recommender System")

selected_movie = st.selectbox(
    "Search for a movie:", movies["title"].values
)

if st.button("Recommend"):
    recs = recommend(selected_movie)

    if not recs:
        st.warning("❌ Movie not found in database.")
    else:
        st.write("### Top 5 Recommendations:")

        cols = st.columns(5, gap="large")
        for idx, (title, poster) in enumerate(recs):
            with cols[idx]:
                st.image(poster, use_column_width=True)
                st.markdown(
                    f"<p style='text-align:center; margin-top:10px;'>{title}</p>",
                    unsafe_allow_html=True,
                )
