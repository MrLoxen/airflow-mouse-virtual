"""
Proyecto: Airflow - Mouse virtual
Autor: Manuel Fereira
Descripción: Script principal para el control del mouse mediante visión por computadora.
Mapea los gestos de la mano capturados en tiempo real para ejecutar movimientos, 
clics, arrastres y scroll en el sistema operativo.
"""

import cv2
import numpy as np
import Hand_TrackingMin as HTM
import time
import os
import tkinter as tk
from pynput.mouse import Button, Controller
from collections import deque

# Configuración
w_cam, h_cam = 640, 480
frame_reduction = 100
smoothing = 4  
mouse = Controller()

# Obtener resolución de pantalla usando tkinter (nativo)
root = tk.Tk()
w_screen = root.winfo_screenwidth()
h_screen = root.winfo_screenheight()
root.destroy()

# Variables de sensibilidad
sensitivity = 1.5  
MAX_SENSITIVITY = 3.0
MIN_SENSITIVITY = 0.5

cap = cv2.VideoCapture(0)
cap.set(3, w_cam)
cap.set(4, h_cam)

detector = HTM.HandDetector(max_hands=1)
prev_x, prev_y = w_screen / 2, h_screen / 2  
prev_time = 0
dragging = False

# Estados del mouse
MOUSE_MOVE = 0
LEFT_CLICK = 1
RIGHT_CLICK = 2
SCROLL_UP = 3
DRAG = 4
NONE = 5
EXIT = 6
SCROLL_DOWN = 7

# Colores para visualización
COLOR_MOVE = (255, 0, 255)  
COLOR_CLICK = (0, 255, 0)  
COLOR_RIGHT = (0, 165, 255)  
COLOR_SCROLL = (0, 255, 255)  
COLOR_DRAG = (0, 0, 255)  
COLOR_SENS = (0, 255, 255)  

# Sistema de efectos de clic
click_effects = deque()
CLICK_EFFECT_DURATION = 0.5  
CLICK_EFFECT_MAX_RADIUS = 50

# Crear ventana con barra de sensibilidad
cv2.namedWindow("Virtual Mouse")
cv2.createTrackbar('Sensibilidad', 'Virtual Mouse', int(sensitivity * 10),
                   int(MAX_SENSITIVITY * 10), lambda x: None)

# Control de clics 
last_left_click_time = 0
LEFT_CLICK_DELAY = 0.25  # Tiempo perfecto para que Windows detecte doble clic
right_click_ready = True
mode_buffer = deque(maxlen=7)  # Memoria para estabilizar gestos (Debounce)

