"""
Proyecto: Airflow - Hand Tracking Module
Autor: Manuel Fereira
Descripción: Módulo central de detección y seguimiento de manos utilizando MediaPipe.
Extrae los puntos de referencia y calcula la orientación, distancias 
y estados de los dedos para identificar gestos.
"""

import cv2
import mediapipe as mp
import time
import math

class HandDetector:
    def __init__(self, mode=False, max_hands=1, model_complexity=1, detection_con=0.4, track_con=0.5, min_area=500, max_area=1000):
        self.mode = mode
        self.max_hands = max_hands
        self.model_complex = model_complexity
        self.detection_con = detection_con
        self.track_con = track_con
        self.min_area = min_area
        self.max_area = max_area

        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=self.mode,
            max_num_hands=self.max_hands,
            model_complexity=self.model_complex,
            min_detection_confidence=self.detection_con,
            min_tracking_confidence=self.track_con
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.tip_ids = [4, 8, 12, 16, 20]
        self.lm_list = []

    def find_hands(self, img, draw=True):
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = self.hands.process(img_rgb)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                if draw:
                    self.mp_draw.draw_landmarks(
                        img, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
        return img, results

    def find_position(self, img, results, hand_no=0, draw=True):
        self.lm_list = []
        if not results or not results.multi_hand_landmarks:
            return self.lm_list, []

        hand_landmarks = results.multi_hand_landmarks[hand_no]
        h, w, c = img.shape

        x_list = []
        y_list = []

        for lm in hand_landmarks.landmark:
            cx, cy = int(lm.x * w), int(lm.y * h)
            x_list.append(cx)
            y_list.append(cy)
            self.lm_list.append([cx, cy])

            if draw:
                cv2.circle(img, (cx, cy), 5, (255, 0, 255), cv2.FILLED)

        if not x_list or not y_list:
            return self.lm_list, []

        x_min, x_max = min(x_list), max(x_list)
        y_min, y_max = min(y_list), max(y_list)
        bbox = (x_min, y_min, x_max, y_max)

        if draw:
            cv2.rectangle(img, (x_min - 20, y_min - 20), (x_max + 20, y_max + 20), (0, 255, 0), 2)

        return self.lm_list, bbox

    def fingers_up(self):
        if len(self.lm_list) < 21:
            return [0] * 5

        fingers = []
        
        # Determinar orientación de la mano comparando el nudillo del índice (5) con el del meñique (17)
        is_right_orientation = self.lm_list[5][0] > self.lm_list[17][0]

        # Pulgar (comparación dinámica según orientación)
        if is_right_orientation:
            fingers.append(1 if self.lm_list[self.tip_ids[0]][0] > self.lm_list[self.tip_ids[0] - 1][0] else 0)
        else:
            fingers.append(1 if self.lm_list[self.tip_ids[0]][0] < self.lm_list[self.tip_ids[0] - 1][0] else 0)

        # Otros dedos (Índice, Medio, Anular, Meñique) 
        wrist = self.lm_list[0]  
        
        for tip_id in self.tip_ids[1:]:
            tip = self.lm_list[tip_id]          
            pip = self.lm_list[tip_id - 2]      
            
            dist_tip = math.hypot(tip[0] - wrist[0], tip[1] - wrist[1])
            dist_pip = math.hypot(pip[0] - wrist[0], pip[1] - wrist[1])
            
            # Eliminamos el multiplicador que causaba los falsos positivos
            fingers.append(1 if dist_tip > dist_pip else 0)

        return fingers

    def find_distance(self, p1, p2, img, draw=True, r=15, t=3):
        if len(self.lm_list) < max(p1, p2) + 1:
            return 0, img, []

        x1, y1 = self.lm_list[p1]
        x2, y2 = self.lm_list[p2]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        if draw:
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), t)
            cv2.circle(img, (x1, y1), r, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), r, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (cx, cy), r, (0, 0, 255), cv2.FILLED)

        length = math.hypot(x2 - x1, y2 - y1)
        return length, img, [x1, y1, x2, y2, cx, cy]

def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: No se pudo abrir la cámara.")
        return

    detector = HandDetector()
    p_time = 0

    while True:
        success, img = cap.read()
        if not success:
            print("Error al leer el frame.")
            break

        img, results = detector.find_hands(img)
        lm_list, bbox = detector.find_position(img, results)

        c_time = time.time()
        fps = 1 / (c_time - p_time) if c_time - p_time > 0 else 0
        p_time = c_time

        cv2.putText(img, f'FPS: {int(fps)}', (10, 70),
                    cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 255), 3)

        cv2.imshow("Hand Tracking", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()