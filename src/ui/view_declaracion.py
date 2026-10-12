"""
ui/view_declaracion.py
Formulario para la Declaración Jurada de Bolsistas UNMSM con autollenado.
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from ui.config import (
    COLOR_PRIMARIO, COLOR_HOVER, COLOR_FONDO, IMAGE_FILETYPES
)
from controllers.bolsista_controller import BolsistaController
from user_profile import UserProfile


class ViewDeclaracion(ctk.CTkFrame):
    """Vista de formulario para la Declaración Jurada."""

    def __init__(self, master, on_back_callback):
        super().__init__(master, fg_color=COLOR_FONDO)
        self.on_back_callback = on_back_callback
        
        self._entries = {}
        self._var_firma = tk.StringVar(value="")
        
        self._build_ui()
        self._cargar_autollenado()

    def _build_ui(self):
        """Construye los campos del formulario."""
        # Top Bar: Volver + Título
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=20, pady=(15, 10))

        ctk.CTkButton(
            top_bar,
            text="← Volver",
            width=90,
            fg_color="#555555",
            hover_color="#333333",
            command=self.on_back_callback
        ).pack(side="left")

        ctk.CTkLabel(
            top_bar,
            text="📜 Declaración Jurada de No Pertenecer a Órganos de Gobierno",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLOR_PRIMARIO
        ).pack(side="left", padx=15)

        # Botón Guardar Perfil
        ctk.CTkButton(
            top_bar,
            text="💾 Guardar Datos",
            width=110,
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            command=self._guardar_perfil_manual
        ).pack(side="right")

        # Form Scrollable Body
        form_frame = ctk.CTkScrollableFrame(self, fg_color="white", corner_radius=10)
        form_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        form_frame.columnconfigure(1, weight=1)

        campos = [
            ("ap_paterno", "Apellido Paterno *", "ROMAN"),
            ("ap_materno", "Apellido Materno *", "HURTADO"),
            ("nombres",    "Nombres Completos *", "MAXIMO LENNY"),
            ("dni",        "Nº Documento (DNI) *", "72626630"),
            ("domicilio",  "Domicilio", "BQ MARCAVALLE W101 AAVV MARCAVALLE"),
            ("distrito",   "Distrito", "SANTA ROSA DE SACCO"),
            ("telefono",   "Teléfono / Celular", "910454394"),
            ("email",      "Correo Institucional", "maximo.roman@unmsm.edu.pe"),
            ("facultad",   "Facultad", "Facultad de Ingeniería de Sistemas e Informática"),
            ("fecha",      "Fecha de emisión", "Lima, 30 de Abril del 2026"),
        ]

        for idx, (key, label, placeholder) in enumerate(campos):
            ctk.CTkLabel(
                form_frame, text=label,
                font=ctk.CTkFont(weight="bold", size=12)
            ).grid(row=idx, column=0, sticky="w", padx=15, pady=(10, 2))

            entry = ctk.CTkEntry(form_frame, placeholder_text=placeholder)
            entry.grid(row=idx, column=1, sticky="ew", padx=15, pady=(10, 2))
            self._entries[key] = entry

        # Campo de Firma
        row_idx = len(campos)
        ctk.CTkLabel(
            form_frame, text="Imagen de Firma Manuscrita",
            font=ctk.CTkFont(weight="bold", size=12)
        ).grid(row=row_idx, column=0, sticky="w", padx=15, pady=(10, 2))

        box_firma = ctk.CTkFrame(form_frame, fg_color="transparent")
        box_firma.grid(row=row_idx, column=1, sticky="ew", padx=15, pady=(10, 2))
        box_firma.columnconfigure(0, weight=1)

        ctk.CTkEntry(box_firma, textvariable=self._var_firma, state="readonly").grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ctk.CTkButton(
            box_firma, text="📂 Buscar", width=80,
            fg_color=COLOR_PRIMARIO, hover_color=COLOR_HOVER,
            command=self._buscar_firma
        ).grid(row=0, column=1)

        # Contenedor de Botones de Acción (Monolito vs Distribuido)
        btn_box = ctk.CTkFrame(form_frame, fg_color="transparent")
        btn_box.grid(row=row_idx + 1, column=0, columnspan=2, padx=15, pady=25, sticky="ew")
        btn_box.columnconfigure((0, 1), weight=1)

        # 1. Modo Local (Monolito)
        ctk.CTkButton(
            btn_box,
            text="⚡ Generar en Local (Monolito)",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#555555",
            hover_color="#333333",
            height=40,
            command=self._generar
        ).grid(row=0, column=0, padx=(0, 10), sticky="ew")

        # 2. Modo Distribuido (API REST + Middleware)
        ctk.CTkButton(
            btn_box,
            text="☁️ Enviar a API REST (Distribuido)",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=COLOR_PRIMARIO,
            hover_color=COLOR_HOVER,
            height=40,
            command=self._enviar_a_api
        ).grid(row=0, column=1, padx=(10, 0), sticky="ew")

    def _cargar_autollenado(self):
        """Pre-llena los campos con los datos del perfil guardado."""
        profile = UserProfile.cargar()
        for key, entry in self._entries.items():
            if profile.get(key):
                entry.delete(0, "end")
                entry.insert(0, profile[key])
        if profile.get("firma_path"):
            self._var_firma.set(profile["firma_path"])

    def _guardar_perfil_manual(self):
        """Guarda manualmente los datos ingresados."""
        datos = {key: entry.get().strip() for key, entry in self._entries.items()}
        datos["firma_path"] = self._var_firma.get() or None
        UserProfile.guardar(datos)
        messagebox.showinfo("💾 Autollenado Guardado", "Tus datos se han guardado exitosamente para futuros formularios.")

    def _buscar_firma(self):
        """Abre diálogo para seleccionar la firma."""
        ruta = filedialog.askopenfilename(
            title="Seleccionar imagen de la firma",
            filetypes=IMAGE_FILETYPES
        )
        if ruta:
            self._var_firma.set(ruta)

    def _generar(self):
        """Llama al controlador para validar y generar el PDF."""
        datos = {key: entry.get().strip() for key, entry in self._entries.items()}
        datos["condicion"] = "Estudiante"
        datos["firma_path"] = self._var_firma.get() or None

        exito, resultado = BolsistaController.generar_declaracion(datos)
        if exito:
            messagebox.showinfo("✅ Éxito", f"Declaración Jurada generada exitosamente:\n\n{resultado}")
        else:
            messagebox.showerror("Error", resultado)

    def _enviar_a_api(self):
        """Envía los datos a la API REST (FastAPI) para procesamiento asíncrono vía RabbitMQ."""
        datos = {key: entry.get().strip() for key, entry in self._entries.items()}
        datos["condicion"] = "Estudiante"
        datos["email"] = datos.get("email") or "bolsista@unmsm.edu.pe"
        datos["para_nombre"] = "DR. CARLOS SÁNCHEZ VELÁSQUEZ"
        datos["para_cargo"] = "Director de Escuela Profesional"
        datos["actividades"] = [
            "Mantenimiento de equipos de laboratorio.",
            "Configuración de entornos para cátedras de arquitectura.",
            "Desarrollo de scripts de automatización de reportes."
        ]

        try:
            import requests
            api_url = "http://localhost:8000/api/expedientes"
            resp = requests.post(api_url, json=datos, timeout=5)
            if resp.status_code in (200, 201):
                res_data = resp.json()
                exp_id = res_data.get("expediente_id")
                mq_status = res_data.get("middleware_status", {}).get("detalle", "Encolado")
                messagebox.showinfo(
                    "☁️ Enviado a la API REST",
                    f"¡Expediente registrado con éxito!\n\n"
                    f"• ID Expediente: {exp_id}\n"
                    f"• Estado inicial: {res_data.get('estado')}\n"
                    f"• Middleware: {mq_status}\n\n"
                    f"El DocsService generará los PDFs en segundo plano y pasará el estado a Documentos_Generados."
                )
            else:
                messagebox.showerror("Error en API", f"La API retornó código {resp.status_code}:\n{resp.text}")
        except Exception as e:
            messagebox.showwarning(
                "API no disponible",
                f"No se pudo conectar a la API REST en http://localhost:8000.\n\n"
                f"Asegúrate de iniciar el servicio con 'docker-compose up' o 'uvicorn services.api.main:app'."
            )
