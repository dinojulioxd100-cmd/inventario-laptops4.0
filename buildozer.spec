[app]
# Nombre de la aplicación
title = Inventario Laptops
# Nombre del paquete
package.name = inventario_laptops
# Dominio del paquete
package.domain = org.multiservicios.hans
# Agregar la versión de la aplicación
version = 1.0.0  # Esta es la versión que puedes cambiar según sea necesario
# Extensiones a incluir en el APK
source.include_exts = py, kv, png, jpg, jpeg

# Excluir archivos de ciertas extensiones del APK
source.exclude_exts = spec

# Herramienta de bootstrap a usar (SDL2 para apps móviles)
p4a.bootstrap = sdl2

# Directorio donde está el código fuente
source.dir = .

# Permisos necesarios para la app (si los hay)
android.permissions = 

# Versión mínima del SDK de Android
android.sdk = 30
# Versión mínima de la API de Android
android.api = 30
# Versión del NDK
android.ndk = r21e
# Arquitectura
android.arch = arm64-v8a

# Configuración de la entrada de la app
android.entrypoint = main.py

# Bibliotecas adicionales necesarias (si las hay)
android.libraries = 

# Ruta del AndroidManifest.xml si lo personalizas
# android.manifest = ./AndroidManifest.xml

# Versión mínima del API de Android
android.minapi = 21

# Paquete de la app (nombre del paquete)
android.package = org.multiservicios.hans.inventario_laptops

# Hacer un APK de depuración
android.debug = True

# Plataforma de destino
buildozer.target = android

# Modo de compilación
buildozer.build = debug

# Ruta al icono de la aplicación
android.icon = icon.png

# Hacer la app a pantalla completa (sin barra de estado)
android.white = False

# Versión de la aplicación
android.app_version = 1.0

# Versión de Python a utilizar
python.version = 3.8

# Paquetes adicionales de Python a incluir
# python.include_packages = numpy, kivy

# Ruta al archivo AndroidManifest.xml, si lo necesitas personalizar
# android.manifest = ./AndroidManifest.xml
