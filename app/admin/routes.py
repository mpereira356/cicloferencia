from datetime import datetime
from decimal import Decimal

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.admin.forms import (
    BannerForm,
    BrandForm,
    CategoryForm,
    CustomerForm,
    ProductForm,
    SaleForm,
    ServiceForm,
    SiteSettingForm,
    TestimonialForm,
    UserForm,
)
from app.extensions import db
from app.models import (
    AuditLog,
    Banner,
    Brand,
    Category,
    ContactMessage,
    Customer,
    LoginAttemptLog,
    Product,
    ProductImage,
    Role,
    Sale,
    Service,
    SiteSetting,
    SubCategory,
    Testimonial,
    User,
)
from app.utils.security import audit_event, role_required, save_image
from app.utils.sku import generate_product_sku, generate_sale_number


admin_bp = Blueprint("admin", __name__)


@admin_bp.before_request
@login_required
@role_required("admin", "manager")
def restrict_admin():
    return None


def _product_form_choices(form):
    form.category_id.choices = [(item.id, item.name) for item in Category.query.order_by(Category.name).all()]
    form.subcategory_id.choices = [(0, "Sem subcategoria")] + [
        (item.id, f"{item.category.name} / {item.name}") for item in SubCategory.query.order_by(SubCategory.name).all()
    ]
    form.brand_id.choices = [(item.id, item.name) for item in Brand.query.order_by(Brand.name).all()]


def _sale_form_choices(form):
    form.customer_id.choices = [(item.id, item.name) for item in Customer.query.filter_by(is_active=True).order_by(Customer.name).all()]
    form.product_id.choices = [(0, "Venda sem produto vinculado")] + [
        (item.id, f"{item.name} ({item.sku})") for item in Product.query.filter_by(is_active=True).order_by(Product.name).all()
    ]


def _setting_value(key, default=""):
    setting = SiteSetting.query.filter_by(key=key).first()
    return setting.value if setting else default


def _admin_unseen_messages_count():
    last_seen_raw = _setting_value("admin_last_seen_message_id", "0")
    try:
        last_seen_id = int(last_seen_raw or 0)
    except ValueError:
        last_seen_id = 0
    return ContactMessage.query.filter(ContactMessage.id > last_seen_id).count()


@admin_bp.app_context_processor
def inject_admin_context():
    return {
        "admin_unseen_messages_count": _admin_unseen_messages_count(),
    }


@admin_bp.route("/")
def dashboard():
    stats = {
        "users": User.query.count(),
        "products": Product.query.count(),
        "categories": Category.query.count(),
        "messages": ContactMessage.query.count(),
        "customers": Customer.query.count(),
        "sales": Sale.query.count(),
        "out_of_stock": Product.query.filter(Product.stock <= 0).count(),
        "login_failures": LoginAttemptLog.query.filter_by(successful=False).order_by(LoginAttemptLog.created_at.desc()).limit(10).all(),
        "recent_audits": AuditLog.query.order_by(AuditLog.created_at.desc()).limit(10).all(),
        "recent_users": User.query.order_by(User.last_login_at.desc().nullslast()).limit(8).all(),
        "low_stock": Product.query.filter(Product.stock <= 2).order_by(Product.stock.asc()).limit(8).all(),
    }
    chart = {
        "labels": ["Bikes", "Peças", "Acessórios", "Usados"],
        "values": [
            Product.query.filter_by(is_bike=True).count(),
            Product.query.filter_by(is_parts=True).count(),
            Product.query.filter_by(is_accessory=True).count(),
            Product.query.filter_by(is_used=True).count(),
        ],
    }
    return render_template("admin/dashboard.html", stats=stats, chart=chart)


@admin_bp.route("/produtos")
def products():
    return render_template("admin/products.html", items=Product.query.order_by(Product.created_at.desc()).all())


