from flask import Flask, request, jsonify, send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, text
import os
from flask_mail import Mail, Message
import hashlib
import secrets
import string
from datetime import datetime, timedelta
from io import BytesIO
import dropbox
from reportlab.pdfgen import canvas
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

sender_email = 'samrig25@gmail.com'
sender_password = ''
client_id=''
client_secret=''
refresh_token=''
DROPBOX_ACCESS_TOKEN=''



app = Flask(__name__)
CORS(app)
# CORS(app, resources={r"/api/*": {"origins": "http://localhost:4200"}})


app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:0000@localhost/user'
app.config['MAIL_SERVER'] = 'smtp.gmail.com' 
app.config['MAIL_PORT'] = 587  
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'samrig25@gmail.com'  
app.config['MAIL_PASSWORD'] = 'irnc kkpy gnfs mwga'
db = SQLAlchemy(app)
mail = Mail(app)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    otp = db.Column(db.String(6))
    otp_expiry = db.Column(db.DateTime)


class User(db.Model):
    id = db.Column(db.String(15), primary_key=True, nullable=False )
    fullname = db.Column(db.String(100), nullable=False)
    fathername = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.String(20), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    age_group = db.Column(db.String(10), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    examCenter = db.Column(db.String(100), nullable=False)
    examCenterAddress = db.Column(db.String(100), nullable=False)
def create_tables():
    with app.app_context():
        db.create_all()

def register_user(data):
    data = request.get_json()

    existing_user = User.query.filter_by(email=data['email']).first()

    if existing_user:
        return jsonify({'error': 'User with this email already exists'})

    # print("here")
    last_user = User.query.order_by(User.id.desc()).first()

    # Extract the last 3 digits from the id and increment it
    if last_user:
        last_three_digits = int(last_user.id[-3:])
        new_last_three_digits = f"{last_three_digits + 1:03d}"
    else:
        new_last_three_digits = "001"  # Initial value if no users exist

    # Construct the new id for the user
    new_user_id = data['age_group'][:2] + data['examCenter'][:2].lower() + new_last_three_digits

    new_user = User(
        id = new_user_id,
        fullname=data['fullname'],
        fathername=data['fathername'],
        dob=data['dob'],
        age=data['age'],
        age_group=data['age_group'],
        email=data['email'],
        # examCenter=data['examCenter']
        examCenter=data['examCenter'],
        examCenterAddress=data['examCenterAddress']
        
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'})




def send_confirmation_email(email, fullname):
    msg = Message('Subscription Confirmation',
                  sender='samrig25@gmail.com',
                  recipients=[email])
    msg.body = f'Hello {fullname},\n\nThank you for subscribing!'
    
    mail.send(msg)


# @app.route('/')
# def hello():
#     return 'hello there'

@app.route('/api/generate_pdf', methods=['OPTIONS'])
def handle_options():
    return '', 200, {
        'Access-Control-Allow-Origin': 'http://localhost:4200',
        'Access-Control-Allow-Methods': 'POST',
        'Access-Control-Allow-Headers': 'Content-Type'
    }

# @app.route('/')
# def hello():
#     return 'hello there'


@app.route('/generate_pdf', methods=['POST'])
def generate_certificate_route():
    data = request.get_json()
    register_user(data)
    fullname = data.get('fullname')
    fathername = data.get('fathername')
    dob = data.get('date')
    age = data.get('age')
    age_group = data.get('age_group')
    email = data.get('email')
    # logo_path = data.get('logoPath')
    filename = 'certificate.pdf'  
    data = request.get_json()
    user_data = {
    'fullname' : data.get('fullname'),
    'fathername' : data.get('fathername'),
    'dob': data.get('date'),
    'age': data.get('age'),
    'age_group': data.get('age_group'),
    'email': data.get('email'),
    'examCenter' : data.get('examCenter'),
    'examCenterAddress' : data.get('examCenterAddress')
    }
    # logo_path = data.get('logoPath')
    filename = email

    
    send_confirmation_email(email, fullname)

    pdf_data=generate_hall_ticket("AG/EC.123", fullname, age, age_group, fathername,"123456789012", "9876543210", "ExamCentreA", "Country", "hall_ticket.pdf", "10-Mar-2024")
    
    save_to_dropbox(pdf_data, filename)

    return jsonify({'success': True, 'filename': filename})



def save_to_dropbox(pdf_data, filename):
    try:
        dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
        with dropbox.Dropbox(DROPBOX_ACCESS_TOKEN) as dbx:
            dbx.files_upload(pdf_data, f'/generated_pdfs/{filename}'+'.pdf')
    except:
        DROPBOX_ACCESS_TOKEN=refresh_access_token(refresh_token, client_id, client_secret)
        dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
        with dropbox.Dropbox(DROPBOX_ACCESS_TOKEN) as dbx:
            dbx.files_upload(pdf_data, f'/generated_pdfs/{filename}'+'.pdf')
        print("Access token refreshed")

    # Upload the PDF file to Dropbox
    

def refresh_access_token(refresh_token, client_id, client_secret):
    # Endpoint for refreshing access token
    endpoint = 'https://api.dropbox.com/oauth2/token'

    # Parameters for refreshing token
    data = {
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token',
        'client_id': client_id,
        'client_secret': client_secret
    }

    try:
        # Send POST request to refresh access token
        response = requests.post(endpoint, data=data)
        response_data = response.json()

        # Extract new access token from response
        new_access_token = response_data.get('access_token')

        # Return the new access token
        return new_access_token
    except Exception as e:
        # Handle any errors that occur during token refresh
        print("Error refreshing access token:", e)
        return None

def generate_hall_ticket(roll_no, name, age, age_group, father_name, aadhar_no, mobile_no,  exam_centre, exam_centre_address, filename, exam_date):
    buffer = BytesIO()  # Create a BytesIO object to store PDF data

    # Create the PDF content
    c = canvas.Canvas(buffer, pagesize=(505, 405))
    
    c.setStrokeColorRGB(1, 0.5, 0)
    # Draw border for entire document
    c.rect(5, 5, 495, 395)

    # Draw border for main content area
    c.rect(20, 20, 460, 360)

    c.setStrokeColorRGB(1, 0.5, 0)

    # Roll No/Ref No
    c.drawString(30, 350, f"Roll No/Ref No.: {roll_no}")

    # Name
    c.drawString(30, 300, f"Name: {name}")

    # Age
    c.drawString(30, 275, f"Age: {age}")

    # Age Group
    c.drawString(30, 255, f"Age Group: {age_group}")

    # Father's Name
    c.drawString(30, 235, f"Father's Name: {father_name}")

    # Aadhar Card Number
    c.drawString(30, 215, f"Aadhar Card Number: {aadhar_no}")

    # Mobile Number
    c.drawString(30, 195, f"Mobile Number: {mobile_no}")

    # Exam Date
    c.drawString(30, 175, f"Exam Date: {exam_date}")

    # Exam Centre
    c.drawString(30, 155, f"Exam Centre: {examCenter}")

    # Exam Centre Address
    c.drawString(30, 135, f"Exam Centre Address: {examCenterAddress}")

    # Signature of Participant
    c.drawString(180, 100, "Signature of Participant:")
    c.line(320, 100, 460, 100)

    # Signature of Bible Quiz Convener
    c.drawString(180, 60, "Signature of Bible Quiz Convener:")
    c.line(365, 60, 460, 60)

    # Draw the logo in the top right corner
    c.drawImage('./imyf_landing_page/src/assets/imgs/IMYF_logo.jpg', 400, 315, width=60, height=60)
    c.save()

    pdf_data = buffer.getvalue() 
    buffer.close()  

    return pdf_data

# Example usage:
# generate_hall_ticket("AG/EC.123", "John Doe", "25", "AG", "John Doe Sr.", "1234 5678 9012", "9876543210", "March 15, 2024", "Exam Centre A", "123 Main St, City, Country", "hall_ticket_shorter.pdf")

# def generate_refNo(age_group, examCenter, mobile_no):
    





@app.route('/get_pdf', methods=['GET'])
def get_pdf():
    pdf_filename = request.args.get('email') 

    pdf_data = download_from_dropbox(pdf_filename)

    if pdf_data:
        return send_file(
            BytesIO(pdf_data),
            mimetype='application/pdf',
            as_attachment=True,
			download_name=f'{pdf_filename}.pdf'
        )
    else:
        return jsonify({'error': 'PDF not found'})

def download_from_dropbox(filename):
    try:
        dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
    except:
        DROPBOX_ACCESS_TOKEN=refresh_access_token(refresh_token, client_id, client_secret)
        dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
        print("Access token refreshed")

    try:
        metadata, res = dbx.files_download('/generated_pdfs/' + filename+'.pdf')
        print("File downloaded successfully")
        return res.content
    except dropbox.exceptions.HttpError as err:
        if err.status_code == 404:
            return None  # PDF file not found
        else:
            raise







def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_otp():
    return ''.join(secrets.choice(string.digits) for _ in range(6))

def send_otp_email(username, otp):
    msg = Message('Password Reset OTP', sender='samrig25@gmail.com', recipients=[username])
    msg.body = f'Your OTP for password reset is: {otp}'
    mail.send(msg)


@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    
    admin = Admin.query.filter_by(username=username).first()
    if not admin or admin.password != hash_password(password):
        return jsonify({'success': False, 'message' : 'Invalid username or password'}), 401
    
    return jsonify({'success': True, 'message': 'Login successful', 'data': {'username': admin.username}})


@app.route('/forgot_password', methods=['POST'])
def forgot_password():
    username = request.json.get('username')
    
    admin = Admin.query.filter_by(username=username).first()
    if not admin:
        print(username)
        return jsonify({'success': False, 'message': 'Username is not found habibi', 'username' : username }), 404
    
    otp = generate_otp()
    admin.otp = otp
    admin.otp_expiry = datetime.now() + timedelta(minutes=10)  
    db.session.commit()
    send_otp_email(admin.username, otp)
    
    return jsonify({'success': True, 'message': 'OTP sent successfully'}), 200

@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    username = request.json.get('username')
    otp = request.json.get('otp')
    
    admin = Admin.query.filter_by(username=username).first()
    if not admin or admin.otp != otp or admin.otp_expiry < datetime.now():
        return jsonify({'success': False, 'message': 'Invalid OTP'}), 400
    
    return jsonify({'success': True, 'message': 'Valid OTP'}), 200

@app.route('/reset_password', methods=['POST'])
def reset_password():
    username = request.json.get('username')
    new_password = request.json.get('new_password')
    
    
    admin = Admin.query.filter_by(username=username).first()
    if not admin:
        return jsonify({'success': False, 'message': 'Username not found'}), 404
    
    admin.password = hash_password(new_password)
    admin.otp = None  
    admin.otp_expiry = None
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Password reset successful'}), 200




@app.route('/send_email', methods=['GET'])
def send_email():
    email = request.args.get('email')
    pdf_filename = email
    pdf_data = download_from_dropbox(pdf_filename)
    if pdf_data:
        msg = Message('Subject',
                      sender='samrig25@gmail.com',
                      recipients=[email])
        msg.body = 'Some message content'
        msg.attach(pdf_filename, 'application/pdf', pdf_data)
        mail.send(msg)
        return 'Email sent successfully'
    else:
        return f'PDF file "{pdf_filename}" not found on Dropbox'





if __name__ == '__main__':
    create_tables()
    app.run(debug=True)
