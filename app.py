import json
import random
from pathlib import Path
from typing import Dict, List, Tuple

import streamlit as st

st.set_page_config(
    page_title="Карточки вопросов",
    page_icon="💬",
    layout="centered",
    initial_sidebar_state="collapsed",
)

DATA_PATH = Path(__file__).parent / "data" / "questions.json"

# UI categories (includes "mix", which is not stored in JSON)
CATEGORIES_UI: Dict[str, Dict[str, str]] = {
    "mix": {"ru": "Микс", "en": "Mix", "emoji": "🃏", "bottom": "🃏"},
    "friends": {"ru": "Друзья", "en": "Friends", "emoji": "🤝", "bottom": "🤝"},
    "couple": {"ru": "Романтика", "en": "Romance", "emoji": "💞", "bottom": "💗"},  # bottom heart
    "party": {"ru": "Вечеринка", "en": "Party", "emoji": "🎉", "bottom": "🎉"},
    "smart": {"ru": "Умники", "en": "Smart", "emoji": "🧠", "bottom": "🧠"},
    "adult": {"ru": "18+", "en": "18+", "emoji": "🔥", "bottom": "🔥"},
}


@st.cache_data(show_spinner=False)
def load_questions() -> Tuple[Dict[str, dict], Dict[str, List[str]]]:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    by_id: Dict[str, dict] = {q["id"]: q for q in data["questions"]}
    by_cat: Dict[str, List[str]] = {}
    for q in data["questions"]:
        by_cat.setdefault(q["category"], []).append(q["id"])
    for k in by_cat:
        by_cat[k] = sorted(by_cat[k])
    return by_id, by_cat


Q_BY_ID, IDS_BY_CAT = load_questions()
ALL_IDS = [qid for cat in sorted(IDS_BY_CAT.keys()) for qid in IDS_BY_CAT[cat]]


def t(ru: str, en: str) -> str:
    return ru if st.session_state.lang == "ru" else en


def ui_label(cat_key: str) -> str:
    meta = CATEGORIES_UI[cat_key]
    return f'{meta["emoji"]} {meta[st.session_state.lang]}'


def bottom_symbol_for_category(cat_key: str) -> str:
    return CATEGORIES_UI.get(cat_key, {}).get("bottom", "💬")


def init_state():
    st.session_state.setdefault("lang", "ru")
    st.session_state.setdefault("category", "mix")
    st.session_state.setdefault("dark_mode", False)
    st.session_state.setdefault("history", [])  # asked question ids in order
    st.session_state.setdefault("decks", {})      # cat_key -> list[qid]
    st.session_state.setdefault("deck_pos", {})   # cat_key -> int
    st.session_state.setdefault("current_qid", {})  # cat_key -> qid
    st.session_state.setdefault("deal_nonce", 0)  # retrigger deal animation


def ids_for_deck(cat_key: str) -> List[str]:
    if cat_key == "mix":
        return list(ALL_IDS)
    return list(IDS_BY_CAT.get(cat_key, []))


def build_deck(cat_key: str) -> List[str]:
    deck = ids_for_deck(cat_key)
    random.shuffle(deck)  # pseudo-random is enough
    return deck


def ensure_ready(cat_key: str):
    decks = st.session_state.decks
    pos = st.session_state.deck_pos
    cur = st.session_state.current_qid

    if cat_key not in decks or not decks[cat_key]:
        decks[cat_key] = build_deck(cat_key)
        pos[cat_key] = 0
        cur[cat_key] = None

    if cur.get(cat_key) is None:
        if pos[cat_key] < len(decks[cat_key]):
            cur[cat_key] = decks[cat_key][pos[cat_key]]
        else:
            cur[cat_key] = None


def draw_next(cat_key: str):
    ensure_ready(cat_key)
    decks = st.session_state.decks
    pos = st.session_state.deck_pos
    cur = st.session_state.current_qid

    # record the current card as "asked" then move forward
    if cur.get(cat_key) is not None:
        st.session_state.history.append(cur[cat_key])

    pos[cat_key] += 1
    if pos[cat_key] >= len(decks[cat_key]):
        cur[cat_key] = None
    else:
        cur[cat_key] = decks[cat_key][pos[cat_key]]

    st.session_state.deal_nonce += 1


def reset_deck(cat_key: str):
    st.session_state.decks[cat_key] = build_deck(cat_key)
    st.session_state.deck_pos[cat_key] = 0
    st.session_state.current_qid[cat_key] = st.session_state.decks[cat_key][0] if st.session_state.decks[cat_key] else None
    st.session_state.deal_nonce += 1


def get_text(qid: str) -> str:
    q = Q_BY_ID[qid]
    return q["ru"] if st.session_state.lang == "ru" else q["en"]


def get_category_of(qid: str) -> str:
    return Q_BY_ID[qid]["category"]


