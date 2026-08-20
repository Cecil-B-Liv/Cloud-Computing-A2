"""
Online Music Subscription -- Flask web app.

Run locally:  .venv/Scripts/python.exe app.py   ->  http://localhost:5000
Routes map directly to the assignment's rubric (Tasks 3, 4, 5).
"""
from functools import wraps
from flask import (Flask, render_template, request, redirect, url_for, session)

import config
import aws_helpers

app = Flask(__name__)
app.secret_key = config.SECRET_KEY  # signs the session cookie that keeps you logged in


def login_required(view):
    """Decorator: bounce anyone without a session back to the login page."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "email" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def attach_images(items):
    """Give each item a fresh presigned S3 image URL the browser can load."""
    for it in items:
        it["image"] = aws_helpers.presigned_image_url(it.get("s3_key"))
    return items


def contains_all_words(field_value, query_text):
    """
    Word-based, case-insensitive match: every word typed must appear somewhere
    in the field value (order doesn't matter). So "girl american" matches
    "American Girl". A plain substring query still works (it's one word / phrase).
    """
    value = str(field_value).lower()
    return all(word in value for word in query_text.lower().split())


def load_subscriptions(email):
    """Return this user's subscribed songs, each with a presigned image URL."""
    from boto3.dynamodb.conditions import Key
    items = aws_helpers.table(config.SUBSCRIPTIONS_TABLE).query(
        KeyConditionExpression=Key("email").eq(email)
    ).get("Items", [])
    return attach_images(items)


def load_all_music():
    """All songs (sorted by title) for the default browse list on the main page."""
    songs = aws_helpers.table(config.MUSIC_TABLE).scan().get("Items", [])
    songs.sort(key=lambda s: s.get("title", "").lower())
    return attach_images(songs)


@app.route("/")
def index():
    return redirect(url_for("login"))


# ----------------------------------------------------------------------
# Task 3 -- Login page
# ----------------------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        item = None
        if email:
            item = aws_helpers.table(config.LOGIN_TABLE).get_item(
                Key={"email": email}
            ).get("Item")

        if item and item.get("password") == password:
            session["email"] = email                       # 3.2 valid
            session["user_name"] = item.get("user_name", "")
            return redirect(url_for("main"))
        error = "email or password is invalid"             # 3.1 invalid

    return render_template("login.html", error=error)


# ----------------------------------------------------------------------
# Task 4 -- Register page
# ----------------------------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        table = aws_helpers.table(config.LOGIN_TABLE)
        existing = table.get_item(Key={"email": email}).get("Item") if email else None

        if existing:
            error = "The email already exists"             # 4.1
        elif email and username and password:
            table.put_item(Item={                          # 4.2 store new user
                "email": email,
                "user_name": username,
                "password": password,
            })
            return redirect(url_for("login"))              # 4.2 back to login
        else:
            error = "Please fill in all fields"

    return render_template("register.html", error=error)


# ----------------------------------------------------------------------
# Task 5 -- Main page
# ----------------------------------------------------------------------
@app.route("/main")
@login_required
def main():
    # 5.1 user area + 5.2 subscription area; browse = full list to scroll before searching
    browse = load_all_music()
    return render_template(
        "main.html",
        user_name=session.get("user_name", ""),
        subscriptions=load_subscriptions(session["email"]),
        results=None,
        browse=browse,
        total_songs=len(browse),
        query_message=None,
        query={"title": "", "year": "", "artist": ""},
    )


# 5.3 -- Query the music table
@app.route("/query", methods=["POST"])
@login_required
def query():
    title = request.form.get("title", "").strip()
    year = request.form.get("year", "").strip()
    artist = request.form.get("artist", "").strip()

    # Scan the whole music table (128 items) and filter in Python so we can do
    # case-insensitive "contains" combined with AND across the given fields.
    all_songs = aws_helpers.table(config.MUSIC_TABLE).scan().get("Items", [])

    def matches(item):
        # Each provided field must match by words; fields combine with AND.
        if title and not contains_all_words(item.get("title", ""), title):
            return False
        if year and not contains_all_words(item.get("year", ""), year):
            return False
        if artist and not contains_all_words(item.get("artist", ""), artist):
            return False
        # If the user typed nothing at all, treat it as "no match".
        return any([title, year, artist])

    results = attach_images([s for s in all_songs if matches(s)])

    # 5.3.1 no match -> message; 5.3.2 -> show the results
    query_message = None if results else "No result is retrieved. Please query again"

    return render_template(
        "main.html",
        user_name=session.get("user_name", ""),
        subscriptions=load_subscriptions(session["email"]),
        results=results,
        browse=[],
        total_songs=len(all_songs),
        query_message=query_message,
        query={"title": title, "year": year, "artist": artist},
    )


# 5.3.2.3 -- Subscribe to a song
@app.route("/subscribe", methods=["POST"])
@login_required
def subscribe():
    aws_helpers.table(config.SUBSCRIPTIONS_TABLE).put_item(Item={
        "email": session["email"],
        "title": request.form.get("title", ""),
        "artist": request.form.get("artist", ""),
        "year": request.form.get("year", ""),
        "s3_key": request.form.get("s3_key", ""),
    })
    return redirect(url_for("main"))


# 5.2.3 -- Remove a subscription
@app.route("/remove", methods=["POST"])
@login_required
def remove():
    aws_helpers.table(config.SUBSCRIPTIONS_TABLE).delete_item(Key={
        "email": session["email"],
        "title": request.form.get("title", ""),
    })
    return redirect(url_for("main"))


# 5.4 -- Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
