import os
from datetime import datetime, timedelta, date
from dataclasses import asdict
from typing import List, Dict, Optional, Tuple

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
)
import bcrypt
import csv
from io import StringIO, BytesIO
from openpyxl import load_workbook

# -----------------------------
# App and Config
# -----------------------------

def create_app() -> Flask:
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret")
    db_path = os.path.join(os.path.dirname(__file__), "bizforecast.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    return app

app = create_app()
db = SQLAlchemy(app)
jwt = JWTManager(app)

# -----------------------------
# Models
# -----------------------------

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    plan = db.Column(db.String(50), default="free")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    profile = db.relationship("BusinessProfile", backref="user", uselist=False, cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        self.password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def check_password(self, password: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode("utf-8"), self.password_hash.encode("utf-8"))
        except Exception:
            return False

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "email": self.email,
            "plan": self.plan,
            "created_at": self.created_at.isoformat(),
        }


class BusinessProfile(db.Model):
    __tablename__ = "business_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(255))
    industry = db.Column(db.String(100))
    starting_cash = db.Column(db.Float, default=100000.0)
    monthly_revenue = db.Column(db.Float, default=300000.0)
    fixed_expenses = db.Column(db.Float, default=150000.0)
    payment_cycle_days = db.Column(db.Integer, default=30)
    min_cash_threshold = db.Column(db.Float, default=50000.0)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "industry": self.industry,
            "starting_cash": self.starting_cash,
            "monthly_revenue": self.monthly_revenue,
            "fixed_expenses": self.fixed_expenses,
            "payment_cycle_days": self.payment_cycle_days,
            "min_cash_threshold": self.min_cash_threshold,
        }


class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(255))
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'income' | 'expense'
    category = db.Column(db.String(100))
    source = db.Column(db.String(20), default="manual")  # 'manual' | 'import'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "date": self.date.isoformat(),
            "description": self.description,
            "amount": self.amount,
            "type": self.type,
            "category": self.category,
            "source": self.source,
            "created_at": self.created_at.isoformat(),
        }


class BudgetItem(db.Model):
    __tablename__ = "budget_items"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    cadence = db.Column(db.String(20), nullable=False)  # 'monthly'|'weekly'|'daily'
    type = db.Column(db.String(20), nullable=False)  # 'fixed'|'variable'

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "amount": self.amount,
            "cadence": self.cadence,
            "type": self.type,
        }


class Forecast(db.Model):
    __tablename__ = "forecasts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    horizon_days = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    points = db.relationship("ForecastPoint", backref="forecast", cascade="all, delete-orphan")

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "horizon_days": self.horizon_days,
            "created_at": self.created_at.isoformat(),
        }


class ForecastPoint(db.Model):
    __tablename__ = "forecast_points"

    id = db.Column(db.Integer, primary_key=True)
    forecast_id = db.Column(db.Integer, db.ForeignKey("forecasts.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    opening_balance = db.Column(db.Float, nullable=False)
    inflow = db.Column(db.Float, nullable=False)
    outflow = db.Column(db.Float, nullable=False)
    closing_balance = db.Column(db.Float, nullable=False)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "forecast_id": self.forecast_id,
            "date": self.date.isoformat(),
            "opening_balance": self.opening_balance,
            "inflow": self.inflow,
            "outflow": self.outflow,
            "closing_balance": self.closing_balance,
        }


class Alert(db.Model):
    __tablename__ = "alerts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    trigger_date = db.Column(db.Date)
    amount = db.Column(db.Float)
    severity = db.Column(db.String(10), default="info")  # 'info'|'warn'|'crit'
    status = db.Column(db.String(20), default="active")  # 'active'|'resolved'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type,
            "message": self.message,
            "trigger_date": self.trigger_date.isoformat() if self.trigger_date else None,
            "amount": self.amount,
            "severity": self.severity,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }


with app.app_context():
    db.create_all()

# -----------------------------
# Helpers: auth and utilities
# -----------------------------

def get_current_user() -> User:
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    return user


def parse_date(value: str) -> date:
    return datetime.fromisoformat(value).date()


