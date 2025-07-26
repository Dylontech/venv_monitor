"""
monitor_graph.py: ventana de gráficas en tiempo real para Raspberry Pi

Este script abre una ventana independiente con gráficas en tiempo real
para el uso de CPU, memoria, disco, velocidades de red y temperatura
de la CPU. También mantiene un historial de la temperatura y muestra
los valores máximo y mínimo observados durante la ejecución.

Se apoya en Tkinter para la interfaz de usuario y en matplotlib
para las gráficas embebidas en la ventana.

Requisitos:
  * Python 3 con soporte para Tkinter
  * psutil (para obtener estadísticas del sistema)
  * matplotlib

Uso:
  python3 monitor_graph.py

Nota: este script está pensado para ejecutarse en un entorno gráfico
de Raspberry Pi OS u otra distribución de Linux con soporte Tk.
"""

import psutil
import tkinter as tk
from typing import List, Tuple
import matplotlib

matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class GraphMonitor:
    """Ventana con gráficas en tiempo real."""

    def __init__(self, max_points: int = 60) -> None:
        # Número de muestras a mantener en el historial
        self.max_points = max_points
        # Inicializar datos
        self.cpu_data: List[float] = []
        self.mem_data: List[float] = []
        self.disk_data: List[float] = []
        self.net_down_data: List[float] = []
        self.net_up_data: List[float] = []
        self.temp_data: List[float] = []
        self.prev_recv = psutil.net_io_counters().bytes_recv
        self.prev_sent = psutil.net_io_counters().bytes_sent
        self.max_temp = float('-inf')
        self.min_temp = float('inf')

        # Configurar ventana
        self.root = tk.Tk()
        self.root.title('Monitor RPi - Gráficas')
        # Crear figura con subgráficas
        self.fig = Figure(figsize=(6, 8), dpi=100)
        # Ejes
        gs = self.fig.add_gridspec(5, 1)
        self.ax_cpu = self.fig.add_subplot(gs[0, 0])
        self.ax_mem = self.fig.add_subplot(gs[1, 0])
        self.ax_disk = self.fig.add_subplot(gs[2, 0])
        self.ax_net = self.fig.add_subplot(gs[3, 0])
        self.ax_temp = self.fig.add_subplot(gs[4, 0])
        self.ax_cpu.set_title('Uso CPU (%)')
        self.ax_mem.set_title('Uso Memoria (%)')
        self.ax_disk.set_title('Uso Disco (%)')
        self.ax_net.set_title('Velocidad Red (KB/s)')
        self.ax_temp.set_title('Temperatura CPU (°C)')
        # Crear líneas
        (self.cpu_line,) = self.ax_cpu.plot([], [], color='tab:red')
        (self.mem_line,) = self.ax_mem.plot([], [], color='tab:blue')
        (self.disk_line,) = self.ax_disk.plot([], [], color='tab:green')
        (self.net_down_line,) = self.ax_net.plot([], [], label='Descarga', color='tab:cyan')
        (self.net_up_line,) = self.ax_net.plot([], [], label='Subida', color='tab:orange')
        (self.temp_line,) = self.ax_temp.plot([], [], color='tab:purple')
        self.ax_net.legend(loc='upper right', fontsize='x-small')
        # Ajustar límites iniciales
        for ax in (self.ax_cpu, self.ax_mem, self.ax_disk):
            ax.set_ylim(0, 100)
        self.ax_net.set_ylim(0, 100)  # valor inicial, ajustado dinámicamente
        self.ax_temp.set_ylim(0, 100)
        # Sin márgenes izquierdos innecesarios
        for ax in (self.ax_cpu, self.ax_mem, self.ax_disk, self.ax_net, self.ax_temp):
            ax.set_xlim(0, self.max_points)
            ax.tick_params(labelsize=8)
        # Etiqueta para valores máx/min de temperatura
        self.temp_stats_label = tk.Label(self.root, font=('DejaVu Sans', 9))
        self.temp_stats_label.pack(side='bottom', pady=2)
        # Canvas de matplotlib
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        # Iniciar actualización
        self.update_graphs()

    def update_graphs(self) -> None:
        """Actualiza los datos y las gráficas."""
        # Recoger nuevos datos
        self.cpu_data.append(psutil.cpu_percent(interval=None))
        self.mem_data.append(psutil.virtual_memory().percent)
        self.disk_data.append(psutil.disk_usage('/').percent)
        # Net speed
        io = psutil.net_io_counters()
        down_speed = (io.bytes_recv - self.prev_recv) / 1024.0
        up_speed = (io.bytes_sent - self.prev_sent) / 1024.0
        self.prev_recv, self.prev_sent = io.bytes_recv, io.bytes_sent
        self.net_down_data.append(down_speed)
        self.net_up_data.append(up_speed)
        # Temp
        temp = self._read_temp()
        self.temp_data.append(temp)
        # Actualizar máximos y mínimos de temperatura
        if temp > self.max_temp:
            self.max_temp = temp
        if temp < self.min_temp:
            self.min_temp = temp
        # Ajustar longitud de listas
        for lst in (self.cpu_data, self.mem_data, self.disk_data, self.net_down_data, self.net_up_data, self.temp_data):
            if len(lst) > self.max_points:
                lst.pop(0)
        x_vals = list(range(len(self.cpu_data)))
        # Actualizar líneas
        self.cpu_line.set_data(x_vals, self.cpu_data)
        self.mem_line.set_data(x_vals, self.mem_data)
        self.disk_line.set_data(x_vals, self.disk_data)
        # Red
        self.net_down_line.set_data(x_vals, self.net_down_data)
        self.net_up_line.set_data(x_vals, self.net_up_data)
        # Ajustar límites Y de red dinámicamente
        max_net = max(self.net_down_data + self.net_up_data + [1])
        self.ax_net.set_ylim(0, max(max_net * 1.2, 10))
        # Temperatura
        self.temp_line.set_data(x_vals, self.temp_data)
        max_temp_data = max(self.temp_data)
        min_temp_data = min(self.temp_data)
        # Ajustar límites Y de temperatura con margen
        self.ax_temp.set_ylim(min(self.temp_data) - 5, max(self.temp_data) + 5)
        # Actualizar estadísticas de temperatura
        self.temp_stats_label.config(
            text=f"Temp actual: {temp:.1f}°C  •  Máx: {self.max_temp:.1f}°C  •  Mín: {self.min_temp:.1f}°C"
        )
        # Ajustar ejes X para todas las gráficas
        for ax in (self.ax_cpu, self.ax_mem, self.ax_disk, self.ax_net, self.ax_temp):
            ax.set_xlim(0, self.max_points)
        # Redibujar
        self.canvas.draw()
        # Programar siguiente actualización
        self.root.after(1000, self.update_graphs)

    def _read_temp(self) -> float:
        """Obtiene la temperatura de la CPU en °C."""
        # Usar psutil.sensors_temperatures si está disponible
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                if 'cpu_thermal' in temps and temps['cpu_thermal']:
                    return float(temps['cpu_thermal'][0].current)
                first_key = next(iter(temps))
                if temps[first_key]:
                    return float(temps[first_key][0].current)
        except Exception:
            pass
        # Fallback: leer archivo del sistema
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                return float(f.read().strip()) / 1000.0
        except Exception:
            return float('nan')

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    monitor = GraphMonitor(max_points=60)
    monitor.run()


if __name__ == '__main__':
    main()