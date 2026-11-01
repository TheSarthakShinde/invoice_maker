from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt, get_jwt_identity
from extensions import db
from models import Business, User

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def make_token(user):
    return create_access_token(
        identity=str(user.id),
        additional_claims={"business_id": user.business_id},
    )


@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    business_name = (data.get("business_name") or "").strip()

    if not email or not business_name or len(password) < 8:
        return jsonify({"error": "business_name, email, password (min 8 chars) required"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "email already registered"}), 409

    business = Business(name=business_name)
    db.session.add(business)
    db.session.flush()  # get business.id before commit

    user = User(
        business_id=business.id,
        email=email,
        password_hash=generate_password_hash(password),
        role="owner",
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({"token": make_token(user)}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "invalid email or password"}), 401
    return jsonify({"token": make_token(user)})


@auth_bp.route("/me")
@jwt_required()
def me():
    user = db.session.get(User, int(get_jwt_identity()))
    return jsonify({
        "email": user.email,
        "role": user.role,
        "business_id": get_jwt()["business_id"],
    })