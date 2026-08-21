from functools import wraps
from flask import (Flask, render_template, request, redirect, url_for, session)

import config
import aws_helpers

app = Flask(__name__)
app.secret_key = config.SECRET_KEY


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "email" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def attach_images(items):
    for it in items:
        it["image"] = aws_helpers.presigned_image_url(it.get("s3_key"))
    return items


def contains_all_words(field_value, query_text):
    # every typed word must appear somewhere in the field, any order
    value = str(field_value).lower()
    return all(word in value for word in query_text.lower().split())


def song_matches(item, title, year, artist):
    # title/artist by words, year exact, all fields AND together
    if title and not contains_all_words(item.get("title", ""), title):
        return False
    if year and str(item.get("year", "")).strip() != year:
        return False
    if artist and not contains_all_words(item.get("artist", ""), artist):
        return False
    return True


def load_subscriptions(email):
    from boto3.dynamodb.conditions import Key
    items = aws_helpers.table(config.SUBSCRIPTIONS_TABLE).query(
        KeyConditionExpression=Key("email").eq(email)
    ).get("Items", [])
    return attach_images(items)


def load_all_music():
    songs = aws_helpers.table(config.MUSIC_TABLE).scan().get("Items", [])
    songs.sort(key=lambda s: s.get("title", "").lower())
    return attach_images(songs)


@app.route("/")
def index():
    return redirect(url_for("login"))


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
            session["email"] = email
            session["user_name"] = item.get("user_name", "")
            return redirect(url_for("main"))
        error = "email or password is invalid"

    return render_template("login.html", error=error)


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
            error = "The email already exists"
        elif email and username and password:
            table.put_item(Item={
                "email": email,
                "user_name": username,
                "password": password,
            })
            return redirect(url_for("login"))
        else:
            error = "Please fill in all fields"

    return render_template("register.html", error=error)


@app.route("/main")
@login_required
def main():
    # search comes in as GET params; blank = show everything
    title = request.args.get("title", "").strip()
    year = request.args.get("ye ar", "").strip()
    artist = request.args.get("artist", "").strip()
    is_query = bool(title or year or artist)

    all_songs = load_all_music()
    if is_query:
        songs = [s for s in all_songs if song_matches(s, title, year, artist)]
        query_message = None if songs else "No result is retrieved. Please query again"
    else:
        songs = all_songs
        query_message = None

    return render_template(
        "main.html",
        user_name=session.get("user_name", ""),
        subscriptions=load_subscriptions(session["email"]),
        songs=songs,
        is_query=is_query,
        total_songs=len(all_songs),
        query_message=query_message,
        query={"title": title, "year": year, "artist": artist},
    )


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


@app.route("/remove", methods=["POST"])
@login_required
def remove():
    aws_helpers.table(config.SUBSCRIPTIONS_TABLE).delete_item(Key={
        "email": session["email"],
        "title": request.form.get("title", ""),
    })
    return redirect(url_for("main"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