def inject_css():
    theme = "dark" if st.session_state.dark_mode else "light"

    if theme == "light":
        bg1 = "#F8B29A"
        bg2 = "#FDE3D8"
        card_bg = "#FFFFFF"
        text = "rgba(17,24,39,.92)"
        sub = "rgba(17,24,39,.62)"
        outer = "rgba(255,255,255,.58)"
        inner = "rgba(248,178,154,.95)"
        shadow = "rgba(0,0,0,.18)"
        primary = "#F0483E"          # stronger contrast for light mode
        primary_text = "#FFFFFF"
        secondary_bg = "rgba(255,255,255,.62)"
        secondary_border = "rgba(17,24,39,.16)"
        secondary_text = "rgba(17,24,39,.90)"
        tab_text = "rgba(17,24,39,.92)"
    else:
        bg1 = "#0B0F14"
        bg2 = "#1C1438"
        card_bg = "#0F172A"
        text = "rgba(255,255,255,.92)"
        sub = "rgba(255,255,255,.68)"
        outer = "rgba(255,255,255,.11)"
        inner = "rgba(124,58,237,.65)"
        shadow = "rgba(0,0,0,.45)"
        primary = "#7C3AED"
        primary_text = "#FFFFFF"
        secondary_bg = "rgba(255,255,255,.09)"
        secondary_border = "rgba(255,255,255,.16)"
        secondary_text = "rgba(255,255,255,.92)"
        tab_text = "rgba(255,255,255,.92)"

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@500;700;800;900&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif !important;
        }}

        .stApp {{
            background: radial-gradient(1200px 700px at 15% 10%, {bg2} 0%, rgba(0,0,0,0) 60%),
                        linear-gradient(160deg, {bg1} 0%, {bg2} 100%);
            color: {text};
        }}

        #MainMenu, footer {{ visibility: hidden; }}
        header {{ visibility: hidden; height: 0px; }}

        .block-container {{
            padding-top: 1rem;
            padding-bottom: 2.5rem;
            max-width: 720px;
        }}

        /* Chips */
        div[data-baseweb="select"] > div {{ border-radius: 999px !important; }}
        div[data-baseweb="select"] * {{ font-weight: 900 !important; }}
        div[role="radiogroup"] label {{ border-radius: 999px !important; padding: .2rem .55rem !important; }}

        /* Buttons */
        button[data-testid="baseButton-primary"] {{
            width: 100% !important;
            border-radius: 18px !important;
            padding: .95rem 1rem !important;
            border: 0 !important;
            background: {primary} !important;
            color: {primary_text} !important;
            font-weight: 900 !important;
            box-shadow: 0 12px 26px {shadow};
        }}
        button[data-testid="baseButton-secondary"] {{
            width: 100% !important;
            border-radius: 16px !important;
            padding: .8rem .9rem !important;
            background: {secondary_bg} !important;
            color: {secondary_text} !important;
            border: 1px solid {secondary_border} !important;
            font-weight: 900 !important;
        }}

        /* Tabs */
        button[data-baseweb="tab"] {{
            font-weight: 900 !important;
            color: {tab_text} !important;
            opacity: .78 !important;
        }}
        button[data-baseweb="tab"][aria-selected="true"] {{
            opacity: 1 !important;
        }}
        div[data-baseweb="tab-highlight"] {{
            background: {primary} !important;
        }}

        /* Card deck */
        .deck-wrap {{ margin-top: .7rem; margin-bottom: .9rem; }}
        .deck {{ position: relative; width: 100%; min-height: 270px; padding-bottom: 18px; }}
        .card-back, .card-front {{
            border-radius: 26px;
            background: {card_bg};
            border: 2px solid {outer};
            box-shadow: 0 16px 36px {shadow};
        }}
        .card-back {{ position: absolute; inset: 0; opacity: .55; }}
        .card-back.back1 {{ transform: translate(10px, 10px) rotate(1.2deg); opacity: .30; }}
        .card-back.back2 {{ transform: translate(20px, 20px) rotate(2.2deg); opacity: .16; }}

        .card-front {{
            position: relative;
            padding: 1.15rem 1.15rem 1.35rem 1.15rem;
            animation: dealIn .22s ease-out;
        }}
        @keyframes dealIn {{
            from {{ transform: translateY(14px) scale(.985); opacity: 0; }}
            to   {{ transform: translateY(0) scale(1); opacity: 1; }}
        }}
        .card-front::before {{
            content: "";
            position: absolute;
            inset: 16px;
            border-radius: 20px;
            border: 2px solid {inner};
            pointer-events: none;
        }}
        .pill {{
            display: inline-flex;
            align-items: center;
            gap: .45rem;
            padding: .28rem .65rem;
            border-radius: 999px;
            border: 1px solid {outer};
            background: rgba(255,255,255,.10);
            color: {sub};
            font-size: .85rem;
            font-weight: 900;
        }}
        .qtext {{
            font-size: 1.22rem;
            line-height: 1.52;
            font-weight: 900;
            color: {text};
            margin-top: .95rem;
            text-align: center;
            padding: 0 .2rem;
        }}
        .meta {{
            color: {sub};
            font-size: .95rem;
            margin-top: 1.05rem;
            text-align: center;
        }}
        .symbol-badge {{
            position: absolute;
            left: 50%;
            bottom: -14px;
            transform: translateX(-50%);
            width: 54px;
            height: 36px;
            border-radius: 999px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: {card_bg};
            border: 2px solid {inner};
            box-shadow: 0 10px 24px {shadow};
            font-size: 18px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# --------------------
# App
# --------------------
init_state()
inject_css()

st.markdown(
    f"""
    <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:.65rem;">
      <div>
        <div style="font-size:1.45rem;font-weight:900;letter-spacing:-.02em;">{t("Карточки вопросов", "Question Cards")}</div>
        <div style="opacity:.85;margin-top:.15rem;font-weight:700;">{t("Тяните карту — задавайте вопрос — слушайте ✨", "Draw a card — ask — listen ✨")}</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Controls
c1, c2, c3 = st.columns([2.3, 1.0, 1.0], vertical_alignment="center")
with c1:
    st.selectbox(
        t("Тема", "Topic"),
        list(CATEGORIES_UI.keys()),
        format_func=ui_label,
        label_visibility="collapsed",
        key="category",
    )
with c2:
    st.radio(
        t("Язык", "Language"),
        ["ru", "en"],
        format_func=lambda k: "RU" if k == "ru" else "EN",
        horizontal=True,
        label_visibility="collapsed",
        key="lang",
    )
with c3:
    st.toggle(t("Тёмная", "Dark"), key="dark_mode")

tabs = st.tabs([t("Игра", "Play"), t("История", "History")])

# --- Play ---
with tabs[0]:
    cat_key = st.session_state.category
    ensure_ready(cat_key)
    cur_qid = st.session_state.current_qid.get(cat_key)

    if cur_qid is None:
        st.markdown(
            f"""
            <div class="deck-wrap">
              <div class="deck">
                <div class="card-front">
                  <div class="pill" style="justify-content:center;">🎉 {t("Набор закончился","Deck completed")}</div>
                  <div class="qtext">{t("Вы вытащили все карты!","You drew every card!")}</div>
                  <div class="meta">{t("Нажмите «Сбросить», чтобы перемешать и начать заново.","Press Reset to reshuffle and start again.")}</div>
                  <div class="symbol-badge">🃏</div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(t("Сбросить и перемешать", "Reset & shuffle"), type="primary"):
            reset_deck(cat_key)
            st.rerun()
    else:
        actual_cat = get_category_of(cur_qid)
        pos = int(st.session_state.deck_pos.get(cat_key, 0)) + 1
        total = len(st.session_state.decks[cat_key])

        left_pills = []
        if cat_key == "mix":
            left_pills.append(f'<div class="pill">{ui_label("mix")}</div>')
            left_pills.append(f'<div class="pill">{ui_label(actual_cat)}</div>')
        else:
            left_pills.append(f'<div class="pill">{ui_label(actual_cat)}</div>')

        st.markdown(
            f"""
            <div class="deck-wrap">
              <div class="deck">
                <div class="card-back back2"></div>
                <div class="card-back back1"></div>
                <div class="card-front" data-deal="{st.session_state.deal_nonce}">
                  <div style="display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;">
                    <div style="display:flex;gap:10px;flex-wrap:wrap;">
                      {''.join(left_pills)}
                    </div>
                    <div class="pill">{t("карта","card")} {pos}/{total}</div>
                  </div>
                  <div class="qtext">{get_text(cur_qid)}</div>
                  <div class="symbol-badge">{bottom_symbol_for_category(actual_cat)}</div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(t("Следующий вопрос", "Next question"), type="primary"):
            draw_next(cat_key)
            st.rerun()


# --- History ---
with tabs[1]:
    history: List[str] = st.session_state.history
    if not history:
        st.caption(t("Пока пусто. Нажмите «Следующий вопрос» в разделе «Игра».",
                     "Nothing yet. Press Next in Play."))
    else:
        st.caption(t("История идёт в порядке появления (последние сверху).",
                     "History is shown in order (latest on top)."))
        for idx, qid in enumerate(reversed(history), start=1):
            cat = get_category_of(qid)
            st.markdown(
                f"""
                <div class="deck-wrap" style="margin-top:.55rem;">
                  <div class="deck" style="min-height:unset;">
                    <div class="card-front" style="padding:1rem 1rem 1.2rem 1rem;">
                      <div style="display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;">
                        <div class="pill">{ui_label(cat)}</div>
                        <div class="pill">#{len(history)-idx+1}</div>
                      </div>
                      <div class="qtext" style="font-size:1.08rem;margin-top:.75rem;">{get_text(qid)}</div>
                      <div class="symbol-badge">{bottom_symbol_for_category(cat)}</div>
                    </div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if st.button(t("Очистить историю", "Clear history"), type="secondary"):
            st.session_state.history = []
            st.rerun()
