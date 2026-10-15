"""MongoDB data layer for BookSwap (all CRUD lives here)."""
import hashlib
import os
import re
import secrets
from datetime import datetime

import streamlit as st
from bson import ObjectId
from pymongo import MongoClient

GENRES = ["Fiction", "Non-Fiction", "Sci-Fi", "Fantasy", "Mystery", "Romance",
          "Biography", "Self-Help", "History", "Technology", "Academic", "Other"]
CONDITIONS = ["New", "Like New", "Good", "Fair"]


@st.cache_resource
def get_db():
    uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    client = MongoClient(uri, serverSelectionTimeoutMS=3000)
    client.admin.command("ping")  # fail fast if MongoDB is down
    database = client[os.getenv("MONGO_DB", "book_swap")]
    database.users.create_index("email", unique=True)
    database.books.create_index("owner_id")
    database.requests.create_index([("owner_id", 1), ("requester_id", 1)])
    return database


def oid(x):
    return x if isinstance(x, ObjectId) else ObjectId(x)


# ---------------------------------------------------------------- users
def _hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 120_000).hex()
    return salt, digest


def register(name, email, password):
    d, email = get_db(), email.strip().lower()
    if d.users.find_one({"email": email}):
        return None, "That email is already registered."
    salt, digest = _hash(password)
    res = d.users.insert_one({"name": name.strip(), "email": email, "salt": salt,
                              "hash": digest, "created": datetime.utcnow()})
    return d.users.find_one({"_id": res.inserted_id}), None


def login(email, password):
    user = get_db().users.find_one({"email": email.strip().lower()})
    if not user:
        return None
    _, digest = _hash(password, user["salt"])
    return user if secrets.compare_digest(digest, user["hash"]) else None


# ---------------------------------------------------------------- books
def add_book(owner_id, title, author, genre, condition, description):
    return get_db().books.insert_one({
        "owner_id": oid(owner_id), "title": title.strip(), "author": author.strip(),
        "genre": genre, "condition": condition, "description": description.strip(),
        "status": "Available", "created": datetime.utcnow()})


def list_books(owner_id=None, exclude_owner=None, q="", genre="All", cond="All", status=None, limit=0):
    query = {}
    if owner_id:
        query["owner_id"] = oid(owner_id)
    if exclude_owner:
        query["owner_id"] = {"$ne": oid(exclude_owner)}
    if q:
        rx = {"$regex": re.escape(q), "$options": "i"}
        query["$or"] = [{"title": rx}, {"author": rx}]
    if genre != "All":
        query["genre"] = genre
    if cond != "All":
        query["condition"] = cond
    if status:
        query["status"] = status
    cur = get_db().books.find(query).sort("created", -1)
    if limit:
        cur = cur.limit(limit)
    books = list(cur)
    owners = {u["_id"]: u["name"] for u in get_db().users.find({"_id": {"$in": [b["owner_id"] for b in books]}})}
    for b in books:
        b["owner_name"] = owners.get(b["owner_id"], "Unknown")
    return books


def update_book(book_id, title, author, genre, condition, description):
    get_db().books.update_one({"_id": oid(book_id)}, {"$set": {
        "title": title.strip(), "author": author.strip(), "genre": genre,
        "condition": condition, "description": description.strip()}})


def delete_book(book_id):
    d = get_db()
    d.books.delete_one({"_id": oid(book_id)})
    d.requests.delete_many({"$or": [{"book_id": oid(book_id)}, {"offered_id": oid(book_id)}]})


# ---------------------------------------------------------------- requests
def create_request(book_id, requester_id, offered_id, message):
    d = get_db()
    book = d.books.find_one({"_id": oid(book_id)})
    if not book or book["status"] != "Available":
        return False
    if d.requests.find_one({"book_id": book["_id"], "requester_id": oid(requester_id), "status": "pending"}):
        return False
    d.requests.insert_one({"book_id": book["_id"], "owner_id": book["owner_id"],
                           "requester_id": oid(requester_id), "offered_id": oid(offered_id),
                           "message": message.strip(), "status": "pending",
                           "created": datetime.utcnow()})
    return True