# -----------------------------
# Forecasting and Finance Logic
# -----------------------------

def _aggregate_transactions(user_id: int, lookback_days: int = 90) -> Tuple[float, float]:
    since = datetime.utcnow().date() - timedelta(days=lookback_days)
    txns: List[Transaction] = (
        db.session.query(Transaction)
        .filter(Transaction.user_id == user_id, Transaction.date >= since)
        .all()
    )
    if not txns:
        return 0.0, 0.0
    total_in = sum(t.amount for t in txns if t.type == "income")
    total_out = sum(t.amount for t in txns if t.type == "expense")
    avg_daily_in = total_in / max(1, lookback_days)
    avg_daily_out = total_out / max(1, lookback_days)
    return avg_daily_in, avg_daily_out


def _apply_scenario(inflow_schedule: List[float], outflow_schedule: List[float], scenario: Dict) -> None:
    sales_pct = float(scenario.get("sales_pct", 0.0) or 0.0)
    receivable_delay_days = int(scenario.get("receivable_delay_days", 0) or 0)
    expense_shock = float(scenario.get("expense_shock", 0.0) or 0.0)

    if sales_pct != 0.0:
        for i in range(len(inflow_schedule)):
            inflow_schedule[i] = inflow_schedule[i] * (1.0 + sales_pct)

    if receivable_delay_days > 0:
        shifted = [0.0] * receivable_delay_days + inflow_schedule
        inflow_schedule[:] = shifted[: len(inflow_schedule)]

    if expense_shock > 0.0 and len(outflow_schedule) > 0:
        outflow_schedule[0] += expense_shock


def _generate_baseline_schedules(profile: BusinessProfile, budget_items: List[BudgetItem], horizon_days: int, user_id: int) -> Tuple[List[float], List[float]]:
    inflow = [0.0 for _ in range(horizon_days)]
    outflow = [0.0 for _ in range(horizon_days)]

    # If historical transactions exist, use smoothed averages as base
    avg_in, avg_out = _aggregate_transactions(user_id)
    if avg_in > 0 or avg_out > 0:
        for d in range(horizon_days):
            inflow[d] += avg_in
            outflow[d] += avg_out
    else:
        # Starter Mode parameters: schedule monthly revenue and fixed expenses on cycle boundaries
        cycle = max(1, int(profile.payment_cycle_days or 30))
        for d in range(horizon_days):
            if (d + 1) % cycle == 0:
                inflow[d] += float(profile.monthly_revenue or 0.0)
                outflow[d] += float(profile.fixed_expenses or 0.0)

    # Budget items
    for item in budget_items:
        if item.cadence == "daily":
            for d in range(horizon_days):
                if item.type == "fixed":
                    outflow[d] += item.amount
                else:
                    # Variable: link to revenue proxy if available
                    inflow_proxy = profile.monthly_revenue / max(1, profile.payment_cycle_days)
                    outflow[d] += item.amount * (inflow_proxy / max(1.0, 100000.0))
        elif item.cadence == "weekly":
            for d in range(horizon_days):
                if (d + 1) % 7 == 0:
                    if item.type == "fixed":
                        outflow[d] += item.amount
                    else:
                        inflow_proxy = profile.monthly_revenue / max(1, profile.payment_cycle_days)
                        outflow[d] += item.amount * (inflow_proxy / max(1.0, 100000.0))
        elif item.cadence == "monthly":
            for d in range(horizon_days):
                if (d + 1) % 30 == 0:
                    if item.type == "fixed":
                        outflow[d] += item.amount
                    else:
                        inflow_proxy = profile.monthly_revenue / max(1, profile.payment_cycle_days)
                        outflow[d] += item.amount * (inflow_proxy / max(1.0, 100000.0))

    return inflow, outflow


