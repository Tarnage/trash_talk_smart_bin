#!/bin/bash
gunicorn mqtt_flask_smartbin:smartbin --bind 0.0.0.0:$PORT
