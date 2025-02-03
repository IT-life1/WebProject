import os
from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@db:5432/mydatabase'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    salt = db.Column(db.String(120), nullable=False)

@app.route('/')
def index():
    return redirect('/register')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        salt = "salt"
        password_hash = generate_password_hash(password + salt)

        new_user = User(username=username, password_hash=password_hash, salt=salt)
        db.session.add(new_user)
        db.session.commit()

        return redirect('/users')
    return render_template('register.html')


@app.route('/users')
def users():
    all_users = User.query.all()
    hostname = os.popen('hostname').read()
    return render_template('users.html', users=all_users, hostname=hostname)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
