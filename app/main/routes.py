from decimal import Decimal

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from app.extensions import db
from app.main.forms import ContactForm, NewsletterForm
from app.models import (
    Banner,
    Brand,
    Category,
    ContactMessage,
    Favorite,
    NewsletterSubscriber,
    Product,
    Service,
    SubCategory,
    Testimonial,
)
from app.utils.security import audit_event


main_bp = Blueprint("main", __name__)


def _catalog_query():
    query = Product.query.filter_by(is_active=True)
    search = request.args.get("q", "").strip()
    category_slug = request.args.get("category")
    subcategory_slug = request.args.get("subcategory")
    brand_slug = request.args.get("brand")
    availability = request.args.get("availability")
    condition = request.args.get("condition")
    sort = request.args.get("sort", "featured")
    min_price = request.args.get("min_price")
    max_price = request.args.get("max_price")

    if search:
        query = query.filter(or_(Product.name.ilike(f"%{search}%"), Product.description.ilike(f"%{search}%")))
    if category_slug:
        query = query.join(Category).filter(Category.slug == category_slug)
    if subcategory_slug:
        query = query.join(SubCategory, isouter=True).filter(SubCategory.slug == subcategory_slug)
    if brand_slug:
        query = query.join(Brand).filter(Brand.slug == brand_slug)
    if availability == "in_stock":
        query = query.filter(Product.stock > 0)
    if condition == "used":
        query = query.filter(Product.is_used.is_(True))
    elif condition == "new":
        query = query.filter(Product.is_used.is_(False))
    if min_price:
        query = query.filter(Product.price >= Decimal(min_price))
    if max_price:
        query = query.filter(Product.price <= Decimal(max_price))

    sort_map = {
        "price_asc": Product.price.asc(),
        "price_desc": Product.price.desc(),
        "name_asc": Product.name.asc(),
        "recent": Product.created_at.desc(),
        "featured": Product.is_featured.desc(),
    }
    return query.order_by(sort_map.get(sort, Product.is_featured.desc()))


@main_bp.route("/")
def home():
    return render_template(
        "main/home.html",
        banners=Banner.query.filter_by(is_active=True).order_by(Banner.sort_order.asc()).all(),
        featured_products=Product.query.filter_by(is_active=True, is_featured=True).limit(6).all(),
        used_bikes=Product.query.filter_by(is_active=True, is_bike=True, is_used=True).limit(4).all(),
        services=Service.query.filter_by(is_active=True).limit(4).all(),
        testimonials=Testimonial.query.filter_by(is_active=True).limit(6).all(),
        newsletter_form=NewsletterForm(),
    )


@main_bp.route("/catalogo")
def catalog():
    products = _catalog_query().paginate(page=request.args.get("page", 1, type=int), per_page=12)
    filters = {
        "categories": Category.query.filter_by(is_active=True).all(),
        "subcategories": SubCategory.query.filter_by(is_active=True).all(),
        "brands": Brand.query.filter_by(is_active=True).all(),
    }
    return render_template("main/catalog.html", products=products, filters=filters)


@main_bp.route("/produto/<slug>")
def product_detail(slug):
    product = Product.query.filter_by(slug=slug, is_active=True).first_or_404()
    product.view_count += 1
    db.session.commit()
    related_products = (
        Product.query.filter(
            Product.category_id == product.category_id,
            Product.id != product.id,
            Product.is_active.is_(True),
        )
        .limit(4)
        .all()
    )
    favorite_ids = {item.product_id for item in current_user.favorites} if current_user.is_authenticated else set()
    return render_template(
        "main/product_detail.html",
        product=product,
        related_products=related_products,
        favorite_ids=favorite_ids,
    )


@main_bp.route("/bicicletas")
def bikes():
    products = _catalog_query().filter(Product.is_bike.is_(True)).paginate(page=request.args.get("page", 1, type=int), per_page=12)
    return render_template("main/bikes.html", products=products)


