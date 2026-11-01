from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from extensions import db


class Business(db.Model):
    __tablename__ = "businesses"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.Text)
    state = db.Column(db.String(50))
    gstin = db.Column(db.String(15))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    logo_url = db.Column(db.String(500))
    bank_name = db.Column(db.String(100))
    account_number = db.Column(db.String(30))
    ifsc = db.Column(db.String(11))
    upi_id = db.Column(db.String(100))
    invoice_prefix = db.Column(db.String(10), default="INV")
    default_terms = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey("businesses.id"), nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="owner")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Customer(db.Model):
    __tablename__ = "customers"
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey("businesses.id"), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.Text)
    state = db.Column(db.String(50))
    gstin = db.Column(db.String(15))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))


class Item(db.Model):
    __tablename__ = "items"
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey("businesses.id"), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    hsn_sac = db.Column(db.String(10))
    unit = db.Column(db.String(20), default="pcs")
    rate = db.Column(db.Numeric(12, 2), nullable=False)
    gst_rate = db.Column(db.Numeric(5, 2), default=18)


class Invoice(db.Model):
    __tablename__ = "invoices"
    __table_args__ = (
        db.UniqueConstraint("business_id", "invoice_number", name="uq_business_invoice_number"),
    )
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey("businesses.id"), nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    invoice_number = db.Column(db.String(30), nullable=False)
    invoice_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date)
    place_of_supply = db.Column(db.String(50))
    taxable_total = db.Column(db.Numeric(12, 2), default=0)
    cgst_total = db.Column(db.Numeric(12, 2), default=0)
    sgst_total = db.Column(db.Numeric(12, 2), default=0)
    igst_total = db.Column(db.Numeric(12, 2), default=0)
    grand_total = db.Column(db.Numeric(12, 2), default=0)
    status = db.Column(db.String(20), default="unpaid")
    snapshot = db.Column(JSONB)  # business + customer details frozen at creation
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship("InvoiceItem", backref="invoice", cascade="all, delete-orphan")


class InvoiceItem(db.Model):
    __tablename__ = "invoice_items"
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoices.id"), nullable=False, index=True)
    description = db.Column(db.String(300), nullable=False)
    hsn_sac = db.Column(db.String(10))
    quantity = db.Column(db.Numeric(10, 2), nullable=False)
    unit = db.Column(db.String(20))
    rate = db.Column(db.Numeric(12, 2), nullable=False)
    gst_rate = db.Column(db.Numeric(5, 2), default=18)
    taxable_value = db.Column(db.Numeric(12, 2), nullable=False)


class InvoiceSequence(db.Model):
    __tablename__ = "invoice_sequences"
    __table_args__ = (
        db.UniqueConstraint("business_id", "fiscal_year", name="uq_business_fy"),
    )
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey("businesses.id"), nullable=False)
    fiscal_year = db.Column(db.String(9), nullable=False)  # e.g. 2026-27
    last_number = db.Column(db.Integer, default=0, nullable=False)