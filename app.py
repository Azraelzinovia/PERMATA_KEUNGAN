from flask import Flask, render_template, request, redirect, session, send_file, send_from_directory
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = "permata123"

# PASSWORD LOGIN
PASSWORD_WEB = "keunganPermataPermataQQ9007&"

# FOLDER UPLOAD RAILWAY
UPLOAD_FOLDER = "/tmp/uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

# TEMPAT MENYIMPAN DATA TRANSAKSI
data_transaksi = []


def bersihkan_nominal(nom):
    nom = nom.replace(".", "").replace(",", "")
    return int(nom)


def buat_grafik_bulanan(df):
    plt.figure(figsize=(8, 4))
    df.groupby("jenis")["nominal"].sum().plot(kind="bar", color=["blue", "red"])
    plt.title("Rekap Keuangan PERMATA Pengumben")
    plt.ylabel("Jumlah (Rp)")
    plt.tight_layout()

    grafik_path = "/tmp/grafik.png"
    plt.savefig(grafik_path)
    plt.close()

    return grafik_path


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


@app.route("/dashboard")
def dashboard():
    if "logged_in" not in session:
        return redirect("/login")

    df = pd.DataFrame(data_transaksi)

    total_pemasukan = 0
    total_pengeluaran = 0
    grafik_url = None

    if not df.empty:
        total_pemasukan = df[df["jenis"] == "Pemasukan"]["nominal"].sum()
        total_pengeluaran = df[df["jenis"] == "Pengeluaran"]["nominal"].sum()

        grafik_path = buat_grafik_bulanan(df)
        grafik_url = "/uploads/" + os.path.basename(grafik_path)

    return render_template("index.html",
                           data=data_transaksi,
                           pemasukan=total_pemasukan,
                           pengeluaran=total_pengeluaran,
                           grafik=grafik_url)


@app.route("/tambah", methods=["GET", "POST"])
def tambah():
    if "logged_in" not in session:
        return redirect("/login")

    if request.method == "POST":
        jenis = request.form["jenis"]
        nominal = bersihkan_nominal(request.form["nominal"])
        keterangan = request.form["keterangan"]
        penginput = request.form["penginput"]

        bukti = request.files["bukti"]
        bukti_name = None

        if bukti:
            bukti_name = datetime.now().strftime("%Y%m%d%H%M%S_") + secure_filename(bukti.filename)
            bukti.save(os.path.join(UPLOAD_FOLDER, bukti_name))

        transaksi = {
            "jenis": jenis,
            "nominal": nominal,
            "keterangan": keterangan,
            "penginput": penginput,
            "foto_bukti": bukti_name,
            "waktu": datetime.now().strftime("%d-%m-%Y %H:%M")
        }

        data_transaksi.append(transaksi)
        return redirect("/dashboard")

    return render_template("tambah.html")


@app.route("/hapus/<int:index>")
def hapus(index):
    if "logged_in" not in session:
        return redirect("/login")

    if 0 <= index < len(data_transaksi):
        data_transaksi.pop(index)

    return redirect("/dashboard")


@app.route("/export")
def export_excel():
    if "logged_in" not in session:
        return redirect("/login")

    if not data_transaksi:
        return "Tidak ada data."

    df = pd.DataFrame(data_transaksi)
    file_path = "/tmp/laporan_keuangan.xlsx"
    df.to_excel(file_path, index=False)

    return send_file(file_path, as_attachment=True)


@app.route("/export_pdf")
def export_pdf():
    if "logged_in" not in session:
        return redirect("/login")

    pdf_path = "/tmp/laporan_keuangan.pdf"
    c = canvas.Canvas(pdf_path, pagesize=A4)

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 800, "Laporan Keuangan PERMATA Pengumben")

    y = 760
    for t in data_transaksi:
        c.setFont("Helvetica", 11)
        c.drawString(50, y,
                     f"{t['waktu']} | {t['jenis']} | Rp {t['nominal']} | {t['keterangan']} | {t['penginput']}")
        y -= 20

        if y < 50:
            c.showPage()
            y = 800

    c.save()
    return send_file(pdf_path, as_attachment=True)


# ROUTE MENAYANGKAN FILE DI /tmp/uploads
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory("/tmp", filename) if filename == "grafik.png" else send_from_directory("/tmp/uploads", filename)


if __name__ == "__main__":
    app.run(debug=True)
