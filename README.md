# 📚 BookSwap - Book Swapping System
Python (Streamlit) frontend + MongoDB (PyMongo) backend.

## Features
- Register / Login (PBKDF2-hashed passwords, salted)
- **Create** books, **Read/Search/Filter** them, **Update** and **Delete** your own
- Swap requests: send, accept, reject, cancel (accepting marks both books as Swapped)
- Dashboard with live stats and genre chart

## Run
1. Install Python 3.9+ and MongoDB Community (or use a free MongoDB Atlas cluster).
2. `pip install -r requirements.txt`
3. Make sure MongoDB is running (default `mongodb://localhost:27017`).
   For Atlas: `export MONGO_URI="mongodb+srv://user:pass@cluster/..."` (Windows: `set MONGO_URI=...`)
4. `streamlit run app.py`
5. Click **Load demo data** on the login page, then login with `demo@bookswap.com` / `demo123`
   (second user: `alex@bookswap.com` / `demo123` - log in as each to test swaps).

## Files
- `app.py` - UI and pages
- `db.py` - MongoDB connection and all CRUD logic
- `styles.py` - CSS and HTML cards
- `.streamlit/config.toml` - theme

## Collections
`users`, `books`, `requests`
