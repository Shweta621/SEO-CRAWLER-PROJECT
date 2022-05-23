
import flask
from models import db, creatuser, User
from flask import Flask, jsonify, render_template, request, flash, redirect, url_for,session
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.sqlite'
app.secret_key = 'thisisaverysecretkey'
import pandas as pd
import advertools as adv

with app.app_context():
    db.init_app(app)
    db.create_all()

def collect_data(website):
    path = "content/"+website.replace('https://','').replace('http://','').replace('/','_')+'.jl'
    adv.crawl(website, path, follow_links=True)
    return path

@app.route('/')
def index():

    return render_template('index.html')

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email  = request.form.get('email')
        password = request.form.get('password')
        print(email, password)
        if email and password:
            user = User.query.filter_by(email=email).first()
            if user is None or not user.check_password(password):
                flash('Invalid email or password','danger')
                return redirect(url_for('login'))
            else:
                flash('Login successfully','success')
                session['user'] = user.name
                session['id'] = user.id
                session['email'] = user.email
                session['is_auth'] = True
                return redirect('/dashboard')
    return render_template('login.html')


@app.route('/register',methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email  = request.form.get('email')
        password = request.form.get('password')
        cpass  = request.form.get('cpass')
        if not name or not email or not password or not cpass:
            flash('Please enter all the details', 'danger')
            return redirect('/register')
        elif User.query.filter_by(email=email).first():
            flash('email already exist', 'danger')
            return redirect('/register')
        else:
            user = creatuser(name=name,email=email,password=password,cpass=cpass)
            flash('Registered successfully', 'success')
            return redirect('/login')
    return render_template('register.html')   
    

@app.route('/dashboard',methods=['GET','POST'])
def dashboard():
    return render_template('dashboard.html')

@app.route('/collect_data',methods=['POST'])
def collector():
    if request.method =='POST':
        print(request.form)
        website = request.form.get('website')
        if website:
            session['path'] = collect_data(website)
            session['website'] = website
            df = pd.read_json(session.get('path'),lines=True)
            return jsonify({'success':'success','df':df.to_html()})
        else:
            flash('provide a website address to get results','danger')
            return jsonify({'error':'no website'})
    flash('Use the form to collect website data','warning')
    return redirect('/dashboard')

@app.route('/results')
def results():
    if 'path' in session:
        df = pd.read_json(session.get('path'),lines=True)
        return render_template('results.html',df=df.to_html(),rows= df.shape[0],cols=df.columns.tolist())
    else:
        redirect('/dashboard')

@app.route('/logout')
def logout():
    if 'is_auth' in session:
        session.pop('is_auth')
        flash('You are logged out','success')
    return redirect('/')


if __name__ == '__main__':
  app.run(host='127.0.0.1', port=8000, debug=True)