def _compute_forecast(user: User, horizon_days: int, granularity: str, scenario: Optional[Dict]) -> Dict:
    profile = user.profile
    if not profile:
        profile = BusinessProfile(
            user_id=user.id,
            name=None,
            industry=None,
            starting_cash=100000.0,
            monthly_revenue=300000.0,
            fixed_expenses=150000.0,
            payment_cycle_days=30,
            min_cash_threshold=50000.0,
        )
        db.session.add(profile)
        db.session.commit()

    budget_items = db.session.query(BudgetItem).filter(BudgetItem.user_id == user.id).all()

    inflow_schedule, outflow_schedule = _generate_baseline_schedules(profile, budget_items, horizon_days, user.id)

    if scenario:
        _apply_scenario(inflow_schedule, outflow_schedule, scenario)

    points: List[Dict] = []
    current_date = datetime.utcnow().date()
    opening_balance = float(profile.starting_cash or 0.0)
    worst_balance = opening_balance
    next_crossing_date: Optional[date] = None

    for d in range(horizon_days):
        day = current_date + timedelta(days=d)
        inflow = float(inflow_schedule[d])
        outflow = float(outflow_schedule[d])
        closing_balance = opening_balance + inflow - outflow

        if next_crossing_date is None and closing_balance < float(profile.min_cash_threshold or 0.0):
            next_crossing_date = day
        if closing_balance < worst_balance:
            worst_balance = closing_balance

        points.append(
            {
                "date": day.isoformat(),
                "opening_balance": round(opening_balance, 2),
                "inflow": round(inflow, 2),
                "outflow": round(outflow, 2),
                "closing_balance": round(closing_balance, 2),
            }
        )
        opening_balance = closing_balance

    aggregates = {
        "total_inflow": round(sum(p["inflow"] for p in points), 2),
        "total_outflow": round(sum(p["outflow"] for p in points), 2),
        "ending_balance": round(points[-1]["closing_balance"], 2) if points else round(float(profile.starting_cash or 0.0), 2),
    }

    # Burn and runway using trailing 90 days transactions or profile fallback
    avg_in, avg_out = _aggregate_transactions(user.id, 90)
    if avg_in == 0 and avg_out == 0:
        # Fallback: approximate monthly -> daily
        avg_in = (profile.monthly_revenue or 0.0) / max(1, profile.payment_cycle_days or 30)
        avg_out = (profile.fixed_expenses or 0.0) / max(1, profile.payment_cycle_days or 30)
    gross_burn_monthly = avg_out * 30.0
    net_burn_monthly = max(0.0, (avg_out - avg_in) * 30.0)
    runway_months = (points[0]["opening_balance"] if points else (profile.starting_cash or 0.0)) / net_burn_monthly if net_burn_monthly > 0 else None

    metrics = {
        "gross_burn_monthly": round(gross_burn_monthly, 2),
        "net_burn_monthly": round(net_burn_monthly, 2),
        "runway_months": round(runway_months, 1) if runway_months else None,
        "runway_date": (current_date + timedelta(days=int(runway_months * 30))) .isoformat() if runway_months else None,
        "dso_days": int(profile.payment_cycle_days or 30),
        "dpo_days": 15,
        "ccc_days": int(profile.payment_cycle_days or 30) - 15,
    }

    # Persist forecast and points
    forecast = Forecast(user_id=user.id, horizon_days=horizon_days)
    db.session.add(forecast)
    db.session.flush()

    for p in points:
        fp = ForecastPoint(
            forecast_id=forecast.id,
            date=datetime.fromisoformat(p["date"]).date(),
            opening_balance=p["opening_balance"],
            inflow=p["inflow"],
            outflow=p["outflow"],
            closing_balance=p["closing_balance"],
        )
        db.session.add(fp)

    db.session.commit()

    # Alerts and insights
    alerts = _evaluate_alerts(user, points, profile)
    insights = _generate_insights(points, profile, metrics, alerts)

    # Optionally aggregate weekly for client if requested
    if granularity == "weekly":
        points = _aggregate_weekly(points)

    return {
        "points": points,
        "aggregates": aggregates,
        "next_crossing_date": next_crossing_date.isoformat() if next_crossing_date else None,
        "worst_balance": round(worst_balance, 2),
        "metrics": metrics,
        "alerts": [a.to_dict() for a in alerts],
        "insights": insights,
    }


