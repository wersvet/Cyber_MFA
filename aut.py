import sqlite3
import random
import smtplib
import pyotp
import qrcode
import requests
from flask import Flask, render_template, request, redirect, session, url_for
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Создание базы данных
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    login TEXT UNIQUE, 
                    email TEXT UNIQUE, 
                    password TEXT, 
                    phone TEXT UNIQUE,
                    totp_secret TEXT,
                    confirmed INTEGER DEFAULT 0)''')
conn.commit()

# Функция для проверки пароля
def is_valid_password(password):
    import re
    return (len(password) >= 8 and 
            any(char.isupper() for char in password) and 
            any(char.isdigit() for char in password) and 
            any(char in "@#$%^&+=" for char in password))

# Функция для проверки почты
def is_valid_email(email):
    return email.endswith("@gmail.com")

# Функция для проверки номера телефона
def is_valid_phone(phone):
    import re
    return bool(re.fullmatch(r"(\+7|8)7\d{9}", phone))

# Функция для отправки кода на Email
def send_email(email, code):
    sender_email = "alimzhanbaizhanov22@gmail.com"  
    sender_password = "fxqk bxhu xllk sulj"  # Убери пробелы в пароле приложения!
    subject = "Код подтверждения"
    message = f"Ваш код подтверждения: {code}"

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = email
    msg["Subject"] = subject
    msg.attach(MIMEText(message, "plain", "utf-8"))

    try:
        print(f"📨 Отправляем письмо на {email} с кодом: {code}")  # Добавил print()
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, email, msg.as_string())
        server.quit()
        print("✅ Email отправлен успешно!")
    except Exception as e:
        print(f"❌ Ошибка при отправке Email: {e}")  # Логируем ошибку



# Главная страница
@app.route("/")
def home():
    if "user" in session:
        return render_template("home.html", user=session["user"])
    return render_template("home.html")

# Страница входа с MFA
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login = request.form.get("login")
        password = request.form.get("password")

        cursor.execute("SELECT * FROM users WHERE login=? AND password=?", (login, password))
        user = cursor.fetchone()

        if user:
            session["user"] = login
            session["totp_secret"] = user[5]
            return redirect(url_for("mfa_select"))
        else:
            return "Ошибка: Неверный логин или пароль"

    return render_template("login.html")

# Выбор метода MFA
@app.route("/mfa_select", methods=["GET", "POST"])
def mfa_select():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        method = request.form.get("mfa_method")
        session["mfa_method"] = method
        
        if method == "sms":
            session["mfa_code"] = str(random.randint(100000, 999999))
            print(f"[DEBUG] Код по SMS: {session['mfa_code']}")
            return redirect(url_for("mfa_verify"))
        elif method == "totp":
            return redirect(url_for("mfa_totp_setup"))
    
    return render_template("mfa_select.html")

# Настройка Google Authenticator
@app.route("/mfa_totp_setup")
def mfa_totp_setup():
    if "user" not in session:
        return redirect(url_for("login"))

    # Получаем TOTP-ключ пользователя из БД
    cursor.execute("SELECT totp_secret FROM users WHERE login=?", (session["user"],))
    totp_secret = cursor.fetchone()[0]

    if not totp_secret:
        return "Ошибка: У пользователя нет TOTP-ключа!"

    # Создаём Google Authenticator TOTP
    totp = pyotp.TOTP(totp_secret)
    uri = totp.provisioning_uri(name=session["user"], issuer_name="FlaskApp")

    # Генерируем QR-код
    import qrcode
    img = qrcode.make(uri)
    img.save("static/qr.png")

    return render_template("mfa_totp.html", qr_code="/static/qr.png")


# Подтверждение MFA
@app.route("/mfa_verify", methods=["GET", "POST"])
def mfa_verify():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        code = request.form.get("code")
        method = session.get("mfa_method")

        if method == "sms" and code == session.get("mfa_code"):
            return redirect(url_for("dashboard"))
        elif method == "totp":
            totp = pyotp.TOTP(session["totp_secret"])
            if totp.verify(code):
                return redirect(url_for("dashboard"))
    
    return render_template("mfa_verify.html")

# Выход из аккаунта
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        login = request.form["login"]
        email = request.form["email"]
        password = request.form["password"]
        phone = request.form["phone"]

        # Проверка на уникальность логина, почты и телефона
        cursor.execute("SELECT * FROM users WHERE login=? OR email=? OR phone=?", (login, email, phone))
        if cursor.fetchone():
            return "Ошибка: Логин, почта или номер телефона уже зарегистрированы!"

        # Генерируем уникальный TOTP-секретный ключ
        totp_secret = pyotp.random_base32()

        # Генерируем код подтверждения Email
        code = random.randint(100000, 999999)
        session["confirmation_code"] = code
        session["user_data"] = (login, email, password, phone, totp_secret)

        # Отправляем код на Email
        send_email(email, code)

        return redirect(url_for("confirm"))

    return render_template("register.html")

# Страница после входа (доступна только авторизованным пользователям)
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    return render_template("dashboard.html")


@app.route("/confirm", methods=["GET", "POST"])
def confirm():
    if request.method == "POST":
        code = request.form["code"]
        if "confirmation_code" in session and int(code) == session["confirmation_code"]:
            # Добавляем пользователя в БД
            login, email, password, phone, totp_secret = session["user_data"]
            cursor.execute("INSERT INTO users (login, email, password, phone, totp_secret, confirmed) VALUES (?, ?, ?, ?, ?, ?)",
                           (login, email, password, phone, totp_secret, 1))
            conn.commit()

            session.pop("confirmation_code", None)
            session.pop("user_data", None)

            return redirect(url_for("home"))
        else:
            return "Ошибка: Неверный код подтверждения"

    return render_template("confirm.html")




if __name__ == "__main__":
    app.run(debug=True)