@admin_bp.route("/produtos/novo", methods=["GET", "POST"])
@admin_bp.route("/produtos/<int:product_id>/editar", methods=["GET", "POST"])
def product_form(product_id=None):
    product = Product.query.get(product_id) if product_id else Product()
    form = ProductForm(obj=product)
    _product_form_choices(form)

    if request.method == "GET" and product_id:
        form.subcategory_id.data = product.subcategory_id or 0

    if form.validate_on_submit():
        product.name = form.name.data.strip()
        product.sku = (form.sku.data or "").strip().upper()
        product.short_description = form.short_description.data.strip()
        product.description = form.description.data.strip()
        product.technical_specs = form.technical_specs.data.strip()
        product.price = form.price.data
        product.promotional_price = form.promotional_price.data
        product.stock = int(form.stock.data)
        product.category_id = form.category_id.data
        product.subcategory_id = form.subcategory_id.data or None
        product.brand_id = form.brand_id.data
        product.is_featured = form.is_featured.data
        product.is_promotional = form.is_promotional.data
        product.is_used = form.is_used.data
        product.is_bike = form.is_bike.data
        product.is_parts = form.is_parts.data
        product.is_accessory = form.is_accessory.data
        product.is_active = form.is_active.data

        db.session.add(product)
        db.session.flush()
        if not product.sku:
            product.sku = generate_product_sku(product)

        for upload in form.images.data:
            if upload and upload.filename:
                filename = save_image(upload)
                db.session.add(
                    ProductImage(
                        product_id=product.id,
                        file_name=filename,
                        alt_text=product.name,
                        is_primary=(len(product.images) == 0),
                    )
                )

        audit_event(
            "product_updated" if product_id else "product_created",
            "product",
            product.id,
            f"Produto {product.name} salvo por {current_user.email}",
        )
        db.session.commit()
        flash("Produto salvo com sucesso.", "success")
        return redirect(url_for("admin.products"))

    return render_template("admin/product_form.html", form=form, product=product)


@admin_bp.route("/produtos/<int:product_id>/toggle", methods=["POST"])
def toggle_product(product_id):
    product = Product.query.get_or_404(product_id)
    product.is_active = not product.is_active
    audit_event("product_toggle", "product", product.id, f"Ativo: {product.is_active}")
    db.session.commit()
    flash("Status do produto atualizado.", "info")
    return redirect(url_for("admin.products"))


@admin_bp.route("/produtos/<int:product_id>/excluir", methods=["POST"])
@role_required("admin")
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    audit_event("product_deleted", "product", product.id, product.name)
    db.session.delete(product)
    db.session.commit()
    flash("Produto excluído.", "warning")
    return redirect(url_for("admin.products"))


@admin_bp.route("/clientes")
def customers():
    return render_template("admin/customers.html", items=Customer.query.order_by(Customer.created_at.desc()).all())


@admin_bp.route("/clientes/novo", methods=["GET", "POST"])
@admin_bp.route("/clientes/<int:customer_id>/editar", methods=["GET", "POST"])
def customer_form(customer_id=None):
    customer = Customer.query.get(customer_id) if customer_id else Customer()
    form = CustomerForm(obj=customer)
    if form.validate_on_submit():
        customer.name = form.name.data.strip()
        customer.person_type = form.person_type.data
        customer.document = form.document.data.strip()
        customer.contact_name = form.contact_name.data.strip()
        customer.phone = form.phone.data.strip()
        customer.whatsapp = form.whatsapp.data.strip()
        customer.email = form.email.data.strip().lower()
        customer.address = form.address.data.strip()
        customer.city = form.city.data.strip()
        customer.state = form.state.data.strip()
        customer.postal_code = form.postal_code.data.strip()
        customer.notes = form.notes.data.strip()
        customer.is_active = form.is_active.data
        db.session.add(customer)
        audit_event(
            "customer_updated" if customer_id else "customer_created",
            "customer",
            customer.id,
            f"Cliente {customer.name} salvo por {current_user.email}",
        )
        db.session.commit()
        flash("Cliente salvo com sucesso.", "success")
        return redirect(url_for("admin.customers"))
    return render_template("admin/customer_form.html", form=form, customer=customer)


@admin_bp.route("/vendas")
def sales():
    items = Sale.query.order_by(Sale.sold_at.desc()).all()
    return render_template("admin/sales.html", items=items)


