from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SECRET_KEY'] = 'your_secret'
db = SQLAlchemy(app)


@app.route('/')
def index():
    return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
   
   return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    
    return render_template('dashboard.html')

@app.route('/logs')
def logs():
    
    return render_template('logs.html')
@app.route('/status')
def status():
    
    return render_template('status.html')
    

@app.route('/error')
def error():
    
    return render_template('404.html')

@app.route('/about')
def about():
    
    return render_template('about.html')

@app.route('/contact')
def contact():
    
    return render_template('contact.html')

if __name__ == '__main__':
    app.run(debug=True)