from functools import wraps
from pathlib import Path
from uuid import uuid4

from flask import current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import AuditLog


def role_required(*roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated or not current_user.has_role(*roles):
                flash("Você não tem permissão para acessar esta área.", "danger")
                return redirect(url_for("main.home"))
            return func(*args, **kwargs)

        return wrapper

    return decorator


def save_image(file: FileStorage):
    if not file or not file.filename:
        return None
    ext = Path(file.filename).suffix.lower()
    if ext not in current_app.config["UPLOAD_EXTENSIONS"]:
        raise ValueError("Formato de imagem não permitido.")
    filename = secure_filename(file.filename)
    safe_name = f"{uuid4().hex}-{filename}"
    target = Path(current_app.config["UPLOAD_FOLDER"]) / safe_name
    file.save(target)
    return safe_name


def register_security_headers(app):
    @app.after_request
    def apply_headers(response):
        response.headers["Content-Security-Policy"] = app.config["SECURITY_CSP"]
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(error):
        return render_template("404.html"), 404

    @app.errorhandler(413)
    def too_large(error):
        flash("Arquivo muito grande. Envie imagens menores.", "danger")
        return redirect(request.referrer or url_for("main.home"))

    @app.errorhandler(500)
    def server_error(error):
        db.session.rollback()
        return render_template("500.html"), 500


def audit_event(action, entity_type, entity_id=None, details=None):
    actor_id = current_user.id if current_user.is_authenticated else None
    db.session.add(
        AuditLog(
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=request.headers.get("X-Forwarded-For", request.remote_addr),
        )
    )
