# app.py
import os
import pickle
from pathlib import Path
from typing import List, Dict, Tuple

import numpy as np
import pandas as pd
import requests
import streamlit as st
from PIL import Image

try:
    import gdown  # for public Google Drive downloads
except Exception:
    gdown = None

# ===============================
# App Config
# ===============================
st.set_page_config(
    page_title="Movie Recommender",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ===============================
# THEME & APP STYLES
# ===============================
APP_CSS = """
<style>
/* Global tweaks */
:root {
  --card-bg: #ffffff;
  --card-border: #e6e6e6;
  --text-muted: rgba(60, 60, 67, 0.6);
  --accent: #7c3aed; /* purple */
}
[data-theme="dark"] :root {
  --card-bg: #111318;
  --card-border: #26282e;
  --text-muted: rgba(235, 235, 245, 0.6);
  --accent: #a78bfa;
}

/* Header bar (fake navbar) */
.app-header {
  background: linear-gradient(90deg, #111827 0%, #1f2937 100%);
  padding: 16px 20px;
  border-radius: 16px;
  display: flex; 
  align-items: center; 
  justify-content: space-between;
  color: #fff;
  margin-bottom: 16px;
}
.app-title {
  display:flex; gap:12px; align-items:center;
  font-weight: 700; font-size: 20px;
}
.app-sub {
  font-size: 13px; opacity: .8;
}

/* Search & controls container */
.controls {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 16px;
  padding: 16px;
}

/* Card grid */
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 18px;
}

/* Movie card */
.card {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 16px;
  overflow: hidden;
  transition: transform .15s ease, box-shadow .15s ease, border-color .2s ease;
  box-shadow: 0 1px 2px rgba(0,0,0,0.03);
}
.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.08);
  border-color: rgba(124,58,237,.35);
}
.card-img {
  aspect-ratio: 2/3;
  width: 100%;
  object-fit: cover;
  display: block;
}
.card-body {
  padding: 10px 12px 12px 12px;
}
.card-title {
  font-weight: 700;
  font-size: 14px;
  line-height: 1.25;
  margin: 6px 0 2px 0;
}
.card-meta {
  font-size: 12px;
  color: var(--text-muted);
}

/* Stars (visual only) */
.stars {
  position: relative;
  display: inline-block;
  font-size: 18px;
  line-height: 1;
  color: #d0d4db;  /* empty star color */
  letter-spacing: 3px;
  user-select: none;
}
.stars::before {
  content: "★★★★★";
}
.stars-fill {
  position: absolute;
  inset: 0 auto 0 0;
  overflow: hidden;
  white-space: nowrap;
  width: 0;
  color: #f5a623;  /* filled star color */
}
.stars-fill::before {
  content: "★★★★★";
  letter-spacing: 3px;
}

/* Buttons row */
.card-actions {
  display: flex; gap: 8px; margin-top: 10px;
}
.btn {
  display: inline-flex; align-items: center; justify-content: center;
  border-radius: 999px; padding: 6px 10px;
  font-size: 12px; font-weight: 600; border: 1px solid var(--card-border);
  background: #f8f9fb; color: #111827;
}
[data-theme="dark"] .btn {
  background: #1a1d24; color: #e5e7eb;
}
.btn:hover {
  border-color: var(--accent);
}

/* Footer note */
.footer-note {
  color: var(--text-muted);
  font-size: 12px;
  text-align: center;
  margin-top: 18px;
}
</style>
"""
st.markdown(APP_CSS, unsafe_allow_html=True)

# ===============================
# Config & Constants
# ===============================
TMDB_API_KEY = os.getenv("TMDB_API_KEY") or st.secrets.get("TMDB_API_KEY", None)

MOVIE_DIC_ID = "1DwzwzVJ_rwpNt-IN92ymqYRbWsREpivZ"   # movie_dic.pkl
SIMILARITY_ID = "1wOIEQa6K6aVwklVrgH8-RyxrbocFr-GT"  # similarity.pkl

MOVIE_DIC_FILE = Path("movie_dic.pkl")
SIMILARITY_FILE = Path("similarity.pkl")

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "streamlit-movie-recs/2.0"})
TIMEOUT = 12

# ===============================
# Helpers
# ===============================
@st.cache_data(show_spinner=False)
def download_file(file_id: str, output: str) -> bool:
    """Download file from Google Drive if missing."""
    path = Path(output)
    if path.exists():
        return True
    url = f"https://drive.google.com/uc?id={file_id}"
    try:
        if gdown:
            gdown.download(url, output, quiet=True)
        else:
            r = SESSION.get(url, timeout=TIMEOUT)
            r.raise_for_status()
            path.write_bytes(r.content)
    except Exception:
        return False
    return path.exists()

@st.cache_data(show_spinner=False)
def load_artifacts() -> Tuple[pd.DataFrame, np.ndarray]:
    ok1 = download_file(MOVIE_DIC_ID, str(MOVIE_DIC_FILE))
    ok2 = download_file(SIMILARITY_ID, str(SIMILARITY_FILE))
    if not (ok1 and ok2):
        raise FileNotFoundError("Model artifacts missing. Check Drive IDs or network.")
    movies_dict = pickle.loads(MOVIE_DIC_FILE.read_bytes())
    similarity = pickle.loads(SIMILARITY_FILE.read_bytes())
    df = pd.DataFrame(movies_dict)
    # optional helpers
    if "year" not in df.columns:
        df["year"] = pd.NA
    df["_norm_title"] = df["title"].astype(str).str.casefold()
    return df, np.array(similarity)

