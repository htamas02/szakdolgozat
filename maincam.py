import network
import socket
import camera
import time
import urequests
import machine


#Wifi csatlakozás
ssid = "HEGYINET"
password = ""

station = network.WLAN(network.STA_IF)
station.active(True)
station.connect(ssid, password)

for _ in range(20):
    if station.isconnected():
        break
    time.sleep(1)

if station.isconnected():
    print("WiFi csatlakozva:", station.ifconfig())
else:
    print("WiFi hiba! Ellenőrizd az SSID-t és jelszót.")

camera.init(0, format=camera.JPEG, fb_location=camera.PSRAM)
camera.quality(10)


while True:
    time.sleep(5)
    buf = camera.capture()
    try:
        url = "http://192.168.0.37:5000/upload_cam"  # Flask szerver
        headers = {"Content-Type": "application/octet-stream"}
        r = urequests.post(url, data=buf, headers=headers)
        print("Kép elküldve, válasz:", r.text)
        r.close()
    except Exception as e:
        print("Hiba kép küldés közben:", e)
    #camera.deinit()
    time.sleep(300)

