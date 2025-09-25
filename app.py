
import os
import pickle
import requests
import pandas as pd
import streamlit as st
import gdown
from PIL import Image


try:
    from dotenv import load_dotenv  # type: ignore
except Exception:  # package not installed
    def load_dotenv(*args, **kwargs):
        return False


st.set_page_config(page_title="Movie Recommender", page_icon="🎬", layout="wide")

st.markdown("""
<style>
.block-container { max-width: 1000px; margin: 0 auto; }
[data-testid="stVerticalBlock"] { gap: 0.75rem; }


.stars{
  position:relative; display:inline-block; font-size:20px; line-height:1;
  color:#d0d4db; letter-spacing:3px; user-select:none; white-space:nowrap;
}
.stars::before{ content:"★★★★★"; white-space:nowrap; }
.stars-fill{
  position:absolute; top:0; left:0; overflow:hidden; white-space:nowrap;
  width:0; color:#f5a623;
}
.stars-fill::before{ content:"★★★★★"; letter-spacing:3px; white-space:nowrap; }


.caption{ text-align:center; margin-top:10px; line-height:1.2; }

.caption .title{
  display:-webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;     /* show up to 2 lines */
  overflow:hidden;
  text-overflow:ellipsis;
  white-space:normal;         /* allow wrapping */
  font-weight:700;
  margin:8px 0 6px;
}


@media (max-width: 420px){
  .stars{ font-size:18px; letter-spacing:2px; }
}
</style>
""", unsafe_allow_html=True)


L, C, R = st.columns([1, 6, 1])
with C:
    try:
        banner = Image.open("banner.webp")
        st.image(banner, use_container_width=True)
    except Exception:
        pass
    st.markdown("<h1 style='text-align:center;'>Movie Recommender System</h1>", unsafe_allow_html=True)


load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY") or st.secrets.get("TMDB_API_KEY", None)

# Google Drive file IDs
MOVIE_DIC_ID = "1DwzwzVJ_rwpNt-IN92ymqYRbWsREpivZ"   # movie_dic.pkl
SIMILARITY_ID = "1wOIEQa6K6aVwklVrgH8-RyxrbocFr-GT"  # similarity.pkl

@st.cache_data(show_spinner=False)
def _download_once(file_id: str, output: str) -> str:
    """Download a file from Google Drive to local path if missing; return path."""
    if not os.path.exists(output):
        url = f"https://drive.google.com/uc?id={file_id}"
        # quiet=True to keep logs clean on Streamlit Cloud
        gdown.download(url, output, quiet=True)
    return output

def download_file(file_id: str, output: str) -> None:
    _download_once(file_id, output)

def _placeholder_poster() -> str:
    return "https://via.placeholder.com/500x750.png?text=No+Image"

@st.cache_data(ttl=24*3600, show_spinner=False)
def fetch_poster(movie_id: int, api_key: str | None) -> str:
    """Fetch poster URL from TMDB; cache for a day."""
    if not api_key:
        return _placeholder_poster()
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"
    try:
        r = requests.get(url, timeout=12)
        r.raise_for_status()
        data = r.json()
        path = data.get("poster_path")
        if path:
            return "https://image.tmdb.org/t/p/w500" + path
    except Exception:
        pass
    return _placeholder_poster()

def _stars_from_score(score: float, s_min: float, s_max: float) -> tuple[float, float]:
    """Map similarity -> (0..5 stars, 0..100% width)."""
    if s_max <= s_min:
        rating = 5.0 if score > 0 else 0.0
    else:
        rating = 5.0 * ((score - s_min) / (s_max - s_min))
    rating = max(0.0, min(5.0, float(rating)))
    return rating, rating / 5.0 * 100.0

def recommend(df_movies: pd.DataFrame, similarity, movie: str, k: int = 12):
    """
    Return top-k similar movies with dicts:
    { title, poster, stars (0..5), stars_pct (0..100 for CSS) }
    """
    movie = str(movie).lower()
    matches = df_movies[df_movies["title"].str.lower() == movie]
    if matches.empty:
        return []
    movie_index = matches.index[0]
    distances = similarity[movie_index]
    ranked = sorted(enumerate(distances), key=lambda x: x[1], reverse=True)

    pool = [(idx, float(score)) for idx, score in ranked if idx != movie_index][:max(k, 16)]
    if not pool:
        return []
    pool_scores = [s for _, s in pool]
    s_min, s_max = min(pool_scores), max(pool_scores)

    recs = []
    for idx, score in pool[:k]:
        row = df_movies.iloc[idx]
        title = str(row.title)
        poster = fetch_poster(int(row.movie_id), TMDB_API_KEY)
        stars, stars_pct = _stars_from_score(score, s_min, s_max)
        recs.append({"title": title, "poster": poster, "stars": stars, "stars_pct": stars_pct})
    return recs


download_file(MOVIE_DIC_ID, "movie_dic.pkl")
download_file(SIMILARITY_ID, "similarity.pkl")

try:
    with open("movie_dic.pkl", "rb") as f:
        movies = pd.DataFrame(pickle.load(f))
    with open("similarity.pkl", "rb") as f:
        similarity = pickle.load(f)
except Exception as e:
    st.error("Failed to load model files. Please verify Google Drive IDs or files.")
    st.stop()


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

    # Optional: auto-run when a movie is chosen (comment out if you prefer the button)
    if selected_movie and not go:
        go = True

    if not TMDB_API_KEY:
        st.info("No TMDB_API_KEY set. Posters will use placeholders. Add it via .env or Streamlit Secrets.")


if go and selected_movie:
    recs = recommend(movies, similarity, selected_movie, k=k)

    with C:
        if not recs:
            st.warning("Movie not found in database.")
        else:
            st.subheader(f"Top {len(recs)} Recommendations")
            cols = st.columns(min(5, len(recs)), gap="large")
            for i, r in enumerate(recs):
                with cols[i % len(cols)]:
                    st.image(r["poster"], use_container_width=True)

                    # IMPORTANT: call st.markdown by itself (no st.write(st.markdown(...)))
                    html = f"""
                    <p class="caption">
                        <span class="title" title="{r["title"]}">{r["title"]}</span>
                        <span class="stars" aria-label="rating {r["stars"]:.1f} of 5">
                          <span class="stars-fill" style="width:{r["stars_pct"]:.0f}%"></span>
                        </span>
                    </p>
                    """
                    st.markdown(html, unsafe_allow_html=True)
