from flask import Flask, render_template, request, redirect, session, abort, flash, url_for, jsonify
from werkzeug.utils import secure_filename
from supabase import create_client, ClientOptions
from dotenv import load_dotenv
import httpx
import os
import uuid


load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")

transport = httpx.HTTPTransport(http2=False)
httpx_client = httpx.Client(transport=transport, timeout=10.0)
options = ClientOptions(httpx_client=httpx_client)


if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE env belum diset")


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

    songs = supabase.table("songs").select(
        "*").order("title", desc=False).execute().data

    if session.get("role") == "admin":
        return render_template("dashboard/admin.html", songs=songs)

    return render_template("dashboard/user.html", songs=songs)


@app.route("/songs/add", methods=["POST"])
def add_song():
    admin_required()

    if request.method == "POST":
        title = request.form.get("title")
        artist = request.form.get('artist')
        audio_file = request.files.get('audio_file')
        cover_file = request.files.get('cover_file')

        audio_filename = f"{uuid.uuid4()}-{secure_filename(audio_file.filename)}"
        cover_filename = f"{uuid.uuid4()}-{secure_filename(cover_file.filename)}"

        audio_data = audio_file.read()
        cover_data = cover_file.read()

        supabase.storage.from_("songs").upload(
            path=audio_filename,
            file=audio_data,
            file_options={"content-type": audio_file.content_type}
        )

        audio_url = supabase.storage.from_("songs").get_public_url(
            audio_filename
        )

        supabase.storage.from_("cover_audio").upload(
            path=cover_filename,
            file=cover_data,
            file_options={"content-type": cover_file.content_type}
        )

        cover_url = supabase.storage.from_("cover_audio").get_public_url(
            cover_filename
        )

        supabase.table("songs").insert({
            "title": title,
            "artist": artist,
            "audio_url": audio_url,
            "cover_url": cover_url
        }).execute()

        return redirect("/dashboard")

    return redirect("/dashboard")


@app.route("/songs/edit/<song_id>", methods=["GET", "POST"])
def edit_song(song_id):
    admin_required()

    song = supabase.table("songs").select(
        "*").eq("id", song_id).single().execute().data
    if not song:
        return redirect("/dashboard")

    if request.method == "POST":
        title = request.form.get('title')
        artist = request.form.get('artist')

        res = supabase.table('songs').update({
            "title": title,
            "artist": artist
        }).eq("id", song_id).execute()

        flash('Update berhasil!', 'success')
        return redirect(url_for('dashboard'))

    return render_template("dashboard/edit.html", song=song)


@app.route("/songs/delete/<song_id>", methods=["POST"])
def delete_song(song_id):
    admin_required()

    res = supabase.table('songs').select(
        'audio_url, cover_url').eq('id', song_id).execute()

    if not res.data:
        return jsonify({"success": False, "error": "Song not found"}), 404

    audio_url = res.data[0]["audio_url"]
    cover_url = res.data[0]["cover_url"]
    audio_name = audio_url.split("/")[-1]
    cover_name = cover_url.split("/")[-1]

    supabase.storage.from_("songs").remove([audio_name])
    supabase.storage.from_("cover_audio").remove([cover_name])

    supabase.table('songs').delete().eq('id', song_id).execute()

    return jsonify({"success": True})


if __name__ == "__main__":
    app.run(debug=True)
