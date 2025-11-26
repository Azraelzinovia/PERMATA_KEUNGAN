from flask import Flask, render_template, request, redirect, session, send_file, send_from_directory
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from bson.binary import Binary
from PIL import Image
from io import BytesIO
import os
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt

app = Flask(__name__)
app.secret_key = "permata123"

PASSWORD_WEB = "keunganPermataPermataQQ9007&"

# =============================== #
# CONNECT MONGODB
# =============================== #
MONGO_URI = "URL_MONGODB_ANDA"
client = MongoClient(MONGO_URI)
db = client["permata_keuangan"]
transaksi_col = db["transaksi"]

# =============================== #
# MEMBERSIHKAN NOMINAL
# =============================== #
def bersihkan_nominal(nom):
    return int(nom.replace(".", "").replace(",", ""))

# =============================== #
# RESIZE FOTO
# =============================== #
def compress_image(image_file):
    img = Image.open(image_file)
    img.thumbnail((600, 600))  # mengecilkan otomatis

    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=70)
    buffer.seek(0)
    return buffer

# =============================== #
# LOGIN
# =============================== #
@app.route("/")
def home():
    return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["password"] == PASSWORD_WEB:
            session["logged_in"] = True
            return redirect("/dashboard")
        else:
            return render_template("login.html", error="Password salah")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# =============================== #
# DASHBOARD
# =============================== #
@app.route("/dashboard")
def dashboard():
    if "logged_in" not in session:
        return redirect("/login")

    data = list(transaksi_col.find())

    pemasukan = sum(t["nominal"] for t in data if t["jenis"] == "Pemasukan")
    pengeluaran = sum(t["nominal"] for t in data if t["jenis"] == "Pengeluaran")

    return render_template("index.html",
                           data=data,
                           pemasukan=pemasukan,
                           pengeluaran=pengeluaran,
                           grafik=None)
@app.route("/foto/<id>")
def foto(id):
    t = transaksi_col.find_one({"_id": id})
    if t and "foto_bukti" in t:
        return send_file(BytesIO(t["foto_bukti"]), mimetype="image/jpeg")
    return "Tidak ada foto"
@app.route("/tambah", methods=["GET", "POST"])
def tambah():
    if "logged_in" not in session:
        return redirect("/login")

    if request.method == "POST":
        jenis = request.form["jenis"]
        nominal = bersihkan_nominal(request.form["nominal"])
        keterangan = request.form["keterangan"]
        penginput = request.form["penginput"]
        waktu = datetime.now().strftime("%d-%m-%Y %H:%M")

        foto = request.files["bukti"]
        foto_data = None

        if foto:
            compressed = compress_image(foto)
            foto_data = compressed.read()

        transaksi_col.insert_one({
            "jenis": jenis,
            "nominal": nominal,
            "keterangan": keterangan,
            "penginput": penginput,
            "waktu": waktu,
            "foto_bukti": foto_data
        })

        return redirect("/dashboard")

    return render_template("tambah.html")
