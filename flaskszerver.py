from http.client import responses
from flask import Flask, request, jsonify
import json
import os
from datetime import datetime
from flask import send_from_directory

app = Flask(__name__)
DATA_FILE = ".venv/sensor_log.json"
SETTINGS_FILE = ".venv/settings.json"
DB_FILE = ".venv/db.json"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploaded_images")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# Adatok betöltése
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        all_data = json.load(f)
        if isinstance(all_data, dict):
            all_data = [all_data]
else:
    all_data = []
#palántaszám feltöltés
@app.route("/upload_db", methods=["POST"])
def upload_db():
    config = request.get_json()
    if not config:
        return jsonify({"error":"No config received"}),400
    with open(DB_FILE, "w")as f:
        json.dump(config,f)
    return jsonify({"Message":"Config saved"}),200
#palántaszám lekérés
@app.route("/get_db", methods=["GET"])
def get_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r")as f:
            config = json.load(f)
    return jsonify(config),200

#Képfeltöltés
@app.route("/upload_cam", methods=["POST"])
def upload_cam():
    img_data = request.data
    if not img_data:
        return jsonify({"error": "No image received"}), 400
    filename = datetime.now().strftime("%Y%m%d_%H%M%S") + ".jpg"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    with open(filepath, "wb") as f:
        f.write(img_data)

    return jsonify({"message": "Image saved", "filename": filename}), 200
#legutóbbi adat visszadása
@app.route('/latest_data', methods=['GET'])
def get_latest_data():
    if not os.path.exists(DATA_FILE):
        return jsonify({"error": "No data file found"}), 404

    with open(DATA_FILE, "r") as f:
        try:
            data_list = json.load(f)
        except json.JSONDecodeError:
            return jsonify({"error": "Corrupted JSON file"}), 500

    if not data_list:
        return jsonify({"error": "No data found"}), 404

    if isinstance(data_list, list):
        latest_data = data_list[-1]
    else:
        latest_data = data_list

    return jsonify(latest_data)

#legutóbbi kép visszadása
@app.route('/latest', methods=['GET'])
def get_latest_image():
    files = os.listdir(UPLOAD_FOLDER)
    if not files:
        return jsonify({"error": "No images found"}), 404
    # fájlok dátum szerint rendezése
    files.sort(key=lambda x: os.path.getmtime(os.path.join(UPLOAD_FOLDER, x)))
    latest_file = files[-1]
    return send_from_directory(UPLOAD_FOLDER, latest_file)
#Szenzoradatok fogadása
@app.route('/update', methods=['POST'])
def update_data():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data received"}), 400

    data['timestamp'] = datetime.now().isoformat()
    all_data.append(data)

    with open(DATA_FILE, "w") as f:
        json.dump(all_data, f, indent=4)

    return jsonify({"message": "Data appended and saved"}), 200

#Adatok lekérdezése
@app.route('/data', methods=['GET'])
def get_data():
    return jsonify(all_data), 200

#Beállítások mentése
@app.route('/set_config', methods=['POST'])
def set_config():
    config = request.get_json()
    if not config:
        return jsonify({"error": "No config received"}), 400

    with open(SETTINGS_FILE, "w") as f:
        json.dump(config, f, indent=9)

    return jsonify({"message": "Config saved"}), 200

#Beállítások lekérdezése
@app.route('/get_config', methods=['GET'])
def get_config():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            config = json.load(f)
        #Manuális locsolás visszallitjjuk true
        if config.get("manual_watering", False):
            print("Manuális locsolás parancs észlelve, visszaállítás")
            response = jsonify(config)
            config["manual_watering"] = False

            # Visszamentjük a módosított konfigurációt
            with open(SETTINGS_FILE, "w") as f:
                json.dump(config, f, indent=9)
            return response, 200
        return jsonify(config), 200
    else:
        return jsonify({"error": "No config found"}), 404
#Lokális futtatás
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
