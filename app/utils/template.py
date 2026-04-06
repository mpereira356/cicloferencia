from flask import current_app

from app.models import Category, SiteSetting


def inject_globals(app):
    @app.context_processor
    def global_context():
        settings = {item.key: item.value for item in SiteSetting.query.all()}
        return {
            "site_name": current_app.config["APP_NAME"],
            "site_slug": current_app.config["APP_SLUG"],
            "site_categories": Category.query.filter_by(is_active=True).all(),
            "settings": settings,
            "whatsapp_number": settings.get("whatsapp", current_app.config["CONTACT_WHATSAPP"]),
        }
