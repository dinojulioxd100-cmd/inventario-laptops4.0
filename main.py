import csv
import os
import sqlite3
import textwrap
from datetime import datetime
from pathlib import Path

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.utils import platform

EMPRESA = "MULTISERVICIOS HANS"
TELEFONO = "927872051"
MOUSE_COST = 6.0
LOGO_FILE = "logo_multiservicios_hans.jpg"

RAM_TIPOS = ["DDR3", "DDR4", "DDR5"]
DISCO_TIPOS = ["HDD", "SSD", "M.2"]
ESTADOS = ["Vendido", "En inventario", "Incompleto"]
ACCESORIOS = ["Funda", "Cargador", "Mouse"]

TERMS = [
    "Garantía de 3 meses desde la fecha de venta indicada en la boleta.",
    "El equipo se entrega en el estado en que se encuentra al momento de la venta, habiendo sido probado previamente.",
    "Se realiza test de funcionamiento: teclado, parlantes, micrófono, cámara y funcionamiento general del equipo.",
    "El cliente declara haber revisado y estar conforme con el estado físico y funcional del equipo al momento de la compra.",
    "La garantía cubre únicamente fallas internas de la placa madre o componentes internos, siempre que no sean ocasionadas por mal uso, manipulación indebida o daño físico.",
    "No cubre daños por caídas, golpes, pantalla rota, bisagras, carcasa, teclas, conectores forzados ni daño físico en general.",
    "No cubre daños por líquidos, humedad, quemaduras, cortocircuitos o uso de cargadores no compatibles.",
    "No cubre batería ni accesorios, considerados de desgaste.",
    "No cubre problemas de software, virus, sistema operativo, programas, formateo o pérdida de información.",
    "Abrir el equipo, retirar sellos o manipulación por terceros anula automáticamente la garantía.",
    "No hay devoluciones ni cambios bajo ningún motivo una vez realizada la compra.",
    "No hay devoluciones por incompatibilidad con juegos, programas o aplicaciones, ni por expectativas de rendimiento.",
    "Para cualquier garantía es obligatorio presentar la boleta y el equipo para evaluación técnica.",
]


def to_float(value):
    try:
        return float(str(value or "0").replace("S/", "").replace(",", ".").strip() or 0)
    except Exception:
        return 0.0


def money(value):
    return f"S/ {to_float(value):,.2f}"


def today():
    return datetime.now().strftime("%Y-%m-%d")


def safe_text(value):
    return str(value or "").strip()


def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)
    return path


def public_output_dir():
    # Primero intenta guardar en Descargas; si Android no permite, usa carpeta interna de la app.
    download_dir = "/storage/emulated/0/Download/MultiserviciosHans"
    try:
        ensure_dir(download_dir)
        test_file = Path(download_dir) / ".test_write"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink(missing_ok=True)
        return download_dir
    except Exception:
        return App.get_running_app().user_data_dir


def latin_pdf(text):
    text = str(text or "")
    return text.encode("latin-1", "replace").decode("latin-1")


def pdf_escape(text):
    text = latin_pdf(text)
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def jpeg_size(path):
    # Lee dimensiones de un JPG sin usar Pillow.
    try:
        with open(path, "rb") as f:
            if f.read(2) != b"\xff\xd8":
                return None
            while True:
                marker_start = f.read(1)
                if marker_start != b"\xff":
                    return None
                marker = f.read(1)
                while marker == b"\xff":
                    marker = f.read(1)
                if marker in [b"\xc0", b"\xc1", b"\xc2", b"\xc3", b"\xc5", b"\xc6", b"\xc7", b"\xc9", b"\xca", b"\xcb", b"\xcd", b"\xce", b"\xcf"]:
                    f.read(3)
                    h = int.from_bytes(f.read(2), "big")
                    w = int.from_bytes(f.read(2), "big")
                    return w, h
                size = int.from_bytes(f.read(2), "big")
                f.seek(size - 2, 1)
    except Exception:
        return None


