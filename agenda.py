import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime, date

import customtkinter as ctk
import psycopg2

try:
    from tkcalendar import DateEntry
except ImportError:
    DateEntry = None


ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class AppAgenda(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Agenda 3 Patitos")
        self.geometry("1280x760")
        self.minsize(1050, 650)

        self.conn_params = {
            "dbname": "agenda",
            "user": "postgres",
            "password": "postgres",
            "host": "localhost",
            "port": "5432",
        }

        self.usuarios_combo = {}
        self.categorias_combo = {}
        self.categorias_padre_combo = {}
        self.eventos_combo = {}
        self.ubicaciones_combo = {}  # Restricción 09 y 10
        self.tipos_disponibilidad_combo = {}  # Restricción 11 y 12


        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.crear_sidebar()
        self.crear_area_principal()
        self.configurar_estilos()

        self.actualizar_todas_las_tablas()

        if DateEntry is None:
            self.after(500, lambda: messagebox.showwarning(
                "Calendario no instalado"
            ))

    # -------------------- INFRAESTRUCTURA --------------------

    def obtener_conexion(self):
        conn = psycopg2.connect(**self.conn_params)
        with conn.cursor() as cur:
            cur.execute("SET search_path TO prototipo, public;")
        return conn

    def ejecutar_consulta(self, sql, params=None, fetch=False):
        conn = None
        try:
            conn = self.obtener_conexion()
            with conn.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall() if fetch else None
            conn.commit()
            return rows
        except Exception:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def configurar_estilos(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Treeview", rowheight=30, font=("Arial", 10))
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"))

    def crear_treeview(self, parent, columnas, widths):
        contenedor = ctk.CTkFrame(parent, fg_color="transparent")
        contenedor.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        tree = ttk.Treeview(contenedor, columns=columnas, show="headings")
        for col, width in zip(columnas, widths):
            tree.heading(col, text=col)
            tree.column(col, width=width, anchor="center")
        scroll_y = ttk.Scrollbar(contenedor, orient="vertical", command=tree.yview)
        scroll_x = ttk.Scrollbar(contenedor, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)
        return tree

    def seleccionar_modulo(self, nombre):
        self.tabview.set(nombre)
        for modulo, boton in self.botones_nav.items():
            boton.configure(fg_color=("gray75", "gray25") if modulo == nombre else "transparent")

    def crear_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=235, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)
        self.sidebar_frame.grid_rowconfigure(10, weight=1)

        ctk.CTkLabel(
            self.sidebar_frame,
            text="📅 AGENDA 🦆🦆🦆",
            font=ctk.CTkFont(size=22, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=(28, 5), sticky="w")

        ctk.CTkLabel(
            self.sidebar_frame,
            text="Gestión de usuarios, categorías y eventos",
            font=ctk.CTkFont(size=11),
            wraplength=190,
            justify="left"
        ).grid(row=1, column=0, padx=20, pady=(0, 25), sticky="w")

        self.botones_nav = {}
        for i, (nombre, icono) in enumerate([
            ("Usuarios", "👥"),
            ("Categorías", "📁"),
            ("Eventos", "🗓️"),
            ("Ubicaciones", "📍"),
            ("Disponibilidad", "📓"),
            ("Tareas", "📝"),
        ], start=2):
            btn = ctk.CTkButton(
                self.sidebar_frame, text=f"{icono}  {nombre}",
                anchor="w", fg_color="transparent",
                command=lambda n=nombre: self.seleccionar_modulo(n)
            )
            btn.grid(row=i, column=0, padx=15, pady=5, sticky="ew")
            self.botones_nav[nombre] = btn

        ctk.CTkButton(
            self.sidebar_frame,
            text="🔄  Recargar datos",
            command=self.actualizar_todas_las_tablas
        ).grid(row=9, column=0, padx=15, pady=(20, 5), sticky="ew")

        ctk.CTkLabel(self.sidebar_frame, text="APARIENCIA", font=ctk.CTkFont(size=11, weight="bold")).grid(
            row=11, column=0, padx=20, pady=(10, 5), sticky="w"
        )
        self.option_mode = ctk.CTkOptionMenu(
            self.sidebar_frame,
            values=["System", "Dark", "Light"],
            command=ctk.set_appearance_mode
        )
        self.option_mode.set("System")
        self.option_mode.grid(row=12, column=0, padx=15, pady=(0, 25), sticky="ew")

    def crear_area_principal(self):
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        self.tabview = ctk.CTkTabview(self.main_container, command=self.al_cambiar_pestana)
        self.tabview.grid(row=0, column=0, sticky="nsew")

        self.tab_usuarios = self.tabview.add("Usuarios")
        self.tab_categorias = self.tabview.add("Categorías")
        self.tab_eventos = self.tabview.add("Eventos")
        self.tab_ubicaciones = self.tabview.add("Ubicaciones")
        self.tab_disponibilidad = self.tabview.add("Disponibilidad")
        self.tab_tareas = self.tabview.add("Tareas")

        self.configurar_pestana_usuarios()
        self.configurar_pestana_categorias()
        self.configurar_pestana_eventos()
        self.configurar_pestana_ubicaciones()
        self.configurar_pestana_disponibilidad()
        self.configurar_pestana_tareas()
        self.seleccionar_modulo("Usuarios")

    def al_cambiar_pestana(self):
        nombre = self.tabview.get()
        if nombre in self.botones_nav:
            for modulo, boton in self.botones_nav.items():
                boton.configure(fg_color=("gray75", "gray25") if modulo == nombre else "transparent")

    def crear_encabezado(self, parent, titulo, descripcion):
        ctk.CTkLabel(parent, text=titulo, font=ctk.CTkFont(size=24, weight="bold")).pack(
            anchor="w", padx=15, pady=(15, 0)
        )
        ctk.CTkLabel(parent, text=descripcion, font=ctk.CTkFont(size=12)).pack(
            anchor="w", padx=15, pady=(0, 12)
        )

    # -------------------- USUARIOS --------------------

    def configurar_pestana_usuarios(self):
        self.crear_encabezado(self.tab_usuarios, "Usuarios", "Registra, consulta y administra los usuarios de la agenda.")

        cuerpo = ctk.CTkFrame(self.tab_usuarios, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=10, pady=5)
        cuerpo.grid_columnconfigure(0, weight=3)
        cuerpo.grid_columnconfigure(1, weight=1)
        cuerpo.grid_rowconfigure(0, weight=1)

        tabla_frame = ctk.CTkFrame(cuerpo)
        tabla_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        form = ctk.CTkScrollableFrame(cuerpo, width=300)
        form.grid(row=0, column=1, sticky="nsew")

        self.tree_usuarios = self.crear_treeview(
            tabla_frame, ("ID", "Nombre", "Apellido", "Registro", "Activo"),
            (70, 160, 160, 160, 80)
        )
        self.tree_usuarios.bind("<<TreeviewSelect>>", self.cargar_usuario_seleccionado)

        ctk.CTkLabel(form, text="Formulario de usuario", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 15))
        self.entry_nombre = ctk.CTkEntry(form, placeholder_text="Nombre")
        self.entry_nombre.pack(fill="x", padx=10, pady=6)
        self.entry_apellido = ctk.CTkEntry(form, placeholder_text="Apellido")
        self.entry_apellido.pack(fill="x", padx=10, pady=6)

        self.switch_usuario_activo = ctk.CTkSwitch(form, text="Usuario activo")
        self.switch_usuario_activo.select()
        self.switch_usuario_activo.pack(anchor="w", padx=12, pady=10)

        ctk.CTkButton(form, text="➕ Registrar usuario", command=self.agregar_usuario).pack(fill="x", padx=10, pady=(12, 5))
        ctk.CTkButton(form, text="💾 Actualizar seleccionado", command=self.actualizar_usuario).pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(form, text="🧹 Nuevo / Limpiar", command=self.limpiar_form_usuario, fg_color="gray").pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(form, text="🗑️ Eliminar seleccionado", command=self.eliminar_usuario, fg_color="#b33939", hover_color="#8f2d2d").pack(fill="x", padx=10, pady=5)

    def usuario_seleccionado_id(self):
        sel = self.tree_usuarios.selection()
        return self.tree_usuarios.item(sel[0])["values"][0] if sel else None

    def cargar_usuario_seleccionado(self, _=None):
        sel = self.tree_usuarios.selection()
        if not sel:
            return
        vals = self.tree_usuarios.item(sel[0])["values"]
        self.entry_nombre.delete(0, tk.END); self.entry_nombre.insert(0, vals[1])
        self.entry_apellido.delete(0, tk.END); self.entry_apellido.insert(0, vals[2])
        if vals[4]:
            self.switch_usuario_activo.select()
        else:
            self.switch_usuario_activo.deselect()

    def limpiar_form_usuario(self):
        self.tree_usuarios.selection_remove(self.tree_usuarios.selection())
        self.entry_nombre.delete(0, tk.END)
        self.entry_apellido.delete(0, tk.END)
        self.switch_usuario_activo.select()

    def agregar_usuario(self):
        nombre, apellido = self.entry_nombre.get().strip(), self.entry_apellido.get().strip()
        if not nombre or not apellido:
            return messagebox.showwarning("Campos incompletos", "Indica nombre y apellido.")
        try:
            self.ejecutar_consulta("INSERT INTO usuarios (nombre, apellido, activo) VALUES (%s, %s, %s)",
                                (nombre, apellido, self.switch_usuario_activo.get() == 1))
            self.limpiar_form_usuario(); self.actualizar_todas_las_tablas()
            messagebox.showinfo("Éxito", "Usuario registrado correctamente.")
        except Exception as e:
            messagebox.showerror("Error de base de datos", str(e))

    def actualizar_usuario(self):
        uid = self.usuario_seleccionado_id()
        if uid is None:
            return messagebox.showwarning("Selección requerida", "Selecciona un usuario para actualizar.")
        nombre, apellido = self.entry_nombre.get().strip(), self.entry_apellido.get().strip()
        if not nombre or not apellido:
            return messagebox.showwarning("Campos incompletos", "Indica nombre y apellido.")
        try:
            self.ejecutar_consulta("UPDATE usuarios SET nombre=%s, apellido=%s, activo=%s WHERE id_usuario=%s",
                                (nombre, apellido, self.switch_usuario_activo.get() == 1, uid))
            self.actualizar_todas_las_tablas()
            messagebox.showinfo("Éxito", "Usuario actualizado.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def eliminar_usuario(self):
        uid = self.usuario_seleccionado_id()
        if uid is None:
            return messagebox.showwarning("Selección requerida", "Selecciona un usuario.")
        if not messagebox.askyesno("Confirmar", "¿Eliminar el usuario seleccionado?"):
            return
        try:
            self.ejecutar_consulta("DELETE FROM usuarios WHERE id_usuario=%s", (uid,))
            self.limpiar_form_usuario(); self.actualizar_todas_las_tablas()
            messagebox.showinfo("Eliminado", "Usuario eliminado.")
        except Exception as e:
            messagebox.showerror("No se pudo eliminar", str(e))

    def cargar_datos_usuarios(self):
        try:
            rows = self.ejecutar_consulta(
                "SELECT id_usuario, nombre, apellido, fecha_registro, activo FROM usuarios ORDER BY nombre, apellido",
                fetch=True
            )
            for item in self.tree_usuarios.get_children(): self.tree_usuarios.delete(item)
            self.usuarios_combo = {}
            for row in rows:
                registro = row[3].strftime("%Y-%m-%d %H:%M") if hasattr(row[3], "strftime") else row[3]
                self.tree_usuarios.insert("", "end", values=(row[0], row[1], row[2], registro, "Sí" if row[4] else "No"))
                etiqueta = f"{row[1]} {row[2]} — #{row[0]}"
                self.usuarios_combo[etiqueta] = row[0]
        except Exception as e:
            print(f"Error cargando usuarios: {e}")

    # -------------------- CATEGORÍAS --------------------

    def configurar_pestana_categorias(self):
        self.crear_encabezado(self.tab_categorias, "Categorías", "Organiza los eventos mediante categorías y subcategorías.")

        cuerpo = ctk.CTkFrame(self.tab_categorias, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=10, pady=5)
        cuerpo.grid_columnconfigure(0, weight=3); cuerpo.grid_columnconfigure(1, weight=1); cuerpo.grid_rowconfigure(0, weight=1)

        tabla = ctk.CTkFrame(cuerpo); tabla.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        form = ctk.CTkScrollableFrame(cuerpo, width=320); form.grid(row=0, column=1, sticky="nsew")

        self.tree_categorias = self.crear_treeview(tabla, ("ID", "Categoría", "Categoría padre"), (80, 230, 230))
        self.tree_categorias.bind("<<TreeviewSelect>>", self.cargar_categoria_seleccionada)

        ctk.CTkLabel(form, text="Formulario de categoría", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 15))
        self.entry_cat_nombre = ctk.CTkEntry(form, placeholder_text="Nombre de la categoría")
        self.entry_cat_nombre.pack(fill="x", padx=10, pady=6)

        ctk.CTkLabel(form, text="Categoría padre").pack(anchor="w", padx=10, pady=(10, 2))
        self.combo_cat_padre = ctk.CTkComboBox(form, values=["Sin categoría padre"], state="readonly")
        self.combo_cat_padre.set("Sin categoría padre")
        self.combo_cat_padre.pack(fill="x", padx=10, pady=6)

        ctk.CTkButton(form, text="➕ Crear categoría", command=self.agregar_categoria).pack(fill="x", padx=10, pady=(15, 5))
        ctk.CTkButton(form, text="💾 Actualizar seleccionada", command=self.actualizar_categoria).pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(form, text="🧹 Nueva / Limpiar", command=self.limpiar_form_categoria, fg_color="gray").pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(form, text="🗑️ Eliminar seleccionada", command=self.eliminar_categoria, fg_color="#b33939", hover_color="#8f2d2d").pack(fill="x", padx=10, pady=5)

    def categoria_seleccionada_id(self):
        sel = self.tree_categorias.selection()
        return self.tree_categorias.item(sel[0])["values"][0] if sel else None

    def cargar_categoria_seleccionada(self, _=None):
        sel = self.tree_categorias.selection()
        if not sel: return
        vals = self.tree_categorias.item(sel[0])["values"]
        self.entry_cat_nombre.delete(0, tk.END); self.entry_cat_nombre.insert(0, vals[1])
        padre = vals[2]
        self.combo_cat_padre.set(padre if padre in self.categorias_padre_combo else "Sin categoría padre")

    def limpiar_form_categoria(self):
        self.tree_categorias.selection_remove(self.tree_categorias.selection())
        self.entry_cat_nombre.delete(0, tk.END); self.combo_cat_padre.set("Sin categoría padre")

    def _padre_id_actual(self):
        valor = self.combo_cat_padre.get()
        return None if valor == "Sin categoría padre" else self.categorias_padre_combo.get(valor)

    def agregar_categoria(self):
        nombre = self.entry_cat_nombre.get().strip()
        if not nombre: return messagebox.showwarning("Campo requerido", "Indica el nombre de la categoría.")
        try:
            self.ejecutar_consulta("INSERT INTO categorias (nombre, id_categoria_padre) VALUES (%s, %s)",
                                (nombre, self._padre_id_actual()))
            self.limpiar_form_categoria(); self.actualizar_todas_las_tablas()
            messagebox.showinfo("Éxito", "Categoría creada.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def actualizar_categoria(self):
        cid = self.categoria_seleccionada_id()
        if cid is None: return messagebox.showwarning("Selección requerida", "Selecciona una categoría.")
        nombre = self.entry_cat_nombre.get().strip(); padre = self._padre_id_actual()
        if not nombre: return messagebox.showwarning("Campo requerido", "Indica el nombre.")
        if padre == cid: return messagebox.showwarning("Relación inválida", "Una categoría no puede ser su propia categoría padre.")
        try:
            self.ejecutar_consulta("UPDATE categorias SET nombre=%s, id_categoria_padre=%s WHERE id_categoria=%s",
                                (nombre, padre, cid))
            self.actualizar_todas_las_tablas(); messagebox.showinfo("Éxito", "Categoría actualizada.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def eliminar_categoria(self):
        cid = self.categoria_seleccionada_id()
        if cid is None: return messagebox.showwarning("Selección requerida", "Selecciona una categoría.")
        if not messagebox.askyesno("Confirmar", "¿Eliminar la categoría seleccionada?"): return
        try:
            self.ejecutar_consulta("DELETE FROM categorias WHERE id_categoria=%s", (cid,))
            self.limpiar_form_categoria(); self.actualizar_todas_las_tablas()
            messagebox.showinfo("Eliminado", "Categoría eliminada.")
        except Exception as e:
            messagebox.showerror("No se pudo eliminar", str(e))

    def cargar_datos_categorias(self):
        try:
            rows = self.ejecutar_consulta("""
                SELECT c.id_categoria, c.nombre, p.nombre
                FROM categorias c
                LEFT JOIN categorias p ON p.id_categoria = c.id_categoria_padre
                ORDER BY c.nombre
            """, fetch=True)
            ids = self.ejecutar_consulta("SELECT id_categoria, nombre FROM categorias ORDER BY nombre", fetch=True)

            for item in self.tree_categorias.get_children(): self.tree_categorias.delete(item)
            self.categorias_combo = {}
            self.categorias_padre_combo = {}
            for cid, nombre in ids:
                etiqueta = f"{nombre} — #{cid}"
                self.categorias_combo[etiqueta] = cid
                self.categorias_padre_combo[etiqueta] = cid
            for row in rows:
                padre = "Sin categoría padre"
                if row[2] is not None:

                    for etiqueta, cid in self.categorias_padre_combo.items():
                        if etiqueta.startswith(f"{row[2]} —"):
                            padre = etiqueta; break
                self.tree_categorias.insert("", "end", values=(row[0], row[1], padre))

            valores_padre = ["Sin categoría padre"] + list(self.categorias_padre_combo.keys())
            self.combo_cat_padre.configure(values=valores_padre)
            if self.combo_cat_padre.get() not in valores_padre:
                self.combo_cat_padre.set("Sin categoría padre")
        except Exception as e:
            print(f"Error cargando categorías: {e}")

    # -------------------- EVENTOS --------------------

    def configurar_pestana_eventos(self):
        self.crear_encabezado(
            self.tab_eventos,
            "Eventos",
            "Programa eventos seleccionando usuarios, categorías, ubicación, fechas y horas."
        )

        cuerpo = ctk.CTkFrame(self.tab_eventos, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=10, pady=5)
        cuerpo.grid_columnconfigure(0, weight=3)
        cuerpo.grid_columnconfigure(1, weight=1)
        cuerpo.grid_rowconfigure(0, weight=1)

        tabla = ctk.CTkFrame(cuerpo)
        tabla.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        form = ctk.CTkScrollableFrame(cuerpo, width=350)
        form.grid(row=0, column=1, sticky="nsew")

        # Requerimiento 09: ahora la tabla de eventos muestra también la ubicación asociada.
        self.tree_eventos = self.crear_treeview(
            tabla,
            ("ID", "Propietario", "Categoría", "Ubicación", "Título", "Inicio", "Fin"),
            (70, 170, 150, 190, 220, 150, 150)
        )
        self.tree_eventos.bind("<<TreeviewSelect>>", self.cargar_evento_seleccionado)

        ctk.CTkLabel(
            form,
            text="Formulario de evento",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(10, 12))

        self.entry_ev_titulo = ctk.CTkEntry(form, placeholder_text="Título del evento")
        self.entry_ev_titulo.pack(fill="x", padx=10, pady=6)

        ctk.CTkLabel(form, text="Propietario").pack(anchor="w", padx=10, pady=(8, 2))
        self.combo_ev_usuario = ctk.CTkComboBox(
            form, values=["Seleccione un usuario"], state="readonly"
        )
        self.combo_ev_usuario.set("Seleccione un usuario")
        self.combo_ev_usuario.pack(fill="x", padx=10, pady=4)

        ctk.CTkLabel(form, text="Categoría").pack(anchor="w", padx=10, pady=(8, 2))
        self.combo_ev_categoria = ctk.CTkComboBox(
            form, values=["Seleccione una categoría"], state="readonly"
        )
        self.combo_ev_categoria.set("Seleccione una categoría")

        self.combo_ev_categoria.pack(fill="x", padx=10, pady=4)

        # RF-09: la ubicación pertenece al EVENTO, por eso el selector va aquí.
        ctk.CTkLabel(form, text="Ubicación").pack(anchor="w", padx=10, pady=(8, 2))
        self.combo_ev_ubicacion = ctk.CTkComboBox(
            form, values=["Seleccione una ubicación"], state="readonly"
        )
        self.combo_ev_ubicacion.set("Seleccione una ubicación")
        self.combo_ev_ubicacion.pack(fill="x", padx=10, pady=4)

        ctk.CTkLabel(form, text="Inicio").pack(anchor="w", padx=10, pady=(10, 2))
        fila_inicio = ctk.CTkFrame(form, fg_color="transparent")
        fila_inicio.pack(fill="x", padx=10)
        self.fecha_inicio = self.crear_selector_fecha(fila_inicio)
        self.fecha_inicio.pack(side="left", fill="x", expand=True)
        self.hora_inicio = ctk.CTkEntry(fila_inicio, placeholder_text="HH:MM", width=75)
        self.hora_inicio.pack(side="left", padx=(6, 0))

        ctk.CTkLabel(form, text="Fin").pack(anchor="w", padx=10, pady=(10, 2))
        fila_fin = ctk.CTkFrame(form, fg_color="transparent")
        fila_fin.pack(fill="x", padx=10)
        self.fecha_fin = self.crear_selector_fecha(fila_fin)
        self.fecha_fin.pack(side="left", fill="x", expand=True)
        self.hora_fin = ctk.CTkEntry(fila_fin, placeholder_text="HH:MM", width=75)
        self.hora_fin.pack(side="left", padx=(6, 0))

        ctk.CTkButton(form, text="➕ Crear evento", command=self.agregar_evento).pack(
            fill="x", padx=10, pady=(16, 5)
        )
        ctk.CTkButton(form, text="💾 Actualizar seleccionado", command=self.actualizar_evento).pack(
            fill="x", padx=10, pady=5
        )
        ctk.CTkButton(
            form, text="🧹 Nuevo / Limpiar", command=self.limpiar_form_evento, fg_color="gray"
        ).pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(
            form, text="🗑️ Eliminar seleccionado", command=self.eliminar_evento, fg_color="#b33939", hover_color="#8f2d2d").pack(fill="x", padx=10, pady=5)

        self.limpiar_form_evento()

    def crear_selector_fecha(self, parent):
        if DateEntry is not None:
            return DateEntry(parent, date_pattern="yyyy-mm-dd", font=("Arial", 10))
        return ttk.Entry(parent)

    def obtener_fecha(self, widget):
        if DateEntry is not None:
            return widget.get_date().strftime("%Y-%m-%d")
        return widget.get().strip()

    def establecer_fecha(self, widget, valor):
        fecha = valor.date() if hasattr(valor, "date") else datetime.strptime(
            str(valor)[:10], "%Y-%m-%d"
        ).date()
        if DateEntry is not None:
            widget.set_date(fecha)
        else:
            widget.delete(0, tk.END)
            widget.insert(0, fecha.strftime("%Y-%m-%d"))

    def evento_seleccionado_id(self):
        sel = self.tree_eventos.selection()
        return self.tree_eventos.item(sel[0])["values"][0] if sel else None

    def cargar_evento_seleccionado(self, _=None):
        sel = self.tree_eventos.selection()
        if not sel:
            return

        vals = self.tree_eventos.item(sel[0])["values"]

        # Columnas: ID, Propietario, Categoría, Ubicación, Título, Inicio, Fin
        self.entry_ev_titulo.delete(0, tk.END)
        self.entry_ev_titulo.insert(0, vals[4])
        self.combo_ev_usuario.set(vals[1])
        self.combo_ev_categoria.set(vals[2])
        self.combo_ev_ubicacion.set(vals[3])

        try:
            ini = datetime.strptime(str(vals[5]), "%Y-%m-%d %H:%M")
            fin = datetime.strptime(str(vals[6]), "%Y-%m-%d %H:%M")
            self.establecer_fecha(self.fecha_inicio, ini)
            self.establecer_fecha(self.fecha_fin, fin)
            self.hora_inicio.delete(0, tk.END)
            self.hora_inicio.insert(0, ini.strftime("%H:%M"))
            self.hora_fin.delete(0, tk.END)
            self.hora_fin.insert(0, fin.strftime("%H:%M"))
        except ValueError:
            pass

    def limpiar_form_evento(self):
        self.tree_eventos.selection_remove(self.tree_eventos.selection())
        self.entry_ev_titulo.delete(0, tk.END)
        self.combo_ev_usuario.set("Seleccione un usuario")
        self.combo_ev_categoria.set("Seleccione una categoría")
        self.combo_ev_ubicacion.set("Seleccione una ubicación")

        hoy = datetime.now()
        self.establecer_fecha(self.fecha_inicio, hoy)
        self.establecer_fecha(self.fecha_fin, hoy)
        self.hora_inicio.delete(0, tk.END)
        self.hora_inicio.insert(0, "09:00")
        self.hora_fin.delete(0, tk.END)
        self.hora_fin.insert(0, "10:00")

    def datos_evento_formulario(self):
        titulo = self.entry_ev_titulo.get().strip()
        usuario = self.usuarios_combo.get(self.combo_ev_usuario.get())
        categoria = self.categorias_combo.get(self.combo_ev_categoria.get())
        ubicacion = self.ubicaciones_combo.get(self.combo_ev_ubicacion.get())

        try:
            inicio = datetime.strptime(
                f"{self.obtener_fecha(self.fecha_inicio)} {self.hora_inicio.get().strip()}",
                "%Y-%m-%d %H:%M"
            )
            fin = datetime.strptime(
                f"{self.obtener_fecha(self.fecha_fin)} {self.hora_fin.get().strip()}",
                "%Y-%m-%d %H:%M"
            )
        except ValueError:
            raise ValueError("La hora debe tener formato HH:MM, por ejemplo 09:30.")

        if not titulo or usuario is None or categoria is None:
            raise ValueError("Completa título, propietario y categoría.")
        if ubicacion is None:
            raise ValueError("Selecciona una ubicación para el evento.")
        if fin <= inicio:
            raise ValueError("La fecha y hora de finalización deben ser posteriores al inicio.")

        return usuario, categoria, ubicacion, titulo, inicio, fin

    def validar_conflicto_ubicacion(self, id_ubicacion, inicio, fin, id_evento_excluir=None):
        """Requerimiento 09: hace que dos eventos sean simultáneos en la misma ubicación."""
        sql = """
            SELECT id_evento, titulo, fecha_inicio, fecha_fin
            FROM eventos
            WHERE id_ubicacion = %s
            AND fecha_inicio < %s
            AND fecha_fin > %s
        """
        params = [id_ubicacion, fin, inicio]

        if id_evento_excluir is not None:
            sql += " AND id_evento <> %s"
            params.append(id_evento_excluir)

        sql += " ORDER BY fecha_inicio LIMIT 1"
        conflicto = self.ejecutar_consulta(sql, tuple(params), fetch=True)

        if conflicto:
            evento = conflicto[0]
            inicio_conflicto = evento[2].strftime("%Y-%m-%d %H:%M")
            fin_conflicto = evento[3].strftime("%Y-%m-%d %H:%M")
            raise ValueError(
                f"La ubicación ya está ocupada por '{evento[1]}' "
                f"desde {inicio_conflicto} hasta {fin_conflicto}."
            )

    def agregar_evento(self):
        try:
            datos = self.datos_evento_formulario()
            usuario, categoria, ubicacion, titulo, inicio, fin = datos
            self.validar_conflicto_ubicacion(ubicacion, inicio, fin)
            self.ejecutar_consulta("""
                INSERT INTO eventos
                    (id_usuario_propietario, id_categoria, id_ubicacion,
                    titulo, fecha_inicio, fecha_fin)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, datos)

            self.limpiar_form_evento()
            self.actualizar_todas_las_tablas()
            messagebox.showinfo("Éxito", "Evento creado correctamente.")
        except Exception as e:
            messagebox.showerror("No se pudo crear el evento", str(e))

    def actualizar_evento(self):
        eid = self.evento_seleccionado_id()
        if eid is None:
            return messagebox.showwarning("Selección requerida", "Selecciona un evento.")

        try:
            usuario, categoria, ubicacion, titulo, inicio, fin = self.datos_evento_formulario()
            self.validar_conflicto_ubicacion(ubicacion, inicio, fin, eid)
            self.ejecutar_consulta("""
                UPDATE eventos
                SET id_usuario_propietario=%s,
                    id_categoria=%s,
                    id_ubicacion=%s,
                    titulo=%s,
                    fecha_inicio=%s,
                    fecha_fin=%s
                WHERE id_evento=%s
            """, (usuario, categoria, ubicacion, titulo, inicio, fin, eid))

            self.actualizar_todas_las_tablas()
            messagebox.showinfo("Éxito", "Evento actualizado.")
        except Exception as e:
            messagebox.showerror("No se pudo actualizar", str(e))

    def eliminar_evento(self):
        eid = self.evento_seleccionado_id()
        if eid is None:
            return messagebox.showwarning("Selección requerida", "Selecciona un evento.")
        if not messagebox.askyesno("Confirmar", "¿Eliminar el evento seleccionado?"):
            return

        try:
            self.ejecutar_consulta("DELETE FROM eventos WHERE id_evento=%s", (eid,))
            self.limpiar_form_evento()
            self.actualizar_todas_las_tablas()
            messagebox.showinfo("Eliminado", "Evento eliminado.")
        except Exception as e:
            messagebox.showerror("No se pudo eliminar", str(e))

    def cargar_datos_eventos(self):
        try:
            rows = self.ejecutar_consulta("""
                SELECT
                    e.id_evento,
                    u.id_usuario,
                    u.nombre,
                    u.apellido,
                    c.id_categoria,
                    c.nombre,
                    e.titulo,
                    e.fecha_inicio,
                    e.fecha_fin,
                    ub.id_ubicacion,
                    ub.nombre,
                    ub.ciudad
                FROM eventos e
                JOIN usuarios u
                    ON u.id_usuario = e.id_usuario_propietario
                JOIN categorias c
                    ON c.id_categoria = e.id_categoria
                LEFT JOIN ubicaciones ub
                    ON ub.id_ubicacion = e.id_ubicacion
                ORDER BY e.fecha_inicio DESC
            """, fetch=True)

            for item in self.tree_eventos.get_children():
                self.tree_eventos.delete(item)

            self.eventos_combo = {}

            for row in rows:
                usuario = f"{row[2]} {row[3]} — #{row[1]}"
                categoria = f"{row[5]} — #{row[4]}"

                if row[9] is not None:
                    # Debe coincidir exactamente con la etiqueta usada en ubicaciones_combo.
                    ubicacion = f"{row[10]} - {row[11]} (#{row[9]})"
                else:
                    ubicacion = "Sin ubicación"

                inicio = row[7].strftime("%Y-%m-%d %H:%M") if hasattr(row[7], "strftime") else row[7]
                fin = row[8].strftime("%Y-%m-%d %H:%M") if hasattr(row[8], "strftime") else row[8]

                etiqueta_evento = f"{row[6]} - #{row[0]}"
                self.eventos_combo[etiqueta_evento] = row[0]

                self.tree_eventos.insert(
                    "",
                    "end",
                    values=(row[0], usuario, categoria, ubicacion, row[6], inicio, fin)
                )

            valores_u = ["Seleccione un usuario"] + list(self.usuarios_combo.keys())
            valores_c = ["Seleccione una categoría"] + list(self.categorias_combo.keys())
            valores_ub = ["Seleccione una ubicación"] + list(self.ubicaciones_combo.keys())

            self.combo_ev_usuario.configure(values=valores_u)
            self.combo_ev_categoria.configure(values=valores_c)
            self.combo_ev_ubicacion.configure(values=valores_ub)

            if self.combo_ev_usuario.get() not in valores_u:
                self.combo_ev_usuario.set("Seleccione un usuario")
            if self.combo_ev_categoria.get() not in valores_c:
                self.combo_ev_categoria.set("Seleccione una categoría")
            if self.combo_ev_ubicacion.get() not in valores_ub:
                self.combo_ev_ubicacion.set("Seleccione una ubicación")

        except Exception as e:
            print(f"Error cargando eventos: {e}")


    # -------------------- UBICACIONES --------------------

    def configurar_pestana_ubicaciones(self):
        self.crear_encabezado(
            self.tab_ubicaciones,
            "Ubicaciones",
            "Administra recintos y consulta el ranking de ocupación y demanda."
        )

        cuerpo = ctk.CTkFrame(self.tab_ubicaciones, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=10, pady=5)
        cuerpo.grid_columnconfigure(0, weight=3)
        cuerpo.grid_columnconfigure(1, weight=1)
        cuerpo.grid_rowconfigure(0, weight=3)
        cuerpo.grid_rowconfigure(1, weight=2)

        # ---------------- Requerimiento 08  ------------------
        tabla = ctk.CTkFrame(cuerpo)
        tabla.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        form = ctk.CTkScrollableFrame(cuerpo, width=350)
        form.grid(row=0, column=1, sticky="nsew")

        self.tree_ubicaciones = self.crear_treeview(
            tabla,
            ("ID", "Nombre", "Dirección", "Ciudad", "Capacidad"),
            (70, 170, 210, 150, 100)
        )
        self.tree_ubicaciones.bind(
            "<<TreeviewSelect>>",
            self.cargar_ubicacion_seleccionada
        )

        ctk.CTkLabel(
            form,
            text="Formulario de ubicación",
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(pady=(10, 15))

        self.entry_ubi_nombre = ctk.CTkEntry(form, placeholder_text="Nombre del recinto")
        self.entry_ubi_nombre.pack(fill="x", padx=10, pady=6)

        self.entry_ubi_direccion = ctk.CTkEntry(form, placeholder_text="Dirección")
        self.entry_ubi_direccion.pack(fill="x", padx=10, pady=6)

        self.entry_ubi_ciudad = ctk.CTkEntry(form, placeholder_text="Ciudad")
        self.entry_ubi_ciudad.pack(fill="x", padx=10, pady=6)

        self.entry_ubi_capacidad = ctk.CTkEntry(form, placeholder_text="Capacidad")
        self.entry_ubi_capacidad.pack(fill="x", padx=10, pady=6)

        ctk.CTkButton(
            form, text="➕ Registrar ubicación", command=self.agregar_ubicacion
        ).pack(fill="x", padx=10, pady=(15, 5))

        ctk.CTkButton(
            form, text="💾 Actualizar seleccionada", command=self.actualizar_ubicacion
        ).pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(
            form,
            text="🧹 Nueva / Limpiar",
            command=self.limpiar_form_ubicacion,
            fg_color="gray"
        ).pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(
            form,
            text="🗑️ Eliminar seleccionada",
            command=self.eliminar_ubicacion,
            fg_color="#b33939",
            hover_color="#8f2d2d"
        ).pack(fill="x", padx=10, pady=5)

        # ---------------- Requerimiento 10: Reporte analítico ----------------
        reporte_frame = ctk.CTkFrame(cuerpo)
        reporte_frame.grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="nsew",
            pady=(10, 0)
        )

        ctk.CTkLabel(
            reporte_frame,
            text="📊 Reporte de ocupación y demanda de espacios",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=15, pady=(12, 2))

        ctk.CTkLabel(
            reporte_frame,
            text="Ranking dinámico de recintos según la cantidad de eventos asociados.",
            font=ctk.CTkFont(size=11)
        ).pack(anchor="w", padx=15, pady=(0, 4))

        self.label_resumen_ubicaciones = ctk.CTkLabel(
            reporte_frame,
            text="Cargando información...",
            font=ctk.CTkFont(size=12)
        )
        self.label_resumen_ubicaciones.pack(anchor="w", padx=15, pady=(0, 8))

        
        self.tree_reporte_ubicaciones = self.crear_treeview(
            reporte_frame,
            ("Ranking", "Ubicación", "Ciudad", "Capacidad", "Eventos agendados", "Demanda"),
            (80, 220, 150, 100, 145, 100)
        )

    def ubicacion_seleccionada_id(self):
        sel = self.tree_ubicaciones.selection()
        if not sel:
            return None
        return self.tree_ubicaciones.item(sel[0])["values"][0]

    def cargar_ubicacion_seleccionada(self, _=None):
        sel = self.tree_ubicaciones.selection()
        if not sel:
            return

        vals = self.tree_ubicaciones.item(sel[0])["values"]
        self.entry_ubi_nombre.delete(0, tk.END)
        self.entry_ubi_nombre.insert(0, vals[1])
        self.entry_ubi_direccion.delete(0, tk.END)
        self.entry_ubi_direccion.insert(0, vals[2])
        self.entry_ubi_ciudad.delete(0, tk.END)
        self.entry_ubi_ciudad.insert(0, vals[3])
        self.entry_ubi_capacidad.delete(0, tk.END)
        self.entry_ubi_capacidad.insert(0, vals[4])

    def limpiar_form_ubicacion(self):
        self.tree_ubicaciones.selection_remove(self.tree_ubicaciones.selection())
        self.entry_ubi_nombre.delete(0, tk.END)
        self.entry_ubi_direccion.delete(0, tk.END)
        self.entry_ubi_ciudad.delete(0, tk.END)
        self.entry_ubi_capacidad.delete(0, tk.END)

    def _datos_ubicacion_formulario(self):
        nombre = self.entry_ubi_nombre.get().strip()
        direccion = self.entry_ubi_direccion.get().strip()
        ciudad = self.entry_ubi_ciudad.get().strip()
        capacidad = self.entry_ubi_capacidad.get().strip()

        if not nombre or not direccion or not ciudad or not capacidad:
            raise ValueError("Todos los campos son obligatorios.")

        if not capacidad.isdigit() or int(capacidad) <= 0:
            raise ValueError("La capacidad debe ser un número entero mayor a 0.")

        return nombre, direccion, ciudad, int(capacidad)

    def agregar_ubicacion(self):
        try:
            datos = self._datos_ubicacion_formulario()
            self.ejecutar_consulta("""
                INSERT INTO ubicaciones (nombre, direccion, ciudad, capacidad)
                VALUES (%s, %s, %s, %s)
            """, datos)

            self.limpiar_form_ubicacion()
            self.actualizar_todas_las_tablas()
            messagebox.showinfo("Éxito", "Ubicación registrada correctamente.")
        except ValueError as e:
            messagebox.showwarning("Datos inválidos", str(e))
        except Exception as e:
            messagebox.showerror("Error de base de datos", str(e))

    def actualizar_ubicacion(self):
        uid = self.ubicacion_seleccionada_id()
        if uid is None:
            return messagebox.showwarning(
                "Selección requerida",
                "Selecciona una ubicación para actualizar."
            )

        try:
            nombre, direccion, ciudad, capacidad = self._datos_ubicacion_formulario()
            self.ejecutar_consulta(
                """
                UPDATE ubicaciones
                SET nombre=%s, direccion=%s, ciudad=%s, capacidad=%s
                WHERE id_ubicacion=%s
                """,
                (nombre, direccion, ciudad, capacidad, uid)
            )
            self.actualizar_todas_las_tablas()
            messagebox.showinfo("Éxito", "Ubicación actualizada.")
        except ValueError as e:
            messagebox.showwarning("Datos inválidos", str(e))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def eliminar_ubicacion(self):
        uid = self.ubicacion_seleccionada_id()
        if uid is None:
            return messagebox.showwarning(
                "Selección requerida",
                "Selecciona una ubicación."
            )

        if not messagebox.askyesno("Confirmar", "¿Eliminar la ubicación seleccionada?"):
            return

        try:
            self.ejecutar_consulta(
                "DELETE FROM ubicaciones WHERE id_ubicacion=%s",
                (uid,)
            )
            self.limpiar_form_ubicacion()
            self.actualizar_todas_las_tablas()
            messagebox.showinfo("Eliminado", "Ubicación eliminada.")
        except psycopg2.errors.ForeignKeyViolation:
            messagebox.showerror(
                "No se puede eliminar",
                "Esta ubicación tiene eventos asociados. Elimina o reasigna esos eventos primero."
            )
        except Exception as e:
            messagebox.showerror("No se pudo eliminar", str(e))

    def cargar_datos_ubicaciones(self):
        try:
            rows = self.ejecutar_consulta(
                """
                SELECT id_ubicacion, nombre, direccion, ciudad, capacidad
                FROM ubicaciones
                ORDER BY nombre
                """,
                fetch=True
            )

            for item in self.tree_ubicaciones.get_children():
                self.tree_ubicaciones.delete(item)

            self.ubicaciones_combo = {}

            for row in rows:
                self.tree_ubicaciones.insert("", "end", values=row)
                etiqueta = f"{row[1]} - {row[3]} (#{row[0]})"
                self.ubicaciones_combo[etiqueta] = row[0]

        except Exception as e:
            print(f"Error cargando ubicaciones: {e}")

    def cargar_reporte_ubicaciones(self):
        """Requirimiento 10"""
        try:
            rows = self.ejecutar_consulta("""
                SELECT
                    ub.nombre,
                    ub.ciudad,
                    ub.capacidad,
                    COUNT(e.id_evento) AS total_eventos
                FROM ubicaciones ub
                LEFT JOIN eventos e
                    ON e.id_ubicacion = ub.id_ubicacion
                GROUP BY ub.id_ubicacion, ub.nombre, ub.ciudad, ub.capacidad
                ORDER BY total_eventos DESC, ub.nombre
            """, fetch=True)

            for item in self.tree_reporte_ubicaciones.get_children():
                self.tree_reporte_ubicaciones.delete(item)

            total_eventos = sum(row[3] for row in rows)
            ubicaciones_sin_uso = 0

            for posicion, row in enumerate(rows, start=1):
                nombre, ciudad, capacidad, eventos = row

                if eventos == 0:
                    ubicaciones_sin_uso += 1

                if total_eventos == 0:
                    porcentaje = 0
                else:
                    porcentaje = round((eventos * 100) / total_eventos, 2)

                self.tree_reporte_ubicaciones.insert(
                    "",
                    "end",
                    values=(
                        posicion, nombre, ciudad, capacidad, eventos,f"{porcentaje}%")
                )

            self.label_resumen_ubicaciones.configure(
                text=(
                    f"Ubicaciones: {len(rows)}   |   "
                    f"Eventos asociados: {total_eventos}   |   "
                    f"Ubicaciones sin uso: {ubicaciones_sin_uso}"
                )
            )

        except Exception as e:
            print(f"Error cargando reporte de ubicaciones: {e}")
            self.label_resumen_ubicaciones.configure(
                text="No se pudo cargar el reporte. Revisa que eventos tenga la columna id_ubicacion."
            )

    def configurar_pestana_disponibilidad(self):
        self.crear_encabezado(
            self.tab_disponibilidad,
            "Disponibilidad de usuarios",
            "Administra franjas de disponibilidad y consulta qué usuarios están libres en un horario específico."
        )

        cuerpo = ctk.CTkFrame(self.tab_disponibilidad, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=10, pady=5)
        cuerpo.grid_columnconfigure(0, weight=3)
        cuerpo.grid_columnconfigure(1, weight=1)
        cuerpo.grid_rowconfigure(0, weight=3)
        cuerpo.grid_rowconfigure(1, weight=2)

        # ----------------Requerimiento 11 de las disponibilidades ----------------
        tabla = ctk.CTkFrame(cuerpo)
        tabla.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        form = ctk.CTkScrollableFrame(cuerpo, width=350)
        form.grid(row=0, column=1, sticky="nsew")

        self.tree_disponibilidades = self.crear_treeview(
            tabla,
            ("ID", "Usuario", "Fecha", "Inicio", "Fin", "Estado"),
            (70, 220, 120, 90, 90, 130)
        )
        self.tree_disponibilidades.bind(
            "<<TreeviewSelect>>",
            self.cargar_disponibilidad_seleccionada
        )

        ctk.CTkLabel(
            form,
            text="Formulario de disponibilidad",
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(pady=(10, 15))

        ctk.CTkLabel(form, text="Usuario").pack(anchor="w", padx=10, pady=(5, 2))
        self.combo_disp_usuario = ctk.CTkComboBox(
            form,
            values=["Seleccione un usuario"],
            state="readonly"
        )
        self.combo_disp_usuario.set("Seleccione un usuario")
        self.combo_disp_usuario.pack(fill="x", padx=10, pady=4)

        ctk.CTkLabel(form, text="Fecha").pack(anchor="w", padx=10, pady=(8, 2))
        self.fecha_disponibilidad = self.crear_selector_fecha(form)
        self.fecha_disponibilidad.pack(fill="x", padx=10, pady=4)

        ctk.CTkLabel(form, text="Horario").pack(anchor="w", padx=10, pady=(8, 2))
        fila_horario = ctk.CTkFrame(form, fg_color="transparent")
        fila_horario.pack(fill="x", padx=10)

        self.hora_disp_inicio = ctk.CTkEntry(
            fila_horario,
            placeholder_text="Inicio HH:MM"
        )
        self.hora_disp_inicio.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.hora_disp_fin = ctk.CTkEntry(
            fila_horario,
            placeholder_text="Fin HH:MM"
        )
        self.hora_disp_fin.pack(side="left", fill="x", expand=True, padx=(4, 0))

        ctk.CTkLabel(form, text="Estado de disponibilidad").pack(
            anchor="w", padx=10, pady=(8, 2)
        )
        self.combo_disp_tipo = ctk.CTkComboBox(
            form,
            values=["Seleccione un estado"],
            state="readonly"
        )
        self.combo_disp_tipo.set("Seleccione un estado")
        self.combo_disp_tipo.pack(fill="x", padx=10, pady=4)

        ctk.CTkButton(
            form,
            text="➕ Registrar disponibilidad",
            command=self.agregar_disponibilidad
        ).pack(fill="x", padx=10, pady=(15, 5))

        ctk.CTkButton(
            form,
            text="💾 Actualizar seleccionada",
            command=self.actualizar_disponibilidad
        ).pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(
            form,
            text="🧹 Nueva / Limpiar",
            command=self.limpiar_form_disponibilidad,
            fg_color="gray"
        ).pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(
            form,
            text="🗑️ Eliminar seleccionada",
            command=self.eliminar_disponibilidad,
            fg_color="#b33939",
            hover_color="#8f2d2d"
        ).pack(fill="x", padx=10, pady=5)

        # ---------------- RF-12: análisis de intervalos ----------------
        analisis = ctk.CTkFrame(cuerpo)
        analisis.grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="nsew",
            pady=(10, 0)
        )

        ctk.CTkLabel(
            analisis,
            text="🔎 Análisis de usuarios libres y disponibles",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=15, pady=(12, 2))

        ctk.CTkLabel(
            analisis,
            text="Cruza las franjas declaradas con los eventos ya agendados para detectar solapamientos.",
            font=ctk.CTkFont(size=11)
        ).pack(anchor="w", padx=15, pady=(0, 8))

        filtros = ctk.CTkFrame(analisis, fg_color="transparent")
        filtros.pack(fill="x", padx=15, pady=(0, 8))

        self.fecha_busqueda_disponibilidad = self.crear_selector_fecha(filtros)
        self.fecha_busqueda_disponibilidad.pack(side="left", padx=(0, 6))

        self.hora_busqueda_inicio = ctk.CTkEntry(
            filtros,
            width=95,
            placeholder_text="Inicio HH:MM"
        )
        self.hora_busqueda_inicio.pack(side="left", padx=4)

        self.hora_busqueda_fin = ctk.CTkEntry(
            filtros,
            width=95,
            placeholder_text="Fin HH:MM"
        )
        self.hora_busqueda_fin.pack(side="left", padx=4)

        ctk.CTkButton(
            filtros,
            text="Buscar disponibilidad",
            width=180,
            command=self.buscar_usuarios_disponibles
        ).pack(side="left", padx=(8, 0))

        self.label_resumen_disponibilidad = ctk.CTkLabel(
            analisis,
            text="Define una fecha y un rango horario para realizar el análisis.",
            font=ctk.CTkFont(size=12)
        )
        self.label_resumen_disponibilidad.pack(anchor="w", padx=15, pady=(0, 6))

        self.tree_analisis_disponibilidad = self.crear_treeview(
            analisis,
            ("Usuario", "Resultado", "Detalle"),
            (250, 150, 520)
        )

        self.limpiar_form_disponibilidad()
        self.hora_busqueda_inicio.insert(0, "14:00")
        self.hora_busqueda_fin.insert(0, "16:00")

    def disponibilidad_seleccionada_id(self):
        sel = self.tree_disponibilidades.selection()
        if not sel:
            return None
        return self.tree_disponibilidades.item(sel[0])["values"][0]

    def cargar_disponibilidad_seleccionada(self, _=None):
        sel = self.tree_disponibilidades.selection()
        if not sel:
            return

        vals = self.tree_disponibilidades.item(sel[0])["values"]
        self.combo_disp_usuario.set(vals[1])
        self.establecer_fecha(self.fecha_disponibilidad, str(vals[2]))
        self.hora_disp_inicio.delete(0, tk.END)
        self.hora_disp_inicio.insert(0, str(vals[3]))
        self.hora_disp_fin.delete(0, tk.END)
        self.hora_disp_fin.insert(0, str(vals[4]))
        self.combo_disp_tipo.set(vals[5])

    def limpiar_form_disponibilidad(self):
        if hasattr(self, "tree_disponibilidades"):
            self.tree_disponibilidades.selection_remove(
                self.tree_disponibilidades.selection()
            )
        self.combo_disp_usuario.set("Seleccione un usuario")
        self.combo_disp_tipo.set("Seleccione un estado")
        self.establecer_fecha(self.fecha_disponibilidad, datetime.now())
        self.hora_disp_inicio.delete(0, tk.END)
        self.hora_disp_inicio.insert(0, "09:00")
        self.hora_disp_fin.delete(0, tk.END)
        self.hora_disp_fin.insert(0, "10:00")

    def datos_disponibilidad_formulario(self):
        usuario = self.usuarios_combo.get(self.combo_disp_usuario.get())
        tipo = self.tipos_disponibilidad_combo.get(self.combo_disp_tipo.get())
        fecha = self.obtener_fecha(self.fecha_disponibilidad)

        try:
            inicio = datetime.strptime(self.hora_disp_inicio.get().strip(), "%H:%M").time()
            fin = datetime.strptime(self.hora_disp_fin.get().strip(), "%H:%M").time()
        except ValueError:
            raise ValueError("Las horas deben tener formato HH:MM, por ejemplo 08:30.")

        if usuario is None:
            raise ValueError("Selecciona un usuario.")
        if tipo is None:
            raise ValueError("Selecciona un estado de disponibilidad.")
        if fin <= inicio:
            raise ValueError("La hora final debe ser posterior a la hora de inicio.")

        return usuario, fecha, inicio, fin, tipo

    def validar_solapamiento_disponibilidad(self, id_usuario, fecha, inicio, fin, id_excluir=None):
        sql = """
            SELECT id_disponibilidad
            FROM disponibilidades
            WHERE id_usuario = %s
            AND fecha = %s
            AND hora_inicio < %s
            AND hora_fin > %s
        """
        params = [id_usuario, fecha, fin, inicio]

        if id_excluir is not None:
            sql += " AND id_disponibilidad <> %s"
            params.append(id_excluir)

        sql += " LIMIT 1"
        conflicto = self.ejecutar_consulta(sql, tuple(params), fetch=True)
        if conflicto:
            raise ValueError(
                "El usuario ya tiene otra franja de disponibilidad que se cruza con ese horario."
            )

    def agregar_disponibilidad(self):
        try:
            usuario, fecha, inicio, fin, tipo = self.datos_disponibilidad_formulario()
            self.validar_solapamiento_disponibilidad(usuario, fecha, inicio, fin)

            self.ejecutar_consulta("""
                INSERT INTO disponibilidades
                    (id_usuario, fecha, hora_inicio, hora_fin, id_tipo_disponibilidad)
                VALUES (%s, %s, %s, %s, %s)
            """, (usuario, fecha, inicio, fin, tipo))

            self.limpiar_form_disponibilidad()
            self.actualizar_todas_las_tablas()
            messagebox.showinfo("Éxito", "Disponibilidad registrada correctamente.")
        except ValueError as e:
            messagebox.showwarning("Datos inválidos", str(e))
        except Exception as e:
            messagebox.showerror("Error de base de datos", str(e))

    def actualizar_disponibilidad(self):
        did = self.disponibilidad_seleccionada_id()
        if did is None:
            return messagebox.showwarning(
                "Selección requerida",
                "Selecciona una disponibilidad para actualizar."
            )

        try:
            usuario, fecha, inicio, fin, tipo = self.datos_disponibilidad_formulario()
            self.validar_solapamiento_disponibilidad(usuario, fecha, inicio, fin, did)

            self.ejecutar_consulta("""
                UPDATE disponibilidades
                SET id_usuario=%s,
                    fecha=%s,
                    hora_inicio=%s,
                    hora_fin=%s,
                    id_tipo_disponibilidad=%s
                WHERE id_disponibilidad=%s
            """, (usuario, fecha, inicio, fin, tipo, did))

            self.actualizar_todas_las_tablas()
            messagebox.showinfo("Éxito", "Disponibilidad actualizada.")
        except ValueError as e:
            messagebox.showwarning("Datos inválidos", str(e))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def eliminar_disponibilidad(self):
        did = self.disponibilidad_seleccionada_id()
        if did is None:
            return messagebox.showwarning(
                "Selección requerida",
                "Selecciona una disponibilidad."
            )

        if not messagebox.askyesno("Confirmar", "¿Eliminar la disponibilidad seleccionada?"):
            return

        try:
            self.ejecutar_consulta(
                "DELETE FROM disponibilidades WHERE id_disponibilidad=%s",
                (did,)
            )
            self.limpiar_form_disponibilidad()
            self.actualizar_todas_las_tablas()
            messagebox.showinfo("Eliminado", "Disponibilidad eliminada.")
        except Exception as e:
            messagebox.showerror("No se pudo eliminar", str(e))

    def cargar_datos_disponibilidades(self):
        try:
            tipos = self.ejecutar_consulta("""
                SELECT id_tipo_disponibilidad, nombre
                FROM tipos_disponibilidad
                ORDER BY id_tipo_disponibilidad
            """, fetch=True)

            self.tipos_disponibilidad_combo = {
                nombre: tid for tid, nombre in tipos
            }

            valores_tipos = ["Seleccione un estado"] + list(
                self.tipos_disponibilidad_combo.keys()
            )
            self.combo_disp_tipo.configure(values=valores_tipos)
            if self.combo_disp_tipo.get() not in valores_tipos:
                self.combo_disp_tipo.set("Seleccione un estado")

            valores_usuarios = ["Seleccione un usuario"] + list(self.usuarios_combo.keys())
            self.combo_disp_usuario.configure(values=valores_usuarios)
            if self.combo_disp_usuario.get() not in valores_usuarios:
                self.combo_disp_usuario.set("Seleccione un usuario")

            rows = self.ejecutar_consulta("""
                SELECT
                    d.id_disponibilidad,
                    u.id_usuario,
                    u.nombre,
                    u.apellido,
                    d.fecha,
                    d.hora_inicio,
                    d.hora_fin,
                    td.nombre
                FROM disponibilidades d
                JOIN usuarios u
                    ON u.id_usuario = d.id_usuario
                JOIN tipos_disponibilidad td
                    ON td.id_tipo_disponibilidad = d.id_tipo_disponibilidad
                ORDER BY d.fecha DESC, d.hora_inicio, u.nombre, u.apellido
            """, fetch=True)

            for item in self.tree_disponibilidades.get_children():
                self.tree_disponibilidades.delete(item)

            for row in rows:
                usuario = f"{row[2]} {row[3]} — #{row[1]}"
                fecha = row[4].strftime("%Y-%m-%d")
                inicio = row[5].strftime("%H:%M")
                fin = row[6].strftime("%H:%M")
                self.tree_disponibilidades.insert(
                    "",
                    "end",
                    values=(row[0], usuario, fecha, inicio, fin, row[7])
                )

        except Exception as e:
            print(f"Error cargando disponibilidades: {e}")

    def buscar_usuarios_disponibles(self):
        try:
            fecha = self.obtener_fecha(self.fecha_busqueda_disponibilidad)
            inicio_texto = self.hora_busqueda_inicio.get().strip()
            fin_texto = self.hora_busqueda_fin.get().strip()

            inicio = datetime.strptime(inicio_texto, "%H:%M").time()
            fin = datetime.strptime(fin_texto, "%H:%M").time()

            if fin <= inicio:
                raise ValueError("La hora final debe ser posterior a la hora de inicio.")

            fecha_date = datetime.strptime(fecha, "%Y-%m-%d").date()
            inicio_evento = datetime.combine(fecha_date, inicio)
            fin_evento = datetime.combine(fecha_date, fin)

            # 1. Usuarios activos.
            usuarios = self.ejecutar_consulta("""
                SELECT id_usuario, nombre, apellido
                FROM usuarios
                WHERE activo = TRUE
                ORDER BY nombre, apellido
            """, fetch=True)

            # 2. Usuarios que declararon una franja disponible que cubre el horario completo.
            disponibles_rows = self.ejecutar_consulta("""
                SELECT d.id_usuario
                FROM disponibilidades d
                JOIN tipos_disponibilidad td
                    ON td.id_tipo_disponibilidad = d.id_tipo_disponibilidad
                WHERE d.fecha = %s
                AND td.nombre = 'disponible'
                AND d.hora_inicio <= %s
                AND d.hora_fin >= %s
            """, (fecha, inicio, fin), fetch=True)
            ids_disponibles = {row[0] for row in disponibles_rows}

            # 3. Franjas declaradas como ocupado o no disponible que se cruzan con la búsqueda.
            bloqueados_rows = self.ejecutar_consulta("""
                SELECT d.id_usuario
                FROM disponibilidades d
                JOIN tipos_disponibilidad td
                    ON td.id_tipo_disponibilidad = d.id_tipo_disponibilidad
                WHERE d.fecha = %s
                AND td.nombre IN ('ocupado', 'no disponible')
                AND d.hora_inicio < %s
                AND d.hora_fin > %s
            """, (fecha, fin, inicio), fetch=True)
            ids_bloqueados = {row[0] for row in bloqueados_rows}

            # 4. Propietarios que ya tienen un evento sobrepuesto.
            propietarios_rows = self.ejecutar_consulta("""
                SELECT DISTINCT id_usuario_propietario
                FROM eventos
                WHERE fecha_inicio < %s
                AND fecha_fin > %s
            """, (fin_evento, inicio_evento), fetch=True)
            ids_con_evento = {row[0] for row in propietarios_rows}

            # 5. Invitados que ya participan en un evento sobrepuesto.
            invitados_rows = self.ejecutar_consulta("""
                SELECT DISTINCT p.id_invitado
                FROM participaciones p
                JOIN eventos e ON e.id_evento = p.id_evento
                WHERE e.fecha_inicio < %s
                AND e.fecha_fin > %s
            """, (fin_evento, inicio_evento), fetch=True)
            ids_con_evento.update(row[0] for row in invitados_rows)

            for item in self.tree_analisis_disponibilidad.get_children():
                self.tree_analisis_disponibilidad.delete(item)

            cantidad_disponibles = 0

            for id_usuario, nombre, apellido in usuarios:
                usuario = f"{nombre} {apellido} — #{id_usuario}"

                if id_usuario not in ids_disponibles:
                    resultado = "No disponible"
                    detalle = "No tiene una franja disponible que cubra todo el horario."
                elif id_usuario in ids_bloqueados:
                    resultado = "No disponible"
                    detalle = "Tiene una franja ocupada o no disponible que se cruza con el horario."
                elif id_usuario in ids_con_evento:
                    resultado = "No disponible"
                    detalle = "Tiene un evento agendado que se cruza con el horario."
                else:
                    resultado = "Disponible"
                    detalle = "Tiene disponibilidad registrada y no posee eventos sobrepuestos."
                    cantidad_disponibles += 1

                self.tree_analisis_disponibilidad.insert(
                    "",
                    "end",
                    values=(usuario, resultado, detalle)
                )

            self.label_resumen_disponibilidad.configure(
                text=(
                    f"Horario analizado: {fecha} de {inicio_texto} a {fin_texto}   |   "
                    f"Usuarios disponibles: {cantidad_disponibles} de {len(usuarios)}"
                )
            )

        except ValueError as e:
            messagebox.showwarning("Datos inválidos", str(e))
        except Exception as e:
            messagebox.showerror("No se pudo realizar el análisis", str(e))

    def configurar_pestana_tareas(self):
        self.crear_encabezado(
            self.tab_tareas,
            "Tareas asociadas a eventos",
            "Administra tareas por evento y consulta la carga de trabajo, pendientes y vencimientos por usuario."
        )

        cuerpo = ctk.CTkFrame(self.tab_tareas, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=10, pady=5)
        cuerpo.grid_columnconfigure(0, weight=3)
        cuerpo.grid_columnconfigure(1, weight=1)
        cuerpo.grid_rowconfigure(0, weight=3)
        cuerpo.grid_rowconfigure(1, weight=2)

        # ---------------- RF-15: CRUD de tareas ----------------
        tabla = ctk.CTkFrame(cuerpo)
        tabla.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        form = ctk.CTkScrollableFrame(cuerpo, width=360)
        form.grid(row=0, column=1, sticky="nsew")

        self.tree_tareas = self.crear_treeview(
            tabla,
            ("ID", "Evento", "Título", "Responsable", "Prioridad", "Estado", "Fecha límite", "Situación"),
            (60, 190, 190, 190, 90, 110, 110, 110)
        )
        self.tree_tareas.bind("<<TreeviewSelect>>", self.cargar_tarea_seleccionada)

        ctk.CTkLabel(
            form,
            text="Formulario de tarea",
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(pady=(10, 15))

        self.entry_tarea_titulo = ctk.CTkEntry(form, placeholder_text="Título de la tarea")
        self.entry_tarea_titulo.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(form, text="Descripción").pack(anchor="w", padx=10, pady=(8, 2))
        self.text_tarea_descripcion = ctk.CTkTextbox(form, height=80)
        self.text_tarea_descripcion.pack(fill="x", padx=10, pady=4)

        ctk.CTkLabel(form, text="Evento asociado").pack(anchor="w", padx=10, pady=(8, 2))
        self.combo_tarea_evento = ctk.CTkComboBox(
            form,
            values=["Seleccione un evento"],
            state="readonly"
        )
        self.combo_tarea_evento.set("Seleccione un evento")
        self.combo_tarea_evento.pack(fill="x", padx=10, pady=4)

        ctk.CTkLabel(form, text="Responsable").pack(anchor="w", padx=10, pady=(8, 2))
        self.combo_tarea_usuario = ctk.CTkComboBox(
            form,
            values=["Seleccione un usuario"],
            state="readonly"
        )
        self.combo_tarea_usuario.set("Seleccione un usuario")
        self.combo_tarea_usuario.pack(fill="x", padx=10, pady=4)

        ctk.CTkLabel(form, text="Prioridad").pack(anchor="w", padx=10, pady=(8, 2))
        self.combo_tarea_prioridad = ctk.CTkComboBox(
            form,
            values=["baja", "media", "alta"],
            state="readonly"
        )
        self.combo_tarea_prioridad.set("media")
        self.combo_tarea_prioridad.pack(fill="x", padx=10, pady=4)

        ctk.CTkLabel(form, text="Estado").pack(anchor="w", padx=10, pady=(8, 2))
        self.combo_tarea_estado = ctk.CTkComboBox(
            form,
            values=["pendiente", "en progreso", "completada", "cancelada"],
            state="readonly"
        )
        self.combo_tarea_estado.set("pendiente")
        self.combo_tarea_estado.pack(fill="x", padx=10, pady=4)

        ctk.CTkLabel(form, text="Fecha límite").pack(anchor="w", padx=10, pady=(8, 2))
        self.fecha_limite_tarea = self.crear_selector_fecha(form)
        self.fecha_limite_tarea.pack(fill="x", padx=10, pady=4)

        ctk.CTkButton(
            form,
            text="➕ Crear tarea",
            command=self.agregar_tarea
        ).pack(fill="x", padx=10, pady=(15, 5))

        ctk.CTkButton(
            form,
            text="💾 Actualizar seleccionada",
            command=self.actualizar_tarea
        ).pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(
            form,
            text="🧹 Nueva / Limpiar",
            command=self.limpiar_form_tarea,
            fg_color="gray"
        ).pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(
            form,
            text="🗑️ Eliminar seleccionada",
            command=self.eliminar_tarea,
            fg_color="#b33939",
            hover_color="#8f2d2d"
        ).pack(fill="x", padx=10, pady=5)

        # ---------------- Requerimientos 16 y 17: reportes ----------------
        reporte = ctk.CTkFrame(cuerpo)
        reporte.grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="nsew",
            pady=(10, 0)
        )
        reporte.grid_columnconfigure(0, weight=1)
        reporte.grid_columnconfigure(1, weight=1)
        reporte.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            reporte,
            text="📊 Reporte de carga de trabajo y tareas pendientes",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(12, 2))

        self.label_resumen_tareas = ctk.CTkLabel(
            reporte,
            text="Cargando información...",
            font=ctk.CTkFont(size=12)
        )
        self.label_resumen_tareas.grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="w",
            padx=15,
            pady=(0, 6)
        )

        resumen_frame = ctk.CTkFrame(reporte)
        resumen_frame.grid(row=2, column=0, sticky="nsew", padx=(10, 5), pady=(0, 10))

        vencidas_frame = ctk.CTkFrame(reporte)
        vencidas_frame.grid(row=2, column=1, sticky="nsew", padx=(5, 10), pady=(0, 10))

        ctk.CTkLabel(
            resumen_frame,
            text="Carga activa por usuario",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=15, pady=(8, 4))

        self.tree_reporte_tareas = self.crear_treeview(
            resumen_frame,
            ("Usuario", "Pendientes", "En progreso", "Activas", "Vencidas"),
            (220, 90, 100, 90, 90)
        )

        ctk.CTkLabel(
            vencidas_frame,
            text="Eventos con tareas vencidas",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=15, pady=(8, 4))

        self.tree_tareas_vencidas = self.crear_treeview(
            vencidas_frame,
            ("Tarea", "Evento", "Responsable", "Fecha límite", "Días vencida"),
            (190, 180, 180, 110, 100)
        )

        self.limpiar_form_tarea()

    def tarea_seleccionada_id(self):
        sel = self.tree_tareas.selection()
        if not sel:
            return None
        return self.tree_tareas.item(sel[0])["values"][0]

    def cargar_tarea_seleccionada(self, _=None):
        tid = self.tarea_seleccionada_id()
        if tid is None:
            return

        try:
            rows = self.ejecutar_consulta("""
                SELECT
                    t.titulo,
                    t.descripcion,
                    t.prioridad,
                    t.estado,
                    t.fecha_limite,
                    t.id_evento,
                    e.titulo,
                    t.id_usuario,
                    u.nombre,
                    u.apellido
                FROM tareas t
                JOIN eventos e ON e.id_evento = t.id_evento
                JOIN usuarios u ON u.id_usuario = t.id_usuario
                WHERE t.id_tarea = %s
            """, (tid,), fetch=True)

            if not rows:
                return

            row = rows[0]
            evento = f"{row[6]} - #{row[5]}"
            usuario = f"{row[8]} {row[9]} — #{row[7]}"

            self.entry_tarea_titulo.delete(0, tk.END)
            self.entry_tarea_titulo.insert(0, row[0])
            self.text_tarea_descripcion.delete("1.0", tk.END)
            self.text_tarea_descripcion.insert("1.0", row[1] or "")
            self.combo_tarea_evento.set(evento)
            self.combo_tarea_usuario.set(usuario)
            self.combo_tarea_prioridad.set(row[2])
            self.combo_tarea_estado.set(row[3])
            self.establecer_fecha(self.fecha_limite_tarea, row[4])

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def limpiar_form_tarea(self):
        if hasattr(self, "tree_tareas"):
            self.tree_tareas.selection_remove(self.tree_tareas.selection())
        self.entry_tarea_titulo.delete(0, tk.END)
        self.text_tarea_descripcion.delete("1.0", tk.END)
        self.combo_tarea_evento.set("Seleccione un evento")
        self.combo_tarea_usuario.set("Seleccione un usuario")
        self.combo_tarea_prioridad.set("media")
        self.combo_tarea_estado.set("pendiente")
        self.establecer_fecha(self.fecha_limite_tarea, datetime.now())

    def datos_tarea_formulario(self):
        titulo = self.entry_tarea_titulo.get().strip()
        descripcion = self.text_tarea_descripcion.get("1.0", tk.END).strip()
        evento = self.eventos_combo.get(self.combo_tarea_evento.get())
        usuario = self.usuarios_combo.get(self.combo_tarea_usuario.get())
        prioridad = self.combo_tarea_prioridad.get()
        estado = self.combo_tarea_estado.get()
        fecha_limite = self.obtener_fecha(self.fecha_limite_tarea)

        if not titulo:
            raise ValueError("Indica el título de la tarea.")
        if evento is None:
            raise ValueError("Selecciona el evento asociado.")
        if usuario is None:
            raise ValueError("Selecciona el usuario responsable.")
        if prioridad not in ("baja", "media", "alta"):
            raise ValueError("Selecciona una prioridad válida.")
        if estado not in ("pendiente", "en progreso", "completada", "cancelada"):
            raise ValueError("Selecciona un estado válido.")

        return titulo, descripcion, prioridad, estado, fecha_limite, evento, usuario

    def agregar_tarea(self):
        try:
            datos = self.datos_tarea_formulario()
            self.ejecutar_consulta("""
                INSERT INTO tareas
                    (titulo, descripcion, prioridad, estado, fecha_limite, id_evento, id_usuario)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, datos)

            self.limpiar_form_tarea()
            self.actualizar_todas_las_tablas()
            messagebox.showinfo("Éxito", "Tarea creada correctamente.")
        except ValueError as e:
            messagebox.showwarning("Datos inválidos", str(e))
        except Exception as e:
            messagebox.showerror("Error de base de datos", str(e))

    def actualizar_tarea(self):
        tid = self.tarea_seleccionada_id()
        if tid is None:
            return messagebox.showwarning(
                "Selección requerida",
                "Selecciona una tarea para actualizar."
            )

        try:
            titulo, descripcion, prioridad, estado, fecha_limite, evento, usuario = self.datos_tarea_formulario()
            self.ejecutar_consulta("""
                UPDATE tareas
                SET titulo=%s,
                    descripcion=%s,
                    prioridad=%s,
                    estado=%s,
                    fecha_limite=%s,
                    id_evento=%s,
                    id_usuario=%s
                WHERE id_tarea=%s
            """, (
                titulo, descripcion, prioridad, estado,
                fecha_limite, evento, usuario, tid
            ))

            self.actualizar_todas_las_tablas()
            messagebox.showinfo("Éxito", "Tarea actualizada.")
        except ValueError as e:
            messagebox.showwarning("Datos inválidos", str(e))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def eliminar_tarea(self):
        tid = self.tarea_seleccionada_id()
        if tid is None:
            return messagebox.showwarning(
                "Selección requerida",
                "Selecciona una tarea."
            )

        if not messagebox.askyesno("Confirmar", "¿Eliminar la tarea seleccionada?"):
            return

        try:
            self.ejecutar_consulta("DELETE FROM tareas WHERE id_tarea=%s", (tid,))
            self.limpiar_form_tarea()
            self.actualizar_todas_las_tablas()
            messagebox.showinfo("Eliminado", "Tarea eliminada.")
        except Exception as e:
            messagebox.showerror("No se pudo eliminar", str(e))

    def cargar_datos_tareas(self):
        try:
            valores_eventos = ["Seleccione un evento"] + list(self.eventos_combo.keys())
            valores_usuarios = ["Seleccione un usuario"] + list(self.usuarios_combo.keys())

            self.combo_tarea_evento.configure(values=valores_eventos)
            self.combo_tarea_usuario.configure(values=valores_usuarios)

            if self.combo_tarea_evento.get() not in valores_eventos:
                self.combo_tarea_evento.set("Seleccione un evento")
            if self.combo_tarea_usuario.get() not in valores_usuarios:
                self.combo_tarea_usuario.set("Seleccione un usuario")

            rows = self.ejecutar_consulta("""
                SELECT
                    t.id_tarea,
                    t.id_evento,
                    e.titulo,
                    t.titulo,
                    t.id_usuario,
                    u.nombre,
                    u.apellido,
                    t.prioridad,
                    t.estado,
                    t.fecha_limite
                FROM tareas t
                JOIN eventos e ON e.id_evento = t.id_evento
                JOIN usuarios u ON u.id_usuario = t.id_usuario
                ORDER BY t.fecha_limite, t.titulo
            """, fetch=True)

            for item in self.tree_tareas.get_children():
                self.tree_tareas.delete(item)

            for row in rows:
                evento = f"{row[2]} - #{row[1]}"
                usuario = f"{row[5]} {row[6]} — #{row[4]}"
                fecha_limite = row[9]

                if row[8] in ("pendiente", "en progreso") and fecha_limite < date.today():
                    situacion = "⚠ Vencida"
                else:
                    situacion = "Al día"

                self.tree_tareas.insert(
                    "",
                    "end",
                    values=(
                        row[0], evento, row[3], usuario,
                        row[7], row[8], fecha_limite.strftime("%Y-%m-%d"), situacion
                    )
                )

        except Exception as e:
            print(f"Error cargando tareas: {e}")

    def cargar_reporte_tareas(self):
        """RF-16 / RF-17: reporte usando consultas sencillas y conteos en Python."""
        try:
            usuarios = self.ejecutar_consulta("""
                SELECT id_usuario, nombre, apellido
                FROM usuarios
                WHERE activo = TRUE
                ORDER BY nombre, apellido
            """, fetch=True)

            tareas_activas = self.ejecutar_consulta("""
                SELECT id_usuario, estado, fecha_limite
                FROM tareas
                WHERE estado IN ('pendiente', 'en progreso')
            """, fetch=True)

            conteo = {}
            for id_usuario, _, _ in usuarios:
                conteo[id_usuario] = {
                    "pendientes": 0,
                    "en_progreso": 0,
                    "activas": 0,
                    "vencidas": 0
                }

            for id_usuario, estado, fecha_limite in tareas_activas:
                if id_usuario not in conteo:
                    continue

                conteo[id_usuario]["activas"] += 1

                if estado == "pendiente":
                    conteo[id_usuario]["pendientes"] += 1
                elif estado == "en progreso":
                    conteo[id_usuario]["en_progreso"] += 1

                if fecha_limite < date.today():
                    conteo[id_usuario]["vencidas"] += 1

            for item in self.tree_reporte_tareas.get_children():
                self.tree_reporte_tareas.delete(item)

            total_activas = 0
            total_vencidas = 0

            for id_usuario, nombre, apellido in usuarios:
                datos = conteo[id_usuario]
                total_activas += datos["activas"]
                total_vencidas += datos["vencidas"]

                usuario = f"{nombre} {apellido} — #{id_usuario}"
                self.tree_reporte_tareas.insert(
                    "",
                    "end",
                    values=(
                        usuario,
                        datos["pendientes"],
                        datos["en_progreso"],
                        datos["activas"],
                        datos["vencidas"]
                    )
                )

            vencidas = self.ejecutar_consulta("""
                SELECT
                    t.titulo,
                    e.titulo,
                    u.nombre,
                    u.apellido,
                    t.fecha_limite
                FROM tareas t
                JOIN eventos e ON e.id_evento = t.id_evento
                JOIN usuarios u ON u.id_usuario = t.id_usuario
                WHERE t.estado IN ('pendiente', 'en progreso')
                AND t.fecha_limite < CURRENT_DATE
                ORDER BY t.fecha_limite
            """, fetch=True)

            for item in self.tree_tareas_vencidas.get_children():
                self.tree_tareas_vencidas.delete(item)

            for row in vencidas:
                responsable = f"{row[2]} {row[3]}"
                dias_vencida = (date.today() - row[4]).days
                self.tree_tareas_vencidas.insert(
                    "",
                    "end",
                    values=(
                        f"⚠ {row[0]}",
                        row[1],
                        responsable,
                        row[4].strftime("%Y-%m-%d"),
                        dias_vencida
                    )
                )

            self.label_resumen_tareas.configure(
                text=(
                    f"Tareas activas: {total_activas} | "
                    f"Tareas vencidas: {total_vencidas} | "
                    f"Usuarios con seguimiento: {len(usuarios)}"
                )
            )

        except Exception as e:
            print(f"Error cargando reporte de tareas: {e}")
            self.label_resumen_tareas.configure(
                text="No se pudo cargar el reporte de tareas. Revisa la base de datos."
            )

    def actualizar_todas_las_tablas(self):
        self.cargar_datos_usuarios()
        self.cargar_datos_categorias()
        self.cargar_datos_ubicaciones()
        self.cargar_datos_eventos()
        self.cargar_reporte_ubicaciones()  # RF-10
        self.cargar_datos_disponibilidades()  # RF-11
        self.cargar_datos_tareas()  # RF-15
        self.cargar_reporte_tareas()  # RF-16 y RF-17


if __name__ == "__main__":
    app = AppAgenda()
    app.mainloop()
