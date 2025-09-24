import streamlit as st
import pickle
import pandas as pd
import requests
import os
import gdown
from dotenv import load_dotenv
from PIL import Image

# ------------------------------
# Page config + global width cap
# ------------------------------
st.set_page_config(page_title="Movie Recommender", page_icon="🎬", layout="wide")
st.markdown("""
<style>
/* cap the page width and center the whole app */
.block-container { max-width: 1000px; margin: 0 auto; }
/* smaller gaps for a tighter look */
[data-testid="stVerticalBlock"] { gap: 0.75rem; }
/* star rating (visual only) */
.stars{position:relative;display:inline-block;font-size:20px;line-height:1;color:#d0d4db;letter-spacing:3px;user-select:none}
.stars::before{content:"★★★★★"}
.stars-fill{position:absolute;top:0;left:0;overflow:hidden;white-space:nowrap;width:0;color:#f5a623}
.stars-fill::before{content:"★★★★★";letter-spacing:3px}
.caption{text-align:center;margin-top:10px;line-height:1.2}
</style>
""", unsafe_allow_html=True)

# ------------------------------
# Banner + Title + Form (CENTERED)
# ------------------------------
L, C, R = st.columns([1, 6, 1])   # C is the centered content column
with C:
    try:
        banner = Image.open("banner.webp")
        st.image(banner, use_container_width=True)  # banner matches same content width as form
    except Exception:
        pass

    st.markdown("<h1 style='text-align:center;'>Movie Recommender System</h1>", unsafe_allow_html=True)

# ------------------------------
# Secrets / env
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
    placeholder = "https://via.placeholder.com/500x750.png?text=No+Image"
    if not TMDB_API_KEY:
        return placeholder
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"
    try:
        response = requests.get(url, timeout=12)
        response.raise_for_status()
        data = response.json()
        if data.get("poster_path"):
            return "https://image.tmdb.org/t/p/w500" + data["poster_path"]
    except Exception:
        pass
    return placeholder

def _stars_from_score(score, s_min, s_max):
    """Map similarity -> 0..5 stars (float) via min–max scaling (per query)."""
    if s_max <= s_min:
        rating = 5.0 if score > 0 else 0.0
    else:
        rating = 5.0 * ((score - s_min) / (s_max - s_min))
    rating = max(0.0, min(5.0, float(rating)))
    return rating, rating / 5.0 * 100.0  # (stars, percent width)

def recommend(movie, k=12):
    """
    Return top-k similar movies with dicts:
    { title, poster, stars (0..5), stars_pct (0..100 for CSS) }
    """
    movie = str(movie).lower()
    matches = movies[movies["title"].str.lower() == movie]
    if matches.empty:
        return []
    movie_index = matches.index[0]
    distances = similarity[movie_index]
    ranked = sorted(enumerate(distances), key=lambda x: x[1], reverse=True)

    # Small pool to compute min/max for nicer scaling
    pool = [(idx, float(score)) for idx, score in ranked if idx != movie_index][:max(k, 16)]
    if not pool:
        return []
    pool_scores = [s for _, s in pool]
    s_min, s_max = min(pool_scores), max(pool_scores)

    recs = []
    for idx, score in pool[:k]:
        row = movies.iloc[idx]
        title = str(row.title)
        poster = fetch_poster(int(row.movie_id))
        stars, stars_pct = _stars_from_score(score, s_min, s_max)
        recs.append({"title": title, "poster": poster, "stars": stars, "stars_pct": stars_pct})
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
# Controls (still inside centered column)
# ------------------------------
with C:
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_movie = st.selectbox(
            "Search for a movie:",
            movies["title"].values,
            index=None,
            placeholder="Type to search…"
        )
    with col2:
        k = st.slider("How many recommendations?", 3, 30, value=12, step=1)

    # Centered primary button
    b1, b2, b3 = st.columns([3, 2, 3])
    with b2:
        go = st.button("Recommend", type="primary", use_container_width=True)

# ------------------------------
# Results (also inside centered column so widths match)
# ------------------------------
if go and selected_movie:
    recs = recommend(selected_movie, k=k)

    with C:
        if not recs:
            st.warning("Movie not found in database.")
        else:
            st.subheader(f"Top {len(recs)} Recommendations")
            cols = st.columns(min(5, len(recs)), gap="large")
            for i, r in enumerate(recs):
                with cols[i % len(cols)]:
                    st.image(r["poster"], use_container_width=True)
                    st.markdown(
                        f"""
                        <p class="caption">
                            <strong>{r["title"]}</strong><br>
                            <span class="stars" aria-label="rating">
                              <span class="stars-fill" style="width:{r["stars_pct"]:.0f}%"></span>
                            </span>
                        </p>
                        """,
                        unsafe_allow_html=True,
                    )
