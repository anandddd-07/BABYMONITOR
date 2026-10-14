import cv2
import mediapipe as mp
import numpy as np
import time
import threading
import tensorflow as tf
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
from detect_file import Detect_final

# Custom denormalization function to replace broken mediapipe legacy drawing modules
def denormalize_coordinates(normalized_x, normalized_y, image_width, image_height):
    import math
    x_px = min(math.floor(normalized_x * image_width), image_width - 1)
    y_px = min(math.floor(normalized_y * image_height), image_height - 1)
    return x_px, y_px


def handle_left_click(event, x, y, flags, points):
    if event == cv2.EVENT_LBUTTONDOWN:
        points.append([x, y])

def draw_polygon(frame, points):
    for point in points:
        frame = cv2.circle(frame, (point[0], point[1]), 5, (0, 0, 255), -1)  
    if len(points) > 0:
        frame = cv2.polylines(frame, [np.int32(points)], False, (255, 0, 0), thickness=2)
    return frame


start_detect = False
model = Detect_final()
points = []
Ptime = 0

cap = cv2.VideoCapture(0)

# Create the window once before setting mouse callback
cv2.namedWindow("Baby Monitor")
cv2.setMouseCallback('Baby Monitor', handle_left_click, points)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Ignoring empty camera frame.")
        break
        
    frame = cv2.flip(frame, 1)
    
    if start_detect:
        frame = model.output(frame=frame, points=points)
    
    cTime = time.time()
    # Prevent division by zero if time difference is 0
    fps = 1 / (cTime - Ptime) if (cTime - Ptime) > 0 else 0
    Ptime = cTime 

    # Draw polygon points
    frame = draw_polygon(frame, points)
    
    cv2.imshow("Baby Monitor", frame)
    
    key = cv2.waitKey(10) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('d') and len(points) > 0:
        points.append(points[0])
        start_detect = True

cap.release()
cv2.destroyAllWindows()