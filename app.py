"""BookSwap - Streamlit frontend + MongoDB backend."""
import pandas as pd
import streamlit as st

import db
from styles import CSS, STATUS_CLASS, badge, book_card, hero

st.set_page_config(page_title="BookSwap", page_icon="📚", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

try:
    db.get_db()
except Exception as exc:  # MongoDB not reachable
    st.error("Cannot connect to MongoDB. Start MongoDB (or set MONGO_URI) and refresh.")
    st.code(str(exc))
    st.stop()

ss = st.session_state
ss.setdefault("user", None)


# ------------------------------------------------------------------ login
def login_page():
    left, right = st.columns([1.1, 1], gap="large")
    left.markdown(hero(), unsafe_allow_html=True)
    with right:
        st.markdown("## Welcome 👋")
        t_login, t_reg = st.tabs(["🔐 Login", "✨ Create account"])
        with t_login:
            with st.form("login_form"):
                email = st.text_input("Email")
                pw = st.text_input("Password", type="password")
                if st.form_submit_button("Login"):
                    u = db.login(email, pw)
                    if u:
                        ss.user = {"id": str(u["_id"]), "name": u["name"], "email": u["email"]}
                        st.rerun()
                    st.error("Invalid email or password.")
        with t_reg:
            with st.form("reg_form"):
                name = st.text_input("Full name")
                email = st.text_input("Email", key="reg_email")
                pw = st.text_input("Password (min 6 chars)", type="password", key="reg_pw")
                if st.form_submit_button("Sign up"):
                    if not name.strip() or "@" not in email or len(pw) < 6:
                        st.error("Enter a name, a valid email and a password of 6+ characters.")
                    else:
                        u, err = db.register(name, email, pw)
                        if err:
                            st.error(err)
                        else:
                            ss.user = {"id": str(u["_id"]), "name": u["name"], "email": u["email"]}
                            st.rerun()
        st.caption("Just exploring?")
        if st.button("🎁 Load demo data"):
            db.seed_demo()
            st.success("Demo ready - login with demo@bookswap.com / demo123")


# -------------------------------------------------------------- dashboard
def dashboard(uid):
    st.title(f"Hello, {ss.user['name'].split()[0]} 👋")
    s = db.stats(uid)
    c = st.columns(4)
    c[0].metric("📚 Books available", s["available"])
    c[1].metric("📖 My books", s["mine"])
    c[2].metric("📨 Pending requests", s["incoming"])
    c[3].metric("🤝 Completed swaps", s["swaps"])

    st.subheader("Freshly listed")
    recent = db.list_books(status="Available", limit=3)
    if recent:
        for col, b in zip(st.columns(3), recent):
            col.markdown(book_card(b), unsafe_allow_html=True)
    else:
        st.info("No books yet - add the first one!")
    counts = db.genre_counts()
    if counts:
        st.subheader("Library by genre")
        st.bar_chart(pd.DataFrame({"Books": counts}), color="#6C5CE7")


# ----------------------------------------------------------------- browse
def browse(uid):
    st.title("🔎 Browse books")
    c1, c2, c3 = st.columns([2, 1, 1])
    q = c1.text_input("Search title or author", placeholder="e.g. Dune")
    genre = c2.selectbox("Genre", ["All"] + db.GENRES)
    cond = c3.selectbox("Condition", ["All"] + db.CONDITIONS)
    books = db.list_books(exclude_owner=uid, q=q, genre=genre, cond=cond, status="Available")
    mine = db.list_books(owner_id=uid, status="Available")
    if not books:
        st.info("No matching books found.")
        return
    cols = st.columns(3)
    for i, b in enumerate(books):
        with cols[i % 3]:
            st.markdown(book_card(b), unsafe_allow_html=True)
            with st.popover("🔁 Request swap"):
                if not mine:
                    st.warning("Add a book first so you have something to offer.")
                    continue
                with st.form(f"req_{b['_id']}"):
                    idx = st.selectbox("Offer one of your books", range(len(mine)),
                                       format_func=lambda k: mine[k]["title"])
                    msg = st.text_area("Message (optional)", max_chars=200)
                    if st.form_submit_button("Send request"):
                        if db.create_request(b["_id"], uid, mine[idx]["_id"], msg):
                            st.success("Request sent!")
                        else:
                            st.warning("You already have a pending request for this book.")


# --------------------------------------------------------------- add book
def add_book_page(uid):
    st.title("➕ Add a book")
    with st.form("add_book", clear_on_submit=True):
        c1, c2 = st.columns(2)
        title = c1.text_input("Title *")
        author = c2.text_input("Author *")
        genre = c1.selectbox("Genre", db.GENRES)
        cond = c2.selectbox("Condition", db.CONDITIONS, index=1)
        desc = st.text_area("Short description", max_chars=200)
        if st.form_submit_button("Add to my shelf"):
            if title.strip() and author.strip():
                db.add_book(uid, title, author, genre, cond, desc)
                st.success(f"'{title}' added! 🎉")
                st.balloons()
            else:
                st.error("Title and author are required.")


# --------------------------------------------------------------- my books
def my_books(uid):
    st.title("📖 My books")
    books = db.list_books(owner_id=uid)
    if not books:
        st.info("Your shelf is empty. Use 'Add Book' to list your first one.")
        return
    for b in books:
        with st.expander(f"{b['title']}  —  {b['author']}   ·   {b['status']}"):
            with st.form(f"edit_{b['_id']}"):
                c1, c2 = st.columns(2)
                title = c1.text_input("Title", b["title"])
                author = c2.text_input("Author", b["author"])
                genre = c1.selectbox("Genre", db.GENRES,
                                     index=db.GENRES.index(b["genre"]) if b["genre"] in db.GENRES else 0)
                cond = c2.selectbox("Condition", db.CONDITIONS,
                                    index=db.CONDITIONS.index(b["condition"]) if b["condition"] in db.CONDITIONS else 0)
                desc = st.text_area("Description", b.get("description", ""), max_chars=200)
                s, d = st.columns(2)
                if s.form_submit_button("💾 Save changes"):
                    db.update_book(b["_id"], title, author, genre, cond, desc)
                    st.rerun()
                if d.form_submit_button("🗑️ Delete"):
                    db.delete_book(b["_id"])
                    st.rerun()


# --------------------------------------------------------------- requests
def requests_page(uid):
    st.title("🔁 Swap requests")
    t_in, t_out = st.tabs(["📥 Incoming", "📤 Sent"])
    with t_in:
        items = db.requests_view(uid, incoming=True)
        if not items:
            st.info("No incoming requests yet.")
        for r in items:
            with st.container(border=True):
                st.markdown(f"**{r['other']}** wants **{r['book']['title']}** and offers "
                            f"**{r['offered']['title']}** {badge(r['status'], STATUS_CLASS[r['status']])}",
                            unsafe_allow_html=True)
                if r["message"]:
                    st.caption(f"💬 {r['message']}")
                if r["status"] == "pending":
                    a, b = st.columns(2)
                    if a.button("✅ Accept", key=f"a{r['_id']}"):
                        db.respond(r["_id"], True)
                        st.rerun()
                    if b.button("❌ Reject", key=f"r{r['_id']}"):
                        db.respond(r["_id"], False)
                        st.rerun()
    with t_out:
        items = db.requests_view(uid, incoming=False)
        if not items:
            st.info("You haven't sent any requests.")
        for r in items:
            with st.container(border=True):
                st.markdown(f"You asked **{r['other']}** for **{r['book']['title']}**, offering "
                            f"**{r['offered']['title']}** {badge(r['status'], STATUS_CLASS[r['status']])}",
                            unsafe_allow_html=True)
                if r["status"] == "pending" and st.button("Cancel request", key=f"c{r['_id']}"):
                    db.cancel_request(r["_id"])
                    st.rerun()


# ------------------------------------------------------------------- main
if not ss.user:
    login_page()
else:
    uid = ss.user["id"]
    with st.sidebar:
        st.markdown("# 📚 BookSwap")
        st.caption(f"Signed in as {ss.user['email']}")
        page = st.radio("Navigate", ["🏠 Dashboard", "🔎 Browse", "➕ Add Book", "📖 My Books", "🔁 Requests"],
                        label_visibility="collapsed")
        st.divider()
        if st.button("🚪 Logout"):
            ss.user = None
            st.rerun()
    {"🏠 Dashboard": dashboard, "🔎 Browse": browse, "➕ Add Book": add_book_page,
     "📖 My Books": my_books, "🔁 Requests": requests_page}[page](uid)
