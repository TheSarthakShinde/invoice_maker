import os
from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from sqlalchemy import text

from extensions import db, migrate

load_dotenv()

app = Flask(__name__)
CORS(app)

db_url = os.getenv("DATABASE_URL", "")
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

db.init_app(app)
migrate.init_app(app, db)
JWTManager(app)

import models  # noqa: F401
from auth import auth_bp
app.register_blueprint(auth_bp)


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/db-check")
def db_check():
    db.session.execute(text("SELECT 1"))
    return jsonify({"database": "connected"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)