def requests_view(user_id, incoming=True):
    d = get_db()
    key = "owner_id" if incoming else "requester_id"
    out = []
    for r in d.requests.find({key: oid(user_id)}).sort("created", -1):
        r["book"] = d.books.find_one({"_id": r["book_id"]}) or {"title": "(deleted book)"}
        r["offered"] = d.books.find_one({"_id": r["offered_id"]}) or {"title": "(deleted book)"}
        other = r["requester_id"] if incoming else r["owner_id"]
        r["other"] = (d.users.find_one({"_id": other}) or {}).get("name", "Unknown")
        out.append(r)
    return out


def respond(req_id, accept):
    d = get_db()
    r = d.requests.find_one({"_id": oid(req_id)})
    if not r or r["status"] != "pending":
        return
    if not accept:
        d.requests.update_one({"_id": r["_id"]}, {"$set": {"status": "rejected"}})
        return
    ids = [r["book_id"], r["offered_id"]]
    d.books.update_many({"_id": {"$in": ids}}, {"$set": {"status": "Swapped"}})
    d.requests.update_one({"_id": r["_id"]}, {"$set": {"status": "accepted"}})
    d.requests.update_many({"status": "pending", "_id": {"$ne": r["_id"]},
                            "$or": [{"book_id": {"$in": ids}}, {"offered_id": {"$in": ids}}]},
                           {"$set": {"status": "rejected"}})


def cancel_request(req_id):
    get_db().requests.update_one({"_id": oid(req_id), "status": "pending"}, {"$set": {"status": "cancelled"}})


# ---------------------------------------------------------------- stats / demo
def stats(user_id):
    d, u = get_db(), oid(user_id)
    return {
        "available": d.books.count_documents({"status": "Available"}),
        "mine": d.books.count_documents({"owner_id": u}),
        "incoming": d.requests.count_documents({"owner_id": u, "status": "pending"}),
        "swaps": d.requests.count_documents({"status": "accepted", "$or": [{"owner_id": u}, {"requester_id": u}]}),
    }


def genre_counts():
    rows = get_db().books.aggregate([{"$match": {"status": "Available"}},
                                     {"$group": {"_id": "$genre", "Books": {"$sum": 1}}}])
    return {r["_id"]: r["Books"] for r in rows}


def seed_demo():
    d = get_db()
    users = {}
    for name, email in [("Demo User", "demo@bookswap.com"), ("Alex Reader", "alex@bookswap.com")]:
        u = d.users.find_one({"email": email})
        if not u:
            u, _ = register(name, email, "demo123")
        users[email] = u["_id"]
    if d.books.count_documents({"owner_id": {"$in": list(users.values())}}):
        return
    sample = [
        ("demo@bookswap.com", "Atomic Habits", "James Clear", "Self-Help", "Like New", "Tiny changes, remarkable results."),
        ("demo@bookswap.com", "The Hobbit", "J.R.R. Tolkien", "Fantasy", "Good", "There and back again."),
        ("demo@bookswap.com", "Clean Code", "Robert C. Martin", "Technology", "Good", "A handbook of agile craftsmanship."),
        ("alex@bookswap.com", "Dune", "Frank Herbert", "Sci-Fi", "Good", "Spice, sand and politics."),
        ("alex@bookswap.com", "Sapiens", "Yuval Noah Harari", "History", "Like New", "A brief history of humankind."),
        ("alex@bookswap.com", "The Alchemist", "Paulo Coelho", "Fiction", "Fair", "Follow your personal legend."),
        ("alex@bookswap.com", "Gone Girl", "Gillian Flynn", "Mystery", "New", "A twisty psychological thriller."),
    ]
    for email, *fields in sample:
        add_book(users[email], *fields)