import streamlit as st
import pickle
import pandas as pd
import requests
import os
import gdown
from dotenv import load_dotenv
from PIL import Image

# ------------------------------
# Page config + global width cap
# ------------------------------
st.set_page_config(page_title="Movie Recommender", page_icon="🎬", layout="wide")
st.markdown("""
<style>
/* cap the page width and center the whole app */
.block-container { max-width: 1000px; margin: 0 auto; }
/* smaller gaps for a tighter look */
[data-testid="stVerticalBlock"] { gap: 0.75rem; }
/* star rating (visual only) */
.stars{position:relative;display:inline-block;font-size:20px;line-height:1;color:#d0d4db;letter-spacing:3px;user-select:none}
.stars::before{content:"★★★★★"}
.stars-fill{position:absolute;top:0;left:0;overflow:hidden;white-space:nowrap;width:0;color:#f5a623}
.stars-fill::before{content:"★★★★★";letter-spacing:3px}
.caption{text-align:center;margin-top:10px;line-height:1.2}
</style>
""", unsafe_allow_html=True)

# ------------------------------
# Banner + Title + Form (CENTERED)
# ------------------------------
L, C, R = st.columns([1, 6, 1])   # C is the centered content column
with C:
    try:
        banner = Image.open("banner.webp")
        st.image(banner, use_container_width=True)  # banner matches same content width as form
    except Exception:
        pass

    st.markdown("<h1 style='text-align:center;'>Movie Recommender System</h1>", unsafe_allow_html=True)

# ------------------------------
# Secrets / env
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
    placeholder = "https://via.placeholder.com/500x750.png?text=No+Image"
    if not TMDB_API_KEY:
        return placeholder
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"
    try:
        response = requests.get(url, timeout=12)
        response.raise_for_status()
        data = response.json()
        if data.get("poster_path"):
            return "https://image.tmdb.org/t/p/w500" + data["poster_path"]
    except Exception:
        pass
    return placeholder

def _stars_from_score(score, s_min, s_max):
    """Map similarity -> 0..5 stars (float) via min–max scaling (per query)."""
    if s_max <= s_min:
        rating = 5.0 if score > 0 else 0.0
    else:
        rating = 5.0 * ((score - s_min) / (s_max - s_min))
    rating = max(0.0, min(5.0, float(rating)))
    return rating, rating / 5.0 * 100.0  # (stars, percent width)

def recommend(movie, k=12):
    """
    Return top-k similar movies with dicts:
    { title, poster, stars (0..5), stars_pct (0..100 for CSS) }
    """
    movie = str(movie).lower()
    matches = movies[movies["title"].str.lower() == movie]
    if matches.empty:
        return []
    movie_index = matches.index[0]
    distances = similarity[movie_index]
    ranked = sorted(enumerate(distances), key=lambda x: x[1], reverse=True)

    # Small pool to compute min/max for nicer scaling
    pool = [(idx, float(score)) for idx, score in ranked if idx != movie_index][:max(k, 16)]
    if not pool:
        return []
    pool_scores = [s for _, s in pool]
    s_min, s_max = min(pool_scores), max(pool_scores)

    recs = []
    for idx, score in pool[:k]:
        row = movies.iloc[idx]
        title = str(row.title)
        poster = fetch_poster(int(row.movie_id))
        stars, stars_pct = _stars_from_score(score, s_min, s_max)
        recs.append({"title": title, "poster": poster, "stars": stars, "stars_pct": stars_pct})
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
# Controls (still inside centered column)
# ------------------------------
with C:
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_movie = st.selectbox(
            "Search for a movie:",
            movies["title"].values,
            index=None,
            placeholder="Type to search…"
        )
    with col2:
        k = st.slider("How many recommendations?", 3, 30, value=12, step=1)

    # Centered primary button
    b1, b2, b3 = st.columns([3, 2, 3])
    with b2:
        go = st.button("Recommend", type="primary", use_container_width=True)

# ------------------------------
# Results (also inside centered column so widths match)
# ------------------------------
if go and selected_movie:
    recs = recommend(selected_movie, k=k)

    with C:
        if not recs:
            st.warning("Movie not found in database.")
        else:
            st.subheader(f"Top {len(recs)} Recommendations")
            cols = st.columns(min(5, len(recs)), gap="large")
            for i, r in enumerate(recs):
                with cols[i % len(cols)]:
                    st.image(r["poster"], use_container_width=True)
                    st.markdown(
                        f"""
                        <p class="caption">
                            <strong>{r["title"]}</strong><br>
                            <span class="stars" aria-label="rating">
                              <span class="stars-fill" style="width:{r["stars_pct"]:.0f}%"></span>
                            </span>
                        </p>
                        """,
                        unsafe_allow_html=True,
                    )
