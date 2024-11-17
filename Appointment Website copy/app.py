
from flask import Flask, render_template, request, redirect, session, url_for
import re
import sqlite3

# Example: Insert a student into the database
def add_student(student_name, email):
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Students (Student_Name, Email) VALUES (?, ?)", (student_name, email))
    conn.commit()
    conn.close()


app = Flask(__name__)
app.secret_key = "supersecretkey"  # Required for session management

# Validation functions
def is_valid_name(name):
    return re.fullmatch(r'[a-zA-Z]+', name) is not None

def is_valid_email(email):
    return re.fullmatch(r'[0-9]{10}@student\.csn\.edu', email) is not None

def generate_username(first_name, email):
    nshe_last_four = email[6:10]  # Extract the last four digits of the NSHE number
    return first_name.lower() + nshe_last_four

def is_valid_username(username, first_name, email):
    return username == generate_username(first_name, email)

def is_valid_password(password, email):
    return password == email[:10]

# Routes
@app.route('/')
def home():
    return render_template('homepage.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # Clear previous messages
    session.pop('messages', None)
    session.pop('success_message', None)

    if request.method == 'POST':
        messages = []

        # Retrieve form data
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']

        # Validation checks
        if not is_valid_name(first_name):
            messages.append("First name must only contain letters A-Z")
        if not is_valid_name(last_name):
            messages.append("Last name must only contain letters A-Z")
        if not is_valid_email(email):
            messages.append("Email must be NSHE#@student.csn.edu")
        elif not is_valid_username(username, first_name, email):
            messages.append("Username must be first name and last four of NSHE number")
        if not is_valid_password(password, email):
            messages.append("Password must only contain numbers 0-9")

        # If validation fails, store messages in session
        if messages:
            session['messages'] = messages
        else:
            try:
                # Connect to the database
                conn = sqlite3.connect('app.db')
                cursor = conn.cursor()

                # Insert into Students table
                student_name = f"{first_name} {last_name}"
                cursor.execute("INSERT INTO Students (Student_Name, Email) VALUES (?, ?)", (student_name, email))
                student_id = cursor.lastrowid  # Get the last inserted Student_ID

                # Insert into Authentication table
                password_hash = password  # Use hashed password in production
                cursor.execute(
                    "INSERT INTO Authentication (Student_ID, Username, Password_Hash) VALUES (?, ?, ?)",
                    (student_id, username, password_hash),
                )
                conn.commit()
                conn.close()

                # Set a success message
                session['success_message'] = "Sign up successful! Welcome to CSN."
                # Redirect to the homepage
                return redirect(url_for('home'))

            except sqlite3.Error as e:
                messages.append(f"Database error: {e}")
            except Exception as e:
                messages.append(f"Unexpected error: {e}")

    # Render the signup page with messages if any
    return render_template('signup.html')




@app.route('/login', methods=['GET', 'POST'])
def login():
    session.pop('messages', None)

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            # Connect to the database
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            # Validate username and password
            cursor.execute(
                "SELECT * FROM Authentication WHERE Username = ? AND Password_Hash = ?",
                (username, password),
            )
            user = cursor.fetchone()
            conn.close()

            if user:
                # Login successful, redirect to appointment page
                return redirect(url_for('appointment'))
            else:
                # Show error message
                session['messages'] = ["Invalid username or password."]

        except sqlite3.Error as e:
            session['messages'] = [f"Database error: {e}"]

    return render_template('login.html')


@app.route('/appointment')
def appointment():
    return render_template('appointment.html')

@app.route('/reservation')
def reservation():
    return render_template('reservation.html')

# Run the app
if __name__ == "__main__":
    app.run(debug=True)
