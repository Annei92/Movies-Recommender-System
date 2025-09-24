# app.py (compact cards)
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
    import gdown
except Exception:
    gdown = None

st.set_page_config(page_title="Movie Recommender", page_icon="🎬", layout="wide")

# -------------------- Controls for SIZE --------------------
# Small/Medium/Large presets affect grid density + fonts + paddings
SIZE_PRESETS = {
    "Compact": {"card_min": 128, "title_fs": 12, "star_fs": 14, "meta_fs": 11, "pad": 8},
    "Cozy":    {"card_min": 160, "title_fs": 13, "star_fs": 16, "meta_fs": 12, "pad": 10},
    "Roomy":   {"card_min": 200, "title_fs": 14, "star_fs": 18, "meta_fs": 12, "pad": 12},
}

# -------------------- ENV / Files --------------------
TMDB_API_KEY = os.getenv("TMDB_API_KEY") or st.secrets.get("TMDB_API_KEY", None)
MOVIE_DIC_ID = "1DwzwzVJ_rwpNt-IN92ymqYRbWsREpivZ"
SIMILARITY_ID = "1wOIEQa6K6aVwklVrgH8-RyxrbocFr-GT"
MOVIE_DIC_FILE = Path("movie_dic.pkl")
SIMILARITY_FILE = Path("similarity.pkl")

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "streamlit-movie-recs/compact/1.0"})
TIMEOUT = 12

# -------------------- Helpers --------------------
@st.cache_data(show_spinner=False)
def download_file(file_id: str, output: str) -> bool:
    p = Path(output)
    if p.exists():
        return True
    url = f"https://drive.google.com/uc?id={file_id}"
    try:
        if gdown:
            gdown.download(url, output, quiet=True)
        else:
            r = SESSION.get(url, timeout=TIMEOUT)
            r.raise_for_status()
            p.write_bytes(r.content)
    except Exception:
        return False
    return p.exists()

@st.cache_data(show_spinner=False)
def load_artifacts():
    ok1 = download_file(MOVIE_DIC_ID, str(MOVIE_DIC_FILE))
    ok2 = download_file(SIMILARITY_ID, str(SIMILARITY_FILE))
    if not (ok1 and ok2):
        raise FileNotFoundError("Artifacts missing. Check Drive IDs / network.")
    movies_dict = pickle.loads(MOVIE_DIC_FILE.read_bytes())
    similarity = pickle.loads(SIMILARITY_FILE.read_bytes())
    df = pd.DataFrame(movies_dict)
    if "year" not in df.columns:
        df["year"] = pd.NA
    df["_norm_title"] = df["title"].astype(str).str.casefold()
    return df, np.array(similarity)

@st.cache_data(show_spinner=False, ttl=60*60)
def fetch_poster(movie_id: int) -> str:
    placeholder = "https://via.placeholder.com/500x750.png?text=No+Image"
    if not TMDB_API_KEY:
        return placeholder
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    try:
        r = SESSION.get(url, params={"api_key": TMDB_API_KEY, "language": "en-US"}, timeout=TIMEOUT)
        r.raise_for_status()
        path = r.json().get("poster_path")
        if path:
            return "https://image.tmdb.org/t/p/w500" + path
    except Exception:
        pass
    return placeholder

def _stars_from_score(score: float, s_min: float, s_max: float):
    if s_max <= s_min:
        rating = 5.0 if score > 0 else 0.0
    else:
        rating = 5.0 * ((score - s_min) / (s_max - s_min))
    rating = max(0.0, min(5.0, float(rating)))
    return rating, rating / 5.0 * 100.0

@st.cache_data(show_spinner=False)
def get_recs(movies: pd.DataFrame, similarity: np.ndarray, title: str, k: int = 10) -> List[Dict]:
    idxs = movies.index[movies["_norm_title"] == str(title).casefold()].tolist()
    if not idxs:
        return []
    q = idxs[0]
    dists = similarity[q]
    ranked = sorted(enumerate(dists), key=lambda x: x[1], reverse=True)
    pool = [(i, float(s)) for i, s in ranked if i != q][:max(k, 10)]
    if not pool:
        return []
    scores = [s for _, s in pool]
    smin, smax = min(scores), max(scores)

    out = []
    for i, s in pool[:k]:
        row = movies.iloc[i]
        stars, pct = _stars_from_score(s, smin, smax)
        out.append({
            "title": str(row.title),
            "year": "" if pd.isna(row.year) else str(row.year),
            "poster": fetch_poster(int(row.movie_id)),
            "stars_pct": pct,
            "movie_id": int(row.movie_id),
            "index": int(i),
        })
    return out

