from machine import Pin, I2C, ADC, RTC
import time, machine, urequests, network, ntptime
from ssd1306 import SSD1306_I2C
import ahtx0

#WIFI
WIFI_SSID = "HEGYINET"
WIFI_PASS = ""

sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
sta_if.connect(WIFI_SSID, WIFI_PASS)

while not sta_if.isconnected():
    print("Csatlakozás WiFi-hez")
    time.sleep(1)

print("WiFi csatlakoztatva:", sta_if.ifconfig())

#időszinkron
try:
    ntptime.settime()
    print("Idő szinkronizálva")
except Exception as e:
    print("hiba:", e)

#relék
relay = Pin(5, Pin.OUT)     # Szellőztetés
relay2 = Pin(4, Pin.OUT)    # Lámpa
relay3 = Pin(2, Pin.OUT)    # Locsolás

#mindent kikapcs
relay.value(1)
relay2.value(1)
relay3.value(1)

#Változók
watering_active = False
watering_start_time = 0
last_watering_end = 0

#OLED
I2C_SCL = 14
I2C_SDA = 12
WIDTH = 128
HEIGHT = 64
i2c = I2C(scl=Pin(I2C_SCL), sda=Pin(I2C_SDA))
display = SSD1306_I2C(WIDTH, HEIGHT, i2c)


soil_sensor = ADC(0)
DRY_VALUE = 1000
WET_VALUE = 350
sensor = ahtx0.AHT20(i2c)

#Konfig
def get_config():
    try:
        url = "http://192.168.0.37:5000/get_config"
        response = urequests.get(url)
        config = response.json()
        response.close()
        return config
    except Exception as e:
        print("Hiba:", e)
        return None

#Talajnedvesség számolás
def get_soil_percent():
    value = soil_sensor.read()
    percent = int((DRY_VALUE - value) * 100 / (DRY_VALUE - WET_VALUE))
    return max(0, min(100, percent))

#Locsolás
def start_watering(duration):
    global watering_active, watering_start_time, watering_duration
    if time.ticks_diff(time.ticks_ms(), last_watering_end) < 310_000:
        print("Várakozás")
        return
    print(f"Locsolás indul {duration} mp-re")
    relay3.value(0)  # aktív LOW → bekapcsol
    watering_active = True
    watering_start_time = time.ticks_ms()
    watering_duration = duration * 1000

#Kijelző frissítés
def update_display(status):
    try:
        moisture_percent = get_soil_percent()
        display.fill(0)
        display.text("Palanta nevelo", 0, 0)
        display.text(f"Soil: {moisture_percent}%", 0, 20)
        display.text(f"Tmp: {sensor.temperature}C", 0, 35)
        display.text(f"Hum: {sensor.relative_humidity}%", 0, 50)
        display.show()
    except Exception as e:
        print("Kijelző hiba:", e)

#Adatküldés
def send_data():
    try:
        payload = {
            "temperature": sensor.temperature,
            "humidity": sensor.relative_humidity,
            "soil_moisture": get_soil_percent()
        }
        url = "http://192.168.0.37:5000/update"
        res = urequests.post(url, json=payload)
        print("Küldve:", payload, "Válasz:", res.text)
        res.close()
    except Exception as e:
        print("Hiba:", e)


def change_time(timestr):
    hour, minute = map(int, timestr.split(":"))
    return hour, minute

def get_current_time():
    t = time.localtime(time.time() + 1 * 3600)
    return t[3], t[4]

#Lámpa vezérlés
def control_light(on_time, off_time):
    try:
        on_hour, on_min = change_time(on_time)
        off_hour, off_min = change_time(off_time)
        now_hour, now_min = get_current_time()

        now_total = now_hour * 60 + now_min
        on_total = on_hour * 60 + on_min
        off_total = off_hour * 60 + off_min

        print(f"Idő: {now_hour}:{now_min} | Bekapcsol: {on_time} | Kikapcsol: {off_time}")

        if on_total <= now_total < off_total:
            relay2.value(1)  # aktív LOW → bekapcsol
            print("Lámpa bekapcsolva")
        else:
            relay2.value(0)  # kikapcsol
            print("Lámpa kikapcsolva")
    except Exception as e:
        print("Lámpa hiba:", e)

#Beállítás
config = get_config()
if not config:
    print("Alapértelmezett konfiguráció használata")
    config = {
        "moisture_threshold": 50,
        "watering_duration": 10,
        "light_on_time": "18:00",
        "light_off_time": "23:00",
        "HUMIDITY_ON": 70,
        "HUMIDITY_OFF": 60,
        "send_interval": 60,
        "manual_light": 0,
        "manual_watering": False
    }

last_send = time.ticks_ms()

while True:
    update_display("OK")

    now = time.ticks_ms()
    if time.ticks_diff(now, last_send) > (config["send_interval"] * 1000):
        send_data()
        config = get_config() or config
        last_send = now

    soil_percent = get_soil_percent()
    hum = sensor.relative_humidity

    # Automata locsolás
    if not watering_active and soil_percent < config["moisture_threshold"]:
        print("Talaj száraz – automatikus locsolás")
        start_watering(config["watering_duration"])

    # Manuális locsolás
    if not watering_active and config["manual_watering"]:
        print("Manuális locsolás parancs")
        start_watering(config["watering_duration"])

    #Párásítás vezérlés
    if hum > config["HUMIDITY_ON"]:
        print("Pára magas – relé bekapcsol")
        relay.value(0)
    elif hum < config["HUMIDITY_OFF"]:
        print("Pára alacsony – relé kikapcsol")
        relay.value(1)

    #Lámpa vezérlés
    if config["manual_light"] == 0:
        control_light(config["light_on_time"], config["light_off_time"])
    elif config["manual_light"] == 1:
        relay2.value(1) #be
    elif config["manual_light"] == 2:
        relay2.value(0) #ki

    #locsolás leállítás
    if watering_active and time.ticks_diff(time.ticks_ms(), watering_start_time) >= watering_duration:
        relay3.value(1)  # ki
        watering_active = False
        last_watering_end = time.ticks_ms()
        print("Locsolás vége, most szünet jön")
    time.sleep(1)



