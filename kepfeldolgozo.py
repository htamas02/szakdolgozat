import cv2
import numpy as np
import os

def kepvagas(kepnev):
    img = cv2.imread(kepnev)

    pontok = np.float32([
        [93,35],
        [570,13],
        [544,478],
        [136,479]
    ])
    width, height = 500,500
    pts2 = np.float32([[0,0], [width, 0], [width, height], [0, height]])

    matrix = cv2.getPerspectiveTransform(pontok, pts2)
    result = cv2.warpPerspective(img, matrix, (width, height))

    rows, cols = 10,10
    tile_h, tile_w = height // rows, width // cols
    os.makedirs("tiles", exist_ok=True)
    count = 0
    for i in range(rows):
        for j in range(cols):
            y1, y2 = i * tile_h, (i + 1) * tile_h
            x1, x2 = j * tile_w, (j + 1) * tile_w
            tile = result[y1:y2, x1:x2]
            filename = f"tiles/tile_{count:02d}.png"
            cv2.imwrite(filename, tile)
            count += 1

    print(f"{count} db négyzet elmentve a tiles mappába.")