def css(app_size):
    s = SIZE_PRESETS[app_size]
    return f"""
    <style>
    :root {{
      --card-bg: #ffffff;
      --card-border: #e6e6e6;
      --muted: rgba(60,60,67,.6);
    }}
    [data-theme="dark"] :root {{
      --card-bg: #111318;
      --card-border: #26282e;
      --muted: rgba(235,235,245,.6);
    }}

    .header {{
      background: linear-gradient(90deg,#111827 0%,#1f2937 100%);
      padding: 10px 14px;
      border-radius: 12px;
      color:#fff;
      margin-bottom: 10px;
      display:flex; align-items:center; justify-content:space-between;
      font-size: 14px;
    }}
    .header .title {{ font-weight:800; font-size: 16px; }}

    .grid {{
      display:grid;
      grid-template-columns: repeat(auto-fill, minmax({s["card_min"]}px, 1fr));
      gap: 10px;
    }}
    .card {{
      background: var(--card-bg);
      border:1px solid var(--card-border);
      border-radius: 12px;
      overflow:hidden;
      transition: transform .12s ease, box-shadow .12s ease;
      box-shadow: 0 1px 2px rgba(0,0,0,.03);
    }}
    .card:hover {{ transform: translateY(-1px); box-shadow: 0 6px 18px rgba(0,0,0,.08); }}
    .img {{ aspect-ratio: 2/3; width:100%; object-fit:cover; display:block; }}
    .body {{ padding: {s["pad"]}px; }}
    .title {{ font-weight: 700; font-size: {s["title_fs"]}px; line-height:1.25; margin-top: 6px; }}
    .meta {{ font-size: {s["meta_fs"]}px; color: var(--muted); }}

    .stars {{
      position: relative;
      display:inline-block;
      font-size: {s["star_fs"]}px;
      line-height:1;
      color:#d0d4db;
      letter-spacing:2px;
      user-select:none;
    }}
    .stars::before {{ content: "★★★★★"; }}
    .stars-fill {{
      position:absolute; inset:0 auto 0 0; overflow:hidden; white-space:nowrap;
      width:0; color:#f5a623;
    }}
    .stars-fill::before {{ content:"★★★★★"; letter-spacing:2px; }}
    </style>
    """

def card(item: Dict):
    st.markdown(
        f"""
        <div class="card">
          <img class="img" src="{item['poster']}" alt="{item['title']} poster"/>
          <div class="body">
            <span class="stars" aria-label="rating">
              <span class="stars-fill" style="width:{item['stars_pct']:.0f}%"></span>
            </span>
            <div class="title">{item['title']}</div>
            <div class="meta">{item['year']}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# -------------------- UI --------------------
with st.sidebar:
    size = st.radio("Card size", list(SIZE_PRESETS.keys()), index=0, help="Make the boxes smaller or larger.")
    k = st.slider("How many recommendations", 4, 20, value=12, step=1)
    st.caption("TIP: Use **Compact** for a dense, app-like grid.")

st.markdown(css(size), unsafe_allow_html=True)

st.markdown(
    """
    <div class="header">
      <div class="title">🍿 Movie Recommender</div>
      <div>Clean grid • Star ratings • Fast</div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.spinner("Loading model…"):
    try:
        movies, similarity = load_artifacts()
    except Exception:
        st.error("Failed to load artifacts. Check Drive IDs / network.")
        st.stop()

left, right = st.columns([3,1])
with left:
    selected = st.selectbox("Pick a movie", options=movies["title"].values, index=None, placeholder="Type to search…")
with right:
    go = st.button("Recommend", type="primary", use_container_width=True)

if go and not selected:
    st.info("Pick a movie first.")
elif go and selected:
    with st.spinner("Finding matches…"):
        items = get_recs(movies, similarity, selected, k=k)

    if not items:
        st.warning("No matches. Try another title.")
    else:
        st.subheader(f"Because you watched **{selected}**")
        st.markdown('<div class="grid">', unsafe_allow_html=True)
        for it in items:
            card(it)
        st.markdown("</div>", unsafe_allow_html=True)
