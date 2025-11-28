from flask import Flask, render_template, request, redirect, session, send_file
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from bson.objectid import ObjectId
from io import BytesIO
from PIL import Image
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

app = Flask(__name__)
app.secret_key = "permata123"

PASSWORD_WEB = "keunganPermataPermataQQ9007&"

# ============================
# MONGODB
# ============================
MONGO_URI = "mongodb+srv://permata_user:permatasukses123@cluster0.0aooruh.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)
db = client["permata_keuangan"]
transaksi_col = db["transaksi"]

# ============================
# FUNGSI NOMINAL
# ============================
def bersihkan_nominal(x):
    return int(x.replace(".", "").replace(",", ""))

# ============================
# KOMPRES GAMBAR
# ============================
def compress_image(img_file):
    img = Image.open(img_file)
    img.thumbnail((700, 700))
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=70)
    buffer.seek(0)
    return buffer

# ============================
# LOGIN
@app.route("/", methods=["GET", "POST"])
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
    return redirect("/")

# ============================
# DASHBOARD
@app.route("/dashboard")
def dashboard():
    if "logged_in" not in session:
        return redirect("/")

    data = list(transaksi_col.find())

    pemasukan = sum(t["nominal"] for t in data if t["jenis"] == "Pemasukan")
    pengeluaran = sum(t["nominal"] for t in data if t["jenis"] == "Pengeluaran")

    return render_template("index.html",
                           data=data,
                           pemasukan=pemasukan,
                           pengeluaran=pengeluaran,
                           grafik=None)

# ============================
# FOTO BUKTI
@app.route("/foto/<id>")
def foto(id):
    t = transaksi_col.find_one({"_id": ObjectId(id)})
    if t and t.get("foto_bukti"):
        return send_file(BytesIO(t["foto_bukti"]), mimetype="image/jpeg")
    return "Tidak ada foto"

# ============================
# TAMBAH TRANSAKSI
@app.route("/tambah", methods=["GET", "POST"])
def tambah():
    if "logged_in" not in session:
        return redirect("/")

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

# ============================
# HAPUS TRANSAKSI
@app.route("/hapus/<id>")
def hapus(id):
    if "logged_in" not in session:
        return redirect("/")

    transaksi_col.delete_one({"_id": ObjectId(id)})
    return redirect("/dashboard")

# ============================
# EXPORT EXCEL
@app.route("/export")
def export_excel():
    data = list(transaksi_col.find())

    if not data:
        return "Tidak ada data."

    df = pd.DataFrame(data)
    df.drop(columns=["foto_bukti"], inplace=True)

    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)

    return send_file(buffer, as_attachment=True,
                     download_name="laporan_keuangan.xlsx",
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ============================
# EXPORT PDF
@app.route("/export_pdf")
def export_pdf():
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 800, "Laporan Keuangan PERMATA Pengumben")

    y = 760
    for t in transaksi_col.find():
        text = f"{t['waktu']} | {t['jenis']} | Rp {t['nominal']} | {t['keterangan']} | {t['penginput']}"
        c.setFont("Helvetica", 10)
        c.drawString(50, y, text)
        y -= 20
        if y < 50:
            c.showPage()
            y = 800

    c.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name="laporan_keuangan.pdf")

# ============================
if __name__ == "__main__":
    app.run(debug=True)