def _aggregate_weekly(points: List[Dict]) -> List[Dict]:
    weekly = []
    bucket = {"opening_balance": None, "inflow": 0.0, "outflow": 0.0}
    for idx, p in enumerate(points):
        if bucket["opening_balance"] is None:
            bucket["opening_balance"] = p["opening_balance"]
        bucket["inflow"] += p["inflow"]
        bucket["outflow"] += p["outflow"]
        if (idx + 1) % 7 == 0 or idx == len(points) - 1:
            closing = bucket["opening_balance"] + bucket["inflow"] - bucket["outflow"]
            weekly.append(
                {
                    "date": p["date"],
                    "opening_balance": round(bucket["opening_balance"], 2),
                    "inflow": round(bucket["inflow"], 2),
                    "outflow": round(bucket["outflow"], 2),
                    "closing_balance": round(closing, 2),
                }
            )
            bucket = {"opening_balance": None, "inflow": 0.0, "outflow": 0.0}
    return weekly


def _evaluate_alerts(user: User, points: List[Dict], profile: BusinessProfile) -> List[Alert]:
    alerts_created: List[Alert] = []

    threshold = float(profile.min_cash_threshold or 0.0)
    breach_idx = next((i for i, p in enumerate(points) if p["closing_balance"] < threshold), None)
    if breach_idx is not None:
        days_to_breach = breach_idx
        severity = "crit" if days_to_breach <= 30 else "warn"
        message = f"Projected balance crosses threshold (₹{int(threshold)}) in {days_to_breach} days."
        alert = Alert(
            user_id=user.id,
            type="threshold_breach",
            message=message,
            trigger_date=datetime.fromisoformat(points[breach_idx]["date"]).date(),
            amount=points[breach_idx]["closing_balance"],
            severity=severity,
            status="active",
        )
        db.session.add(alert)
        db.session.commit()
        alerts_created.append(alert)

    # Expense drift heuristic: 30d outflows > 1.15 × 90d avg
    last_30_out = sum(p["outflow"] for p in points[:30])
    last_90_out_avg = sum(p["outflow"] for p in points[:90]) / max(1, min(90, len(points)))
    if last_90_out_avg > 0 and last_30_out > 1.15 * (last_90_out_avg * min(30, len(points))):
        alert = Alert(
            user_id=user.id,
            type="expense_drift",
            message="Recent outflows exceed 90-day average by >15%.",
            severity="warn",
            status="active",
        )
        db.session.add(alert)
        db.session.commit()
        alerts_created.append(alert)

    return alerts_created


def _generate_insights(points: List[Dict], profile: BusinessProfile, metrics: Dict, alerts: List[Alert]) -> List[str]:
    insights: List[str] = []

    if metrics.get("runway_months") is not None:
        insights.append(
            f"Runway approx {metrics['runway_months']} months (cash-out around {metrics['runway_date']})."
        )
    if any(a.type == "threshold_breach" for a in alerts):
        insights.append(
            "Consider accelerating collections (reduce DSO), delaying discretionary spend, or negotiating better payment terms (increase DPO)."
        )
    if metrics.get("ccc_days") is not None and metrics["ccc_days"] > 30:
        insights.append(
            "High cash conversion cycle suggests receivables delays are straining liquidity. Focus on collections."
        )

    return insights


# -----------------------------
# Routes: Auth
# -----------------------------

@app.post("/api/auth/signup")
def signup():
    data = request.get_json(force=True)
    email = (data.get("email") or "").strip().lower()
    password = data.get("password")
    if not email or not password:
        return jsonify({"error": "email and password required"}), 400

    if db.session.query(User).filter(User.email == email).first():
        return jsonify({"error": "email already in use"}), 400

    user = User(email=email, plan="free")
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    # Default profile per Starter Mode defaults
    profile = BusinessProfile(
        user_id=user.id,
        name=None,
        industry=None,
        starting_cash=100000.0,
        monthly_revenue=300000.0,
        fixed_expenses=150000.0,
        payment_cycle_days=30,
        min_cash_threshold=50000.0,
    )
    db.session.add(profile)
    db.session.commit()

    token = create_access_token(identity=user.id)
    return jsonify({"token": token})


