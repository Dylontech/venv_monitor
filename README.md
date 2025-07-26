Monitor de Recursos para Raspberry Pi
Este proyecto proporciona un visor “flotante” que muestra en tiempo real
el uso de CPU, memoria RAM, espacio en disco, velocidad de red y la
temperatura del procesador en una Raspberry Pi 4 (o cualquier otra
máquina Linux con Python y Tkinter). La interfaz se presenta en una
ventana sin bordes y siempre visible, con controles para minimizar,
maximizar/restaurar y cerrar.

Funcionalidades
CPU : porcentaje de utilización actualizado cada segundo.

Memoria : porcentaje de uso de la memoria RAM.

Disco : porcentaje de uso del disco principal (/).

Red : velocidad de descarga y subida (KB/s) calculada a partir de
la diferencia de bytes recibidos/enviados desde la última
actualización.

Temperatura : lectura de la temperatura de la CPU en °C usando
psutil.sensors_temperatures() o, en su defecto, el archivo
/sys/class/thermal/thermal_zone0/temp.

Ventana flotante : la ventana carece de barra de título del
sistema y permanece al frente (topmost). Cuenta con barra de título
personalizada con botones para minimizar, maximizar/restaurar y
cerrar.

Arrastrable : puedes moverla por la pantalla arrastrando la
barra superior.

Requisitos
Python 3 instalado en el sistema.

Biblioteca psutil (ya suele estar instalada en las imágenes
oficiales de Raspberry Pi OS). Para otras distribuciones, se puede
instalar mediante pip install psutil en un entorno virtual.

Tkinter (python3-tk). Suele venir preinstalado; de lo contrario,
instálalo con sudo apt install python3-tk.

Instalación
Clona este repositorio o copia los archivos en tu Raspberry Pi:

bash
Copy
Edit
git clone <URL-del-repositorio> monitor-rpi
cd monitor-rpi/monitor
(Opcional) crea un entorno virtual para aislar dependencias:

bash
Copy
Edit
python3 -m venv venv_monitor
source venv_monitor/bin/activate
pip install psutil
Si ya tienes psutil en el sistema, el entorno virtual no es
imprescindible.

Asegúrate de que Tkinter está disponible. En Raspberry Pi OS se
instala con:

bash
Copy
Edit
sudo apt update
sudo apt install python3-tk
Ejecución
Para iniciar el monitor, ejecuta el script monitor.py con Python 3:

bash
Copy
Edit
cd monitor  # carpeta donde reside monitor.py
python3 monitor.py
Si estás usando un entorno virtual, asegúrate de activarlo antes.

Una vez lanzado, aparecerá una pequeña ventana oscura que muestra los
valores actualizados cada segundo. Los controles de la barra superior
permiten minimizar (–), maximizar/restaurar (□) y cerrar (×) la
aplicación. También puedes arrastrar la ventana desde la barra para
colocarla en la posición que prefieras.

Autoinicio opcional
Si deseas que el monitor se inicie automáticamente al arrancar la
sesión gráfica, crea un archivo .desktop en
~/.config/autostart/ con contenido similar al siguiente:

ini
Copy
Edit
[Desktop Entry]
Type=Application
Name=Monitor RPi
Exec=/ruta/a/tu/python /ruta/al/proyecto/monitor/monitor.py
X-GNOME-Autostart-enabled=true
Terminal=false
Reemplaza /ruta/a/tu/python con el intérprete de tu entorno virtual
si corresponde, y /ruta/al/proyecto/monitor/monitor.py con la ruta
absoluta al script.

Licencia
Puedes utilizar y modificar este proyecto libremente para tus
necesidades personales. Si encuentras mejoras o problemas,
considera contribuir con un pull request o abrir un issue.