import streamlit as st
import pickle
import pandas as pd
import requests
import os
import gdown
from dotenv import load_dotenv
from PIL import Image

# ------------------------------
# Page config + global width cap
# ------------------------------
st.set_page_config(page_title="Movie Recommender", page_icon="🎬", layout="wide")
st.markdown("""
<style>
/* cap the page width and center the whole app */
.block-container { max-width: 1000px; margin: 0 auto; }
/* smaller gaps for a tighter look */
[data-testid="stVerticalBlock"] { gap: 0.75rem; }
/* star rating (visual only) */
.stars{position:relative;display:inline-block;font-size:20px;line-height:1;color:#d0d4db;letter-spacing:3px;user-select:none}
.stars::before{content:"★★★★★"}
.stars-fill{position:absolute;top:0;left:0;overflow:hidden;white-space:nowrap;width:0;color:#f5a623}
.stars-fill::before{content:"★★★★★";letter-spacing:3px}
.caption{text-align:center;margin-top:10px;line-height:1.2}
</style>
""", unsafe_allow_html=True)

# ------------------------------
# Banner + Title + Form (CENTERED)
# ------------------------------
L, C, R = st.columns([1, 6, 1])   # C is the centered content column
with C:
    try:
        banner = Image.open("banner.webp")
        st.image(banner, use_container_width=True)  # banner matches same content width as form
    except Exception:
        pass

    st.markdown("<h1 style='text-align:center;'>Movie Recommender System</h1>", unsafe_allow_html=True)

# ------------------------------
# Secrets / env
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
    placeholder = "https://via.placeholder.com/500x750.png?text=No+Image"
    if not TMDB_API_KEY:
        return placeholder
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"
    try:
        response = requests.get(url, timeout=12)
        response.raise_for_status()
        data = response.json()
        if data.get("poster_path"):
            return "https://image.tmdb.org/t/p/w500" + data["poster_path"]
    except Exception:
        pass
    return placeholder

def _stars_from_score(score, s_min, s_max):
    """Map similarity -> 0..5 stars (float) via min–max scaling (per query)."""
    if s_max <= s_min:
        rating = 5.0 if score > 0 else 0.0
    else:
        rating = 5.0 * ((score - s_min) / (s_max - s_min))
    rating = max(0.0, min(5.0, float(rating)))
    return rating, rating / 5.0 * 100.0  # (stars, percent width)

def recommend(movie, k=12):
    """
    Return top-k similar movies with dicts:
    { title, poster, stars (0..5), stars_pct (0..100 for CSS) }
    """
    movie = str(movie).lower()
    matches = movies[movies["title"].str.lower() == movie]
    if matches.empty:
        return []
    movie_index = matches.index[0]
    distances = similarity[movie_index]
    ranked = sorted(enumerate(distances), key=lambda x: x[1], reverse=True)

    # Small pool to compute min/max for nicer scaling
    pool = [(idx, float(score)) for idx, score in ranked if idx != movie_index][:max(k, 16)]
    if not pool:
        return []
    pool_scores = [s for _, s in pool]
    s_min, s_max = min(pool_scores), max(pool_scores)

    recs = []
    for idx, score in pool[:k]:
        row = movies.iloc[idx]
        title = str(row.title)
        poster = fetch_poster(int(row.movie_id))
        stars, stars_pct = _stars_from_score(score, s_min, s_max)
        recs.append({"title": title, "poster": poster, "stars": stars, "stars_pct": stars_pct})
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
# Controls (still inside centered column)
# ------------------------------
with C:
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_movie = st.selectbox(
            "Search for a movie:",
            movies["title"].values,
            index=None,
            placeholder="Type to search…"
        )
    with col2:
        k = st.slider("How many recommendations?", 3, 30, value=12, step=1)

    # Centered primary button
    b1, b2, b3 = st.columns([3, 2, 3])
    with b2:
        go = st.button("Recommend", type="primary", use_container_width=True)

# ------------------------------
# Results (also inside centered column so widths match)
# ------------------------------
if go and selected_movie:
    recs = recommend(selected_movie, k=k)

    with C:
        if not recs:
            st.warning("Movie not found in database.")
        else:
            st.subheader(f"Top {len(recs)} Recommendations")
            cols = st.columns(min(5, len(recs)), gap="large")
            for i, r in enumerate(recs):
                with cols[i % len(cols)]:
                    st.image(r["poster"], use_container_width=True)
                    st.markdown(
                        f"""
                        <p class="caption">
                            <strong>{r["title"]}</strong><br>
                            <span class="stars" aria-label="rating">
                              <span class="stars-fill" style="width:{r["stars_pct"]:.0f}%"></span>
                            </span>
                        </p>
                        """,
                        unsafe_allow_html=True,
                    )
