from flask import Flask, render_template, request, redirect, make_response, flash
import pymysql
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Секретный ключ для работы с flash-сообщениями

# Настройки подключения к базе данных
db_config = {
    'host': 'db',
    'user': 'root',
    'password': 'sova',
    'database': 'first',
    'cursorclass': pymysql.cursors.DictCursor
}

@app.route('/')
def index():
    # Проверка наличия куки
    if 'User' in request.cookies:
        return redirect('/dashboard')
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['login']
        password = request.form['password']

        # Проверка наличия всех полей
        if not email or not username or not password:
            flash("Пожалуйста, введите все значения!", "error")
            return redirect('/register')

        # Подключение к базе данных
        connection = pymysql.connect(**db_config)
        try:
            with connection.cursor() as cursor:
                # Проверка, существует ли пользователь с таким email или логином
                sql = "SELECT * FROM users WHERE email = %s OR username = %s"
                cursor.execute(sql, (email, username))
                user = cursor.fetchone()
                if user:
                    flash("Пользователь с таким email или логином уже существует!", "error")
                    return redirect('/register')

                # Хэширование пароля
                from werkzeug.security import generate_password_hash
                password_hash = generate_password_hash(password)

                # Вставка данных в таблицу users
                sql = "INSERT INTO users (email, username, password) VALUES (%s, %s, %s)"
                cursor.execute(sql, (email, username, password_hash))
            connection.commit()
        except Exception as e:
            flash(f"Не удалось добавить пользователя: {e}", "error")
            return redirect('/register')
        finally:
            connection.close()

        # Установка куки
        response = make_response(redirect('/dashboard'))
        response.set_cookie('User', username)
        return response

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['login']
        password = request.form['password']

        # Проверка наличия всех полей
        if not username or not password:
            flash("Пожалуйста, введите все значения!", "error")
            return redirect('/login')

        # Подключение к базе данных
        connection = pymysql.connect(**db_config)
        try:
            with connection.cursor() as cursor:
                # Поиск пользователя по логину
                sql = "SELECT * FROM users WHERE username = %s"
                cursor.execute(sql, (username,))
                user = cursor.fetchone()
                if not user:
                    flash("Пользователь с таким логином не найден!", "error")
                    return redirect('/login')

                # Проверка пароля
                if not check_password_hash(user['password'], password):
                    flash("Неверный пароль!", "error")
                    return redirect('/login')

        except Exception as e:
            flash(f"Ошибка при входе: {e}", "error")
            return redirect('/login')
        finally:
            connection.close()

        # Установка куки
        response = make_response(redirect('/dashboard'))
        response.set_cookie('User', username)
        return response

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    # Проверка наличия куки
    if 'User' not in request.cookies:
        return redirect('/login')
    return f"Добро пожаловать, {request.cookies['User']}!"

@app.route('/logout')
def logout():
    # Удаление куки
    response = make_response(redirect('/login'))
    response.delete_cookie('User')
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)