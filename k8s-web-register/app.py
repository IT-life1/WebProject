from flask import Flask, render_template, request, redirect, make_response
import psycopg2
import os

app = Flask(__name__)

# Database connection
db = psycopg2.connect(
    host="db",
    user="postgres",
    password="sova",
    database="first"
)

def initialize_database():
    # Database connection
    try:
        cursor = db.cursor()
        # SQL statements to create tables
        users_table = """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) NOT NULL UNIQUE,
            username VARCHAR(255) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL
        );
        """
        posts_table = """
        CREATE TABLE IF NOT EXISTS posts (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            main_text TEXT NOT NULL,
            user_id INT REFERENCES users(id) ON DELETE CASCADE
        );
        """
        # Execute the table creation queries
        cursor.execute(users_table)
        cursor.execute(posts_table)
        db.commit()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.cookies.get('User'):
        return redirect('/profile')
    if request.method == 'POST':
        username = request.form['login']
        password = request.form['password']
        if not username or not password:
            return "Пожалуйста введите все значения!"
        
        try:
            cursor = db.cursor()
            query = "SELECT * FROM users WHERE username=%s AND password=%s"
            cursor.execute(query, (username, password))
            result = cursor.fetchone()
            if result:
                response = make_response(redirect('/profile'))
                response.set_cookie('User', username, max_age=7200)  # Cookie expires in 2 hours
                return response
            else:
                return "Не правильное имя или пароль"
        except Exception as e:
            db.rollback()
            print(f"Error during login: {e}")
            return "Произошла ошибка при авторизации."
    return render_template('login.html')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    username = request.cookies.get('User')
    if not username:
        return redirect('/login')
    
    if request.method == 'POST':
        title = request.form['title']
        main_text = request.form['text']
        if not title or not main_text:
            return "Заполните все поля!"
        
        try:
            cursor = db.cursor()
            query = "INSERT INTO posts (title, main_text) VALUES (%s, %s)"
            cursor.execute(query, (title, main_text))
            db.commit()
            
            # Handle file upload
            file = request.files['file']
            if file:
                if file.content_type in ['image/gif', 'image/jpeg', 'image/jpg', 'image/pjpeg', 'image/x-png', 'image/png']:
                    if file.content_length < 102400:  # 100 KB limit
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                        file.save(file_path)
                        return f"Load in: {file_path}"
                    else:
                        return "Файл слишком большой!"
                else:
                    return "Недопустимый формат файла!"
        except Exception as e:
            db.rollback()
            print(f"Error during post creation: {e}")
            return "Ошибка при создании поста."
    
    return render_template('profile.html', username=username)

@app.route('/post/<int:id>')
def show_post(id):
    try:
        cursor = db.cursor(cursor_factory=psycopg2.extras.DictCursor)
        query = "SELECT * FROM posts WHERE id=%s"
        cursor.execute(query, (id,))
        row = cursor.fetchone()
        if row:
            title = row['title']
            main_text = row['main_text']
            return render_template('post.html', title=title, main_text=main_text)
        else:
            return "Post not found!", 404
    except Exception as e:
        db.rollback()
        print(f"Error fetching post: {e}")
        return "Ошибка при получении поста.", 500

@app.route('/')
def index():
    username = request.cookies.get('User')
    if not username:
        return render_template('index.html', posts=None, logged_in=False)
    
    try:
        cursor = db.cursor(cursor_factory=psycopg2.extras.DictCursor)
        query = "SELECT * FROM posts"
        cursor.execute(query)
        rows = cursor.fetchall()
        posts = [{'id': row['id'], 'title': row['title']} for row in rows]
        return render_template('index.html', posts=posts, logged_in=True)
    except Exception as e:
        db.rollback()
        print(f"Error fetching posts: {e}")
        return "Ошибка при получении постов.", 500

@app.route('/registration', methods=['GET', 'POST'])
def registration():
    username = request.cookies.get('User')
    if username:
        return redirect('/login')  # Если пользователь уже авторизован, отправляем его на страницу логина

    if request.method == 'POST':
        email = request.form['email']
        username = request.form['login']
        password = request.form['password']

        # Проверка, что все поля заполнены
        if not email or not username or not password:
            return render_template(
                'registration.html',
                error="Пожалуйста, заполните все поля!",
                email=email,
                login=username
            )

        try:
            cursor = db.cursor()
            # Проверяем, существует ли пользователь с таким email или username
            cursor.execute("SELECT * FROM users WHERE email=%s OR username=%s", (email, username))
            existing_user = cursor.fetchone()

            if existing_user:
                # Отображаем общее сообщение об ошибке без уточнения причин
                return render_template(
                    'registration.html',
                    error="Пользователь с такими данными уже зарегистрирован.",
                    email=email,
                    login=username
                )

            # Если пользователя нет, регистрируем нового
            query = "INSERT INTO users (email, username, password) VALUES (%s, %s, %s)"
            cursor.execute(query, (email, username, password))
            db.commit()

            # После успешной регистрации перенаправляем на страницу логина
            return redirect('/login')

        except Exception as e:
            # Логируем ошибку для отладки, но не показываем её пользователю
            print(f"Error during registration: {e}")
            db.rollback()
            return render_template(
                'registration.html',
                error="Произошла ошибка при регистрации. Попробуйте позже.",
                email=email,
                login=username
            )

    # При GET-запросе просто показываем форму регистрации
    return render_template('registration.html', error=None)

if __name__ == '__main__':
    initialize_database()
    app.run(host="0.0.0.0", port=5000, debug=True)