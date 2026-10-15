"""Custom CSS and HTML snippets for a polished look."""
import html

CSS = """
<style>
#MainMenu, footer {visibility:hidden;}
.stApp {background: linear-gradient(135deg,#F7F5FF 0%,#EEF3FF 100%);}
section[data-testid="stSidebar"] {background: linear-gradient(180deg,#4B3FD1 0%,#7B5CFA 60%,#B06AF5 100%);}
section[data-testid="stSidebar"] * {color:#fff !important;}
.stButton>button, .stFormSubmitButton>button {
    width:100%; border-radius:12px; border:0; padding:.55rem 1rem; font-weight:600;
    background: linear-gradient(90deg,#6C5CE7,#A66CFF); color:#fff;
    transition: transform .15s, box-shadow .15s;}
.stButton>button:hover, .stFormSubmitButton>button:hover {
    transform: translateY(-2px); box-shadow:0 8px 20px rgba(108,92,231,.35); color:#fff;}
div[data-testid="stMetric"] {background:#fff; padding:16px 18px; border-radius:16px;
    box-shadow:0 6px 18px rgba(108,92,231,.10); border-left:5px solid #6C5CE7;}
.hero {padding:48px 40px; border-radius:24px; color:#fff; min-height:430px;
    background: linear-gradient(135deg,#6C5CE7,#A66CFF 55%,#FF7EB3);
    box-shadow:0 20px 50px rgba(108,92,231,.35);}
.hero h1 {font-size:3rem; margin:0 0 8px; color:#fff;}
.hero p {font-size:1.1rem; opacity:.95;}
.hero li {margin:8px 0; font-size:1.05rem;}
.book {background:#fff; border-radius:18px; overflow:hidden; margin-bottom:10px;
    box-shadow:0 8px 24px rgba(45,42,74,.08); transition: transform .2s;}
.book:hover {transform: translateY(-4px);}
.cover {height:110px; display:flex; align-items:center; justify-content:center; font-size:2.6rem;}
.body {padding:14px 16px 12px;}
.body h4 {margin:0; font-size:1.05rem; color:#2D2A4A;}
.body .by {color:#7a7799; font-size:.88rem; margin-bottom:8px;}
.badge {display:inline-block; padding:2px 10px; border-radius:20px; font-size:.75rem;
    font-weight:600; margin-right:6px; background:#EDE9FF; color:#5B4BD6;}
.badge.green {background:#DFF8EA; color:#1B8A4B;} .badge.orange {background:#FFF0DB; color:#B76A00;}
.badge.red {background:#FFE3E6; color:#C0283C;} .badge.grey {background:#ECECF3; color:#666;}
.desc {color:#55526f; font-size:.88rem; margin-top:8px; min-height:38px;}
.owner {color:#9b98b5; font-size:.8rem; margin-top:6px;}
</style>
"""

STATUS_CLASS = {"Available": "green", "Swapped": "grey", "pending": "orange",
                "accepted": "green", "rejected": "red", "cancelled": "grey"}


def badge(text, cls=""):
    return f"<span class='badge {cls}'>{html.escape(str(text))}</span>"


def hero():
    return """<div class='hero'><h1>📚 BookSwap</h1>
    <p>Trade the books you've finished for the ones you've been dying to read.</p>
    <ul><li>📖 List your books in seconds</li><li>🔎 Search a growing community library</li>
    <li>🔁 Send &amp; manage swap requests</li><li>🌱 Read more, spend nothing</li></ul></div>"""


def book_card(b):
    hue = sum(map(ord, b["title"])) % 360
    emoji = {"Sci-Fi": "🚀", "Fantasy": "🐉", "Mystery": "🕵️", "Romance": "💕", "Technology": "💻",
             "History": "🏛️", "Biography": "👤", "Self-Help": "🌱", "Academic": "🎓"}.get(b.get("genre"), "📕")
    e = html.escape
    return f"""<div class='book'>
      <div class='cover' style='background:linear-gradient(135deg,hsl({hue},75%,62%),hsl({(hue+50)%360},80%,70%))'>{emoji}</div>
      <div class='body'><h4>{e(b['title'])}</h4><div class='by'>by {e(b['author'])}</div>
      {badge(b['genre'])}{badge(b['condition'], 'orange')}{badge(b['status'], STATUS_CLASS.get(b['status'], ''))}
      <div class='desc'>{e(b.get('description') or 'No description.')}</div>
      <div class='owner'>👤 {e(b.get('owner_name', 'You'))}</div></div></div>"""
