# Inventario de Laptops Hans - Versión Android

Esta es una versión Android real creada con Kivy. No es la versión Windows/Tkinter.
Está preparada para compilarse como APK con GitHub Actions.

## Funciones incluidas

- Registro de laptops.
- Foto del equipo por ruta/selector de archivo.
- Marca, modelo, RAM, disco, video, procesador, generación, fechas, estado, cliente y accesorios.
- Costos: compra, cargador, reparación, componentes y precio de venta.
- Descuento automático de mouse: S/ 6.00 cuando se marca Mouse.
- Edición de registros.
- Eliminación de registros.
- Búsqueda por texto.
- Filtro por estado.
- Búsqueda por fecha de venta desde/hasta.
- Dashboard con total de equipos, inventario, vendidos, inversión total, ventas totales y ganancia neta.
- Exportación a Excel compatible mediante archivo CSV.
- Generación de boleta PDF offline.
- Vista previa de boleta antes de generar.
- Términos y condiciones actualizados.

## Cómo subirlo a GitHub de la forma más fácil

1. Entra a GitHub.
2. Crea un repositorio nuevo, por ejemplo: `inventario-laptops-hans-android`.
3. Entra al repositorio.
4. Presiona **Add file** > **Upload files**.
5. Sube todos los archivos y carpetas de este proyecto:
   - `main.py`
   - `buildozer.spec`
   - `logo_multiservicios_hans.jpg`
   - la carpeta `.github`
6. Presiona **Commit changes**.

## Cómo generar el APK en GitHub

1. En tu repositorio, entra a la pestaña **Actions**.
2. Abre el workflow llamado **Build Android APK**.
3. Presiona **Run workflow**.
4. Espera a que termine.
5. En la ejecución finalizada, baja hasta **Artifacts**.
6. Descarga **Inventario-Laptops-Hans-APK**.
7. Dentro estará el archivo `.apk` para instalar en tu celular.

## Importante

- La app no necesita internet para funcionar.
- La base de datos se guarda localmente en el celular.
- Las boletas y exportaciones se intentan guardar en:
  `/storage/emulated/0/Download/MultiserviciosHans`
- Si Android no permite guardar ahí, se guardan en la carpeta interna de la app.
- En Android moderno, puede ser necesario dar permiso de almacenamiento manualmente desde Ajustes > Aplicaciones.
