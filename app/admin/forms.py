from flask_wtf import FlaskForm
from flask_wtf.file import MultipleFileField
from wtforms import BooleanField, DecimalField, PasswordField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional


class CategoryForm(FlaskForm):
    name = StringField("Nome", validators=[DataRequired(), Length(max=80)])
    description = TextAreaField("Descrição", validators=[Optional(), Length(max=500)])
    is_active = BooleanField("Ativo", default=True)
    submit = SubmitField("Salvar")


class BrandForm(FlaskForm):
    name = StringField("Nome", validators=[DataRequired(), Length(max=80)])
    description = TextAreaField("Descrição", validators=[Optional(), Length(max=500)])
    is_active = BooleanField("Ativo", default=True)
    submit = SubmitField("Salvar")


class ServiceForm(FlaskForm):
    name = StringField("Nome", validators=[DataRequired(), Length(max=120)])
    short_description = StringField("Resumo", validators=[Optional(), Length(max=255)])
    description = TextAreaField("Descrição")
    base_price = DecimalField("Preço base", validators=[Optional()], places=2)
    icon = StringField("Ícone", validators=[Optional(), Length(max=50)])
    is_active = BooleanField("Ativo", default=True)
    submit = SubmitField("Salvar")


class BannerForm(FlaskForm):
    title = StringField("Título", validators=[DataRequired(), Length(max=120)])
    subtitle = StringField("Subtítulo", validators=[Optional(), Length(max=255)])
    cta_text = StringField("CTA", validators=[Optional(), Length(max=60)])
    cta_url = StringField("URL CTA", validators=[Optional(), Length(max=255)])
    is_active = BooleanField("Ativo", default=True)
    submit = SubmitField("Salvar")


class TestimonialForm(FlaskForm):
    author_name = StringField("Autor", validators=[DataRequired(), Length(max=120)])
    author_role = StringField("Cargo/Perfil", validators=[Optional(), Length(max=120)])
    content = TextAreaField("Depoimento", validators=[DataRequired(), Length(min=10, max=1000)])
    is_active = BooleanField("Ativo", default=True)
    submit = SubmitField("Salvar")


class ProductForm(FlaskForm):
    name = StringField("Nome", validators=[DataRequired(), Length(max=150)])
    sku = StringField("SKU", validators=[DataRequired(), Length(max=50)])
    short_description = StringField("Resumo", validators=[Optional(), Length(max=255)])
    description = TextAreaField("Descrição")
    technical_specs = TextAreaField("Especificações")
    price = DecimalField("Preço", validators=[DataRequired()], places=2)
    promotional_price = DecimalField("Preço promocional", validators=[Optional()], places=2)
    stock = StringField("Estoque", validators=[DataRequired()])
    category_id = SelectField("Categoria", coerce=int, validators=[DataRequired()])
    subcategory_id = SelectField("Subcategoria", coerce=int, validators=[Optional()])
    brand_id = SelectField("Marca", coerce=int, validators=[DataRequired()])
    images = MultipleFileField("Imagens")
    is_featured = BooleanField("Destaque")
    is_promotional = BooleanField("Promocional")
    is_used = BooleanField("Usado")
    is_bike = BooleanField("Bike")
    is_parts = BooleanField("Peça")
    is_accessory = BooleanField("Acessório")
    is_active = BooleanField("Ativo", default=True)
    submit = SubmitField("Salvar")


class UserForm(FlaskForm):
    name = StringField("Nome", validators=[DataRequired(), Length(max=120)])
    email = StringField("E-mail", validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField("Telefone", validators=[Optional(), Length(max=20)])
    role_id = SelectField("Perfil", coerce=int, validators=[DataRequired()])
    is_active = BooleanField("Conta ativa", default=True)
    password = PasswordField("Nova senha", validators=[Optional(), Length(min=8, max=128)])
    submit = SubmitField("Salvar")


class SiteSettingForm(FlaskForm):
    phone = StringField("Telefone", validators=[Optional(), Length(max=120)])
    whatsapp = StringField("WhatsApp", validators=[Optional(), Length(max=120)])
    address = StringField("Endereço", validators=[Optional(), Length(max=255)])
    hours = StringField("Horário", validators=[Optional(), Length(max=255)])
    instagram = StringField("Instagram", validators=[Optional(), Length(max=255)])
    submit = SubmitField("Salvar configurações")
