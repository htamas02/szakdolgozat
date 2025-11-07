import tensorflow as tf
from tensorflow.keras import layers, models

#Adatbetöltés
train_ds = tf.keras.preprocessing.image_dataset_from_directory(
    "dataset/",
    image_size=(64, 64),
    batch_size=8
)
model = models.Sequential([
    layers.RandomFlip("horizontal_and_vertical"),
    layers.RandomRotation(0.1),
    layers.RandomZoom(0.1),
    layers.RandomContrast(0.1),
    layers.Rescaling(1./255, input_shape=(64, 64, 3)),
    layers.Conv2D(16, 3, activation='relu'),
    layers.MaxPooling2D(),
    layers.Conv2D(32, 3, activation='relu'),
    layers.MaxPooling2D(),
    layers.Flatten(),
    layers.Dense(64, activation='relu'),
    layers.Dense(1, activation='sigmoid')
])

model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
model.fit(train_ds, epochs=40)
print(train_ds.class_names)
# Mentés
model.save('my_model.keras')
