from datetime import datetime

from flask_login import UserMixin
from sqlalchemy import UniqueConstraint, event
from sqlalchemy.ext.hybrid import hybrid_property

from app.extensions import db
from app.utils.slug import slugify


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class StatusMixin:
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)


class Role(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(60), unique=True, nullable=False)
    description = db.Column(db.String(255))
    users = db.relationship("User", back_populates="role", lazy=True)


class User(UserMixin, TimestampMixin, StatusMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    last_login_at = db.Column(db.DateTime)
    last_login_ip = db.Column(db.String(45))
    two_factor_enabled = db.Column(db.Boolean, default=False, nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey("role.id"), nullable=False)
    role = db.relationship("Role", back_populates="users")
    favorites = db.relationship("Favorite", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        from werkzeug.security import generate_password_hash

        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash

        return check_password_hash(self.password_hash, password)

    def has_role(self, *role_names):
        return self.role and self.role.slug in role_names

    @property
    def is_admin(self):
        return self.has_role("admin", "manager")


class LoginAttemptLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), index=True)
    ip_address = db.Column(db.String(45), index=True)
    user_agent = db.Column(db.String(255))
    successful = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)


class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    actor = db.relationship("User")
    action = db.Column(db.String(120), nullable=False, index=True)
    entity_type = db.Column(db.String(80), nullable=False)
    entity_id = db.Column(db.Integer)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)


class Category(TimestampMixin, StatusMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)
    slug = db.Column(db.String(90), nullable=False, unique=True)
    description = db.Column(db.Text)
    subcategories = db.relationship("SubCategory", back_populates="category", cascade="all, delete-orphan")
    products = db.relationship("Product", back_populates="category")


class SubCategory(TimestampMixin, StatusMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(90), nullable=False)
    description = db.Column(db.Text)
    category = db.relationship("Category", back_populates="subcategories")
    products = db.relationship("Product", back_populates="subcategory")

    __table_args__ = (UniqueConstraint("category_id", "slug", name="uq_subcategory_category_slug"),)


class Brand(TimestampMixin, StatusMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)
    slug = db.Column(db.String(90), nullable=False, unique=True)
    description = db.Column(db.Text)
    products = db.relationship("Product", back_populates="brand")


class Product(TimestampMixin, StatusMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, index=True)
    slug = db.Column(db.String(170), nullable=False, unique=True, index=True)
    sku = db.Column(db.String(50), nullable=False, unique=True)
    short_description = db.Column(db.String(255))
    description = db.Column(db.Text)
    technical_specs = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    promotional_price = db.Column(db.Numeric(10, 2))
    stock = db.Column(db.Integer, default=0, nullable=False)
    is_featured = db.Column(db.Boolean, default=False, nullable=False)
    is_promotional = db.Column(db.Boolean, default=False, nullable=False)
    is_used = db.Column(db.Boolean, default=False, nullable=False)
    is_bike = db.Column(db.Boolean, default=False, nullable=False)
    is_parts = db.Column(db.Boolean, default=False, nullable=False)
    is_accessory = db.Column(db.Boolean, default=False, nullable=False)
    view_count = db.Column(db.Integer, default=0, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)
    subcategory_id = db.Column(db.Integer, db.ForeignKey("sub_category.id"))
    brand_id = db.Column(db.Integer, db.ForeignKey("brand.id"), nullable=False)
    category = db.relationship("Category", back_populates="products")
    subcategory = db.relationship("SubCategory", back_populates="products")
    brand = db.relationship("Brand", back_populates="products")
    images = db.relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")
    favorites = db.relationship("Favorite", back_populates="product", cascade="all, delete-orphan")

    @hybrid_property
    def display_price(self):
        return self.promotional_price or self.price

    @property
    def in_stock(self):
        return self.stock > 0


class ProductImage(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    alt_text = db.Column(db.String(150))
    is_primary = db.Column(db.Boolean, default=False, nullable=False)
    product = db.relationship("Product", back_populates="images")


class Testimonial(TimestampMixin, StatusMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author_name = db.Column(db.String(120), nullable=False)
    author_role = db.Column(db.String(120))
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, default=5, nullable=False)


class ContactMessage(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    subject = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(50), default="contato", nullable=False)
    is_resolved = db.Column(db.Boolean, default=False, nullable=False)


class Banner(TimestampMixin, StatusMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    subtitle = db.Column(db.String(255))
    cta_text = db.Column(db.String(60))
    cta_url = db.Column(db.String(255))
    image_path = db.Column(db.String(255))
    sort_order = db.Column(db.Integer, default=0, nullable=False)


class Service(TimestampMixin, StatusMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(130), nullable=False, unique=True)
    short_description = db.Column(db.String(255))
    description = db.Column(db.Text)
    base_price = db.Column(db.Numeric(10, 2))
    icon = db.Column(db.String(50), default="wrench")


class Favorite(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    user = db.relationship("User", back_populates="favorites")
    product = db.relationship("Product", back_populates="favorites")

    __table_args__ = (UniqueConstraint("user_id", "product_id", name="uq_favorite_user_product"),)


class NewsletterSubscriber(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)


class SiteSetting(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(80), unique=True, nullable=False)
    value = db.Column(db.Text)


def _set_slug(mapper, connection, target):
    if hasattr(target, "name") and hasattr(target, "slug") and (not target.slug):
        target.slug = slugify(target.name)
    if hasattr(target, "title") and hasattr(target, "slug") and (not target.slug):
        target.slug = slugify(target.title)


for model in [Role, Category, SubCategory, Brand, Product, Service]:
    event.listen(model, "before_insert", _set_slug)