class SimplePDF:
    """Generador PDF mínimo, sin reportlab. Funciona offline en Android."""
    def __init__(self, path, logo_path=None):
        self.path = path
        self.logo_path = logo_path if logo_path and os.path.exists(logo_path) else None
        self.commands = []

    def color(self, r, g, b, stroke=False):
        op = "RG" if stroke else "rg"
        self.commands.append(f"{r:.3f} {g:.3f} {b:.3f} {op}")

    def rect(self, x, y, w, h, fill=False, stroke=True):
        if fill and stroke:
            op = "B"
        elif fill:
            op = "f"
        else:
            op = "S"
        self.commands.append(f"{x:.2f} {y:.2f} {w:.2f} {h:.2f} re {op}")

    def text(self, x, y, text, size=9, bold=False):
        font = "/F2" if bold else "/F1"
        self.commands.append(f"BT {font} {size} Tf {x:.2f} {y:.2f} Td ({pdf_escape(text)}) Tj ET")

    def line_text(self, x, y, text, size=8, bold=False, max_chars=86, leading=10):
        current = y
        for part in textwrap.wrap(str(text or ""), width=max_chars):
            self.text(x, current, part, size=size, bold=bold)
            current -= leading
        return current

    def logo(self, x, y, w, h):
        if self.logo_path:
            self.commands.append(f"q {w:.2f} 0 0 {h:.2f} {x:.2f} {y:.2f} cm /Im1 Do Q")

    def build(self):
        # A4 portrait: 595 x 842 puntos
        objects = []
        font1 = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
        font2 = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>"
        objects.append(font1)  # 1
        objects.append(font2)  # 2

        resources = b"<< /Font << /F1 1 0 R /F2 2 0 R >>"
        image_obj_index = None
        if self.logo_path:
            img_size = jpeg_size(self.logo_path)
            if img_size:
                w, h = img_size
                data = Path(self.logo_path).read_bytes()
                img_obj = (
                    f"<< /Type /XObject /Subtype /Image /Width {w} /Height {h} "
                    f"/ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length {len(data)} >>\nstream\n"
                ).encode("latin-1") + data + b"\nendstream"
                objects.append(img_obj)  # 3 si existe
                image_obj_index = len(objects)
                resources = f"<< /Font << /F1 1 0 R /F2 2 0 R >> /XObject << /Im1 {image_obj_index} 0 R >> >>".encode("latin-1")

        content = "\n".join(self.commands).encode("latin-1", "replace")
        content_obj = f"<< /Length {len(content)} >>\nstream\n".encode("latin-1") + content + b"\nendstream"
        objects.append(content_obj)
        content_index = len(objects)

        page_obj = (
            f"<< /Type /Page /Parent {content_index + 2} 0 R /MediaBox [0 0 595 842] "
            f"/Resources {resources.decode('latin-1')} /Contents {content_index} 0 R >>"
        ).encode("latin-1")
        objects.append(page_obj)
        page_index = len(objects)

        pages_obj = f"<< /Type /Pages /Kids [{page_index} 0 R] /Count 1 >>".encode("latin-1")
        objects.append(pages_obj)
        pages_index = len(objects)

        catalog_obj = f"<< /Type /Catalog /Pages {pages_index} 0 R >>".encode("latin-1")
        objects.append(catalog_obj)
        catalog_index = len(objects)

        out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = []
        for i, obj in enumerate(objects, start=1):
            offsets.append(len(out))
            out.extend(f"{i} 0 obj\n".encode("latin-1"))
            out.extend(obj)
            out.extend(b"\nendobj\n")
        xref = len(out)
        out.extend(f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode("latin-1"))
        for offset in offsets:
            out.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))
        out.extend(f"trailer\n<< /Size {len(objects)+1} /Root {catalog_index} 0 R >>\nstartxref\n{xref}\n%%EOF".encode("latin-1"))
        Path(self.path).write_bytes(out)


