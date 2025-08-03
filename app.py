from flask import Flask, request, redirect, session, render_template_string
import sqlite3, os
from functools import wraps

app = Flask(__name__)
app.secret_key = 'secret-key'

# --- Database Setup ---
def init_db():
    if not os.path.exists('ngo.db'):
        conn = sqlite3.connect('ngo.db')
        c = conn.cursor()
        c.executescript('''
            CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT);
            CREATE TABLE volunteers (id INTEGER PRIMARY KEY, name TEXT, activity TEXT);
            CREATE TABLE donations (id INTEGER PRIMARY KEY, name TEXT, amount REAL);
        ''')
        conn.commit()
        conn.close()

init_db()

# --- HTML Template ---
template = '''
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>NGO Connect - {{ title }}</title>
  <style>
    body {
      margin: 0; font-family: 'Segoe UI', sans-serif;
      background: linear-gradient(to right, #1d2b64, #f8cdda); color: white; text-align: center;
    }
    .container {
      width: 90%%; max-width: 600px; margin: 80px auto; background: rgba(255,255,255,0.05);
      padding: 30px; border-radius: 16px; box-shadow: 0 8px 32px 0 rgba(31,38,135,0.37);
      backdrop-filter: blur(6.5px); border: 1px solid rgba(255,255,255,0.18);
    }
    input, button {
      width: 90%%; padding: 10px; margin: 10px 0; border-radius: 10px; border: none;
    }
    button {
      background: #ff6a00; color: white; font-weight: bold; cursor: pointer;
      transition: all 0.3s ease-in-out;
    }
    button:hover { transform: scale(1.05); background: #ff8c42; }
    .nav a {
      margin: 0 10px; color: white; text-decoration: none; font-weight: bold;
    }
    .nav { margin-top: 20px; }
    h1, h2 { text-shadow: 1px 1px 2px black; }
  </style>
</head>
<body>
  <div class="container">
    <h1>NGO Connect - {{ title }}</h1>
    {% if session.get('user') %}
    <div class="nav">
      <a href="/">Home</a>
      <a href="/volunteer">Volunteer</a>
      <a href="/donation">Donate</a>
      <a href="/history">History</a>
      <a href="/contact">Contact</a>
      <a href="/logout">Logout ({{ session['user'] }})</a>
    </div><hr>
    {% endif %}
    {{ content | safe }}
  </div>
</body>
</html>
'''

# --- Login Required Decorator ---
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('user'):
            return redirect('/login')
        return f(*args, **kwargs)
    return wrapper

# --- Routes ---
@app.route('/')
@login_required
def home():
    return render_template_string(template, title="Home", content="<p>Welcome to NGO Connect. Make a difference today.</p>")

@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('ngo.db')
        user = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password)).fetchone()
        conn.close()
        if user:
            session['user'] = username
            return redirect('/')
        msg = 'Invalid login!'
    html = f'''
      <h2>Login</h2>
      <form method="POST">
        <input name="username" placeholder="Username" required>
        <input name="password" type="password" placeholder="Password" required>
        <button type="submit">Login</button>
      </form>
      <p>{msg}</p>
      <p>Don't have an account? <a href="/signup">Register here</a></p>
    '''
    return render_template_string(template, title="Login", content=html)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            conn = sqlite3.connect('ngo.db')
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            conn.close()
            return redirect('/login')
        except:
            msg = "User already exists!"
    html = f'''
      <h2>Sign Up</h2>
      <form method="POST">
        <input name="username" placeholder="Username" required>
        <input name="password" type="password" placeholder="Password" required>
        <button type="submit">Register</button>
      </form>
      <p>{msg}</p>
      <p><a href="/login">Back to Login</a></p>
    '''
    return render_template_string(template, title="Signup", content=html)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/volunteer', methods=['GET', 'POST'])
@login_required
def volunteer():
    conn = sqlite3.connect('ngo.db')
    if request.method == 'POST':
        conn.execute("INSERT INTO volunteers (name, activity) VALUES (?, ?)",
                     (request.form['name'], request.form['activity']))
        conn.commit()
    rows = conn.execute("SELECT name, activity FROM volunteers").fetchall()
    conn.close()
    form = '''
      <form method="POST">
        <input name="name" placeholder="Your Name" required>
        <input name="activity" placeholder="Activity" required>
        <button type="submit">Add Volunteer</button>
      </form>
    '''
    list_html = "<h3>Volunteers</h3><ul>" + "".join(f"<li>{name} - {activity}</li>" for name, activity in rows) + "</ul>"
    return render_template_string(template, title="Volunteer", content=form + list_html)

@app.route('/donation', methods=['GET', 'POST'])
@login_required
def donation():
    if request.method == 'POST':
        conn = sqlite3.connect('ngo.db')
        conn.execute("INSERT INTO donations (name, amount) VALUES (?, ?)",
                     (request.form['name'], float(request.form['amount'])))
        conn.commit()
        conn.close()
    form = '''
      <form method="POST">
        <input name="name" placeholder="Donor Name" required>
        <input name="amount" type="number" step="0.01" placeholder="Amount (INR)" required>
        <button type="submit">Donate</button>
      </form>
    '''
    return render_template_string(template, title="Donation", content=form)

@app.route('/history')
@login_required
def history():
    conn = sqlite3.connect('ngo.db')
    rows = conn.execute("SELECT name, amount FROM donations").fetchall()
    conn.close()
    list_html = "<ul>" + "".join(f"<li>{name} - ₹{amount}</li>" for name, amount in rows) + "</ul>"
    return render_template_string(template, title="Donor History", content=list_html)

@app.route('/contact')
@login_required
def contact():
    contact_info = """
      <h2>Contact Us</h2>
      <p>Email: sameermalik1419@gmail.com<br>
      Phone: +91-9452091278</p>
    """
    return render_template_string(template, title="Contact", content=contact_info)

# --- Run Server ---
if __name__ == '__main__':
    app.run(debug=True)
