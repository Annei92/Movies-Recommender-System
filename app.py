import streamlit as st
import pickle
import pandas as pd
import requests
import os
import gdown
from dotenv import load_dotenv
from PIL import Image

# ------------------------------
# UI: banner + page config
# ------------------------------
st.set_page_config(page_title="Movie Recommender", page_icon="🎬", layout="wide")

try:
    banner = Image.open("banner.webp")
    st.image(banner, use_container_width=True)
except Exception:
    pass

st.markdown("<h1 style='text-align: center;'>Movie Recommender System </h1>", unsafe_allow_html=True)

st.markdown(
    """
    <style>
    .full-width-banner { position: relative; left: 0; width: 100vw; height: auto; }
    [data-testid="stVerticalBlock"] { gap: 0.75rem; }
    .rank { 
        display: inline-block; 
        padding: 2px 8px; 
        border-radius: 999px; 
        background: #f0f2f6; 
        font-weight: 700; 
        font-size: 0.9rem;
    }
    .caption {
        text-align:center; 
        margin-top:10px;
        line-height: 1.2;
    }
    .muted { opacity: 0.7; font-size: 0.9em; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------
# Config: env / keys
# ------------------------------
load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY") or st.secrets.get("TMDB_API_KEY", None)

# Google Drive file IDs
MOVIE_DIC_ID = "1DwzwzVJ_rwpNt-IN92ymqYRbWsREpivZ"   # movie_dic.pkl
SIMILARITY_ID = "1wOIEQa6K6aVwklVrgH8-RyxrbocFr-GT"  # similarity.pkl

# ------------------------------
# Helpers
# ------------------------------
def download_file(file_id, output):
    """Download file from Google Drive if not exists"""
    if not os.path.exists(output):
        url = f"https://drive.google.com/uc?id={file_id}"
        gdown.download(url, output, quiet=False)

def fetch_poster(movie_id):
    """Fetch poster from TMDB API"""
    # Fallback if no key or network error
    placeholder = "https://via.placeholder.com/500x750.png?text=No+Image"
    if not TMDB_API_KEY:
        return placeholder

    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"
    try:
        response = requests.get(url, timeout=12)
        response.raise_for_status()
        data = response.json()
        if "poster_path" in data and data["poster_path"]:
            return "https://image.tmdb.org/t/p/w500" + data["poster_path"]
    except Exception:
        pass
    return placeholder

def recommend(movie, k=5):
    """
    Return top-k similar movies with (rank, title, poster, score).

    rank: 1..k
    title: movie title
    poster: URL string
    score: similarity float
    """
    movie = str(movie).lower()
    matches = movies[movies["title"].str.lower() == movie]
    if matches.empty:
        return []

    movie_index = matches.index[0]
    distances = similarity[movie_index]

    # Sort by similarity descending
    ranked = sorted(enumerate(distances), key=lambda x: x[1], reverse=True)

    recs = []
    rank = 1
    for idx, score in ranked:
        if idx == movie_index:
            continue  # skip the query movie itself
        movie_id = int(movies.iloc[idx].movie_id)
        title = str(movies.iloc[idx].title)
        poster = fetch_poster(movie_id)
        recs.append((rank, title, poster, float(score)))
        rank += 1
        if rank > k:
            break
    return recs

# ------------------------------
# Load artifacts
# ------------------------------
download_file(MOVIE_DIC_ID, "movie_dic.pkl")
download_file(SIMILARITY_ID, "similarity.pkl")

movies = pickle.load(open("movie_dic.pkl", "rb"))
similarity = pickle.load(open("similarity.pkl", "rb"))
movies = pd.DataFrame(movies)

# ------------------------------
# UI controls
# ------------------------------
col1, col2 = st.columns([3, 1])
with col1:
    selected_movie = st.selectbox("Search for a movie:", movies["title"].values, index=None, placeholder="Type to search…")
with col2:
    k = st.slider("How many recommendations?", 3, 10, value=5)

# ------------------------------
# Action
# ------------------------------
if st.button("Recommend", use_container_width=True) and selected_movie:
    recs = recommend(selected_movie, k=k)

    if not recs:
        st.warning("Movie not found in database.")
    else:
        st.write(f"### Top {len(recs)} Recommendations:")
        cols = st.columns(min(5, len(recs)), gap="large")
        for i, (rank, title, poster, score) in enumerate(recs):
            with cols[i % len(cols)]:
                st.image(poster, use_container_width=True)
                st.markdown(
                    f"""
                    <p class="caption">
                        <span class="rank">#{rank}</span> <strong>{title}</strong><br>
                        <span class="muted">similarity: {score:.3f}</span>
                    </p>
                    """,
                    unsafe_allow_html=True,
                )
