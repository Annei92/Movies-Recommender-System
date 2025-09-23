import streamlit as st
import pickle
import pandas as pd
import gdown
import os

def download_file(file_id, output):
    url = f"https://drive.google.com/uc?id={file_id}"
    if not os.path.exists(output):
        gdown.download(url, output, quiet=False)


MOVIE_DIC_ID = "1DwzwzVJ_rwpNt-IN92ymqYRbWsREpivZ"      # movie_dic.pkl
SIMILARITY_ID = "1wOIEQa6K6aVwklVrgH8-RyxrbocFr-GT"    # similarity.pkl

download_file(MOVIE_DIC_ID, "movie_dic.pkl")
download_file(SIMILARITY_ID, "similarity.pkl")

# load Data
movies = pickle.load(open("movie_dic.pkl", "rb"))
similarity = pickle.load(open("similarity.pkl", "rb"))

#recommender Function
def recommend(movie):
    movie = movie.lower()
    matches = movies[movies['title'].str.lower() == movie]

    if matches.empty:
        return ["Movie not found in database"]

    movie_index = matches.index[0]
    distances = similarity[movie_index]
    movie_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    return movies.iloc[[i[0] for i in movie_list]]['title'].tolist()

# sreamlit UI
st.title(" Movie Recommender System")

selected_movie = st.selectbox(
    "Search for a movie:",
    movies['title'].values
)

if st.button("Recommend"):
    recs = recommend(selected_movie)
    st.write("### Top 5 Recommendations:")
    for r in recs:
        st.write("🍿", r)
