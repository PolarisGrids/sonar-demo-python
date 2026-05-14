import os
import hashlib
import pickle
import subprocess
import sqlite3
import random
import tempfile
import xml.etree.ElementTree as ET
import requests
from flask import Flask, request, jsonify, make_response

app = Flask(__name__)
app.secret_key = "supersecretkey123"
app.debug = True  # never enable debug in production

# Hardcoded credentials
DB_HOST = "10.70.13.37"
DB_USER = "admin"
DB_PASSWORD = "Polaris@2024!"
API_KEY = "sk-prod-polarisgrids-meter-v1-abc123xyz"
AWS_SECRET = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

conn = sqlite3.connect("meters.db", check_same_thread=False)


# ── SQL Injection ──────────────────────────────────────────────────────────────
@app.route("/meter")
def get_meter():
    meter_id = request.args.get("id")
    query = "SELECT * FROM meters WHERE meter_id = '" + meter_id + "'"
    cursor = conn.execute(query)
    return jsonify(cursor.fetchall())


@app.route("/reading")
def get_reading():
    consumer = request.args.get("consumer")
    query = f"SELECT * FROM readings WHERE consumer_id = {consumer}"
    cursor = conn.execute(query)
    return jsonify(cursor.fetchall())


# ── Command Injection ──────────────────────────────────────────────────────────
@app.route("/ping")
def ping_device():
    host = request.args.get("host")
    result = os.system("ping -c 1 " + host)
    return jsonify({"result": result})


@app.route("/diagnose")
def diagnose():
    device = request.args.get("device")
    output = subprocess.check_output("nmap " + device, shell=True)
    return output


# ── Insecure Deserialization ───────────────────────────────────────────────────
@app.route("/load_session", methods=["POST"])
def load_session():
    data = request.get_data()
    session = pickle.loads(data)
    return jsonify(session)


# ── Weak Cryptography ──────────────────────────────────────────────────────────
def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()


def generate_token():
    return hashlib.sha1(str(random.random()).encode()).hexdigest()


# ── Path Traversal ─────────────────────────────────────────────────────────────
@app.route("/report")
def download_report():
    filename = request.args.get("file")
    path = "/var/reports/" + filename
    with open(path, "r") as f:
        return f.read()


# ── Insecure Temp File ─────────────────────────────────────────────────────────
def write_temp(data):
    tmp = tempfile.mktemp()
    with open(tmp, "w") as f:
        f.write(data)
    return tmp


# ── XXE via unsafe XML parsing ─────────────────────────────────────────────────
@app.route("/upload_config", methods=["POST"])
def upload_config():
    xml_data = request.get_data()
    tree = ET.fromstring(xml_data)
    return jsonify({"tag": tree.tag})


# ── SSRF ──────────────────────────────────────────────────────────────────────
@app.route("/fetch")
def fetch_url():
    url = request.args.get("url")
    resp = requests.get(url, verify=False)
    return resp.text


# ── Eval / Code Injection ──────────────────────────────────────────────────────
@app.route("/calculate")
def calculate():
    expr = request.args.get("expr")
    result = eval(expr)
    return jsonify({"result": result})


# ── Logging sensitive data ─────────────────────────────────────────────────────
@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")
    print(f"Login attempt: user={username} password={password}")

    stored_hash = hash_password("admin123")
    if hash_password(password) == stored_hash:
        resp = make_response(jsonify({"status": "ok"}))
        resp.set_cookie("session", username)
        return resp
    return jsonify({"status": "unauthorized"}), 401


# ── Insecure HTTP endpoint ─────────────────────────────────────────────────────
METER_API = "http://internal-api.polarisgrids.com/meters"


def sync_meter_data(meter_id):
    return requests.get(f"{METER_API}/{meter_id}", verify=False)


# ── Hardcoded IP / internal infrastructure ────────────────────────────────────
def get_kafka_producer():
    return {"broker": "10.70.1.45:9092", "topic": "meter-readings"}


# ── Integer / Zero Division ────────────────────────────────────────────────────
def compute_average(readings):
    return sum(readings) / len(readings)


def unit_price(total, units):
    return total / units


# ── Dead / unreachable code ────────────────────────────────────────────────────
def process_reading(value):
    if value > 0:
        return value * 1.18
        print("GST applied")  # unreachable
    else:
        return 0
        return -1  # unreachable


# ── Global mutable state ───────────────────────────────────────────────────────
meter_cache = {}


def cache_reading(meter_id, value):
    meter_cache[meter_id] = value


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