@admin_bp.route("/vendas/nova", methods=["GET", "POST"])
def sale_form():
    if Customer.query.filter_by(is_active=True).count() == 0:
        flash("Cadastre ao menos um cliente antes de registrar vendas.", "warning")
        return redirect(url_for("admin.customer_form"))
    form = SaleForm()
    _sale_form_choices(form)
    if request.method == "GET":
        form.sold_at.data = datetime.utcnow()

    if form.validate_on_submit():
        product = Product.query.get(form.product_id.data) if form.product_id.data else None
        product_name = form.product_name.data.strip() if form.product_name.data else ""
        if product and not product_name:
            product_name = product.name
        if not product_name:
            flash("Informe um item vendido ou selecione um produto.", "danger")
            return render_template("admin/sale_form.html", form=form)

        quantity = int(form.quantity.data)
        unit_price = Decimal(form.unit_price.data)
        sale = Sale(
            sale_number="PENDENTE",
            customer_id=form.customer_id.data,
            product_id=product.id if product else None,
            recorded_by_id=current_user.id,
            product_name=product_name,
            sku=product.sku if product else None,
            quantity=quantity,
            unit_price=unit_price,
            total_price=unit_price * quantity,
            payment_method=form.payment_method.data,
            status=form.status.data,
            sold_at=form.sold_at.data,
            notes=form.notes.data.strip(),
        )
        db.session.add(sale)
        db.session.flush()
        sale.sale_number = generate_sale_number(sale)
        if product and product.stock >= quantity:
            product.stock -= quantity
        audit_event("sale_created", "sale", sale.id, f"Venda {sale.sale_number} registrada")
        db.session.commit()
        flash("Venda registrada com sucesso.", "success")
        return redirect(url_for("admin.sales"))

    return render_template("admin/sale_form.html", form=form)


@admin_bp.route("/categorias", methods=["GET", "POST"])
def categories():
    form = CategoryForm()
    if form.validate_on_submit():
        db.session.add(Category(name=form.name.data.strip(), description=form.description.data.strip(), is_active=form.is_active.data))
        audit_event("category_created", "category", details=form.name.data.strip())
        db.session.commit()
        flash("Categoria criada.", "success")
        return redirect(url_for("admin.categories"))
    return render_template("admin/categories.html", items=Category.query.order_by(Category.name).all(), form=form)


@admin_bp.route("/marcas", methods=["GET", "POST"])
def brands():
    form = BrandForm()
    if form.validate_on_submit():
        db.session.add(Brand(name=form.name.data.strip(), description=form.description.data.strip(), is_active=form.is_active.data))
        audit_event("brand_created", "brand", details=form.name.data.strip())
        db.session.commit()
        flash("Marca criada.", "success")
        return redirect(url_for("admin.brands"))
    return render_template("admin/brands.html", items=Brand.query.order_by(Brand.name).all(), form=form)


@admin_bp.route("/banners", methods=["GET", "POST"])
def banners():
    form = BannerForm()
    if form.validate_on_submit():
        db.session.add(
            Banner(
                title=form.title.data.strip(),
                subtitle=form.subtitle.data.strip(),
                cta_text=form.cta_text.data.strip(),
                cta_url=form.cta_url.data.strip(),
                is_active=form.is_active.data,
            )
        )
        audit_event("banner_created", "banner", details=form.title.data.strip())
        db.session.commit()
        flash("Banner criado.", "success")
        return redirect(url_for("admin.banners"))
    return render_template("admin/banners.html", items=Banner.query.order_by(Banner.created_at.desc()).all(), form=form)


@admin_bp.route("/servicos", methods=["GET", "POST"])
def services():
    form = ServiceForm()
    if form.validate_on_submit():
        db.session.add(
            Service(
                name=form.name.data.strip(),
                short_description=form.short_description.data.strip(),
                description=form.description.data.strip(),
                base_price=form.base_price.data,
                icon=form.icon.data.strip(),
                is_active=form.is_active.data,
            )
        )
        audit_event("service_created", "service", details=form.name.data.strip())
        db.session.commit()
        flash("Serviço cadastrado.", "success")
        return redirect(url_for("admin.services"))
    return render_template("admin/services.html", items=Service.query.order_by(Service.name).all(), form=form)


