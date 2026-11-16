import os
import re
import cloudinary
import cloudinary.uploader
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from extensions import db
from models import Business

business_bp = Blueprint("business", __name__, url_prefix="/api/business")

GSTIN_RE = re.compile(r"^\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")
ALLOWED_TYPES = {"image/png", "image/jpeg"}
MAX_LOGO_BYTES = 2 * 1024 * 1024

FIELDS = [
    "name", "address", "state", "gstin", "phone", "email",
    "bank_name", "account_number", "ifsc", "upi_id",
    "invoice_prefix", "default_terms",
]


def configure_cloudinary():
    cloudinary.config(
        cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key=os.getenv("CLOUDINARY_API_KEY"),
        api_secret=os.getenv("CLOUDINARY_API_SECRET"),
        secure=True,
    )


def to_dict(b):
    d = {f: getattr(b, f) for f in FIELDS}
    d["logo_url"] = b.logo_url
    return d


def current_business():
    return db.session.get(Business, get_jwt()["business_id"])


@business_bp.route("", methods=["GET"])
@jwt_required()
def get_business():
    return jsonify(to_dict(current_business()))


@business_bp.route("", methods=["PUT"])
@jwt_required()
def update_business():
    b = current_business()
    data = request.get_json() or {}

    gstin = (data.get("gstin") or "").strip().upper()
    if gstin and not GSTIN_RE.match(gstin):
        return jsonify({"error": "invalid GSTIN format"}), 400
    if "name" in data and not (data["name"] or "").strip():
        return jsonify({"error": "name cannot be empty"}), 400

    for f in FIELDS:
        if f in data:
            value = data[f]
            if f == "gstin":
                value = gstin or None
            setattr(b, f, value)
    db.session.commit()
    return jsonify(to_dict(b))


@business_bp.route("/logo", methods=["POST"])
@jwt_required()
def upload_logo():
    file = request.files.get("logo")
    if not file:
        return jsonify({"error": "no file"}), 400
    if file.mimetype not in ALLOWED_TYPES:
        return jsonify({"error": "only PNG or JPEG allowed"}), 400

    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > MAX_LOGO_BYTES:
        return jsonify({"error": "max 2MB"}), 400

    b = current_business()
    configure_cloudinary()
    result = cloudinary.uploader.upload(
        file,
        folder="invoice-logos",
        public_id=f"business_{b.id}",
        overwrite=True,
        transformation=[{"width": 400, "height": 400, "crop": "limit"}],
    )
    b.logo_url = result["secure_url"]
    db.session.commit()
    return jsonify({"logo_url": b.logo_url})


@business_bp.route("/logo", methods=["DELETE"])
@jwt_required()
def delete_logo():
    b = current_business()
    configure_cloudinary()
    cloudinary.uploader.destroy(f"invoice-logos/business_{b.id}")
    b.logo_url = None
    db.session.commit()
    return jsonify({"logo_url": None})