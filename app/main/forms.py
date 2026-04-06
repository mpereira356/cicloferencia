from flask_wtf import FlaskForm
from wtforms import EmailField, HiddenField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional


class ContactForm(FlaskForm):
    name = StringField("Nome", validators=[DataRequired(), Length(max=120)])
    email = EmailField("E-mail", validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField("Telefone", validators=[Optional(), Length(max=20)])
    subject = StringField("Assunto", validators=[DataRequired(), Length(max=150)])
    message = TextAreaField("Mensagem", validators=[DataRequired(), Length(min=10, max=2000)])
    message_type = HiddenField(default="contato")
    submit = SubmitField("Enviar mensagem")


class NewsletterForm(FlaskForm):
    email = EmailField("E-mail", validators=[DataRequired(), Email(), Length(max=120)])
    submit = SubmitField("Assinar")