@admin_bp.route("/depoimentos", methods=["GET", "POST"])
def testimonials():
    form = TestimonialForm()
    if form.validate_on_submit():
        db.session.add(
            Testimonial(
                author_name=form.author_name.data.strip(),
                author_role=form.author_role.data.strip(),
                content=form.content.data.strip(),
                is_active=form.is_active.data,
            )
        )
        audit_event("testimonial_created", "testimonial", details=form.author_name.data.strip())
        db.session.commit()
        flash("Depoimento salvo.", "success")
        return redirect(url_for("admin.testimonials"))
    return render_template("admin/testimonials.html", items=Testimonial.query.order_by(Testimonial.created_at.desc()).all(), form=form)


@admin_bp.route("/mensagens")
def messages():
    items = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    latest_message = ContactMessage.query.order_by(ContactMessage.id.desc()).first()
    setting = SiteSetting.query.filter_by(key="admin_last_seen_message_id").first()
    if not setting:
        setting = SiteSetting(key="admin_last_seen_message_id", value="0")
        db.session.add(setting)
    setting.value = str(latest_message.id if latest_message else 0)
    db.session.commit()
    return render_template("admin/messages.html", items=items)


@admin_bp.route("/mensagens/<int:message_id>/excluir", methods=["POST"])
def delete_message(message_id):
    message = ContactMessage.query.get_or_404(message_id)
    audit_event("message_deleted", "contact_message", message.id, f"Mensagem removida: {message.subject}")
    db.session.delete(message)
    db.session.commit()
    flash("Mensagem excluída com sucesso.", "warning")
    return redirect(url_for("admin.messages"))


@admin_bp.route("/usuarios")
@role_required("admin")
def users():
    return render_template("admin/users.html", items=User.query.order_by(User.created_at.desc()).all())


@admin_bp.route("/usuarios/<int:user_id>/editar", methods=["GET", "POST"])
@role_required("admin")
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)
    form.role_id.choices = [(role.id, role.name) for role in Role.query.order_by(Role.name).all()]
    if form.validate_on_submit():
        user.name = form.name.data.strip()
        user.email = form.email.data.lower().strip()
        user.phone = form.phone.data.strip()
        user.role_id = form.role_id.data
        user.is_active = form.is_active.data
        if form.password.data:
            user.set_password(form.password.data)
        audit_event("user_updated", "user", user.id, f"Perfil alterado para {user.role.slug}")
        db.session.commit()
        flash("Usuário atualizado.", "success")
        return redirect(url_for("admin.users"))
    return render_template("admin/user_form.html", form=form, user=user)


@admin_bp.route("/logs")
def logs():
    return render_template(
        "admin/logs.html",
        audit_logs=AuditLog.query.order_by(AuditLog.created_at.desc()).limit(100).all(),
        login_logs=LoginAttemptLog.query.order_by(LoginAttemptLog.created_at.desc()).limit(100).all(),
    )


@admin_bp.route("/configuracoes", methods=["GET", "POST"])
def settings():
    form = SiteSettingForm(
        phone=_setting_value("phone"),
        whatsapp=_setting_value("whatsapp"),
        address=_setting_value("address"),
        hours=_setting_value("hours"),
        instagram=_setting_value("instagram"),
    )
    if form.validate_on_submit():
        for key in ["phone", "whatsapp", "address", "hours", "instagram"]:
            setting = SiteSetting.query.filter_by(key=key).first()
            if not setting:
                setting = SiteSetting(key=key)
                db.session.add(setting)
            setting.value = getattr(form, key).data.strip()
        audit_event("settings_updated", "site_setting", details="Configurações gerais atualizadas")
        db.session.commit()
        flash("Configurações salvas.", "success")
        return redirect(url_for("admin.settings"))
    return render_template("admin/settings.html", form=form)
