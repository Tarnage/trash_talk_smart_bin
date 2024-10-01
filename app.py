from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Database configuration from environment variables
db_user = os.environ.get('DB_USER')
db_password = os.environ.get('DB_PASSWORD')
db_host = os.environ.get('DB_HOST')
db_name = os.environ.get('DB_NAME')
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_user}:{db_password}@{db_host}/{db_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define SmartBinData model
class SmartBinData(db.Model):
    __tablename__ = 'mockdata'
    __table_args__ = {'schema': 'smartbin'}  # Specify the schema if needed
    bin_id = db.Column(db.String(10), primary_key=True, nullable=False)
    latitude = db.Column(db.Numeric(12, 8))
    longitude = db.Column(db.Numeric(12, 8))
    collection_frequency_per_month = db.Column(db.Integer)
    average_collection_time_days = db.Column(db.Integer)
    tilt_status = db.Column(db.String(20))
    fill_level_percentage = db.Column(db.Numeric(5, 2))
    temperature_celsius = db.Column(db.Numeric(5, 2))
    displacement = db.Column(db.String(20))
    days_since_last_emptied = db.Column(db.Integer)
    communication_status = db.Column(db.String(20))
    battery_level_percentage = db.Column(db.Numeric(4, 2))

# Route to check if the app is running
@app.route('/')
def index():
    return "SmartBin Flask App is running!"

if __name__ == "__main__":
    # Default to port 6969, but allow PORT environment variable to override
    port = int(os.environ.get('PORT', 6969))
    with app.app_context():
        db.create_all()  # Ensure all tables are created
    app.run(host='0.0.0.0', port=port)
