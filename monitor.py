"""
monitor.py: visor flotante de recursos para Raspberry Pi

Este módulo crea una pequeña ventana de Tkinter sin bordes que
muestra continuamente el uso de CPU, memoria RAM, disco,
velocidad de red (descarga y subida) y la temperatura de la CPU.
La ventana está configurada para permanecer siempre encima de
otras ventanas y se puede arrastrar para reubicarla.

Requisitos:
  * Python 3 (Tkinter incluido en la mayoría de instalaciones)
  * psutil (ya disponible en las imágenes estándar de Debian)

Uso:
  python3 monitor.py

Para terminar el programa, cierra la ventana o presiona Ctrl+C en
la terminal. El script está pensado para ejecutarse en un entorno
gráfico (X11 o Wayland) de Raspberry Pi OS.
"""

import psutil
import tkinter as tk
import time
from typing import Tuple


def read_temperature() -> float:
    """Intenta leer la temperatura de la CPU.

    Primero utiliza psutil.sensors_temperatures() y, si no hay
    sensores disponibles, lee directamente el archivo del kernel
    en /sys/class/thermal/thermal_zone0/temp.

    Returns:
        float: temperatura en grados Celsius.
    """
    temps = {}  # type: ignore[var-annotated]
    try:
        temps = psutil.sensors_temperatures()
    except Exception:
        temps = {}
    # psutil devuelve un diccionario de listas de temperaturas. Para
    # Raspberry Pi suele estar la clave 'cpu_thermal'.
    if temps:
        if 'cpu_thermal' in temps and temps['cpu_thermal']:
            return float(temps['cpu_thermal'][0].current)
        # Si 'cpu_thermal' no existe, selecciona la primera entrada
        first_key = next(iter(temps))
        first_entry = temps[first_key]
        if first_entry:
            return float(first_entry[0].current)
    # Fallback: leer del archivo del sistema
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            raw = f.read().strip()
            return float(raw) / 1000.0
    except FileNotFoundError:
        # No disponible; devuelve NaN
        return float('nan')


