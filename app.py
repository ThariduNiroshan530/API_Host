from flask import Flask, jsonify, request, render_template
import pyodbc
import bcrypt
from flask_mysqldb import MySQL
from flask_mail import Mail, Message

app = Flask(__name__)

mysql = MySQL(app)

# Database connection function
def get_db_connection_socondary():
    connection_string = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=tharidu.database.windows.net;DATABASE=Tharidu;UID=tharidu;PWD=PaskaL530@PMCmis"
    try:
        conn = pyodbc.connect(connection_string)
        return conn
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None



# Database connection function for the second database
def get_db_connection_main():
    connection_string = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=tharidu.database.windows.net;DATABASE=Tharidu01;UID=tharidu;PWD=PaskaL530@PMCmis"
    try:
        conn = pyodbc.connect(connection_string)
        return conn
    except Exception as e:
        print(f"Error connecting to the secondary database: {e}")
        return None


mail = Mail(app)

# Initialize Flask-Mail configuration
app.config['MAIL_SERVER'] = "smtp.googlemail.com"
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = "rootxtravel@gmail.com"  # Your email address
app.config['MAIL_PASSWORD'] = "feng tvtc ixkc rpwo"  # Your email password




@app.route('/passenger_signup', methods=['POST'])
def passenger_signup():  # Renamed from signup to passenger_signup
    data = request.get_json()
    email = data.get('email')
    name = data.get('name')  # 'username' changed to 'name'
    phone = data.get('phone')
    password = data.get('password')

    if not email or not name or not phone or not password:
        return jsonify({'error': 'Please provide all fields!'}), 400

    # Get database connection
    conn = get_db_connection_socondary()  # You might want to use get_db_connection_main() if that's the intended DB
    if not conn:
        return jsonify({'error': 'Error connecting to database'}), 500
    
    cur = conn.cursor()
    cur.execute("SELECT * FROM passenger_information_table WHERE email=%s", (email,))
    existing_user = cur.fetchone()

    if existing_user:
        cur.close()
        conn.close()
        return jsonify({'error': 'User already exists!'}), 400

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    cur.execute("INSERT INTO passenger_information_table (Email, Name, Phone_Number, Password) VALUES (%s, %s, %s, %s)",
                (email, name, phone, hashed_password))
    conn.commit()
    cur.close()
    conn.close()
    
    send_email(email, name)

    # Return success response after user registration
    return jsonify({'message': 'User registered successfully!'}), 201


def send_email(to_email, name):
    msg_title = "Welcome to Rootx Mobile App!"
    sender = "aselarohana0522@gmail.com"
    msg = Message(msg_title, sender=sender, recipients=[to_email])

    # Render the welcome email HTML template
    msg.html = render_template("welcomeEmail.html", username=name)  # Pass the name to the template

    try:
        mail.send(msg)  # Use the mail instance to send the message
        print(f"Email sent to {to_email} successfully.")
    except Exception as e:
        print(f"The email was not sent: {e}")




@app.route('/passenger_reset_password', methods=['POST'])
def reset_password():
    data = request.get_json()
    email = data.get('email')
    new_password = data.get('new_password')

    if not email or not new_password:
        return jsonify({'error': 'Please provide both email and new password!'}), 400
    
    conn = get_db_connection_socondary()
    if not conn:
        return jsonify({'error': 'Error connecting to database'}), 500

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM passenger_information_table WHERE email=%s", (email,))
    existing_user = cur.fetchone()

    if not existing_user:
        return jsonify({'error': 'User not found!'}), 404

    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

    cur.execute("UPDATE passenger_information_table SET password=%s WHERE email=%s", (hashed_password, email))
    mysql.connection.commit()
    cur.close()

    return jsonify({'message': 'Password reset successful!'}), 200




@app.route('/passenger_signin', methods=['POST'])
def passenger_signin():  # Renamed to differentiate from driver signin
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Please provide both email and password!'}), 400

    conn = get_db_connection_socondary()
    if not conn:
        return jsonify({'error': 'Error connecting to database'}), 500
    cur = conn.cursor()
    cur.execute("SELECT * FROM passenger_information_table WHERE email=%s", (email,))
    user = cur.fetchone()
    cur.close()

    if user is None:
        return jsonify({'Error': 'User does not exist!'}), 404

    if bcrypt.checkpw(password.encode('utf-8'), user['Password'].encode('utf-8')):
        return jsonify({'message': 'Login successful!', 'user': {
            'email': user['Email'],
            'name': user['Name'],
            'phone': user['Phone_Number']
        }}), 200
    else:
        return jsonify({'Error': 'Invalid password!'}), 401





# Get distinct start locations from Bus_Information_Table
@app.route('/fromLocations', methods=['GET'])
def get_from_locations():
    try:
        conn = get_db_connection_socondary()
        if not conn:
            return jsonify({"error": "Error connecting to database"}), 500
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT Start_Location FROM Bus_Information_Table")
        locations = cur.fetchall()
        cur.close()

        # Extract the locations from the query result
        start_locations = [location[0] for location in locations]  # Access by index
        return jsonify(start_locations)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Error fetching locations"}), 500


# Get distinct end locations from Bus_Information_Table
@app.route('/toLocations', methods=['GET'])
def get_to_locations():
    try:
        conn = get_db_connection_socondary()
        if not conn:
            return jsonify({"error": "Error connecting to database"}), 500
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT End_Location FROM Bus_Information_Table")
        locations = cur.fetchall()
        cur.close()

        # Extract the locations from the query result
        end_locations = [location[0] for location in locations]  # Access by index
        return jsonify(end_locations)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Error fetching locations"}), 500




