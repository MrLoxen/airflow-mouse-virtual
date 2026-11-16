# Airflow - Mouse virtual mediante visión por computadora

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)
![MediaPipe](https://img.shields.io/badge/MediaPipe-00A67E?style=for-the-badge&logo=mediapipe&logoColor=white)

Airflow es un sistema de interacción humano-computadora que permite controlar el cursor y ejecutar acciones del mouse en el sistema operativo utilizando únicamente gestos de la mano capturados a través de una cámara web en tiempo real. 

El proyecto destaca por su sistema de estabilización anti-parpadeo (debounce), el cual garantiza transiciones fluidas entre comandos, y una calibración trigonométrica que vuelve a la inteligencia artificial inmune a la rotación de la mano.


## Características y gestos
El sistema reconoce la orientación de la mano y mapea gestos precisos y exclusivos a funciones del sistema operativo con suavizado de movimiento y efectos visuales:

*   👆 **Movimiento del cursor:** solo el dedo índice extendido (los demás cerrados).
*   🤏 **Clic y doble clic izquierdo:** juntar la punta del pulgar y el índice en forma de pinza. (Se habilita el doble clic si se mantiene presionado).
*   ✌️ **Clic derecho instantáneo:** levantar el dedo índice y el dedo medio. Cuenta con un sistema de "gatillo" para ejecutar la acción una sola vez sin repetir clics accidentales.
*   ✊ **Arrastrar y soltar:** puño completamente cerrado.
*   🖐️ **Scroll arriba:** todos los dedos extendidos.
*   ✋ **Scroll abajo:** cuatro dedos extendidos (pulgar oculto).
*   ❌ **Salir del programa:** levantar únicamente el dedo meñique.

## Instalación y uso

1. **Clona este repositorio:**
   ```bash
   git clone [https://github.com/MrLoxen/airflow-mouse-virtual.git](https://github.com/MrLoxen/airflow-mouse-virtual.git)
   cd airflow-mouse-virtual
   ```

2. **Crea un entorno virtual (recomendado):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows usa: venv\Scripts\activate
   ```

3. **Instala las dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

4. **Ejecuta el programa principal:**
    ```bash
    python MouseVirtual.py
    ```

## Arquitectura del código
Hand_TrackingMin.py: módulo central orientado a objetos que envuelve la solución de MediaPipe para detectar los puntos de referencia de la mano, calculando distancias relativas desde la muñeca para otorgar invulnerabilidad a la rotación.

MouseVirtual.py: script principal que procesa la lógica del negocio, mapea las coordenadas de la cámara a la resolución nativa de la pantalla mediante tkinter, aplica el filtro de memoria (debounce) y ejecuta las acciones del sistema con pynput.

## Autor
Manuel Fereira
Desarrollador Full-stack y estudiante de ingeniería en sistemas.