class FloatingMonitor:
    """Monitor de recursos en una ventana flotante."""

    def __init__(self) -> None:
        self.root = tk.Tk()
        # Configurar apariencia de la ventana
        self.root.title('Monitor RPi')
        # Eliminar la barra de título y bordes para crear nuestros propios controles
        self.root.overrideredirect(True)
        # Mantener la ventana siempre encima
        self.root.wm_attributes('-topmost', True)
        # Fondo oscuro
        self.root.configure(bg='black')
        # Posición inicial
        self.root.geometry('+20+20')
        # Bandera para maximizar/restaurar
        self._is_maximized = False
        self._previous_geometry = None
        # Crear barra de título personalizada con botones de control
        self._create_title_bar()
        # Permitir arrastrar la ventana (en la barra de título)
        self._add_dragging()

        # Variables para la velocidad de red
        io = psutil.net_io_counters()
        self.prev_recv = io.bytes_recv
        self.prev_sent = io.bytes_sent

        # Crear etiquetas con fuente monoespaciada para mejor alineación
        font = ('DejaVu Sans Mono', 10)
        fg_color = 'white'
        self.cpu_label = tk.Label(self.root, font=font, fg=fg_color, bg='black')
        self.mem_label = tk.Label(self.root, font=font, fg=fg_color, bg='black')
        self.disk_label = tk.Label(self.root, font=font, fg=fg_color, bg='black')
        self.net_label = tk.Label(self.root, font=font, fg=fg_color, bg='black')
        self.temp_label = tk.Label(self.root, font=font, fg=fg_color, bg='black')
        # Empaquetar etiquetas
        for label in (
            self.cpu_label,
            self.mem_label,
            self.disk_label,
            self.net_label,
            self.temp_label,
        ):
            label.pack(anchor='w')

        # Iniciar actualización periódica
        self.update_stats()

    def _add_dragging(self) -> None:
        """Permite arrastrar la ventana con el ratón sobre la barra de título."""
        def start_move(event):
            # Guardar la posición inicial del ratón
            self.root._drag_start_x = event.x
            self.root._drag_start_y = event.y

        def do_move(event):
            # Calcular el desplazamiento relativo
            deltax = event.x - self.root._drag_start_x
            deltay = event.y - self.root._drag_start_y
            x = self.root.winfo_x() + deltax
            y = self.root.winfo_y() + deltay
            self.root.geometry(f"+{x}+{y}")

        # Asociar los eventos sólo a la barra de título (para no interferir con botones)
        self.title_bar.bind('<Button-1>', start_move)
        self.title_bar.bind('<B1-Motion>', do_move)

    def _create_title_bar(self) -> None:
        """Crea una barra de título personalizada con botones de control."""
        # Marco que servirá como barra de título
        bar_bg = 'gray20'
        self.title_bar = tk.Frame(self.root, bg=bar_bg)
        self.title_bar.pack(fill='x', side='top')
        # Etiqueta de título (puede servir para arrastrar)
        title = tk.Label(
            self.title_bar,
            text=' Monitor RPi ',
            fg='white',
            bg=bar_bg,
            font=('DejaVu Sans', 9, 'bold')
        )
        title.pack(side='left', padx=(4, 0))
        # Botones de control
        btn_fg = 'white'
        btn_bg = bar_bg
        # Minimizar
        btn_min = tk.Button(
            self.title_bar,
            text='–',
            command=self._minimize_window,
            fg=btn_fg,
            bg=btn_bg,
            relief='flat',
            padx=4,
            pady=0,
            font=('DejaVu Sans', 9)
        )
        # Maximizar/restaurar
        btn_max = tk.Button(
            self.title_bar,
            text='□',
            command=self._toggle_maximize,
            fg=btn_fg,
            bg=btn_bg,
            relief='flat',
            padx=4,
            pady=0,
            font=('DejaVu Sans', 9)
        )
        # Cerrar
        btn_close = tk.Button(
            self.title_bar,
            text='×',
            command=self.root.destroy,
            fg=btn_fg,
            bg=btn_bg,
            relief='flat',
            padx=4,
            pady=0,
            font=('DejaVu Sans', 9)
        )
        # Empaquetar botones a la derecha
        for btn in (btn_close, btn_max, btn_min):
            btn.pack(side='right', padx=(0, 2))

    def _minimize_window(self) -> None:
        """Minimiza la ventana."""
        self.root.iconify()

    def _toggle_maximize(self) -> None:
        """Alterna entre tamaño maximizado y tamaño original."""
        if not self._is_maximized:
            # Guardar geometría actual
            self._previous_geometry = self.root.geometry()
            # Obtener dimensiones de pantalla
            width = self.root.winfo_screenwidth()
            height = self.root.winfo_screenheight()
            # Ajustar al tamaño de la pantalla
            self.root.geometry(f"{width}x{height}+0+0")
            self._is_maximized = True
        else:
            # Restaurar a la geometría anterior
            if self._previous_geometry:
                self.root.geometry(self._previous_geometry)
            self._is_maximized = False

    def update_stats(self) -> None:
        """Recoge las estadísticas y actualiza las etiquetas."""
        # CPU (interval=None para evitar pausa en Tkinter)
        cpu_percent = psutil.cpu_percent(interval=None)
        # Memoria
        mem = psutil.virtual_memory()
        mem_percent = mem.percent
        # Disco
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        # Red: calcular velocidad en KB/s
        io = psutil.net_io_counters()
        down_speed = (io.bytes_recv - self.prev_recv) / 1024.0
        up_speed = (io.bytes_sent - self.prev_sent) / 1024.0
        # Actualizar valores previos
        self.prev_recv = io.bytes_recv
        self.prev_sent = io.bytes_sent
        # Temperatura
        temp_c = read_temperature()

        # Actualizar etiquetas
        self.cpu_label.config(text=f"CPU:  {cpu_percent:5.1f}%")
        self.mem_label.config(text=f"RAM:  {mem_percent:5.1f}%")
        self.disk_label.config(text=f"DISK: {disk_percent:5.1f}%")
        self.net_label.config(
            text=f"NET:  ↓{down_speed:6.1f} KB/s  ↑{up_speed:6.1f} KB/s"
        )
        # Mostrar la temperatura con un valor 'N/A' si es NaN
        temp_text = f"{temp_c:5.1f}°C" if not isinstance(temp_c, float) or not (temp_c != temp_c) else "N/A"
        self.temp_label.config(text=f"TEMP: {temp_text}")

        # Programar siguiente actualización tras 1000 ms
        self.root.after(1000, self.update_stats)

    def run(self) -> None:
        """Ejecuta el bucle principal de la interfaz."""
        self.root.mainloop()


def main() -> None:
    monitor = FloatingMonitor()
    monitor.run()


if __name__ == '__main__':
    main()