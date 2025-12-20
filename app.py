import os
import uuid
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

# CONFIGURACIÓN INICIAL
app = Flask(__name__)
CORS(app)  # ✅ activar CORS

basedir = os.path.abspath(os.path.dirname(__file__))

# SQLite local (ojo: en Render es almacenamiento efímero, sirve para demo)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "db.sqlite3")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ENDPOINTS BÁSICOS (evita 404 en /)
@app.get("/")
def home():
    return jsonify({
        "status": "ok",
        "message": "FoodPlease API running",
        "endpoints": ["/productos", "/productos/<id>", "/health"]
    }), 200

@app.get("/health")
def health():
    return jsonify({"status": "healthy"}), 200


# MODELO DE LA BASE DE DATOS
class Producto(db.Model):
    __tablename__ = "productos"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nombre = db.Column(db.String(100), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    disponible = db.Column(db.Boolean, default=True)
    imagen = db.Column(db.String(200), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "categoria": "Plato de fondo",
            "precio": self.precio,
            "stock": self.stock,
            "disponible": self.disponible,
            "imagen": self.imagen or "assets/images/default_plato.png",
        }


# Crear tablas
with app.app_context():
    db.create_all()


# CRUD PRODUCTOS

# 1) CREAR
@app.route("/productos", methods=["POST"])
def crear_producto():
    data = request.get_json()

    if not data or not all(k in data for k in ("nombre", "precio", "stock")):
        return jsonify({"error": "Faltan datos obligatorios (nombre, precio, stock)"}), 400

    nuevo_producto = Producto(
        nombre=data["nombre"],
        precio=float(data["precio"]),
        stock=int(data["stock"]),
        disponible=bool(data.get("disponible", True)),
        imagen=data.get("imagen")
    )

    try:
        db.session.add(nuevo_producto)
        db.session.commit()
        return jsonify(nuevo_producto.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# 2) LEER TODOS
@app.route("/productos", methods=["GET"])
def obtener_productos():
    productos = Producto.query.all()
    return jsonify([p.to_dict() for p in productos]), 200


# 3) LEER POR ID
@app.route("/productos/<string:id>", methods=["GET"])
def obtener_producto(id):
    producto = Producto.query.get(id)
    if not producto:
        return jsonify({"error": "Producto no encontrado"}), 404
    return jsonify(producto.to_dict()), 200


# 4) ACTUALIZAR
@app.route("/productos/<string:id>", methods=["PUT"])
def actualizar_producto(id):
    producto = Producto.query.get(id)
    if not producto:
        return jsonify({"error": "Producto no encontrado"}), 404

    data = request.get_json() or {}

    if "nombre" in data:
        producto.nombre = data["nombre"]
    if "precio" in data:
        producto.precio = float(data["precio"])
    if "stock" in data:
        producto.stock = int(data["stock"])
    if "disponible" in data:
        producto.disponible = bool(data["disponible"])
    if "imagen" in data:
        producto.imagen = data["imagen"]

    try:
        db.session.commit()
        return jsonify(producto.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# 5) ELIMINAR
@app.route("/productos/<string:id>", methods=["DELETE"])
def eliminar_producto(id):
    producto = Producto.query.get(id)
    if not producto:
        return jsonify({"error": "Producto no encontrado"}), 404

    try:
        db.session.delete(producto)
        db.session.commit()
        return jsonify({"mensaje": "Producto eliminado correctamente"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ARRANQUE LOCAL (Render NO usa esto, Render usa gunicorn)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app
