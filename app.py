from flask import Flask, render_template, request, redirect, url_for, session
from face_recognition_code import take_attendance  # Import face recognition functionality
import os
import cv2

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Admin credentials
USERNAME = 'admin'
PASSWORD = 'admin'

# Ensure uploads folder exists
if not os.path.exists("uploads"):
    os.makedirs("uploads")

# Home route
@app.route('/')
def home():
    return redirect(url_for('login'))

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == USERNAME and password == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

# Dashboard route
@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('dashboard.html')  # Dashboard with options

# Capture image route
import os
import cv2

@app.route('/capture', methods=['GET', 'POST'])
def capture():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']  # Get the name from the form

        # Define the uploads folder path relative to the script's location
        base_dir = os.path.dirname(os.path.abspath(__file__))  # Absolute path to the script
        uploads_dir = os.path.join(base_dir, "uploads")

        # Create the uploads folder if it doesn't exist
        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir)

        # Initialize the camera
        cam = cv2.VideoCapture(0)
        if not cam.isOpened():
            print("Error: Camera could not be opened.")
            return render_template('capture.html', error="Camera not accessible")

        while True:
            ret, frame = cam.read()
            if not ret:
                print("Failed to capture image.")
                break
            cv2.imshow("Capture Image", frame)
            if cv2.waitKey(1) & 0xFF == ord('s'):  # Save image when 's' is pressed
                img_path = os.path.join(uploads_dir, f"{name}.png")
                cv2.imwrite(img_path, frame)
                print(f"Image saved as {img_path}")
                break

        cam.release()
        cv2.destroyAllWindows()
        return redirect(url_for('dashboard'))

    return render_template('capture.html')  # Render the capture form page


# Attendance route
@app.route('/attendance', methods=['GET', 'POST'])
def attendance():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        subject_name = request.form.get('subject')
        if not subject_name:
            return render_template('attendance.html', error="Please provide a subject name.")
        
        try:
            take_attendance(subject_name)
        except Exception as e:
            return render_template('attendance.html', error=f"Error during attendance: {str(e)}")

        return redirect(url_for('dashboard'))

    # Render the attendance form for GET requests
    return render_template('attendance.html')


# Logout route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