while True:
    success, img = cap.read()

    if not success:
        print("Error al leer el frame.")
        break

    sensitivity = cv2.getTrackbarPos('Sensibilidad', 'Virtual Mouse') / 10.0

    lm_list = 0
    current_time = time.time()
    img, results = detector.find_hands(img, draw=True)
    lm_list, bbox = detector.find_position(img, results, draw=False)

    current_mode = NONE
    gesture_text = ""
    x1, y1 = w_cam // 2, h_cam // 2  

    if lm_list and len(lm_list) >= 21:
        fingers = detector.fingers_up()
        finger_tips = [lm_list[i] for i in detector.tip_ids]
        
        # 1. Scroll (hacia arriba): Todos los dedos extendidos
        if all(fingers):
            current_mode = SCROLL_UP
            gesture_text = "SCROLL_UP"
            x1, y1 = finger_tips[1]

        # Scroll (hacia abajo): cuatro dedos levantados, pulgar no levantado
        elif fingers[1] and fingers[2] and fingers[3] and fingers[4] and not fingers[0]:
            current_mode = SCROLL_DOWN
            gesture_text = "SCROLL_DOWN"
            x1, y1 = finger_tips[1]

        # 2. Arrastre: Puño cerrado
        elif not any(fingers):
            current_mode = DRAG
            gesture_text = "DRAG"
            x1, y1 = lm_list[0]

        # 3. Movimiento y Clic Izquierdo fusionados (¡La solución definitiva!)
        elif fingers[1] and not fingers[2] and not fingers[3] and not fingers[4]:
            # Siempre que el índice esté levantado, medimos la distancia a la punta del pulgar
            length, _, _ = detector.find_distance(4, 8, img, draw=False)
            
            if length < 40:
                # Si están tocándose, es un CLIC IZQUIERDO
                current_mode = LEFT_CLICK
                gesture_text = "LEFT CLICK"
                x1 = (lm_list[4][0] + lm_list[8][0]) // 2
                y1 = (lm_list[4][1] + lm_list[8][1]) // 2
            else:
                # Si están separados, es MOVER
                current_mode = MOUSE_MOVE
                gesture_text = "MOVE"
                x1, y1 = finger_tips[1]

        # 4. Clic derecho: Índice y medio extendidos (y aseguramos que anular y meñique estén cerrados)
        elif fingers[1] and fingers[2] and not fingers[3] and not fingers[4]:
            current_mode = RIGHT_CLICK
            gesture_text = "RIGHT CLICK"
            x1, y1 = finger_tips[1] 
        
        # 5. Gesto de salida: Solo el meñique extendido
        elif fingers[4] and not fingers[0] and not fingers[1] and not fingers[2] and not fingers[3]:
            current_mode = EXIT
            gesture_text = "EXIT"
            x1, y1 = finger_tips[4]
            
        # --- FILTRO ANTI-PARPADEO (DEBOUNCE) ---
        mode_buffer.append(current_mode)
        
        # Aplicamos el filtro: gana el gesto más repetido en los últimos frames
        if len(mode_buffer) > 0:
            current_mode = max(set(mode_buffer), key=mode_buffer.count)

    # Visualización del área de trabajo (ahora es solo una guía visual)
    cv2.rectangle(img, (frame_reduction, frame_reduction),
                  (w_cam - frame_reduction, h_cam - frame_reduction), (255, 0, 0), 2)

    # Procesar modo actual con mayor tolerancia
    if current_mode in [MOUSE_MOVE, DRAG, SCROLL_UP, SCROLL_DOWN] and lm_list:
        base_x = np.interp(x1, (0, w_cam), (0, w_screen))
        base_y = np.interp(y1, (0, h_cam), (0, h_screen))

        center_x, center_y = w_cam // 2, h_cam // 2
        rel_x = (x1 - center_x) * sensitivity
        rel_y = (y1 - center_y) * sensitivity

        x = prev_x + (base_x + rel_x - prev_x) / smoothing
        y = prev_y + (base_y + rel_y - prev_y) / smoothing

        x = np.clip(x, 0, w_screen)
        y = np.clip(y, 0, h_screen)

        mouse.position = (x, y)
        prev_x, prev_y = x, y

        if current_mode == MOUSE_MOVE:
            cv2.circle(img, (x1, y1), 15, COLOR_MOVE, cv2.FILLED)
        elif current_mode == SCROLL_UP:
            cv2.circle(img, (x1, y1), 15, COLOR_SCROLL, cv2.FILLED)
        elif current_mode == SCROLL_DOWN:
            cv2.circle(img, (x1, y1), 15, COLOR_SCROLL, cv2.FILLED)
        elif current_mode == DRAG:
            cv2.circle(img, (x1, y1), 20, COLOR_DRAG, cv2.FILLED)

    # Ejecución de clic izquierdo (Temporizador rápido para permitir doble clic)
    if current_mode == LEFT_CLICK:
        if current_time - last_left_click_time > LEFT_CLICK_DELAY:
            mouse.click(Button.left, 1)
            last_left_click_time = current_time
            click_effects.append({
                'x': int(x1), 'y': int(y1), 'start_time': current_time,
                'color': COLOR_CLICK, 'max_radius': CLICK_EFFECT_MAX_RADIUS
            })

    # Ejecución de clic derecho (Gatillo de un solo disparo)
    if current_mode == RIGHT_CLICK:
        if right_click_ready:
            mouse.click(Button.right, 1)
            right_click_ready = False # Descarga el gatillo
            click_effects.append({
                'x': int(x1), 'y': int(y1), 'start_time': current_time,
                'color': COLOR_RIGHT, 'max_radius': CLICK_EFFECT_MAX_RADIUS
            })
    elif current_mode != RIGHT_CLICK:
        right_click_ready = True  # Recarga el gatillo al bajar el dedo medio

    if current_mode == DRAG and not dragging:
        mouse.press(Button.left)
        dragging = True
    elif current_mode != DRAG and dragging:
        mouse.release(Button.left)
        dragging = False

    if current_mode == SCROLL_UP:
        mouse.scroll(0, 2 * sensitivity)
    if current_mode == SCROLL_DOWN:
        mouse.scroll(0, -2 * sensitivity)

    for effect in list(click_effects):
        elapsed = current_time - effect['start_time']
        progress = min(1.0, elapsed / CLICK_EFFECT_DURATION)
        radius = int(progress * effect['max_radius'])
        opacity = 1.0 - progress
        
        overlay = img.copy()
        color = effect['color']
        alpha_color = tuple(int(c * opacity) for c in color)

        cv2.circle(overlay, (effect['x'], effect['y']), radius, alpha_color, 3)
        cv2.addWeighted(overlay, opacity, img, 1 - opacity, 0, img)

        if progress >= 1.0:
            click_effects.remove(effect)

    if gesture_text:
        cv2.putText(img, gesture_text, (10, 120),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    sens_text = f"Sens: {sensitivity:.1f}x"
    cv2.putText(img, sens_text, (w_cam - 200, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, COLOR_SENS, 2)

    bar_width = int(150 * (sensitivity - MIN_SENSITIVITY) / (MAX_SENSITIVITY - MIN_SENSITIVITY))
    cv2.rectangle(img, (w_cam - 200, 70), (w_cam - 200 + bar_width, 85), COLOR_SENS, cv2.FILLED)
    cv2.rectangle(img, (w_cam - 200, 70), (w_cam - 50, 85), COLOR_SENS, 2)

    fps = 1 / (current_time - prev_time) if current_time - prev_time > 0 else 0
    prev_time = current_time
    cv2.putText(img, f'FPS: {int(fps)}', (10, 50),
                cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)

    cv2.imshow("Virtual Mouse", img)
    
    # Cerrar con el teclado (letra q) o con el gesto del meñique
    if cv2.waitKey(1) & 0xFF == ord('q') or current_mode == EXIT:
        print("Cerrando Airflow...")
        break

if dragging:
    mouse.release(Button.left)
cap.release()
cv2.destroyAllWindows()