from flask import Flask, render_template, request, redirect, session, send_file
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from bson.objectid import ObjectId
from PIL import Image
from io import BytesIO
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import os

app = Flask(__name__)
app.secret_key = "permata123"

PASSWORD_WEB = "keunganPermataPermataQQ9007&"

# ===============================
# MONGODB CONNECTION
# ===============================
MONGO_URI = "mongodb+srv://permata_user:permatasukses123@cluster0.0aooruh.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)
db = client["permata_keuangan"]
transaksi_col = db["transaksi"]


# ===============================
# CLEAN NOMINAL
# ===============================
def bersihkan_nominal(nom):
    return int(nom.replace(".", "").replace(",", ""))


# ===============================
# COMPRESS IMAGE
# ===============================
def compress_image(image_file):
    img = Image.open(image_file)
    img.thumbnail((600, 600))

    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=70)
    buffer.seek(0)
    return buffer


# ===============================
# LOGIN SYSTEM
# ===============================
@app.route("/")
def home():
    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["password"] == PASSWORD_WEB:
            session["logged_in"] = True
            return redirect("/dashboard")
        return render_template("login.html", error="Password salah")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ===============================
# DASHBOARD
# ===============================
@app.route("/dashboard")
def dashboard():
    if "logged_in" not in session:
        return redirect("/login")

    data = list(transaksi_col.find())

    pemasukan = sum(t["nominal"] for t in data if t["jenis"] == "Pemasukan")
    pengeluaran = sum(t["nominal"] for t in data if t["jenis"] == "Pengeluaran")

    # Grafik sementara dimatikan supaya tidak error
    grafik = None

    return render_template("index.html",
                           data=data,
                           pemasukan=pemasukan,
                           pengeluaran=pengeluaran,
                           grafik=grafik)


# ===============================
# SHOW FOTO BUKTI
# ===============================
@app.route("/foto/<id>")
def foto(id):
    t = transaksi_col.find_one({"_id": ObjectId(id)})
    if t and t.get("foto_bukti"):
        return send_file(BytesIO(t["foto_bukti"]), mimetype="image/jpeg")
    return "Foto tidak ditemukan"


# ===============================
# TAMBAH TRANSAKSI
# ===============================
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
            foto_data = compress_image(foto).read()

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


# ===============================
# EXPORT EXCEL
# ===============================
@app.route("/export")
def export_excel():
    if "logged_in" not in session:
        return redirect("/login")

    data = list(transaksi_col.find())
    if not data:
        return "Tidak ada data"

    df = pd.DataFrame(data)
    df.drop(columns=["foto_bukti"], inplace=True)

    file_path = "/tmp/laporan_keuangan.xlsx"
    df.to_excel(file_path, index=False)

    return send_file(file_path, as_attachment=True)


# ===============================
# EXPORT PDF
# ===============================
@app.route("/export_pdf")
def export_pdf():
    if "logged_in" not in session:
        return redirect("/login")

    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    file_path = "/tmp/laporan_keuangan.pdf"
    c = canvas.Canvas(file_path, pagesize=A4)

    y = 800
    c.setFont("Helvetica-Bold", 15)
    c.drawString(50, y, "Laporan Keuangan PERMATA Pengumben")
    y -= 30

    data = list(transaksi_col.find())
    c.setFont("Helvetica", 10)

    for t in data:
        c.drawString(50, y, f"{t['waktu']} | {t['jenis']} | Rp {t['nominal']} | {t['penginput']} | {t['keterangan']}")
        y -= 20
        if y < 40:
            c.showPage()
            y = 800

    c.save()
    return send_file(file_path, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