# Endpoint to fetch bus information
@app.route('/buses', methods=['GET'])
def fetch_bus_info():
    conn = get_db_connection_socondary()
    if not conn:
        return jsonify({"error": "Error connecting to database"}), 500

    query = "SELECT * FROM dbo.bus_information_table"
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        buses = [
            {
                "Bus_ID": row.Bus_ID,
                "Start_Location": row.Start_Location,
                "End_Location": row.End_Location,
                "Bus_Number": row.Bus_Number,
                "Ticket_Price": float(row.Ticket_Price),  # Ensure decimal is converted to float
                "Bus_Name": row.Bus_Name,
                "Total_Seats": row.Total_Seats,
                "Route_Number": row.Route_Number,
                "Start_Time": str(row.Start_Time),  # Convert timedelta or time object to string
                #"Travel_Date": row.Travel_Date

            }
            for row in cursor.fetchall()
        ]
        return jsonify(buses)
    except Exception as e:
        print(f"Error fetching data: {e}")
        return jsonify({"error": "Error fetching bus information"}), 500
    finally:
        conn.close()


# Process payment API (make sure a payments table exists)
@app.route('/process_payment', methods=['POST'])
def process_payment():
    data = request.get_json()

    bus_id = data.get('bus_id')
    ticket_price = data.get('ticket_price')
    payment_method = data.get('payment_method')

    if not bus_id or not ticket_price or not payment_method:
        return jsonify({'status': 'error', 'message': 'Missing data'}), 400

    try:
        cur = mysql.connection.cursor()
        
        # Insert payment record into the database
        query = "INSERT INTO payments (Bus_ID, ticket_price, payment_method) VALUES (%s, %s, %s)"
        cur.execute(query, (bus_id, ticket_price, payment_method))
        
        mysql.connection.commit()
        cur.close()

        return jsonify({'status': 'success', 'message': 'Payment processed successfully'}), 200
    except Exception as err:
        print(f"Error: {err}")
        return jsonify({'status': 'error', 'message': 'Database error'}), 500



# Sign up driver
@app.route('/driver_signup', methods=['POST'])
def driver_signup():  # Renamed from signup to driver_signup
    data = request.get_json()
    email = data.get('email')
    name = data.get('name')
    phone = data.get('phone')
    password = data.get('password')
    bus_number = data.get('bus_number')

    if not all([email, name, phone, password, bus_number]):
        return jsonify({'error': 'Please provide all fields!'}), 400


    conn = get_db_connection_socondary()
    if not conn:
        return jsonify({"error": "Error connecting to database"}), 500
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM Driver_Information_Table WHERE Email=%s", (email,))
    if cur.fetchone():
        return jsonify({'error': 'Driver already exists!'}), 400

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    cur.execute("INSERT INTO Driver_Information_Table (Email, Name, Phone_Number, Password, Bus_Number) VALUES (%s, %s, %s, %s, %s)",
                (email, name, phone, hashed_password, bus_number))
    mysql.connection.commit()
    cur.close()

    send_email(email, name)

    return jsonify({'message': 'Driver registered successfully!'}), 201

def send_email(to_email, name):
    msg_title = "Welcome to Rootx Mobile App!"
    sender = "aselarohana0522@gmail.com"
    msg = Message(msg_title, sender=sender, recipients=[to_email])
    msg.html = render_template("welcomeEmail.html", username=name)

    try:
        mail.send(msg)
        print(f"Email sent to {to_email} successfully.")
    except Exception as e:
        print(f"The email was not sent: {e}")

@app.route('/driver_reset_password', methods=['POST'])
def driver_reset_password():  # Renamed to differentiate from passenger reset password
    data = request.get_json()
    email = data.get('email')
    new_password = data.get('new_password')

    if not email or not new_password:
        return jsonify({'error': 'Please provide both email and new password!'}), 400

    conn = get_db_connection_socondary()
    if not conn:
        return jsonify({"error": "Error connecting to database"}), 500

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM Driver_Information_Table WHERE Email=%s", (email,))
    if not cur.fetchone():
        return jsonify({'error': 'Driver not found!'}), 404

    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
    cur.execute("UPDATE Driver_Information_Table SET Password=%s WHERE Email=%s", (hashed_password, email))
    mysql.connection.commit()
    cur.close()

    return jsonify({'message': 'Password reset successful!'}), 200

@app.route('/driver_signin', methods=['POST'])
def driver_signin():  # Renamed to differentiate from passenger signin
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Please provide both email and password!'}), 400

    conn = get_db_connection_socondary()
    if not conn:
        return jsonify({"error": "Error connecting to database"}), 500
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM Driver_Information_Table WHERE Email=%s", (email,))
    driver = cur.fetchone()
    cur.close()

    if driver is None:
        return jsonify({'Error': 'Driver does not exist!'}), 404

    if bcrypt.checkpw(password.encode('utf-8'), driver['Password'].encode('utf-8')):
        return jsonify({'message': 'Login successful!', 'driver': {
            'email': driver['Email'],
            'name': driver['Name'],
            'phone': driver['Phone_Number'],
            'bus_number': driver['Bus_Number']
        }}), 200
    else:
        return jsonify({'Error': 'Invalid password!'}), 401


if __name__ == '__main__':
    app.run(debug=True)
