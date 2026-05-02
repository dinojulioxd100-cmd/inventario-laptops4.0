[app]
title = Inventario Laptops Hans
package.name = inventariolaptopshans
package.domain = org.multiservicioshans
source.dir = .
source.include_exts = py,jpg,jpeg,png,kv
version = 1.0.0
requirements = python3,kivy
orientation = portrait
fullscreen = 0

# La app funciona sin internet. Estos permisos son solo para elegir fotos y guardar PDF/CSV.
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 23
android.archs = arm64-v8a
p4a.bootstrap = sdl2
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