@st.cache_data(show_spinner=False, ttl=60 * 60)
def fetch_poster(movie_id: int) -> str:
    placeholder = "https://via.placeholder.com/500x750.png?text=No+Image"
    if not TMDB_API_KEY:
        return placeholder
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    params = {"api_key": TMDB_API_KEY, "language": "en-US"}
    try:
        r = SESSION.get(url, params=params, timeout=TIMEOUT)
        r.raise_for_status()
        path = r.json().get("poster_path")
        if path:
            return "https://image.tmdb.org/t/p/w500" + path
    except Exception:
        pass
    return placeholder

def _stars_from_score(score: float, s_min: float, s_max: float) -> Tuple[float, float]:
    """Map similarity -> 0..5 stars via min–max scaling (per query)."""
    if s_max <= s_min:
        rating = 5.0 if score > 0 else 0.0
    else:
        rating = 5.0 * ((score - s_min) / (s_max - s_min))
    rating = max(0.0, min(5.0, float(rating)))
    return rating, rating / 5.0 * 100.0  # stars, width%

@st.cache_data(show_spinner=False)
def get_recommendations(
    movies: pd.DataFrame,
    similarity: np.ndarray,
    query_title: str,
    k: int = 8,
) -> List[Dict]:
    """Return list of {title, poster, year, stars, stars_pct} (no similarity shown)."""
    norm = str(query_title).casefold()
    idx_list = movies.index[movies["_norm_title"] == norm].tolist()
    if not idx_list:
        return []
    q_idx = idx_list[0]
    dists = similarity[q_idx]

    ranked = sorted(enumerate(dists), key=lambda x: x[1], reverse=True)
    pool = [(i, float(s)) for i, s in ranked if i != q_idx][:max(k, 10)]
    if not pool:
        return []

    pool_scores = [s for _, s in pool]
    s_min, s_max = min(pool_scores), max(pool_scores)

    recs = []
    for i, s in pool[:k]:
        row = movies.iloc[i]
        poster = fetch_poster(int(row.movie_id))
        stars, pct = _stars_from_score(s, s_min, s_max)
        recs.append(
            {
                "title": str(row.title),
                "year": ("" if pd.isna(row.year) else str(row.year)),
                "poster": poster,
                "stars": stars,
                "stars_pct": pct,
                "movie_id": int(row.movie_id),
                "index": int(i),
            }
        )
    return recs

def render_card(item: Dict, key: str):
    """Render one movie card with poster, title, year, and star rating."""
    st.markdown(
        f"""
        <div class="card">
          <img class="card-img" src="{item['poster']}" alt="{item['title']} poster" />
          <div class="card-body">
            <div class="stars" aria-label="rating">
              <span class="stars-fill" style="width:{item['stars_pct']:.0f}%"></span>
            </div>
            <div class="card-title">{item['title']}</div>
            <div class="card-meta">{item['year'] if item['year'] else ""}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    # Row of lightweight actions
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("More like this", key=f"morelike_{key}", use_container_width=True):
            st.session_state["selected_movie"] = item["title"]
            st.session_state["auto_recommend"] = True
    with col_b:
        st.link_button("Open TMDB", f"https://www.themoviedb.org/movie/{item['movie_id']}", use_container_width=True)

# ===============================
# Sidebar (branding / theme tips)
# ===============================
with st.sidebar:
    st.markdown("### 🎬 Movie Recommender")
    st.caption("Find similar movies with a clean, app-like interface.")
    st.divider()
    st.markdown("**Tips**")
    st.caption("- Add your `TMDB_API_KEY` in *Secrets* or environment.\n- Replace Drive IDs if artifacts move.")
    st.caption("- Use the **More like this** button to pivot quickly.")
    st.divider()
    st.markdown(
        """
        <div class="footer-note">
          Built with Streamlit • Posters via TMDB
        </div>
        """,
        unsafe_allow_html=True,
    )

# ===============================
# Header Bar
# ===============================
st.markdown(
    """
    <div class="app-header">
      <div class="app-title">
        <span>🍿</span> <span>Movie Recommender</span>
      </div>
      <div class="app-sub">Smart, fast, and pretty recommendations</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ===============================
# Main Controls
# ===============================
with st.container():
    with st.spinner("Loading model…"):
        try:
            movies, similarity = load_artifacts()
        except Exception as e:
            st.error("Failed to load artifacts. Check Drive IDs, permissions, or network.")
            st.stop()

    c1, c2, c3 = st.columns([3, 1.2, 1])
    with c1:
        # Selectbox with placeholder-like behavior
        selected = st.selectbox(
            "Search or pick a movie",
            options=movies["title"].values,
            index=None,
            placeholder="Type to search…",
            key="selected_movie",
        )
    with c2:
        k = st.slider("Number of recommendations", 4, 12, value=8)
    with c3:
        center_imgs = st.toggle("Compact posters", value=False, help="Smaller cards for dense grid")

    # action row
    go = st.button("Get Recommendations", type="primary", use_container_width=True)

# Auto-trigger when pivoting via "More like this"
if st.session_state.get("auto_recommend"):
    go = True
    selected = st.session_state.get("selected_movie")
    st.session_state["auto_recommend"] = False

# ===============================
# Results Grid
# ===============================
if go and selected:
    with st.spinner("Finding great matches…"):
        items = get_recommendations(movies, similarity, selected, k=k)

    if not items:
        st.warning("That movie wasn’t found in the database. Try another title.")
    else:
        st.subheader(f"Because you watched **{selected}**")
        # grid container
        # (We use HTML grid to get true masonry-like responsiveness.)
        st.markdown('<div class="grid">', unsafe_allow_html=True)
        for idx, item in enumerate(items):
            with st.container():
                render_card(item, key=f"{item['index']}_{idx}")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="footer-note">Not what you expected? Click “More like this” on any card to pivot.</div>', unsafe_allow_html=True)
elif go and not selected:
    st.info("Pick a movie first to get recommendations.")

