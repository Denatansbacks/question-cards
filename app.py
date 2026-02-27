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
def load_questions(mtime: float) -> Tuple[Dict[str, dict], Dict[str, List[str]]]:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    by_id: Dict[str, dict] = {q["id"]: q for q in data["questions"]}
    by_cat: Dict[str, List[str]] = {}
    for q in data["questions"]:
        by_cat.setdefault(q["category"], []).append(q["id"])
    for k in by_cat:
        by_cat[k] = sorted(by_cat[k])
    return by_id, by_cat


Q_BY_ID, IDS_BY_CAT = load_questions(DATA_PATH.stat().st_mtime)
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
    st.session_state.setdefault("mix_categories", ["friends", "couple", "party", "smart", "adult"])
    st.session_state.setdefault("_mix_categories_prev", ["friends", "couple", "party", "smart", "adult"])
    st.session_state.setdefault("dark_mode", False)
    st.session_state.setdefault("show_settings", False)
    st.session_state.setdefault("history", [])  # asked question ids in order
    st.session_state.setdefault("decks", {})      # cat_key -> list[qid]
    st.session_state.setdefault("deck_pos", {})   # cat_key -> int
    st.session_state.setdefault("current_qid", {})  # cat_key -> qid
    st.session_state.setdefault("deal_nonce", 0)  # retrigger deal animation


def ids_for_deck(cat_key: str) -> List[str]:
    if cat_key == "mix":
        selected = st.session_state.get("mix_categories", [])
        ids: List[str] = []
        for c in selected:
            ids.extend(IDS_BY_CAT.get(c, []))
        return ids
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



