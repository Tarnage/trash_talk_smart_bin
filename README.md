# SmartBin Management System

## Project Overview
The SmartBin Management System is an IoT-based solution for efficient waste management. It consists of a Flask web application and an MQTT client that work together to collect, process, and store data from smart waste bins.

## Features
- Real-time data collection from smart bins via MQTT
- Support for multiple MQTT brokers (Mosquitto and The Things Network)
- Data validation and processing
- Storage of bin data in a PostgreSQL database
- RESTful API for data access and management (provided by Flask)

## Components
1. **Flask Web Application**: Handles API requests and database operations
2. **MQTT Client**: Receives and processes messages from smart bins
3. **Database**: Stores smart bin data using PostgreSQL

## Prerequisites
- Python 3.7+
- PostgreSQL database
- MQTT broker (e.g., Mosquitto, TTN)

## Environment Variables
The application uses the following environment variables:

### Database Configuration
- `DB_USER`: PostgreSQL username
- `DB_PASSWORD`: PostgreSQL password
- `DB_HOST`: PostgreSQL host address
- `DB_NAME`: PostgreSQL database name

### MQTT Configuration (Mosquitto)
- `MQTT_BROKER`: Mosquitto broker address
- `MQTT_PORT`: Mosquitto broker port (default: 1883)
- `MQTT_USER`: Mosquitto username
- `MQTT_PASSWORD`: Mosquitto password
- `MQTT_TOPIC`: Mosquitto topic to subscribe to

### MQTT Configuration (TTN)
- `TTN_MQTT_BROKER`: TTN broker address
- `TTN_MQTT_PORT`: TTN broker port (default: 1883)
- `TTN_MQTT_USER`: TTN username
- `TTN_MQTT_PASSWORD`: TTN password
- `TTN_MQTT_TOPIC`: TTN topic to subscribe to

## Setup and Installation
1. Clone the repository:
   ```
   git clone https://github.com/yourusername/smartbin-management-system.git
   cd smartbin-management-system
   ```

2. Install required packages:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables (see above)

4. Initialize the database:
   ```
   flask db upgrade
   ```

5. Run the application:
   ```
   python app.py
   ```

## Usage
- The Flask application will start and listen for incoming connections (default port: 6969)
- The MQTT client will connect to the configured broker(s) and start listening for messages
- Smart bin data will be automatically processed and stored in the database

## API Endpoints
- `GET /`: Check if the application is running
- (Add other API endpoints as implemented in your Flask app)

## Testing
The project includes comprehensive unit tests for both the Flask application and the MQTT subscriber. These tests ensure the correct functionality of data processing, payload validation, and database operations.

### Running Tests
To run the tests, use the following commands:

1. For MQTT subscriber tests:
   ```
   python -m unittest tests.test_mqtt_subscriber
   ```

2. For Flask application tests:
   ```
   python -m unittest tests.test_flask_app
   ```

### Test Coverage
The unit tests cover the following areas:

#### MQTT Subscriber Tests
- Payload decoding
- Payload validation
- Message handling (creating new bins and updating existing bins)
- Error handling for invalid payloads

#### Flask Application Tests
- Index route functionality

To run all tests together, you can use:
```
python -m unittest discover tests
```

## Contributing
Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License
<<<<<<< HEAD
This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.
=======
This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.
>>>>>>> 25520f5 (SQLALCHEMY_DATABASE_URI)
