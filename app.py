from flask import Flask, render_template, request, redirect, session, send_file
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from bson.objectid import ObjectId
from PIL import Image
from io import BytesIO
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import base64

app = Flask(__name__)
app.secret_key = "permata123"

PASSWORD_WEB = "keunganPermataPermataQQ9007&"

# ==========================
# MONGODB ATLAS CONNECTION
# ==========================
MONGO_URI = "mongodb+srv://permata_user:permatasukses123%40@cluster0.0aooruh.mongodb.net/permata_keuangan?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)

db = client["permata_keuangan"]
transaksi_col = db["transaksi"]


# ==========================
# CLEAN NOMINAL
# ==========================
def bersihkan_nominal(nom):
    return int(nom.replace(".", "").replace(",", ""))


# ==========================
# COMPRESS FOTO
# ==========================
def compress_image(image_file):
    img = Image.open(image_file)
    img.thumbnail((600, 600))

    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=70)
    buffer.seek(0)
    return buffer


# ==========================
# LOGIN PAGE
# ==========================
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


# ==========================
# DASHBOARD PAGE
# ==========================
@app.route("/dashboard")
def dashboard():
    if "logged_in" not in session:
        return redirect("/login")

    data = list(transaksi_col.find())

    # Hitung pemasukan & pengeluaran
    pemasukan = sum(t["nominal"] for t in data if t["jenis"] == "Pemasukan")
    pengeluaran = sum(t["nominal"] for t in data if t["jenis"] == "Pengeluaran")

    return render_template("index.html",
                           data=data,
                           pemasukan=pemasukan,
                           pengeluaran=pengeluaran)


# ==========================
# VIEW FOTO
# ==========================
@app.route("/foto/<id>")
def foto(id):
    try:
        t = transaksi_col.find_one({"_id": ObjectId(id)})
        if t and "foto_bukti" in t and t["foto_bukti"] is not None:
            return send_file(BytesIO(t["foto_bukti"]), mimetype="image/jpeg")
        return "Foto tidak ditemukan"
    except:
        return "Error ID foto"


# ==========================
# TAMBAH TRANSAKSI
# ==========================
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


# ==========================
# HAPUS TRANSAKSI
# ==========================
@app.route("/hapus/<id>")
def hapus(id):
    if "logged_in" not in session:
        return redirect("/login")

    transaksi_col.delete_one({"_id": ObjectId(id)})
    return redirect("/dashboard")


# ==========================
# RUN (LOCAL)
# ==========================
if __name__ == "__main__":
    app.run(debug=True)
