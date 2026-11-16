from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from extensions import db
from models import Customer, Item

crud_bp = Blueprint("crud", __name__, url_prefix="/api")

CUSTOMER_FIELDS = ["name", "address", "state", "gstin", "email", "phone"]
ITEM_FIELDS = ["name", "hsn_sac", "unit", "rate", "gst_rate"]


def bid():
    return get_jwt()["business_id"]


def serialize(obj, fields):
    d = {"id": obj.id}
    for f in fields:
        v = getattr(obj, f)
        d[f] = float(v) if hasattr(v, "as_tuple") else v
    return d


def register_crud(model, fields, path, required):
    def list_all():
        rows = model.query.filter_by(business_id=bid()).order_by(model.id.desc()).all()
        return jsonify([serialize(r, fields) for r in rows])

    def create():
        data = request.get_json() or {}
        for r in required:
            if not data.get(r):
                return jsonify({"error": f"{r} required"}), 400
        obj = model(business_id=bid(), **{f: data[f] for f in fields if f in data})
        db.session.add(obj)
        db.session.commit()
        return jsonify(serialize(obj, fields)), 201

    def get_one(id):
        obj = model.query.filter_by(id=id, business_id=bid()).first_or_404()
        return jsonify(serialize(obj, fields))

    def update(id):
        obj = model.query.filter_by(id=id, business_id=bid()).first_or_404()
        data = request.get_json() or {}
        for f in fields:
            if f in data:
                setattr(obj, f, data[f])
        db.session.commit()
        return jsonify(serialize(obj, fields))

    def delete(id):
        obj = model.query.filter_by(id=id, business_id=bid()).first_or_404()
        db.session.delete(obj)
        db.session.commit()
        return "", 204

    n = model.__tablename__
    crud_bp.add_url_rule(path, f"{n}_list", jwt_required()(list_all), methods=["GET"])
    crud_bp.add_url_rule(path, f"{n}_create", jwt_required()(create), methods=["POST"])
    crud_bp.add_url_rule(f"{path}/<int:id>", f"{n}_get", jwt_required()(get_one), methods=["GET"])
    crud_bp.add_url_rule(f"{path}/<int:id>", f"{n}_update", jwt_required()(update), methods=["PUT"])
    crud_bp.add_url_rule(f"{path}/<int:id>", f"{n}_delete", jwt_required()(delete), methods=["DELETE"])


register_crud(Customer, CUSTOMER_FIELDS, "/customers", ["name"])
register_crud(Item, ITEM_FIELDS, "/items", ["name", "rate"])