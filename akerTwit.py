from flask import Flask
from sqlite3 import dbapi2 as sqlite3
from contextlib import closing

# configuration
DATABASE = 'akerTwit.db'
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

if __name__ == '__main__':
    init_db()
    app.run()
