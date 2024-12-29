from flask import Flask, render_template
import MySQLdb

app = Flask(__name__)

# Veritabanı bağlantısı
db = MySQLdb.connect(host="localhost", user="root", passwd="2121Mirac.", db="bitirme", charset="utf8mb4")
cursor = db.cursor()

@app.route('/')
def home():
    # Tüm dersleri al
    cursor.execute("SELECT DISTINCT DersAdi FROM yoklama")
    dersler = [row[0] for row in cursor.fetchall()]
    return render_template('home.html', dersler=dersler)

@app.route('/ders/<ders_adi>')
def yoklama_goruntule(ders_adi):
    # Seçilen derse ait yoklama verilerini al
    query = """
        SELECT id, OgrenciBilgisi, DersAdi, Gun, GirisSaati, DerseGecGirdiMi
        FROM yoklama WHERE DersAdi = %s
    """
    cursor.execute(query, (ders_adi,))
    yoklama_verileri = cursor.fetchall()
    return render_template('yoklama.html', ders_adi=ders_adi, yoklama_verileri=yoklama_verileri)

if __name__ == '__main__':
    app.run(debug=True)
