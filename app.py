from flask import Flask, render_template, request, redirect, session, abort
from supabase import create_client, ClientOptions
from dotenv import load_dotenv
import httpx
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")

transport = httpx.HTTPTransport(http2=False)
httpx_client = httpx.Client(transport=transport, timeout=10.0)
options = ClientOptions(httpx_client=httpx_client)



supabase = create_client(SUPABASE_URL, SUPABASE_KEY, options)

app = Flask(__name__)
app.secret_key = SECRET_KEY


def login_required():
    if "user_id" not in session:
        return redirect("/login")


def admin_required():
    if session.get("role") != "admin":
        abort(403)


@app.route("/")
def index():
    if "user_id" in session:
        return redirect("/dashboard")
    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        try:
            auth = supabase.auth.sign_in_with_password({
                "email": request.form["email"],
                "password": request.form["password"]
            })

            user = (
                supabase
                .table("users")
                .select("*")
                .eq("id", auth.user.id)
                .single()
                .execute()
                .data
            )

            session["user_id"] = auth.user.id
            session["email"] = auth.user.email
            session["role"] = user["role"]

            return redirect("/dashboard")

        except Exception:
            error = "Email atau password salah"

    return render_template("auth/login.html", error=error, loginPage=True)


@app.route("/register", methods=["GET", "POST"])
def register():
    error = None

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        try:
            auth = supabase.auth.sign_up({
                "email": email,
                "password": password
            })

            supabase.table("users").insert({
                "id": auth.user.id,
                "email": email,
                "role": "user"
            }).execute()

            return redirect("/login")

        except Exception as e:
            print(e)
            error = "Register gagal"

    return render_template("auth/register.html", error=error, loginPage=True)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/dashboard")
def dashboard():
    login_required()

    songs = supabase.table("songs").select("*").execute().data

    if session["role"] == "admin":
        return render_template("dashboard/admin.html", s=songs)

    return render_template("dashboard/user.html", s=songs)


@app.route("/songs/add", methods=["POST"])
def add_song():
    admin_required()

    supabase.table("songs").insert({
        "title": request.form["title"],
        "artist": request.form["artist"],
        "audio_url": request.form["audio_url"],
        "cover_url": request.form["cover_url"]
    }).execute()

    return redirect("/dashboard")

@app.route("/songs/edit/<song_id>", methods=["GET", "POST"])
def edit_song(song_id):
    admin_required()

    song = (
        supabase
        .table("songs")
        .select("*")
        .eq("id", song_id)
        .single()
        .execute()
        .data
    )

    if request.method == "POST":
        supabase.table("songs").update({
            "title": request.form["title"],
            "artist": request.form["artist"],
            "audio_url": request.form["audio_url"],
            "cover_url": request.form["cover_url"]
        }).eq("id", song_id).execute()

        return redirect("/dashboard")

    return render_template("dashboard/edit_song.html", song=song)


@app.route("/songs/delete/<song_id>")
def delete_song(song_id):
    admin_required()

    supabase.table("songs").delete().eq("id", song_id).execute()
    return redirect("/dashboard")


if __name__ == "__main__":
    app.run(debug=True)