@app.post("/api/auth/login")
def login():
    data = request.get_json(force=True)
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user: Optional[User] = db.session.query(User).filter(User.email == email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "invalid credentials"}), 401

    token = create_access_token(identity=user.id)
    return jsonify({"token": token})


# -----------------------------
# Routes: Business
# -----------------------------

@app.get("/api/business/profile")
@jwt_required()
def get_profile():
    user = get_current_user()
    profile = user.profile
    return jsonify(profile.to_dict() if profile else {})


@app.put("/api/business/profile")
@jwt_required()
def update_profile():
    user = get_current_user()
    profile = user.profile
    if not profile:
        profile = BusinessProfile(user_id=user.id)
        db.session.add(profile)

    data = request.get_json(force=True)
    for field in [
        "name",
        "industry",
        "starting_cash",
        "monthly_revenue",
        "fixed_expenses",
        "payment_cycle_days",
        "min_cash_threshold",
    ]:
        if field in data:
            setattr(profile, field, data[field])

    db.session.commit()
    return jsonify(profile.to_dict())


# -----------------------------
# Routes: Transactions
# -----------------------------

@app.get("/api/transactions")
@jwt_required()
def list_transactions():
    user = get_current_user()
    q = db.session.query(Transaction).filter(Transaction.user_id == user.id)
    from_str = request.args.get("from")
    to_str = request.args.get("to")
    ttype = request.args.get("type")
    if from_str:
        q = q.filter(Transaction.date >= parse_date(from_str))
    if to_str:
        q = q.filter(Transaction.date <= parse_date(to_str))
    if ttype in ("income", "expense"):
        q = q.filter(Transaction.type == ttype)
    txns = q.order_by(Transaction.date.desc(), Transaction.id.desc()).all()
    return jsonify([t.to_dict() for t in txns])


@app.post("/api/transactions")
@jwt_required()
def create_transaction():
    user = get_current_user()
    data = request.get_json(force=True)
    try:
        txn = Transaction(
            user_id=user.id,
            date=parse_date(data["date"]),
            description=data.get("description"),
            amount=float(data["amount"]),
            type=data["type"],
            category=data.get("category"),
            source=data.get("source", "manual"),
        )
        if txn.type not in ("income", "expense"):
            return jsonify({"error": "type must be 'income' or 'expense'"}), 400
    except Exception as e:
        return jsonify({"error": f"invalid payload: {e}"}), 400

    db.session.add(txn)
    db.session.commit()
    return jsonify(txn.to_dict()), 201


@app.put("/api/transactions/<int:txn_id>")
@jwt_required()
def update_transaction(txn_id: int):
    user = get_current_user()
    txn: Optional[Transaction] = (
        db.session.query(Transaction)
        .filter(Transaction.user_id == user.id, Transaction.id == txn_id)
        .first()
    )
    if not txn:
        return jsonify({"error": "not found"}), 404

    data = request.get_json(force=True)
    if "date" in data:
        txn.date = parse_date(data["date"])
    for field in ["description", "amount", "type", "category", "source"]:
        if field in data:
            setattr(txn, field, data[field])
    db.session.commit()
    return jsonify(txn.to_dict())


@app.delete("/api/transactions/<int:txn_id>")
@jwt_required()
def delete_transaction(txn_id: int):
    user = get_current_user()
    num = (
        db.session.query(Transaction)
        .filter(Transaction.user_id == user.id, Transaction.id == txn_id)
        .delete()
    )
    db.session.commit()
    if num == 0:
        return jsonify({"error": "not found"}), 404
    return ("", 204)


