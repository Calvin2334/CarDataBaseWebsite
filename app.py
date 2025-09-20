from flask import Flask, render_template, url_for, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mysqldb import MySQL

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'C@lv!n230'
app.config['MYSQL_DB'] = 'mycars'
app.secret_key = 'your_secret_key'
mysql = MySQL(app)

# Fetch cars from the database
def fetch_cars():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM carinv")
    cars = cur.fetchall()
    cur.close()
    return cars

# Sign up route - Create a new user
@app.route('/signup', methods=['POST'])
def signup():
    username = request.form['username']
    password = request.form['password']

    # Hash the password before saving
    hashed_password = generate_password_hash(password)

    try:
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (username, password) VALUES(%s, %s)", (username, hashed_password))
        mysql.connection.commit()
    except Exception as e:
        mysql.connection.rollback()
        return f"Could Not Create Account: {e}", 400
    finally:
        cur.close()
    
    return redirect(url_for('home'))


# Login route - Validate the user's credentials
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # When the form is submitted, check the credentials
        username = request.form['username']
        password = request.form['password']

        # Initialize 'user' variable
        user = None

        # Query the database to check if the user exists
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()

        # Debugging: print the user and check the password hash comparison
        if user:
            print(f"Stored Password Hash: {user[2]}")
            print(f"Entered Password: {password}")

        # Check password hash if the user exists
        if user and check_password_hash(user[2], password):  # Check password hash
            session['user_id'] = user[0]  # Store the user ID in session
            return redirect(url_for('home'))
        else:
            return "Invalid Username or Password", 401


    # If GET request (i.e., just visiting the page), show the login form
    return render_template('index.html')  # Show login form


# Logout route - Clear the session and redirect
@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Remove the user ID from session
    return redirect(url_for('home'))


# Home route - Display cars and show the "Add to Garage" button if logged in
@app.route('/', methods=['GET', 'POST'])
def home():
    cars = fetch_cars()
    show_add_button = session.get('user_id') is not None  # Show button if logged in

    user =None 
    if session.get('user_id'):
        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
            user = cur.fetchone()
        finally:
            cur.close()
    return render_template('index.html', data=cars, show_add_button=show_add_button, user=user)


# Add car to garage route - Add selected car to the user's garage
@app.route('/add_to_garage', methods=['POST'])
def add_to_garage():
    car_id = request.form['car_id']
    user_id = session.get('user_id')

    if user_id:
        try:
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO garage (user_id, car_id) VALUES (%s, %s)", (user_id, car_id))
            mysql.connection.commit()
        except Exception as e:
            mysql.connection.rollback()
            return f"Error adding car to Garage: {e}", 400
        finally:
            cur.close()
    else:
        return "User Not Found!", 403

    return redirect(url_for('home'))


@app.route('/Mygarage', methods=['GET'])
def Mygarage():
    user_id = session.get('user_id')

    if not user_id:
        return redirect(url_for('home'))

    try:
        cur = mysql.connection.cursor()

        # Get the current user
        cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()

        # Get all cars in user's garage
        cur.execute("""
            SELECT carinv.*
            FROM carinv
            INNER JOIN garage ON carinv.car_id = garage.car_id
            WHERE garage.user_id = %s
        """, (user_id,))
        user_cars = cur.fetchall()

    finally:
        cur.close()

    # Pass user and in_garage=True to template
    return render_template('index.html', data=user_cars, in_garage=True, user=user)

    
# Remove car from garage route
@app.route('/remove_from_garage', methods=['POST'])
def remove_from_garage():
    car_id = request.form['car_id']
    user_id = session.get('user_id')

    if user_id:
        try:
            cur = mysql.connection.cursor()
            cur.execute("DELETE FROM garage WHERE user_id = %s AND car_id = %s", (user_id, car_id))
            mysql.connection.commit()
        except Exception as e:
            mysql.connection.rollback()
            return f"Error removing car from Garage: {e}", 400
        finally:
            cur.close()
    else:
        return "User Not Found!", 403

    return redirect(url_for('Mygarage'))  # Redirect back to the garage




# Run the app
if __name__ == '__main__':
    app.run(debug=True)
