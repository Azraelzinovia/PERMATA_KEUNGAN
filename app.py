from flask import Flask, render_template, request, redirect, session, send_file
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from bson import ObjectId
from PIL import Image
from io import BytesIO
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime

app = Flask(__name__)
app.secret_key = "permata123"

PASSWORD_WEB = "keunganPermataPermataQQ9007&"

# MongoDB
MONGO_URI = "mongodb+srv://permata_user:permatasukses123@cluster0.0aooruh.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client["permata_keuangan"]
trans_col = db["transaksi"]

# ---------------------------
# Resize foto
# ---------------------------
def resize_image(file):
    img = Image.open(file)
    img.thumbnail((600, 600))
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=70)
    buffer.seek(0)
    return buffer.read()

# ---------------------------
# Bersihkan nominal
# ---------------------------
def bersihkan_nominal(x):
    return int(x.replace(".", "").replace(",", ""))

# ---------------------------
# LOGIN
# ---------------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["password"] == PASSWORD_WEB:
            session["login"] = True
            return redirect("/dashboard")
        return render_template("login.html", error="Password salah")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------------------
# DASHBOARD
# ---------------------------
@app.route("/dashboard")
def dashboard():
    if "login" not in session:
        return redirect("/")

    data = list(trans_col.find())

    pemasukan = sum(t["nominal"] for t in data if t["jenis"] == "Pemasukan")
    pengeluaran = sum(t["nominal"] for t in data if t["jenis"] == "Pengeluaran")

    return render_template("index.html",
                           data=data,
                           pemasukan=pemasukan,
                           pengeluaran=pengeluaran,
                           grafik=None)

# ---------------------------
# Ambil Foto dari Mongo (FIX)
# ---------------------------
@app.route("/foto/<id>")
def foto(id):
    from bson.objectid import ObjectId
    t = transaksi_col.find_one({"_id": ObjectId(id)})
    if t and "foto_bukti" in t:
        return send_file(BytesIO(t["foto_bukti"]), mimetype="image/jpeg")
    return "Tidak ada foto"

# ---------------------------
# TAMBAH TRANSAKSI
# ---------------------------
@app.route("/tambah", methods=["GET", "POST"])
def tambah():
    if "login" not in session:
        return redirect("/")

    if request.method == "POST":
        jenis = request.form["jenis"]
        nominal = bersihkan_nominal(request.form["nominal"])
        ket = request.form["keterangan"]
        penginput = request.form["penginput"]
        waktu = datetime.now().strftime("%d-%m-%Y %H:%M")

        foto = request.files["bukti"]
        foto_data = resize_image(foto) if foto else None

        trans_col.insert_one({
            "jenis": jenis,
            "nominal": nominal,
            "keterangan": ket,
            "penginput": penginput,
            "waktu": waktu,
            "foto_bukti": foto_data
        })

        return redirect("/dashboard")

    return render_template("tambah.html")

# ---------------------------
# EXPORT EXCEL (FIX)
# ---------------------------
@app.route("/export")
def export_excel():
    if "logged_in" not in session:
        return redirect("/login")

    if transaksi_col.count_documents({}) == 0:
        return "Tidak ada data."

    data = list(transaksi_col.find({}, {"foto_bukti": 0}))  # foto jangan ikut ke excel

    df = pd.DataFrame(data)
    df.drop("_id", axis=1, inplace=True)

    # Simpan ke /tmp
    file_path = "/tmp/laporan_keuangan.xlsx"
    df.to_excel(file_path, index=False)

    return send_file(file_path, as_attachment=True)

# ---------------------------
# EXPORT PDF (FIX)
# ---------------------------
@app.route("/export_pdf")
def export_pdf():
    if "logged_in" not in session:
        return redirect("/login")

    pdf_path = "/tmp/laporan_keuangan.pdf"
    c = canvas.Canvas(pdf_path, pagesize=A4)

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 800, "Laporan Keuangan PERMATA Pengumben")

    y = 760
    for t in transaksi_col.find({}, {"foto_bukti": 0}):
        c.setFont("Helvetica", 11)
        c.drawString(50, y,
            f"{t['waktu']} | {t['jenis']} | Rp {t['nominal']} | {t['keterangan']} | {t['penginput']}"
        )
        y -= 20

        if y < 50:
            c.showPage()
            y = 800

    c.save()
    return send_file(pdf_path, as_attachment=True)

# ---------------------------
if __name__ == "__main__":
    app.run(debug=True)