@main_bp.route("/pecas-e-acessorios")
def parts():
    products = _catalog_query().filter(or_(Product.is_parts.is_(True), Product.is_accessory.is_(True))).paginate(
        page=request.args.get("page", 1, type=int),
        per_page=12,
    )
    return render_template("main/parts.html", products=products)


@main_bp.route("/oficina", methods=["GET", "POST"])
def services_page():
    services = Service.query.filter_by(is_active=True).all()
    form = ContactForm()
    form.message_type.data = "orcamento"
    if form.validate_on_submit():
        db.session.add(
            ContactMessage(
                name=form.name.data.strip(),
                email=form.email.data.strip().lower(),
                phone=form.phone.data.strip(),
                subject=form.subject.data.strip(),
                message=form.message.data.strip(),
                message_type="orcamento",
            )
        )
        db.session.commit()
        flash("Orçamento solicitado. Retornaremos em breve.", "success")
        return redirect(url_for("main.services_page"))
    return render_template("main/services.html", services=services, form=form)


@main_bp.route("/sobre")
def about():
    return render_template("main/about.html")


@main_bp.route("/contato", methods=["GET", "POST"])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        db.session.add(
            ContactMessage(
                name=form.name.data.strip(),
                email=form.email.data.strip().lower(),
                phone=form.phone.data.strip(),
                subject=form.subject.data.strip(),
                message=form.message.data.strip(),
                message_type=form.message_type.data or "contato",
            )
        )
        db.session.commit()
        flash("Mensagem enviada com sucesso.", "success")
        return redirect(url_for("main.contact"))
    return render_template("main/contact.html", form=form)


@main_bp.route("/novidades")
def blog():
    highlights = Product.query.filter_by(is_active=True).order_by(Product.view_count.desc()).limit(6).all()
    return render_template("main/blog.html", highlights=highlights)


@main_bp.route("/newsletter", methods=["POST"])
def newsletter():
    form = NewsletterForm()
    if form.validate_on_submit() and not NewsletterSubscriber.query.filter_by(email=form.email.data.lower().strip()).first():
        db.session.add(NewsletterSubscriber(email=form.email.data.lower().strip()))
        db.session.commit()
        flash("Inscrição confirmada.", "success")
    else:
        flash("Não foi possível salvar este e-mail.", "warning")
    return redirect(request.referrer or url_for("main.home"))


@main_bp.route("/favoritos/<int:product_id>", methods=["POST"])
@login_required
def toggle_favorite(product_id):
    product = Product.query.get_or_404(product_id)
    favorite = Favorite.query.filter_by(user_id=current_user.id, product_id=product.id).first()
    if favorite:
        db.session.delete(favorite)
        flash("Produto removido dos favoritos.", "info")
    else:
        db.session.add(Favorite(user_id=current_user.id, product_id=product.id))
        flash("Produto favoritado.", "success")
    audit_event("favorite_toggle", "product", product.id, f"Usuário {current_user.email} alterou favorito")
    db.session.commit()
    return redirect(request.referrer or url_for("main.product_detail", slug=product.slug))


@main_bp.route("/comparar")
def compare():
    ids = [int(item) for item in request.args.getlist("id") if item.isdigit()][:3]
    products = Product.query.filter(Product.id.in_(ids)).all() if ids else []
    return render_template("main/compare.html", products=products)


@main_bp.route("/sitemap.xml")
def sitemap():
    pages = [
        url_for("main.home", _external=True),
        url_for("main.catalog", _external=True),
        url_for("main.bikes", _external=True),
        url_for("main.parts", _external=True),
        url_for("main.services_page", _external=True),
        url_for("main.about", _external=True),
        url_for("main.contact", _external=True),
    ]
    products = [url_for("main.product_detail", slug=product.slug, _external=True) for product in Product.query.all()]
    xml = render_template("sitemap.xml", pages=pages + products)
    return current_app.response_class(xml, mimetype="application/xml")
