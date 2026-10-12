"""
services/api/database.py
Capa de persistencia basada en JSON (expedientes.json) con sincronización thread-safe.
Maneja el ciclo de vida y los estados: Borrador -> Documentos_Generados -> Pendiente_Jefe.
"""

import json
import os
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any

DB_FILE = os.environ.get("DB_FILE", os.path.join(os.getcwd(), "expedientes.json"))
_lock = threading.Lock()


def _cargar_db() -> Dict[str, Any]:
    if not os.path.exists(DB_FILE):
        return {"expedientes": {}}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"expedientes": {}}


def _guardar_db(data: Dict[str, Any]) -> None:
    directorio = os.path.dirname(os.path.abspath(DB_FILE))
    if directorio:
        os.makedirs(directorio, exist_ok=True)
    temp_file = f"{DB_FILE}.tmp"
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(temp_file, DB_FILE)


def crear_expediente(expediente_id: str, datos_bolsista: dict) -> dict:
    """Crea un nuevo expediente en estado Borrador."""
    with _lock:
        db = _cargar_db()
        ahora = datetime.now().isoformat()
        nuevo = {
            "id": expediente_id,
            "estado": "Borrador",
            "datos_bolsista": datos_bolsista,
            "documentos": {},
            "creado_en": ahora,
            "actualizado_en": ahora,
            "historial_estados": [
                {
                    "estado": "Borrador",
                    "timestamp": ahora,
                    "detalle": "Expediente registrado en la API"
                }
            ],
            "notificacion_jefe": None
        }
        db["expedientes"][expediente_id] = nuevo
        _guardar_db(db)
        return nuevo


def obtener_expediente(expediente_id: str) -> Optional[dict]:
    """Obtiene un expediente por su identificador."""
    with _lock:
        db = _cargar_db()
        return db["expedientes"].get(expediente_id)


def listar_expedientes() -> List[dict]:
    """Retorna todos los expedientes ordenados por fecha de creación descendente."""
    with _lock:
        db = _cargar_db()
        return sorted(
            list(db["expedientes"].values()),
            key=lambda x: x.get("creado_en", ""),
            reverse=True
        )


def actualizar_estado(expediente_id: str, nuevo_estado: str, detalle: str = "") -> Optional[dict]:
    """Actualiza el estado de un expediente y registra la transición en el historial."""
    with _lock:
        db = _cargar_db()
        if expediente_id not in db["expedientes"]:
            return None
        
        ahora = datetime.now().isoformat()
        exp = db["expedientes"][expediente_id]
        exp["estado"] = nuevo_estado
        exp["actualizado_en"] = ahora
        exp["historial_estados"].append({
            "estado": nuevo_estado,
            "timestamp": ahora,
            "detalle": detalle
        })
        _guardar_db(db)
        return exp


def registrar_documentos_generados(expediente_id: str, documentos: dict) -> Optional[dict]:
    """Registra las rutas/enlaces de los documentos generados por el microservicio."""
    with _lock:
        db = _cargar_db()
        if expediente_id not in db["expedientes"]:
            return None
        
        ahora = datetime.now().isoformat()
        exp = db["expedientes"][expediente_id]
        exp["documentos"] = documentos
        exp["estado"] = "Documentos_Generados"
        exp["actualizado_en"] = ahora
        exp["historial_estados"].append({
            "estado": "Documentos_Generados",
            "timestamp": ahora,
            "detalle": f"Documentos generados por DocsService: {list(documentos.keys())}"
        })
        _guardar_db(db)
        return exp


def registrar_notificacion_jefe(expediente_id: str, info_notificacion: dict) -> Optional[dict]:
    """Registra la respuesta de la función Serverless."""
    with _lock:
        db = _cargar_db()
        if expediente_id not in db["expedientes"]:
            return None
        
        exp = db["expedientes"][expediente_id]
        exp["notificacion_jefe"] = info_notificacion
        exp["actualizado_en"] = datetime.now().isoformat()
        _guardar_db(db)
        return exp
