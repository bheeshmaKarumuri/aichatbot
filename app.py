from flask import Flask, redirect, render_template, request, jsonify, session
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

# Initialize SocketIO, SQLAlchemy, and Bcrypt
socketio = SocketIO(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # Using SQLite for simplicity
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# User model for database
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# Create the database tables (run once to initialize)
with app.app_context():
    db.create_all()

# Function to handle Groq client (assuming Groq API setup exists)
try:
    from groq import Groq
    client = Groq(api_key='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')  # Replace with your Groq API key
except Exception as e:
    print(f"Error initializing Groq client: {e}")
    client = None

# Function to generate a request based on user input
def generate_request(user_input):
    if not client:
        return "Error: Groq client not initialized."
    
    chat_completion = client.chat.completions.create(
        messages=[{"role": "system", "content": "Respond to the input with relevant content in any appropriate format."},
                  {"role": "user", "content": user_input}],
        model="llama3-70b-8192"
    )
    return chat_completion.choices[0].message.content

# Routes for the Flask app

# Home route
@app.route('/')
def index():
    return render_template('login.html')

# Main page route after login
@app.route('/index')
def main_page():
    if 'user_id' not in session:
        return redirect('/')
    return render_template('index.html')

# Signup route
@app.route('/signup', methods=['POST'])
def signup():
    username = request.json.get('username')
    email = request.json.get('email')
    password = request.json.get('password')

    # Check if the email already exists
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered!"}), 400

    # Hash the password
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    # Add the user to the database
    new_user = User(username=username, email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User created successfully!"}), 200

# Login route
@app.route('/login', methods=['POST'])
def login():
    email = request.json.get('email')
    password = request.json.get('password')

    user = User.query.filter_by(email=email).first()
    if user and bcrypt.check_password_hash(user.password, password):
        # Set session variables
        session['user_id'] = user.id
        session['username'] = user.username
        return jsonify({"message": "Login successful!"}), 200

    return jsonify({"error": "Invalid credentials!"}), 400

# API route for generating a response
@app.route('/get_response', methods=['POST'])
def get_response():
    user_input = request.json.get('user_input')
    if not user_input:
        return jsonify({"error": "No input provided"}), 400

    try:
        response = generate_request(user_input)
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": f"Failed to process request: {e}"}), 500

# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect('/')

if __name__ == '__main__':
    # socketio.run(app, host='0.0.0.0', debug=True)
    app.run()