def format_question_html(text: str) -> str:
    """Escape text for HTML and force a line break after the 3rd word."""
    import html as _html
    safe = _html.escape(text)
    words = safe.split()
    if len(words) <= 3:
        return safe
    return " ".join(words[:3]) + "<br>" + " ".join(words[3:])

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
        primary = "#F0483E"
        primary_text = "#FFFFFF"
        secondary_bg = "rgba(255,255,255,.88)"
        secondary_border = "rgba(17,24,39,.16)"
        secondary_text = "rgba(17,24,39,.90)"
        tab_text = "rgba(17,24,39,.92)"
        radio_bg = "rgba(17,24,39,.18)"
        toggle_bg = "rgba(17,24,39,.12)"
        toggle_text_off = "rgba(17,24,39,.92)"
        toggle_text_on = "rgba(255,255,255,.98)"
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
        radio_bg = "rgba(255,255,255,.10)"
        toggle_bg = "rgba(255,255,255,.10)"
        toggle_text_off = "rgba(17,24,39,.92)"
        toggle_text_on = "rgba(255,255,255,.98)"

    sidebar_hidden_css = ""
    if not st.session_state.get("show_settings", False):
        sidebar_hidden_css = """
        [data-testid=\"stSidebar\"] { display: none !important; }
        """

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
            max-width: 820px;
        }}

        /* Chips */

        /* Radio pills (RU/EN) — add background for readability */
        div[role="radiogroup"] {{
            gap: .45rem;
        }}
        div[role="radiogroup"] label {{
            background: {radio_bg} !important;
            border: 1px solid {secondary_border} !important;
            box-shadow: 0 8px 18px rgba(0,0,0,.08);
            border-radius: 999px !important;
            padding: .35rem .7rem !important;
            margin: 0 .25rem 0 0 !important;
            color: {secondary_text} !important;
            font-weight: 900 !important;
        }}
        /* Selected radio option */
        div[role="radiogroup"] label:has(input:checked) {{
            background: {primary} !important;
            border-color: {primary} !important;
            color: {primary_text} !important;
        }}
        div[role="radiogroup"] label:has(input:checked) * {{
            color: {primary_text} !important;
        }}

        /* Toggle chip (Dark/Light) — background behind switch+text */

        /* Toggle switch track/thumb visibility */
        div[data-testid="stToggle"] [data-baseweb="switch"] > div {{
            background: rgba(17,24,39,.22) !important;
        }}
        div[data-testid="stToggle"] [data-baseweb="switch"] div[role="switch"][aria-checked="true"] {{
            background: {primary} !important;
        }}
        div[data-testid="stToggle"] [data-baseweb="switch"] div[role="switch"] {{
            box-shadow: inset 0 0 0 1px {secondary_border} !important;
        }}


        div[data-testid="stToggle"] {{
            display: inline-flex !important;
            padding: .05rem;
            border-radius: 999px;
            background: {toggle_bg} !important;
            border: 1px solid {secondary_border} !important;
        }}


        div[data-testid="stToggle"] label {{
            background: {toggle_bg} !important;
            border: 1px solid {secondary_border} !important;
            border-radius: 999px !important;
            padding: .35rem .7rem !important;
            display: inline-flex !important;
            align-items: center !important;
            gap: .6rem !important;
        }}
        div[data-testid="stToggle"] label * {{
            color: {secondary_text} !important;
            font-weight: 900 !important;
        }}

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
        .deck-wrap {{ margin-top: .7rem; margin-bottom: .9rem; display:flex; justify-content:center; }}
        .deck {{ position: relative; width: 100%; padding-bottom: 18px; }}
        /* Main card area: fixed aspect ratio (depends on device aspect) */
        .deck.deck-main {{
            width: min(100%, 860px);
            aspect-ratio: 4 / 3;
        }}
        /* Wide screens: slightly wider card */
        @media (min-aspect-ratio: 4/3) {{
            .deck.deck-main {{ aspect-ratio: 16 / 10; }}
        }}

        /* Mini cards in History: auto height */
        .deck.deck-mini {{
            aspect-ratio: auto;
            padding-bottom: 0;
        }}
        .deck.deck-mini .card-front {{
            height: auto;
        }}

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
            height: 100%;
            padding: 1.35rem 1.25rem 1.55rem 1.25rem;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            gap: .6rem;
            animation: dealIn .22s ease-out;
            overflow: hidden;
        }}
        /* Card aspect ratio changes with device aspect ratio */
        .card-front {{
            aspect-ratio: 4 / 3; /* portrait default */
        }}
        @media (min-aspect-ratio: 4/3) {{
            .card-front {{ aspect-ratio: 16 / 10; }}
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

        /* Pinned top bar inside the card */
        .card-topbar {{
            position: absolute;
            top: 14px;
            left: 14px;
            right: 14px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
            z-index: 2;
        }}
        .card-count {{
            font-size: .9rem;
            font-weight: 900;
            color: {sub};
        }}
        .card-center {{
            flex: 1;
            min-height: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: .6rem;
            padding-top: 2.2rem; /* reserve space under pinned topbar */
            padding-bottom: 1.3rem; /* reserve space above bottom badge */
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
            font-size: 1.38rem;
            line-height: 1.35;
            font-weight: 900;
            color: {text};
            margin-top: .95rem;
            text-align: center;
            padding: 0 .2rem;
            max-height: 66%;
            overflow: hidden;
            
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
            width: 62px;
            height: 40px;
            border-radius: 999px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: {card_bg};
            border: 2px solid {inner};
            box-shadow: 0 10px 24px {shadow};
            font-size: 19px;
        }}
        {sidebar_hidden_css}

        /* Sidebar styling */
        [data-testid="stSidebar"] {{
            border-right: 1px solid {secondary_border} !important;
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
c1, c2, c3, c4 = st.columns([2.3, 1.0, 1.0, 0.65], vertical_alignment="center")
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

with c4:
    # Sidebar is hidden because Streamlit header is hidden; provide our own toggle
    if st.button("⚙️", help=t("Открыть/закрыть настройки (sidebar)", "Open/close settings (sidebar)"), type="secondary"):
        st.session_state.show_settings = not st.session_state.show_settings
        st.rerun()


# Sidebar: Mix categories (only affects "Микс")
if st.session_state.get("show_settings", False):
        with st.sidebar:
        st.markdown("### " + t("Настройки микса", "Mix settings"))
        st.caption(t("Выберите, какие темы попадут в «Микс».", "Choose which topics are included in Mix."))

        mix_opts = [k for k in CATEGORIES_UI.keys() if k != "mix"]

        if st.session_state.category == "mix":
            st.multiselect(
                t("Категории", "Categories"),
                mix_opts,
                format_func=ui_label,
                key="mix_categories",
            )
            cur_sel = list(st.session_state.get("mix_categories", []))
            prev_sel = list(st.session_state.get("_mix_categories_prev", []))

            if len(cur_sel) == 0:
                st.warning(t("Выберите хотя бы одну категорию — иначе колода будет пустой.", "Pick at least one category, otherwise the deck is empty."))

            if cur_sel != prev_sel:
                st.session_state["_mix_categories_prev"] = cur_sel
                reset_deck("mix")
                st.rerun()
        else:
            st.info(t("Переключитесь на «Микс», чтобы выбрать категории.", "Switch to Mix to choose categories."))


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
              <div class="deck deck-main">
                <div class="card-front">
                  <div class="card-topbar">
                    <div class="pill">{ui_label(cat_key)}</div>
                    <div class="card-count">{t("готово","done")}</div>
                  </div>
                  <div class="card-center">
                    <div class="qtext" style="font-size:1.35rem;">{t("Вы вытащили все карты!","You drew every card!")}</div>
                    <div class="meta">{t("Нажмите «Сбросить», чтобы перемешать и начать заново.","Press Reset to reshuffle and start again.")}</div>
                  </div>
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

        # Show only the actual category on the card (no 'mix' label inside)
        left_label = ui_label(actual_cat)
        # Adaptive font size: shrink for long questions (avoid scrolling)
        q_text = get_text(cur_qid)
        q_html = format_question_html(q_text)
        words_n = len(q_text.split())
        chars_n = len(q_text)

        # Keep sizes conservative (mandatory line break after 3rd word adds height)
        if words_n <= 8 and chars_n <= 70:
            q_font = 1.30
        elif words_n <= 12 and chars_n <= 95:
            q_font = 1.18
        elif words_n <= 16 and chars_n <= 125:
            q_font = 1.06
        elif words_n <= 22 and chars_n <= 165:
            q_font = 0.96
        else:
            q_font = 0.86

        st.markdown(
            f"""
            <div class="deck-wrap">
              <div class="deck deck-main">
                <div class="card-back back2"></div>
                <div class="card-back back1"></div>
                <div class="card-front" data-deal="{st.session_state.deal_nonce}">
                  <div class="card-topbar">
                    <div class="pill">{left_label}</div>
                    <div class="card-count">{pos}/{total}</div>
                  </div>
                  <div class="card-center">
                    <div class="qtext" style="font-size:{q_font}rem;">{q_html}</div>
                  </div>
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

        if st.button(t("Перемешать карточки", "Shuffle deck"), type="primary"):
            reset_deck(cat_key)
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
                  <div class="deck deck-mini">
                    <div class="card-front" style="padding:1rem 1rem 1.2rem 1rem;">
                      <div style="display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;">
                        <div class="pill">{ui_label(cat)}</div>
                        <div class="pill">#{len(history)-idx+1}</div>
                      </div>
                      <div class="qtext" style="font-size:1.08rem;margin-top:.75rem;">{format_question_html(get_text(qid))}</div>
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