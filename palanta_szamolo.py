import tensorflow as tf
import numpy as np
import os
import time
from tensorflow.keras.models import load_model
import requests

model = load_model('my_model.keras')
from kepvagasos import kepvagas

urlk = "http://192.168.0.37:5000/latest"
while True:
    resp = requests.get(urlk)
    filename = "latest_image.jpg"
    with open(filename, "wb") as f:
        f.write(resp.content)
    kepvagas(filename)
    images = "tiles/"
    db= 0
    for kep in os.listdir(images):
        imgpath = os.path.join(images, kep)
        img = tf.keras.preprocessing.image.load_img(
            imgpath, target_size=(64,64)
        )
        img_array = tf.keras.preprocessing.image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        prediction = model.predict(img_array)
        print(f"Prediction érték: {prediction[0][0]:.4f}")
        if prediction[0][0] > 0.5:
            db +=1
            print("van palánta a képen")
        else:
            print("Nincs Palánta a képen")
    print(db)
    config= {
        "db": db
    }
    url = "http://192.168.0.37:5000/upload_db"
    response = requests.post(url, json=config)
    print(response.json())
    time.sleep(300)
