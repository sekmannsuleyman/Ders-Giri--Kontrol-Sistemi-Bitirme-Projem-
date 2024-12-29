from flask import Flask, render_template, request, redirect, url_for
import os
from werkzeug.utils import secure_filename
import MySQLdb

app = Flask(__name__)

# Veritabanı bağlantısı
def get_db_connection():
    return MySQLdb.connect(
        host="localhost",
        user="root",
        passwd="2121Mirac.",  # Şifrenizi buraya ekleyin
        db="bitirme",
        charset="utf8mb4"
    )

# Fotoğraf yükleme klasörü
UPLOAD_FOLDER = '/home/sekmansuleyman/Desktop/yen/photos'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Desteklenen dosya uzantıları
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Dosya uzantısını doğrulama
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Ana Sayfa: Öğrenci ve Ders Bilgileri
@app.route('/')
def index():
    db = get_db_connection()
    cursor = db.cursor(MySQLdb.cursors.DictCursor)

    # Öğrenci ve ders bilgilerini getir
    query = '''
        SELECT ogrenciekle.id, ogrenciekle.OgrenciBilgisi, dersekle.DersAdi, dersekle.GirisSaati, dersekle.CikisSaati, dersekle.Gunler
        FROM ogrenciekle
        LEFT JOIN dersekle ON ogrenciekle.DersAdi = dersekle.DersAdi
    '''
    cursor.execute(query)
    data = cursor.fetchall()

    cursor.close()
    db.close()
    return render_template('index.html', data=data)

# Öğrenci Güncelleme
@app.route('/ogrenci-guncelle/<int:id>', methods=['GET', 'POST'])
def ogrenci_guncelle(id):
    db = get_db_connection()
    cursor = db.cursor(MySQLdb.cursors.DictCursor)

    if request.method == 'POST':
        ogrenci_bilgisi = request.form['ogrenci_bilgisi']
        ders_adi = request.form['ders_adi']

        # Öğrenci bilgilerini güncelle
        query = '''
            UPDATE ogrenciekle
            SET OgrenciBilgisi = %s, DersAdi = %s
            WHERE id = %s
        '''
        cursor.execute(query, (ogrenci_bilgisi, ders_adi, id))
        db.commit()

        cursor.close()
        db.close()
        return redirect(url_for('index'))

    # Mevcut öğrenci bilgilerini al
    cursor.execute('SELECT * FROM ogrenciekle WHERE id = %s', (id,))
    ogrenci = cursor.fetchone()

    # Ders bilgilerini al
    cursor.execute('SELECT DersAdi FROM dersekle')
    dersler = cursor.fetchall()

    cursor.close()
    db.close()
    return render_template('ogrenci_guncelle.html', ogrenci=ogrenci, dersler=dersler)

# Öğrenci Silme
@app.route('/ogrenci-sil/<int:id>', methods=['POST'])
def ogrenci_sil(id):
    db = get_db_connection()
    cursor = db.cursor()

    # Öğrenciyi sil
    cursor.execute('DELETE FROM ogrenciekle WHERE id = %s', (id,))
    db.commit()

    cursor.close()
    db.close()
    return redirect(url_for('index'))

# Ders Ekleme
@app.route('/ders-ekle', methods=['GET', 'POST'])
def ders_ekle():
    if request.method == 'POST':
        ders_adi = request.form['ders_adi']
        giris_saati = request.form['giris_saati']
        cikis_saati = request.form['cikis_saati']
        gunler = request.form['gunler']

        db = get_db_connection()
        cursor = db.cursor()

        # Yeni ders ekle
        query = '''
            INSERT INTO dersekle (DersAdi, GirisSaati, CikisSaati, Gunler)
            VALUES (%s, %s, %s, %s)
        '''
        cursor.execute(query, (ders_adi, giris_saati, cikis_saati, gunler))
        db.commit()

        cursor.close()
        db.close()
        return redirect(url_for('index'))

    return render_template('ders_ekle.html')

# Öğrenci Ekleme
@app.route('/ogrenci-ekle', methods=['GET', 'POST'])
def ogrenci_ekle():
    db = get_db_connection()
    cursor = db.cursor(MySQLdb.cursors.DictCursor)

    if request.method == 'POST':
        ogrenci_bilgisi = request.form['ogrenci_bilgisi']
        ders_adi = request.form['ders_adi']

        # Yeni öğrenci ekle
        query = '''
            INSERT INTO ogrenciekle (OgrenciBilgisi, DersAdi)
            VALUES (%s, %s)
        '''
        cursor.execute(query, (ogrenci_bilgisi, ders_adi))
        db.commit()

        cursor.close()
        db.close()
        return redirect(url_for('index'))

    # Ders bilgilerini al
    cursor.execute('SELECT DersAdi FROM dersekle')
    dersler = cursor.fetchall()

    cursor.close()
    db.close()
    return render_template('ogrenci_ekle.html', dersler=dersler)
# Fotoğraf Yükleme Sayfası
@app.route('/fotograf-yukle', methods=['GET', 'POST'])
def fotograf_yukle():
    if request.method == 'POST':
        fotograf_adi = request.form['fotograf_adi']
        file = request.files['file']

        if 'file' not in request.files or file.filename == '':
            return "Fotoğraf seçilmedi, lütfen tekrar deneyin."
        
        if file and allowed_file(file.filename):
            # Güvenli dosya adını oluştur
            filename = secure_filename(f"{fotograf_adi}")
            # Dosyayı yükleme klasörüne kaydet
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('index'))
        else:
            return "Geçersiz dosya formatı, lütfen geçerli bir resim seçin."

    return render_template('fotograf_yukle.html')




if __name__ == '__main__':
    app.run(debug=True)
