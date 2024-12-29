from flask import Flask, render_template, request, redirect, url_for, flash
import MySQLdb
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# MariaDB bağlantı ayarları
db = MySQLdb.connect(
    host="localhost",
    user="root",
    passwd="2121Mirac.",  # MariaDB şifresi
    db="ders",            # Veritabanı adı
    charset="utf8"
)

# Fotoğraf yükleme ayarları
UPLOAD_FOLDER = '/home/sekmansuleyman/Desktop/yen/photos'  # Fotoğrafların kaydedileceği klasör
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'your_secret_key'  # Flash mesajları için secret key
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Klasör yoksa oluştur

@app.route('/')
def index():
    # Veritabanından tüm kayıtları çekme
    cursor = db.cursor()
    cursor.execute("SELECT * FROM kontrol")
    data = cursor.fetchall()
    return render_template('index.html', data=data)

@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        try:
            # Form verilerini al
            student_info = request.form['student_info']
            lesson_name = request.form['lesson_name']
            entry_time = request.form['entry_time']
            exit_time = request.form['exit_time']
            days = request.form['days']

            # Veritabanına ekleme işlemi
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO kontrol (OgrenciBilgi, DersAdi, GirisSaati, CikisSaati, gunler) VALUES (%s, %s, %s, %s, %s)",
                (student_info, lesson_name, entry_time, exit_time, days)
            )
            db.commit()
            print("Kayıt başarıyla eklendi!")
            return redirect(url_for('index'))
        except MySQLdb.Error as e:
            db.rollback()
            print(f"Veritabanı hatası: {e}")
            return f"Kayıt eklenirken bir hata oluştu: {e}", 500

    return render_template('add.html')

@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    cursor = db.cursor()
    if request.method == 'POST':
        try:
            # Form verilerini al
            student_info = request.form['student_info']
            lesson_name = request.form['lesson_name']
            entry_time = request.form['entry_time']
            exit_time = request.form['exit_time']
            days = request.form['days']

            # Veritabanını güncelle
            cursor.execute(
                "UPDATE kontrol SET OgrenciBilgi = %s, DersAdi = %s, GirisSaati = %s, CikisSaati = %s, gunler = %s WHERE id = %s",
                (student_info, lesson_name, entry_time, exit_time, days, id)
            )
            db.commit()
            flash("Kayıt başarıyla güncellendi!", 'success')
            return redirect(url_for('index'))
        except MySQLdb.Error as e:
            db.rollback()
            flash(f"Kayıt güncellenirken bir hata oluştu: {e}", 'error')

    else:
        # Güncelleme formu için mevcut kaydı al
        cursor.execute("SELECT * FROM kontrol WHERE id = %s", (id,))
        record = cursor.fetchone()
        return render_template('update.html', record=record)

@app.route('/delete/<int:id>', methods=['GET'])
def delete(id):
    try:
        cursor = db.cursor()
        cursor.execute("DELETE FROM kontrol WHERE id = %s", (id,))
        db.commit()
        print("Kayıt başarıyla silindi!")
    except MySQLdb.Error as e:
        db.rollback()
        print(f"Veritabanı hatası: {e}")
    return redirect(url_for('index'))

@app.route('/upload_page', methods=['GET'])
def upload_page():
    return render_template('upload_page.html')  # Fotoğraf yükleme sayfası

@app.route('/upload', methods=['POST'])
def upload():
    try:
        # Form verilerini al
        photo_name = request.form['photo_name']
        file = request.files['file']

        if file:
            # Fotoğrafı güvenli bir şekilde kaydet
            filename = secure_filename(photo_name)  # Kullanıcının girdiği adı dosya adı olarak al
            file_extension = os.path.splitext(file.filename)[1]  # Dosyanın uzantısını al (.jpg, .png, vs.)
            full_filename = f"{filename}{file_extension}"  # Adı ve uzantıyı birleştir
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], full_filename)
            
            # Fotoğrafı kaydet
            file.save(file_path)

            # Başarı mesajı
            flash("Fotoğraf başarıyla kaydedildi!", 'success')
            print(f"Fotoğraf başarıyla kaydedildi: {file_path}")
            return redirect(url_for('index'))
        else:
            flash("Fotoğraf yüklenirken bir hata oluştu.", 'error')
            return redirect(url_for('upload_page'))

    except Exception as e:
        flash(f"Fotoğraf yüklenirken bir hata oluştu: {e}", 'error')
        return redirect(url_for('upload_page'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)