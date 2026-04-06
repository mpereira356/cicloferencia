import click
from flask.cli import with_appcontext

from app.extensions import db
from app.models import (
    Banner,
    Brand,
    Category,
    Product,
    ProductImage,
    Role,
    Service,
    SiteSetting,
    SubCategory,
    Testimonial,
    User,
)


def register_cli_commands(app):
    @app.cli.command("create-admin")
    @click.option("--name", prompt=True)
    @click.option("--email", prompt=True)
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    @with_appcontext
    def create_admin(name, email, password):
        role = Role.query.filter_by(slug="admin").first()
        if not role:
            role = Role(name="Administrador", slug="admin", description="Acesso total")
            db.session.add(role)
            db.session.flush()
        user = User(name=name, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo("Admin criado com sucesso.")

    @app.cli.command("seed")
    @with_appcontext
    def seed():
        seed_data()
        click.echo("Seed executado com sucesso.")


def seed_data():
    roles = [
        ("Administrador", "admin", "Acesso total ao sistema"),
        ("Gerente", "manager", "Acesso operacional e editorial"),
        ("Cliente", "customer", "Área do cliente"),
    ]
    for name, slug, description in roles:
        if not Role.query.filter_by(slug=slug).first():
            db.session.add(Role(name=name, slug=slug, description=description))

    bikes = Category.query.filter_by(slug="bicicletas").first() or Category(
        name="Bicicletas",
        slug="bicicletas",
        description="Bikes urbanas, speed, MTB e seminovas revisadas.",
    )
    parts = Category.query.filter_by(slug="pecas").first() or Category(
        name="Peças",
        slug="pecas",
        description="Componentes e reposição com procedência.",
    )
    accessories = Category.query.filter_by(slug="acessorios").first() or Category(
        name="Acessórios",
        slug="acessorios",
        description="Capacetes, luzes, bolsas e itens de performance.",
    )
    db.session.add_all([bikes, parts, accessories])
    db.session.flush()

    for name, slug, category in [
        ("MTB", "mtb", bikes),
        ("Speed", "speed", bikes),
        ("Transmissão", "transmissao", parts),
        ("Freios", "freios", parts),
        ("Capacetes", "capacetes", accessories),
        ("Iluminação", "iluminacao", accessories),
    ]:
        if not SubCategory.query.filter_by(category_id=category.id, slug=slug).first():
            db.session.add(SubCategory(name=name, slug=slug, category=category))

    for name, slug in [("Sense", "sense"), ("Shimano", "shimano"), ("Absolute", "absolute")]:
        if not Brand.query.filter_by(slug=slug).first():
            db.session.add(Brand(name=name, slug=slug))

    for key, value in {
        "phone": "(11) 4000-1234",
        "whatsapp": "5511918669459",
        "address": "Rua das Oficinas, 245 - Centro",
        "hours": "Seg a Sex, 9h às 18h | Sábado, 9h às 14h",
        "instagram": "https://instagram.com/cicloferencia",
    }.items():
        if not SiteSetting.query.filter_by(key=key).first():
            db.session.add(SiteSetting(key=key, value=value))

    for title, subtitle, cta_text, cta_url in [
        (
            "Performance urbana com curadoria técnica",
            "Bikes, peças e oficina com padrão profissional para acompanhar o crescimento da sua pedalada.",
            "Ver catálogo",
            "/catalogo",
        ),
        (
            "Seminovas revisadas e prontas para rodar",
            "Modelos usados com checklist técnico, procedência e acabamento premium.",
            "Explorar bikes usadas",
            "/bicicletas?condition=used",
        ),
    ]:
        if not Banner.query.filter_by(title=title).first():
            db.session.add(Banner(title=title, subtitle=subtitle, cta_text=cta_text, cta_url=cta_url))

    for name, short_description, description, base_price, icon in [
        (
            "Revisão completa",
            "Inspeção técnica, lubrificação, alinhamento e checklist.",
            "Fluxo completo de oficina para manter bike, transmissão e freios em alto nível.",
            189.90,
            "shield",
        ),
        (
            "Troca de peças",
            "Substituição com instalação técnica e regulagem final.",
            "Serviço para upgrades, reposição e melhoria de performance.",
            49.90,
            "gear",
        ),
        (
            "Montagem e regulagem",
            "Montagem segura para bikes novas e ajustes finos de pilotagem.",
            "Ideal para bikes recém-compradas, upgrades de cockpit e setup personalizado.",
            79.90,
            "bolt",
        ),
    ]:
        if not Service.query.filter_by(name=name).first():
            db.session.add(
                Service(
                    name=name,
                    short_description=short_description,
                    description=description,
                    base_price=base_price,
                    icon=icon,
                )
            )

    for author, role_name, content in [
        (
            "Marina Lopes",
            "Cliente MTB",
            "Atendimento muito técnico e transparente. A bike voltou melhor do que quando saiu da fábrica.",
        ),
        (
            "Carlos Nunes",
            "Cliente urbano",
            "Loja organizada, peças boas e orçamento rápido pelo WhatsApp. Passa muita confiança.",
        ),
    ]:
        if not Testimonial.query.filter_by(author_name=author).first():
            db.session.add(Testimonial(author_name=author, author_role=role_name, content=content))

    db.session.flush()
    bike_brand = Brand.query.filter_by(slug="sense").first()
    shimano = Brand.query.filter_by(slug="shimano").first()
    absolute = Brand.query.filter_by(slug="absolute").first()
    mtb = SubCategory.query.filter_by(slug="mtb").first()
    transmissao = SubCategory.query.filter_by(slug="transmissao").first()
    capacetes = SubCategory.query.filter_by(slug="capacetes").first()

    products = [
        {
            "name": "Sense Impact Comp 29",
            "sku": "BIKE-001",
            "price": 5499.90,
            "promotional_price": 5199.90,
            "stock": 3,
            "is_featured": True,
            "is_bike": True,
            "category": bikes,
            "subcategory": mtb,
            "brand": bike_brand,
            "short_description": "MTB alumínio 12v pronta para trilhas e cidade.",
            "description": "Quadro leve, geometria moderna e conjunto confiável para evolução no pedal.",
            "technical_specs": "Quadro alumínio | Suspensão 100 mm | Transmissão 12v | Freio hidráulico",
        },
        {
            "name": "Sense Move Urban usada revisada",
            "sku": "BIKE-002",
            "price": 2490.00,
            "stock": 1,
            "is_featured": True,
            "is_bike": True,
            "is_used": True,
            "category": bikes,
            "subcategory": mtb,
            "brand": bike_brand,
            "short_description": "Bike urbana usada, revisada e com garantia da loja.",
            "description": "Modelo seminovo com checklist técnico completo e excelente custo-benefício.",
            "technical_specs": "Aro 29 | Freio a disco | Revisão completa | Nota fiscal da loja",
        },
        {
            "name": "Cassete Shimano Deore 12v",
            "sku": "PART-001",
            "price": 799.90,
            "stock": 8,
            "is_parts": True,
            "is_promotional": True,
            "category": parts,
            "subcategory": transmissao,
            "brand": shimano,
            "short_description": "Escalonamento preciso e durabilidade para uso intenso.",
            "description": "Componente original com excelente performance em MTB e pedal técnico.",
            "technical_specs": "10-51T | 12 velocidades | Aço tratado",
        },
        {
            "name": "Capacete Absolute Wild Flash",
            "sku": "ACC-001",
            "price": 289.90,
            "stock": 12,
            "is_accessory": True,
            "category": accessories,
            "subcategory": capacetes,
            "brand": absolute,
            "short_description": "Proteção, ventilação e visual limpo para treinos e deslocamentos.",
            "description": "Capacete com ajuste fino, ótima circulação de ar e acabamento premium.",
            "technical_specs": "Ajuste traseiro | 22 entradas de ar | Viseira removível",
        },
    ]

    for data in products:
        if not Product.query.filter_by(sku=data["sku"]).first():
            product = Product(**data)
            db.session.add(product)
            db.session.flush()
            db.session.add(
                ProductImage(
                    product=product,
                    file_name="logo_ciclo.png",
                    alt_text=product.name,
                    is_primary=True,
                )
            )

    db.session.commit()