class InventoryDatabase:
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_db()

    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        ensure_dir(Path(self.db_path).parent)
        with self.connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS laptops (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    foto_path TEXT,
                    marca TEXT NOT NULL,
                    modelo TEXT NOT NULL,
                    ram_gb TEXT,
                    ram_tipo TEXT,
                    disco_tamano TEXT,
                    disco_tipo TEXT,
                    video_gb TEXT,
                    procesador TEXT,
                    generacion TEXT,
                    fecha_compra TEXT,
                    fecha_venta TEXT,
                    estado TEXT,
                    cliente TEXT,
                    accesorios TEXT,
                    precio_compra REAL DEFAULT 0,
                    precio_cargador REAL DEFAULT 0,
                    costos_reparacion REAL DEFAULT 0,
                    costos_componentes REAL DEFAULT 0,
                    precio_venta REAL DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS boletas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero TEXT UNIQUE,
                    laptop_id INTEGER,
                    fecha_emision TEXT,
                    total REAL,
                    pdf_path TEXT
                )
            """)
            conn.commit()

    def save(self, data, laptop_id=None):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        keys = [
            "foto_path", "marca", "modelo", "ram_gb", "ram_tipo", "disco_tamano", "disco_tipo", "video_gb",
            "procesador", "generacion", "fecha_compra", "fecha_venta", "estado", "cliente", "accesorios",
            "precio_compra", "precio_cargador", "costos_reparacion", "costos_componentes", "precio_venta"
        ]
        values = [data.get(k) for k in keys]
        with self.connect() as conn:
            if laptop_id:
                set_clause = ", ".join([f"{k}=?" for k in keys]) + ", updated_at=?"
                conn.execute(f"UPDATE laptops SET {set_clause} WHERE id=?", values + [now, laptop_id])
                conn.commit()
                return laptop_id
            cur = conn.execute(
                f"INSERT INTO laptops ({', '.join(keys)}, created_at, updated_at) VALUES ({', '.join(['?']*len(keys))}, ?, ?)",
                values + [now, now]
            )
            conn.commit()
            return cur.lastrowid

    def delete(self, laptop_id):
        with self.connect() as conn:
            conn.execute("DELETE FROM laptops WHERE id=?", (laptop_id,))
            conn.commit()

    def rows(self, query="", estado="Todos", desde="", hasta=""):
        sql = "SELECT * FROM laptops"
        cond = []
        params = []
        if query:
            cond.append("LOWER(marca || ' ' || modelo || ' ' || IFNULL(cliente,'') || ' ' || IFNULL(procesador,'') || ' ' || IFNULL(generacion,'')) LIKE ?")
            params.append(f"%{query.lower()}%")
        if estado and estado != "Todos":
            cond.append("estado=?")
            params.append(estado)
        if desde:
            cond.append("fecha_venta >= ?")
            params.append(desde)
        if hasta:
            cond.append("fecha_venta <= ?")
            params.append(hasta)
        if cond:
            sql += " WHERE " + " AND ".join(cond)
        sql += " ORDER BY id DESC"
        with self.connect() as conn:
            return conn.execute(sql, params).fetchall()

    def get(self, laptop_id):
        with self.connect() as conn:
            return conn.execute("SELECT * FROM laptops WHERE id=?", (laptop_id,)).fetchone()

    def create_receipt_row(self, laptop_id, total, pdf_path):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.connect() as conn:
            cur = conn.execute(
                "INSERT INTO boletas (laptop_id, fecha_emision, total, pdf_path) VALUES (?, ?, ?, ?)",
                (laptop_id, now, total, pdf_path)
            )
            receipt_id = cur.lastrowid
            numero = f"B001-{receipt_id:06d}"
            conn.execute("UPDATE boletas SET numero=? WHERE id=?", (numero, receipt_id))
            conn.commit()
            return numero


def costo_total(row):
    mouse = MOUSE_COST if "mouse" in safe_text(row["accesorios"]).lower() else 0.0
    return to_float(row["precio_compra"]) + to_float(row["precio_cargador"]) + to_float(row["costos_reparacion"]) + to_float(row["costos_componentes"]) + mouse


def ganancia(row):
    return to_float(row["precio_venta"]) - costo_total(row)


class HansInventoryApp(App):
    def build(self):
        self.title = "Inventario Hans"
        Window.clearcolor = (0.93, 0.95, 0.98, 1)
        self.output_dir = public_output_dir()
        self.boletas_dir = ensure_dir(Path(self.output_dir) / "boletas")
        self.exports_dir = ensure_dir(Path(self.output_dir) / "exports")
        self.logo_path = str(Path(__file__).resolve().parent / LOGO_FILE)
        self.db = InventoryDatabase(str(Path(self.user_data_dir) / "inventario_laptops.sqlite"))
        self.current_id = None
        self.last_pdf_path = None
        self.fields = {}
        self.spinners = {}
        self.checkboxes = {}
        self.list_box = None
        return self.main_ui()

    def main_ui(self):
        root = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(8))
        root.add_widget(self.header())
        root.add_widget(self.dashboard())

        scroll = ScrollView(size_hint=(1, 0.62))
        form = GridLayout(cols=1, spacing=dp(6), size_hint_y=None)
        form.bind(minimum_height=form.setter("height"))
        self.form_container = form
        self.build_form(form)
        scroll.add_widget(form)
        root.add_widget(scroll)

        root.add_widget(self.tools())
        root.add_widget(self.inventory_list())
        Clock.schedule_once(lambda *_: self.refresh(), 0.2)
        return root

    def header(self):
        box = BoxLayout(size_hint_y=None, height=dp(96), padding=dp(8), spacing=dp(8))
        box.canvas.before.clear()
        logo = Image(source=self.logo_path, size_hint_x=None, width=dp(90), allow_stretch=True, keep_ratio=True)
        box.add_widget(logo)
        title_box = BoxLayout(orientation="vertical")
        title_box.add_widget(Label(text="[b]MULTISERVICIOS HANS[/b]", markup=True, font_size="20sp", color=(0.05, 0.17, 0.31, 1), halign="left", valign="middle"))
        title_box.add_widget(Label(text="Inventario de laptops y boletas", font_size="13sp", color=(0.18, 0.25, 0.34, 1), halign="left"))
        title_box.add_widget(Label(text=f"Venta de laptops y computadoras  |  Cel. {TELEFONO}", font_size="11sp", color=(0.35, 0.42, 0.50, 1), halign="left"))
        box.add_widget(title_box)
        return box

    def dashboard_card(self, title, value):
        card = BoxLayout(orientation="vertical", padding=dp(8), size_hint_y=None, height=dp(64))
        card.add_widget(Label(text=title, font_size="10sp", color=(0.40, 0.44, 0.52, 1), halign="left"))
        label = Label(text=value, font_size="16sp", bold=True, color=(0.05, 0.17, 0.31, 1), halign="left")
        card.add_widget(label)
        return card, label

    def dashboard(self):
        grid = GridLayout(cols=2, spacing=dp(5), size_hint_y=None, height=dp(205))
        self.kpi_total_card, self.kpi_total = self.dashboard_card("TOTAL EQUIPOS", "0")
        self.kpi_inv_card, self.kpi_inv = self.dashboard_card("EN INVENTARIO", "0")
        self.kpi_sold_card, self.kpi_sold = self.dashboard_card("VENDIDOS", "0")
        self.kpi_invest_card, self.kpi_invest = self.dashboard_card("INVERSIÓN TOTAL", "S/ 0.00")
        self.kpi_sales_card, self.kpi_sales = self.dashboard_card("VENTAS TOTALES", "S/ 0.00")
        self.kpi_profit_card, self.kpi_profit = self.dashboard_card("GANANCIA NETA", "S/ 0.00")
        for c in [self.kpi_total_card, self.kpi_inv_card, self.kpi_sold_card, self.kpi_invest_card, self.kpi_sales_card, self.kpi_profit_card]:
            grid.add_widget(c)
        return grid

    def input_row(self, label, key, numeric=False):
        row = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(64))
        row.add_widget(Label(text=label, size_hint_y=None, height=dp(20), color=(0.1, 0.1, 0.1, 1), halign="left"))
        ti = TextInput(multiline=False, input_filter="float" if numeric else None, background_color=(1, 1, 1, 1), foreground_color=(0, 0, 0, 1))
        self.fields[key] = ti
        row.add_widget(ti)
        return row

    def spinner_row(self, label, key, values):
        row = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(64))
        row.add_widget(Label(text=label, size_hint_y=None, height=dp(20), color=(0.1, 0.1, 0.1, 1)))
        sp = Spinner(text=values[0], values=values, size_hint_y=None, height=dp(42))
        self.spinners[key] = sp
        row.add_widget(sp)
        return row

    def build_form(self, form):
        form.add_widget(Label(text="[b]REGISTRO / EDICIÓN[/b]", markup=True, size_hint_y=None, height=dp(34), color=(0.05, 0.17, 0.31, 1)))
        form.add_widget(self.input_row("Ruta foto del equipo", "foto_path"))
        photo_btns = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(5))
        photo_btns.add_widget(Button(text="Seleccionar foto", on_press=lambda *_: self.select_photo()))
        photo_btns.add_widget(Button(text="Limpiar foto", on_press=lambda *_: self.set_field("foto_path", "")))
        form.add_widget(photo_btns)
        form.add_widget(self.input_row("Marca *", "marca"))
        form.add_widget(self.input_row("Modelo de laptop *", "modelo"))
        form.add_widget(self.input_row("RAM GB", "ram_gb", numeric=True))
        form.add_widget(self.spinner_row("Tipo RAM", "ram_tipo", RAM_TIPOS))
        form.add_widget(self.input_row("Tamaño disco", "disco_tamano"))
        form.add_widget(self.spinner_row("Tipo disco", "disco_tipo", DISCO_TIPOS))
        form.add_widget(self.input_row("Tarjeta de video GB", "video_gb", numeric=True))
        form.add_widget(self.input_row("Procesador", "procesador"))
        form.add_widget(self.input_row("Generación", "generacion"))
        form.add_widget(self.input_row("Fecha compra AAAA-MM-DD", "fecha_compra"))
        form.add_widget(self.input_row("Fecha venta AAAA-MM-DD", "fecha_venta"))
        date_btns = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(5))
        date_btns.add_widget(Button(text="Compra hoy", on_press=lambda *_: self.set_field("fecha_compra", today())))
        date_btns.add_widget(Button(text="Venta hoy", on_press=lambda *_: self.set_field("fecha_venta", today())))
        form.add_widget(date_btns)
        form.add_widget(self.spinner_row("Estado", "estado", ESTADOS))
        form.add_widget(self.input_row("Nombre cliente", "cliente"))

        form.add_widget(Label(text="Accesorios vendidos", size_hint_y=None, height=dp(24), color=(0.1, 0.1, 0.1, 1)))
        acc_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        for acc in ACCESORIOS:
            mini = BoxLayout()
            cb = CheckBox(size_hint_x=None, width=dp(40))
            self.checkboxes[acc] = cb
            mini.add_widget(cb)
            mini.add_widget(Label(text=acc, color=(0, 0, 0, 1)))
            acc_row.add_widget(mini)
        form.add_widget(acc_row)

        form.add_widget(Label(text="[b]COSTOS Y VENTA[/b]", markup=True, size_hint_y=None, height=dp(34), color=(0.05, 0.17, 0.31, 1)))
        form.add_widget(self.input_row("Precio compra", "precio_compra", numeric=True))
        form.add_widget(self.input_row("Precio cargador", "precio_cargador", numeric=True))
        form.add_widget(self.input_row("Costos reparación", "costos_reparacion", numeric=True))
        form.add_widget(self.input_row("Costos componentes", "costos_componentes", numeric=True))
        form.add_widget(self.input_row("Precio venta", "precio_venta", numeric=True))

    def tools(self):
        tools = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(182), spacing=dp(5))
        filters = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(5))
        self.search_text = TextInput(hint_text="Buscar marca/modelo/cliente", multiline=False)
        self.filter_estado = Spinner(text="Todos", values=["Todos"] + ESTADOS)
        filters.add_widget(self.search_text)
        filters.add_widget(self.filter_estado)
        tools.add_widget(filters)
        dates = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(5))
        self.date_from = TextInput(hint_text="Desde venta AAAA-MM-DD", multiline=False)
        self.date_to = TextInput(hint_text="Hasta venta AAAA-MM-DD", multiline=False)
        dates.add_widget(self.date_from)
        dates.add_widget(self.date_to)
        tools.add_widget(dates)
        row1 = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(5))
        row1.add_widget(Button(text="Buscar", on_press=lambda *_: self.refresh()))
        row1.add_widget(Button(text="Nuevo", on_press=lambda *_: self.clear_form()))
        row1.add_widget(Button(text="Guardar", on_press=lambda *_: self.save_item()))
        row1.add_widget(Button(text="Eliminar", on_press=lambda *_: self.delete_item()))
        tools.add_widget(row1)
        row2 = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(5))
        row2.add_widget(Button(text="Vista previa", on_press=lambda *_: self.preview_receipt()))
        row2.add_widget(Button(text="Boleta PDF", on_press=lambda *_: self.generate_receipt()))
        row2.add_widget(Button(text="Exportar Excel", on_press=lambda *_: self.export_csv()))
        row2.add_widget(Button(text="Imprimir", on_press=lambda *_: self.print_info()))
        tools.add_widget(row2)
        return tools

    def inventory_list(self):
        box = BoxLayout(orientation="vertical", size_hint_y=0.26)
        box.add_widget(Label(text="[b]INVENTARIO[/b]", markup=True, size_hint_y=None, height=dp(28), color=(0.05, 0.17, 0.31, 1)))
        scroll = ScrollView()
        self.list_box = GridLayout(cols=1, spacing=dp(4), size_hint_y=None)
        self.list_box.bind(minimum_height=self.list_box.setter("height"))
        scroll.add_widget(self.list_box)
        box.add_widget(scroll)
        return box

    def set_field(self, key, value):
        self.fields[key].text = value

    def get_data(self):
        accesorios = ", ".join([name for name, cb in self.checkboxes.items() if cb.active])
        return {
            "foto_path": self.fields["foto_path"].text.strip(),
            "marca": self.fields["marca"].text.strip(),
            "modelo": self.fields["modelo"].text.strip(),
            "ram_gb": self.fields["ram_gb"].text.strip(),
            "ram_tipo": self.spinners["ram_tipo"].text,
            "disco_tamano": self.fields["disco_tamano"].text.strip(),
            "disco_tipo": self.spinners["disco_tipo"].text,
            "video_gb": self.fields["video_gb"].text.strip(),
            "procesador": self.fields["procesador"].text.strip(),
            "generacion": self.fields["generacion"].text.strip(),
            "fecha_compra": self.fields["fecha_compra"].text.strip(),
            "fecha_venta": self.fields["fecha_venta"].text.strip(),
            "estado": self.spinners["estado"].text,
            "cliente": self.fields["cliente"].text.strip(),
            "accesorios": accesorios,
            "precio_compra": to_float(self.fields["precio_compra"].text),
            "precio_cargador": to_float(self.fields["precio_cargador"].text),
            "costos_reparacion": to_float(self.fields["costos_reparacion"].text),
            "costos_componentes": to_float(self.fields["costos_componentes"].text),
            "precio_venta": to_float(self.fields["precio_venta"].text),
        }

    def clear_form(self):
        self.current_id = None
        for ti in self.fields.values():
            ti.text = ""
        for name, sp in self.spinners.items():
            sp.text = sp.values[0]
        for cb in self.checkboxes.values():
            cb.active = False
        self.toast("Formulario limpio")

    def save_item(self):
        data = self.get_data()
        if not data["marca"] or not data["modelo"]:
            self.toast("Marca y modelo son obligatorios")
            return
        self.current_id = self.db.save(data, self.current_id)
        self.toast("Registro guardado")
        self.refresh(select_id=self.current_id)

    def delete_item(self):
        if not self.current_id:
            self.toast("Selecciona una laptop")
            return
        self.db.delete(self.current_id)
        self.clear_form()
        self.refresh()
        self.toast("Registro eliminado")

    def load_item(self, laptop_id):
        row = self.db.get(laptop_id)
        if not row:
            return
        self.current_id = row["id"]
        for key, ti in self.fields.items():
            ti.text = safe_text(row[key])
        for key, sp in self.spinners.items():
            sp.text = safe_text(row[key]) or sp.values[0]
        acc_text = safe_text(row["accesorios"]).lower()
        for name, cb in self.checkboxes.items():
            cb.active = name.lower() in acc_text
        self.toast(f"Editando ID {laptop_id}")

    def refresh(self, select_id=None):
        rows = self.db.rows(
            query=self.search_text.text.strip() if hasattr(self, "search_text") else "",
            estado=self.filter_estado.text if hasattr(self, "filter_estado") else "Todos",
            desde=self.date_from.text.strip() if hasattr(self, "date_from") else "",
            hasta=self.date_to.text.strip() if hasattr(self, "date_to") else "",
        )
        self.update_dashboard(rows)
        self.list_box.clear_widgets()
        if not rows:
            self.list_box.add_widget(Label(text="No hay registros", size_hint_y=None, height=dp(40), color=(0, 0, 0, 1)))
            return
        for row in rows:
            txt = f"ID {row['id']} | {row['marca']} {row['modelo']} | {row['estado']} | Venta {money(row['precio_venta'])} | Ganancia {money(ganancia(row))}"
            btn = Button(text=txt, size_hint_y=None, height=dp(52), halign="left")
            btn.bind(on_press=lambda _btn, rid=row["id"]: self.load_item(rid))
            self.list_box.add_widget(btn)
        if select_id:
            self.load_item(select_id)

    def update_dashboard(self, rows):
        total = len(rows)
        inv = sum(1 for r in rows if safe_text(r["estado"]) == "En inventario")
        sold_rows = [r for r in rows if safe_text(r["estado"]) == "Vendido" or to_float(r["precio_venta"]) > 0]
        sold = sum(1 for r in rows if safe_text(r["estado"]) == "Vendido")
        investment = sum(costo_total(r) for r in rows)
        sales = sum(to_float(r["precio_venta"]) for r in sold_rows)
        profit = sum(ganancia(r) for r in sold_rows)
        self.kpi_total.text = str(total)
        self.kpi_inv.text = str(inv)
        self.kpi_sold.text = str(sold)
        self.kpi_invest.text = money(investment)
        self.kpi_sales.text = money(sales)
        self.kpi_profit.text = money(profit)

    def select_photo(self):
        start_path = "/storage/emulated/0"
        if not os.path.exists(start_path):
            start_path = str(Path.home())
        chooser = FileChooserListView(path=start_path, filters=["*.jpg", "*.jpeg", "*.png"])
        layout = BoxLayout(orientation="vertical")
        layout.add_widget(chooser)
        buttons = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(5))
        popup = Popup(title="Seleccionar foto", content=layout, size_hint=(0.95, 0.9))
        buttons.add_widget(Button(text="Cancelar", on_press=lambda *_: popup.dismiss()))
        def choose(*_):
            if chooser.selection:
                self.fields["foto_path"].text = chooser.selection[0]
                popup.dismiss()
        buttons.add_widget(Button(text="Usar foto", on_press=choose))
        layout.add_widget(buttons)
        popup.open()

    def receipt_preview_text(self):
        row = self.current_row_from_form()
        lines = [
            EMPRESA,
            f"Celular: {TELEFONO}",
            "BOLETA DE VENTA",
            "",
            f"Cliente: {row.get('cliente') or 'Consumidor final'}",
            f"Fecha venta: {row.get('fecha_venta') or today()}",
            f"Equipo: {row.get('marca')} {row.get('modelo')}",
            f"Procesador: {row.get('procesador')}",
            f"RAM: {row.get('ram_gb')} GB {row.get('ram_tipo')}",
            f"Disco: {row.get('disco_tamano')} {row.get('disco_tipo')}",
            f"Video: {row.get('video_gb') or 'Integrada / no especifica'}",
            f"Accesorios: {row.get('accesorios') or 'No especifica'}",
            f"Total: {money(row.get('precio_venta'))}",
            "",
            "TÉRMINOS Y CONDICIONES DE GARANTÍA",
        ]
        lines.extend([f"• {t}" for t in TERMS])
        return "\n".join(lines)

    def preview_receipt(self):
        if not self.current_id:
            self.toast("Selecciona o guarda una laptop primero")
            return
        txt = TextInput(text=self.receipt_preview_text(), readonly=True, multiline=True)
        popup = Popup(title="Vista previa de boleta", content=txt, size_hint=(0.95, 0.90))
        popup.open()

    def current_row_from_form(self):
        data = self.get_data()
        data["id"] = self.current_id or 0
        return data

    def generate_receipt(self):
        if not self.current_id:
            self.toast("Primero guarda o selecciona una laptop")
            return
        row = self.db.get(self.current_id)
        if not row:
            self.toast("No se encontró el registro")
            return
        provisional = Path(self.boletas_dir) / f"BOLETA_TEMP_{self.current_id}.pdf"
        numero = self.db.create_receipt_row(self.current_id, to_float(row["precio_venta"]), str(provisional))
        final_path = Path(self.boletas_dir) / f"BOLETA_{numero}.pdf"
        self.make_receipt_pdf(row, numero, str(final_path))
        self.last_pdf_path = str(final_path)
        # Actualiza ruta final en boletas.
        with self.db.connect() as conn:
            conn.execute("UPDATE boletas SET pdf_path=? WHERE numero=?", (str(final_path), numero))
            conn.commit()
        self.toast(f"Boleta generada: {final_path}")
        self.show_file_path("Boleta generada", str(final_path))

    def make_receipt_pdf(self, row, numero, path):
        pdf = SimplePDF(path, self.logo_path)
        # Fondo y encabezado
        pdf.color(0.97, 0.98, 0.99); pdf.rect(28, 740, 540, 78, fill=True, stroke=False)
        pdf.color(0.04, 0.23, 0.43, stroke=True); pdf.rect(28, 740, 540, 78, stroke=True)
        pdf.logo(40, 750, 58, 58)
        pdf.color(0.04, 0.23, 0.43); pdf.text(112, 792, "MULTISERVICIOS", size=12, bold=True)
        pdf.text(112, 770, "HANS", size=23, bold=True)
        pdf.color(0.25, 0.30, 0.36); pdf.text(112, 754, "Soluciones Informáticas | Venta de laptops y computadoras", size=8)
        pdf.text(112, 743, f"Celular: {TELEFONO}", size=8)
        pdf.color(0.04, 0.23, 0.43); pdf.rect(398, 756, 150, 44, fill=True, stroke=False)
        pdf.color(1, 1, 1); pdf.text(414, 784, "BOLETA DE VENTA", size=12, bold=True)
        pdf.text(422, 766, f"N° {numero}", size=11, bold=True)
        pdf.color(0.96, 0.62, 0.04); pdf.rect(28, 732, 540, 5, fill=True, stroke=False)

        y = 710
        def section(title):
            nonlocal y
            pdf.color(0.04, 0.23, 0.43); pdf.rect(28, y - 2, 540, 18, fill=True, stroke=False)
            pdf.color(1, 1, 1); pdf.text(36, y + 3, title, size=8, bold=True)
            y -= 22
        def kv(k, v):
            nonlocal y
            pdf.color(0, 0, 0); pdf.text(38, y, k, size=8, bold=True); pdf.text(150, y, v, size=8)
            y -= 13
        section("DATOS DEL CLIENTE")
        kv("Cliente:", safe_text(row["cliente"]) or "Consumidor final")
        kv("Fecha venta:", safe_text(row["fecha_venta"]) or today())
        kv("Fecha emisión:", today())
        y -= 4

        section("DETALLE DEL EQUIPO")
        kv("Marca:", safe_text(row["marca"]))
        kv("Modelo:", safe_text(row["modelo"]))
        kv("Procesador:", safe_text(row["procesador"]))
        kv("Generación:", safe_text(row["generacion"]))
        kv("Memoria RAM:", f"{safe_text(row['ram_gb'])} GB {safe_text(row['ram_tipo'])}".strip())
        kv("Disco duro:", f"{safe_text(row['disco_tamano'])} {safe_text(row['disco_tipo'])}".strip())
        kv("Tarjeta video:", f"{safe_text(row['video_gb'])} GB" if safe_text(row["video_gb"]) else "Integrada / no especifica")
        kv("Accesorios:", safe_text(row["accesorios"]) or "No especifica")
        y -= 4

        section("RESUMEN DE VENTA")
        kv("Concepto:", f"Venta de laptop {safe_text(row['marca'])} {safe_text(row['modelo'])}".strip())
        kv("TOTAL PAGADO:", money(row["precio_venta"]))
        y -= 4

        section("TÉRMINOS Y CONDICIONES DE GARANTÍA")
        pdf.color(0, 0, 0)
        for term in TERMS:
            y = pdf.line_text(38, y, "• " + term, size=6.1, max_chars=118, leading=7.2)
            y -= 1.5
            if y < 40:
                break
        pdf.color(0.25, 0.30, 0.36)
        pdf.text(126, 24, "Gracias por su compra. Para garantía presente esta boleta y el equipo para evaluación técnica.", size=7)
        pdf.build()

    def export_csv(self):
        rows = self.db.rows()
        if not rows:
            self.toast("No hay datos para exportar")
            return
        path = Path(self.exports_dir) / f"inventario_laptops_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        headers = [
            "id", "foto_path", "marca", "modelo", "ram_gb", "ram_tipo", "disco_tamano", "disco_tipo",
            "video_gb", "procesador", "generacion", "fecha_compra", "fecha_venta", "estado", "cliente",
            "accesorios", "precio_compra", "precio_cargador", "costos_reparacion", "costos_componentes",
            "precio_venta", "ganancia_estimada", "created_at", "updated_at"
        ]
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for r in rows:
                writer.writerow([r[h] if h in r.keys() else (ganancia(r) if h == "ganancia_estimada" else "") for h in headers])
        self.show_file_path("Excel CSV generado", str(path))

    def print_info(self):
        if not self.last_pdf_path:
            self.toast("Primero genera una boleta PDF")
            return
        self.show_file_path("Imprimir boleta", f"Archivo PDF generado:\n{self.last_pdf_path}\n\nPara imprimir: abre el PDF desde el administrador de archivos y elige Compartir/Imprimir.")

    def show_file_path(self, title, text):
        popup = Popup(title=title, content=TextInput(text=text, readonly=True, multiline=True), size_hint=(0.92, 0.45))
        popup.open()

    def toast(self, message):
        popup = Popup(title="Aviso", content=Label(text=message), size_hint=(0.78, 0.28))
        popup.open()
        Clock.schedule_once(lambda *_: popup.dismiss(), 1.4)


if __name__ == "__main__":
    HansInventoryApp().run()
