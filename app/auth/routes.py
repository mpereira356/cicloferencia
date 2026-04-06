from datetime import datetime, timedelta

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import or_

from app.auth.forms import LoginForm, PasswordChangeForm, ProfileForm, RegisterForm
from app.extensions import db, limiter
from app.models import Favorite, LoginAttemptLog, Role, User
from app.utils.security import audit_event


auth_bp = Blueprint("auth", __name__)


def _client_ip():
    return request.headers.get("X-Forwarded-For", request.remote_addr)


def _recent_failures(identifier, ip_address):
    since = datetime.utcnow() - timedelta(minutes=15)
    return LoginAttemptLog.query.filter(
        LoginAttemptLog.created_at >= since,
        LoginAttemptLog.successful.is_(False),
        (LoginAttemptLog.email == identifier) | (LoginAttemptLog.ip_address == ip_address),
    ).count()


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10/minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    form = LoginForm()
    if form.validate_on_submit():
        identifier = form.email.data.lower().strip()
        ip_address = _client_ip()
        if _recent_failures(identifier, ip_address) >= 5:
            flash("Muitas tentativas inválidas. Aguarde alguns minutos e tente novamente.", "danger")
            return render_template("auth/login.html", form=form), 429

        user = User.query.filter(
            or_(
                User.email == identifier,
                User.name.ilike(identifier),
            )
        ).first()
        success = bool(user and user.is_active and user.check_password(form.password.data))

        db.session.add(
            LoginAttemptLog(
                email=identifier,
                ip_address=ip_address,
                user_agent=request.headers.get("User-Agent", "")[:255],
                successful=success,
            )
        )

        if not success:
            db.session.commit()
            flash("Credenciais inválidas.", "danger")
            return render_template("auth/login.html", form=form), 401

        login_user(user, remember=form.remember.data and not user.has_role("admin"))
        user.last_login_at = datetime.utcnow()
        user.last_login_ip = ip_address
        audit_event("login_success", "user", user.id, "Login efetuado com sucesso")
        db.session.commit()
        flash("Login realizado com sucesso.", "success")
        return redirect(request.args.get("next") or url_for("main.home"))

    if request.method == "POST":
        flash("Revise os campos informados e tente novamente.", "danger")

    return render_template("auth/login.html", form=form)


@auth_bp.route("/cadastro", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data.lower().strip()).first():
            flash("Este e-mail já está cadastrado.", "warning")
            return render_template("auth/register.html", form=form)

        role = Role.query.filter_by(slug="customer").first()
        if not role:
            role = Role(name="Cliente", slug="customer", description="Área do cliente")
            db.session.add(role)
            db.session.flush()

        user = User(
            name=form.name.data.strip(),
            email=form.email.data.lower().strip(),
            phone=form.phone.data.strip(),
            role=role,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        audit_event("register", "user", details=f"Novo cadastro: {user.email}")
        db.session.commit()
        flash("Cadastro criado. Faça login para continuar.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    audit_event("logout", "user", current_user.id, "Sessão encerrada")
    db.session.commit()
    logout_user()
    flash("Sessão encerrada com segurança.", "info")
    return redirect(url_for("main.home"))


@auth_bp.route("/conta", methods=["GET", "POST"])
@login_required
def account():
    profile_form = ProfileForm(obj=current_user)
    password_form = PasswordChangeForm()
    favorites = Favorite.query.filter_by(user_id=current_user.id).all()

    if profile_form.submit.data and profile_form.validate_on_submit():
        existing = User.query.filter(User.email == profile_form.email.data.lower().strip(), User.id != current_user.id).first()
        if existing:
            flash("Este e-mail já está em uso.", "danger")
        else:
            current_user.name = profile_form.name.data.strip()
            current_user.email = profile_form.email.data.lower().strip()
            current_user.phone = profile_form.phone.data.strip()
            audit_event("profile_update", "user", current_user.id, "Perfil atualizado")
            db.session.commit()
            flash("Perfil atualizado.", "success")
            return redirect(url_for("auth.account"))

    if password_form.submit.data and password_form.validate_on_submit():
        if not current_user.check_password(password_form.current_password.data):
            flash("Senha atual inválida.", "danger")
        else:
            current_user.set_password(password_form.new_password.data)
            audit_event("password_change", "user", current_user.id, "Senha alterada")
            db.session.commit()
            flash("Senha alterada com sucesso.", "success")
            return redirect(url_for("auth.account"))

    return render_template(
        "auth/account.html",
        profile_form=profile_form,
        password_form=password_form,
        favorites=favorites,
    )
