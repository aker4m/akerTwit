from flask import Flask, request, session, url_for, redirect, \
    render_template, abort, g, flash
from sqlite3 import dbapi2 as sqlite3
from contextlib import closing
from werkzeug.security import check_password_hash, generate_password_hash
import time
from hashlib import md5
from datetime import datetime

# configuration
DATABASE = 'twit.db'
PER_PAGE= 30
DEBUG = True
SECRET_KEY = 'development key'

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

def query_db():
    cur = g.db.execute(query, args)
    rv = [dict((cur.description[idx][0], value) \
                for idx, value in enumerate(row)) \
                    for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv

def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

# create my application
app  = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('AKERTWIT_SETTING', silent=True)

@app.before_request
def before_request():
    g.db = connect_db()
    g.user = None
    if 'user_id' in session:
        g.user = query_db('select * from user where user_id = ?',\
                          [session['user_id']], one=True)

@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()

@app.route('/add_message', methods=['GET', 'POST'])
def add_message():
    if 'user_id' not in session:
        abort(401)
    if request.form['text']:
        g.db.execute('''insert into 
            message (author_id, text, pub_date)
            values (?,?,?)''', (session['user_id'],
                                request.form['text'],
                                int(time.time()))) 
        g.db.commit()
        flash('Your message was recored')
    return redirect(url_for('timeline'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user:
        return redirect(url_for('timeline'))
    error=None
    if request.method == 'POST':
        user = query_db('''select * from user where 
            username = ?''', [request.form['username']], one=True)
        if user is None:
            error='Invalid username'
        elif not check_password_hash(user['pw_hash'], \
                                     request.form['password']):
            error='Invalid password'
        else:
            flash('You were logged in')
            session['user_id'] = user['user_id']
            return redirect(url_for('timeline'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    flash('You were logged out')
    session.pop('user_id', None)
    return redirect(url_for('public_timeline'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if g.user:
        return redirect(url_for('timeline'))
    error = None
    if request.method == 'POST':
        if not request.form['username']:
            error='You have to enter a username'
        elif not request.form['email'] or \
            '@' not in request.form['email']:
            error='You have to enter a valid email adress'
        elif not request.form['password']:
            error='You have to enter a password'
        elif request.form['password'] != request.form['password2']:
            error='The two passwords do not match'
        elif get_user_id(request.form['username']) is not None:
            error='The username is already taken'
        else:
            g.db.execute('''insert into user (
                username, email, pw_hash) values (?,?,?)''',
                [request.form['username'], request.form['email'],
                generate_password_hash(request.form['password'])])
            g.db.commit()
            flash('You were successfully registered and can login now')
            return redirect(url_for('login'))
    return render_template('register.html', error=error)

def gravatar_url(email, size=80):
    return 'http://www.gravatar.com/avatar/%s?d=identicon&s=%d' % \
        (md5(email.strip().lower().encode('utf-8')).hexdigest(), size)

@app.route('/<username>/follow')
def follow_user(username):
    if not g.user:
        abort(401)
    whom_id = get_user_id(username)
    if whom_id is None:
        abort(404)
    g.db.execute('insert into follower (who_id, whom_id) \
                  values (?,?)', [session['user_id'], whom_id])
    g.db.commit()
    flash('You ar now following "%s"' % username)
    return redirect(url_for('user_timeline', username=username))

@app.route('/<username>/unfollow')
def unfollow_user(username):
    if not g.user:
        abort(401)
    whom_id = get_user_id(username)
    if whom_id is None:
        abort(404)
    g.db.execute('delete from follower where who_id=? and \
                  whom_id=?', [session['user_id'], whom_id])
    g.db.commit()
    flash('You are no longer following "%s"' % username)
    return redirect(url_for('user_timeline', username=username))

app.jinja_env.filters['gravatar'] = gravatar_url

if __name__ == '__main__':
    init_db()
    app.run()
