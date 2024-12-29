import cv2
import dlib
import face_recognition
import os
import time
import threading
import MySQLdb
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import RPi.GPIO as GPIO
from datetime import datetime, timedelta

# GPIO Ayarları
RELAY_PIN = 23  # Röle pin numarası
GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN, GPIO.OUT)
GPIO.output(RELAY_PIN, GPIO.HIGH)  # Röle başlangıç durumu kapalı

# Veritabanı bağlantısı
db = MySQLdb.connect(host="localhost", user="root", passwd="2121Mirac.", db="bitirme", charset="utf8mb4")
cursor = db.cursor()

# Türkçe karakter düzeltme fonksiyonu
def turkce_karakter_duzelt(metin):
    return (
        metin.replace("ı", "i")
        .replace("İ", "I")
        .replace("ş", "s")
        .replace("Ş", "S")
        .replace("ç", "c")
        .replace("Ç", "C")
        .replace("ğ", "g")
        .replace("Ğ", "G")
        .replace("ö", "o")
        .replace("Ö", "O")
        .replace("ü", "u")
        .replace("Ü", "U")
    )

# Yüz tanıma için bilinen yüzlerin yüklendiği klasör
image_folder = "/home/sekmansuleyman/Desktop/yen/photos"

# Bilinen yüz verileri ve isimleri
known_face_encodings = []
known_face_names = []

# Bilinen yüzleri yükle
for image_name in os.listdir(image_folder):
    image_path = os.path.join(image_folder, image_name)
    image = face_recognition.load_image_file(image_path)
    encodings = face_recognition.face_encodings(image)

    if encodings:
        known_face_encodings.append(encodings[0])
        known_face_names.append(image_name.split('.')[0])
    else:
        print(f"{image_name} fotoğrafında yüz algılanamadı. Lütfen kontrol edin.")

print(f"{len(known_face_encodings)} yüz başarıyla yüklendi.")

# Kamera başlat
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Kamera açılamadı! Lütfen kamerayı kontrol edin.")
    exit()

print("Yüz tanıma sistemi çalışıyor...")

# Tanıma parametreleri
recognition_delay = 1  # Tanıma sonrası bekleme süresi (saniye)
relay_delay = 1  # Rölenin tekrar çalışması için bekleme süresi (saniye)
threshold = 0.5  # Yüz tanıma eşiği
last_recognition_time = 0
last_relay_time = 0

# Röleyi kontrol etme fonksiyonu
def control_relay():
    global last_relay_time
    GPIO.output(RELAY_PIN, GPIO.LOW)  # Röleyi aç
    time.sleep(5)  # Röle açık kalma süresi
    GPIO.output(RELAY_PIN, GPIO.HIGH)  # Röleyi kapat
    last_relay_time = time.time()

# Görüntüye mesaj yazdırma fonksiyonu
def draw_text_with_background(frame, text_lines, position=(20, 20), font_size=20, font_color=(255, 255, 255), background_color=(0, 0, 0)):
    pil_img = Image.fromarray(frame)
    draw = ImageDraw.Draw(pil_img)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    font = ImageFont.truetype(font_path, font_size)

    padding = 10
    max_width = 0
    total_height = 0

    for line in text_lines:
        text_width, text_height = draw.textsize(line, font=font)
        max_width = max(max_width, text_width)
        total_height += text_height + padding

    draw.rectangle([
        position,
        (position[0] + max_width + padding, position[1] + total_height)
    ], fill=background_color)

    y_offset = position[1]
    for line in text_lines:
        draw.text((position[0] + padding // 2, y_offset + padding // 2), line, font=font, fill=font_color)
        y_offset += text_height + padding

    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Kamera görüntüsü alınamıyor.")
        break

    current_time = time.time()
    if current_time - last_recognition_time < recognition_delay:
        cv2.imshow("Frame", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        continue

    # Yüzleri algıla ve tanı
    face_locations = face_recognition.face_locations(frame)
    face_encodings = face_recognition.face_encodings(frame, face_locations)

    for face_encoding, (top, right, bottom, left) in zip(face_encodings, face_locations):
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=threshold)
        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)

        best_match_index = None
        if len(face_distances) > 0 and min(face_distances) < threshold:
            best_match_index = np.argmin(face_distances)

        if best_match_index is not None and matches[best_match_index]:
            name = known_face_names[best_match_index]

            # Ders ve saat kontrolü
            current_time_str = time.strftime("%H:%M:%S")
            current_day = time.strftime("%A")
            query = f"""
                SELECT DersAdi, GirisSaati, CikisSaati 
                FROM dersekle 
                WHERE gunler = '{turkce_karakter_duzelt(current_day)}' 
                AND GirisSaati <= '{current_time_str}' 
                AND CikisSaati >= '{current_time_str}'
            """
            cursor.execute(query)
            result = cursor.fetchone()

            if result:
                ders_adi, giris_saati, cikis_saati = result

                # Veritabanındaki saat formatını timedelta'ya dönüştür
                if isinstance(giris_saati, timedelta):
                    giris_saati = (datetime.min + giris_saati).time()
                if isinstance(cikis_saati, timedelta):
                    cikis_saati = (datetime.min + cikis_saati).time()

                current_time_obj = datetime.strptime(current_time_str, "%H:%M:%S").time()
                gec_girdi_mi = "Evet" if datetime.combine(datetime.min, current_time_obj) > datetime.combine(datetime.min, giris_saati) + timedelta(minutes=15) else "Hayır"

                cursor.execute(f"SELECT OgrenciBilgisi FROM ogrenciekle WHERE OgrenciBilgisi = '{name}' AND DersAdi = '{ders_adi}'")
                ogrenci_dersi = cursor.fetchone()

                if ogrenci_dersi:
                    # Yoklama kontrolü
                    cursor.execute(f"""
                        SELECT * FROM yoklama 
                        WHERE OgrenciBilgisi = '{name}' 
                        AND DersAdi = '{ders_adi}' 
                        AND Gun = '{turkce_karakter_duzelt(current_day)}'
                    """)
                    yoklama_kaydi = cursor.fetchone()

                    if not yoklama_kaydi:
                        display_message = [f"{name} için kapı açılıyor.", f"Ders: {ders_adi}"]
                        if current_time - last_relay_time > relay_delay:
                            threading.Thread(target=control_relay).start()

                        # Yoklama tablosuna ekleme
                        yoklama_query = f"""
                            INSERT INTO yoklama (OgrenciBilgisi, DersAdi, Gun, GirisSaati, DerseGecGirdiMi)
                            VALUES ('{name}', '{ders_adi}', '{turkce_karakter_duzelt(current_day)}', '{current_time_str}', '{gec_girdi_mi}')
                        """
                        cursor.execute(yoklama_query)
                        db.commit()
                    else:
                        display_message = [f"{name} için yoklama zaten alındı.", f"Ders: {ders_adi}"]
                else:
                    display_message = [f"{name} bu dersi almadığından", f"kapı açılmıyor. Şu anki ders: {ders_adi}"]
            else:
                display_message = [f"{name} için şu anda ders yok.", "Kapı açılıyor."]
                if current_time - last_relay_time > relay_delay:
                    threading.Thread(target=control_relay).start()
        else:
            display_message = ["Tanımlanamayan yüz,", "kapı açılmıyor."]

        frame = draw_text_with_background(frame, display_message)

    # Görüntüyü göster
    cv2.imshow("Frame", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
db.close()
GPIO.cleanup()