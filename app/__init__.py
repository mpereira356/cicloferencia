from pathlib import Path

from flask import Flask, request

from config import config_by_name

from .admin.routes import admin_bp
from .auth.routes import auth_bp
from .extensions import bcrypt, csrf, db, limiter, login_manager, migrate
from .main.routes import main_bp
from .models import User
from .services.cli import register_cli_commands
from .services.logging import configure_logging
from .utils.security import register_error_handlers, register_security_headers
from .utils.template import inject_globals


def create_app(config_name="default"):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    bcrypt.init_app(app)
    limiter.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"

    configure_logging(app)
    inject_globals(app)
    register_security_headers(app)
    register_error_handlers(app)
    register_cli_commands(app)

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    return app


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@login_manager.unauthorized_handler
def unauthorized():
    from flask import flash, redirect, url_for

    flash("Faça login para continuar.", "warning")
    return redirect(url_for("auth.login", next=request.path))
