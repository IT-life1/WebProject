from flask import Flask, render_template, request, redirect, make_response
import psycopg2
import os

app = Flask(__name__)

def initialize_database():
    # Database connection
    db = psycopg2.connect(
        host="db",
        user="postgres",
        password="sova",
        database="first"
    )
    
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
    try:
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
        # Vulnerable to SQL Injection
        cursor = db.cursor()
        query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
        cursor.execute(query)
        result = cursor.fetchone()
        if result:
            response = make_response(redirect('/profile'))
            response.set_cookie('User', username, max_age=7200)  # Cookie expires in 2 hours
            return response
        else:
            return "Не правильное имя или пароль"
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
        # Vulnerable to SQL Injection
        cursor = db.cursor()
        query = f"INSERT INTO posts (title, main_text) VALUES ('{title}', '{main_text}')"
        cursor.execute(query)
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
    return render_template('profile.html', username=username)

@app.route('/post/<int:id>')
def show_post(id):
    cursor = db.cursor(cursor_factory=psycopg2.extras.DictCursor)
    query = f"SELECT * FROM posts WHERE id={id}"
    cursor.execute(query)
    row = cursor.fetchone()
    if row:
        title = row['title']
        main_text = row['main_text']
        return render_template('post.html', title=title, main_text=main_text)
    else:
        return "Post not found!", 404

@app.route('/')
def index():
    username = request.cookies.get('User')
    if not username:
        return render_template('index.html', posts=None, logged_in=False)
    cursor = db.cursor(cursor_factory=psycopg2.extras.DictCursor)
    query = "SELECT * FROM posts"
    cursor.execute(query)
    rows = cursor.fetchall()
    posts = [{'id': row['id'], 'title': row['title']} for row in rows]
    return render_template('index.html', posts=posts, logged_in=True)

@app.route('/registration', methods=['GET', 'POST'])
def registration():
    username = request.cookies.get('User')
    if username:
        return redirect('/login')
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['login']
        password = request.form['password']
        if not email or not username or not password:
            return "Пожалуйста введите все значения!"
        cursor = db.cursor()
        query = f"INSERT INTO users (email, username, password) VALUES ('{email}', '{username}', '{password}')"
        cursor.execute(query)
        db.commit()
        return "Пользователь успешно зарегистрирован!"
    return render_template('registration.html')

if __name__ == '__main__':
    initialize_database()
    app.run(host="0.0.0.0", port=5000, debug=True)