@app.post("/api/transactions/import")
@jwt_required()
def import_transactions():
    user = get_current_user()
    if user.plan == "free":
        return jsonify({"error": "CSV import is available on paid plans."}), 403
    if "file" not in request.files:
        return jsonify({"error": "file missing"}), 400

    file = request.files["file"]
    filename = file.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "csv"

    try:
        rows: List[Dict[str, str]] = []
        if ext in ("xlsx", "xls"):
            # Use openpyxl to read first sheet into rows
            in_mem = BytesIO(file.read())
            wb = load_workbook(in_mem, read_only=True, data_only=True)
            ws = wb.active
            headers = []
            for idx, row in enumerate(ws.iter_rows(values_only=True)):
                if idx == 0:
                    headers = [str(h).strip() if h is not None else "" for h in row]
                    continue
                record = {}
                for j, cell in enumerate(row):
                    key = headers[j] if j < len(headers) else f"col{j}"
                    record[key] = "" if cell is None else str(cell)
                rows.append(record)
        else:
            # CSV via Python csv module
            content = file.read().decode("utf-8", errors="ignore")
            reader = csv.DictReader(StringIO(content))
            for r in reader:
                rows.append({k: (v or "") for k, v in r.items()})
    except Exception as e:
        return jsonify({"error": f"failed to parse file: {e}"}), 400

    # Normalize columns
    if not rows:
        return jsonify({"error": "no rows found"}), 400
    sample_cols = list(rows[0].keys())
    cols = {c.strip().lower(): c for c in sample_cols}
    required = ["date", "description", "amount", "type", "category"]
    missing = [c for c in required if c not in cols]
    if missing:
        return jsonify({"error": f"missing columns: {', '.join(missing)}"}), 400

    ok = 0
    bad = 0
    errors: List[str] = []
    for idx, row in enumerate(rows):
        try:
            raw_date = str(row.get(cols["date"], "")).split(" ")[0]
            desc_val = row.get(cols["description"]) or None
            amt_val = float(str(row.get(cols["amount"], "0")).replace(",", ""))
            type_val = str(row.get(cols["type"], "")).strip().lower()
            cat_val = row.get(cols["category"]) or None

            txn = Transaction(
                user_id=user.id,
                date=parse_date(raw_date),
                description=desc_val,
                amount=amt_val,
                type=type_val,
                category=cat_val,
                source="import",
            )
            if txn.type not in ("income", "expense"):
                raise ValueError("type must be 'income' or 'expense'")
            db.session.add(txn)
            ok += 1
        except Exception as e:
            bad += 1
            errors.append(f"row {idx+1}: {e}")
    db.session.commit()

    return jsonify({"imported": ok, "rejected": bad, "errors": errors[:25]})


# -----------------------------
# Routes: Budget
# -----------------------------

@app.get("/api/budget/items")
@jwt_required()
def list_budget_items():
    user = get_current_user()
    items = db.session.query(BudgetItem).filter(BudgetItem.user_id == user.id).all()
    return jsonify([i.to_dict() for i in items])


@app.post("/api/budget/items")
@jwt_required()
def create_budget_item():
    user = get_current_user()
    data = request.get_json(force=True)
    try:
        item = BudgetItem(
            user_id=user.id,
            name=data["name"],
            amount=float(data["amount"]),
            cadence=data["cadence"],
            type=data["type"],
        )
        if item.cadence not in ("monthly", "weekly", "daily"):
            return jsonify({"error": "cadence must be monthly|weekly|daily"}), 400
        if item.type not in ("fixed", "variable"):
            return jsonify({"error": "type must be fixed|variable"}), 400
    except Exception as e:
        return jsonify({"error": f"invalid payload: {e}"}), 400

    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201


@app.put("/api/budget/items/<int:item_id>")
@jwt_required()
def update_budget_item(item_id: int):
    user = get_current_user()
    item: Optional[BudgetItem] = (
        db.session.query(BudgetItem)
        .filter(BudgetItem.user_id == user.id, BudgetItem.id == item_id)
        .first()
    )
    if not item:
        return jsonify({"error": "not found"}), 404

    data = request.get_json(force=True)
    for field in ["name", "amount", "cadence", "type"]:
        if field in data:
            setattr(item, field, data[field])
    db.session.commit()
    return jsonify(item.to_dict())


@app.delete("/api/budget/items/<int:item_id>")
@jwt_required()
def delete_budget_item(item_id: int):
    user = get_current_user()
    num = (
        db.session.query(BudgetItem)
        .filter(BudgetItem.user_id == user.id, BudgetItem.id == item_id)
        .delete()
    )
    db.session.commit()
    if num == 0:
        return jsonify({"error": "not found"}), 404
    return ("", 204)


# -----------------------------
# Routes: Forecast
# -----------------------------

@app.post("/api/forecast/generate")
@jwt_required()
def generate_forecast():
    user = get_current_user()
    # Example plan gating: free users allowed one forecast per month
    if user.plan == "free":
        cutoff = datetime.utcnow() - timedelta(days=30)
        count = db.session.query(Forecast).filter(Forecast.user_id == user.id, Forecast.created_at >= cutoff).count()
        if count >= 1:
            return jsonify({"error": "Free plan allows 1 forecast/month. Upgrade to continue."}), 402
    data = request.get_json(force=True)
    try:
        horizon_days = int(data.get("horizon_days", 30))
        granularity = data.get("granularity", "daily")
        scenario = data.get("scenario") or {}
        if horizon_days not in (30, 60, 90):
            return jsonify({"error": "horizon_days must be 30|60|90"}), 400
        if granularity not in ("daily", "weekly"):
            return jsonify({"error": "granularity must be daily|weekly"}), 400
    except Exception as e:
        return jsonify({"error": f"invalid payload: {e}"}), 400

    result = _compute_forecast(user, horizon_days, granularity, scenario)
    return jsonify(result)


# -----------------------------
# Routes: Insights
# -----------------------------

@app.post("/api/insights/from-forecast")
@jwt_required()
def insights_from_forecast():
    user = get_current_user()
    if user.plan not in ("premium", "enterprise", "299", "pro"):  # allow multiple labels for top tier
        return jsonify({"error": "Insights available on ₹299 plan.", "insights": []}), 403
    data = request.get_json(force=True)
    points = data.get("points") or []
    profile = user.profile
    # Recompute metrics quickly from provided points
    opening = points[0]["opening_balance"] if points else (profile.starting_cash if profile else 0.0)
    total_in = sum(p.get("inflow", 0.0) for p in points)
    total_out = sum(p.get("outflow", 0.0) for p in points)
    ending = opening + total_in - total_out

    metrics = {
        "gross_burn_monthly": round((total_out / max(1, len(points))) * 30.0, 2) if points else 0.0,
        "net_burn_monthly": round(max(0.0, ((total_out - total_in) / max(1, len(points))) * 30.0), 2) if points else 0.0,
        "runway_months": None,
        "runway_date": None,
        "dso_days": int(profile.payment_cycle_days if profile else 30),
        "dpo_days": 15,
        "ccc_days": int(profile.payment_cycle_days if profile else 30) - 15,
    }
    alerts = []
    text = _generate_insights(points, profile, metrics, alerts)
    return jsonify({"insights": text, "ending_balance": round(ending, 2)})


# -----------------------------
# Routes: Alerts
# -----------------------------

@app.get("/api/alerts")
@jwt_required()
def list_alerts():
    user = get_current_user()
    if user.plan not in ("premium", "enterprise", "299", "pro"):
        return jsonify([])
    alerts = (
        db.session.query(Alert)
        .filter(Alert.user_id == user.id)
        .order_by(Alert.created_at.desc())
        .all()
    )
    return jsonify([a.to_dict() for a in alerts])


@app.post("/api/alerts/check-latest")
@jwt_required()
def check_latest_alerts():
    user = get_current_user()
    if user.plan not in ("premium", "enterprise", "299", "pro"):
        return jsonify({"alerts": []})
    # Evaluate against last forecast points
    last_forecast: Optional[Forecast] = (
        db.session.query(Forecast)
        .filter(Forecast.user_id == user.id)
        .order_by(Forecast.created_at.desc())
        .first()
    )
    if not last_forecast:
        return jsonify({"alerts": []})
    points = [p.to_dict() for p in db.session.query(ForecastPoint).filter(ForecastPoint.forecast_id == last_forecast.id).order_by(ForecastPoint.date.asc()).all()]
    alerts = _evaluate_alerts(user, points, user.profile)
    return jsonify({"alerts": [a.to_dict() for a in alerts]})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)