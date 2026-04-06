from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length


class LoginForm(FlaskForm):
    email = StringField("E-mail ou usuário", validators=[DataRequired(), Length(max=120)])
    password = PasswordField("Senha", validators=[DataRequired(), Length(max=128)])
    remember = BooleanField("Lembrar login")
    submit = SubmitField("Entrar")


class RegisterForm(FlaskForm):
    name = StringField("Nome", validators=[DataRequired(), Length(min=3, max=120)])
    email = StringField("E-mail", validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField("Telefone", validators=[Length(max=20)])
    password = PasswordField("Senha", validators=[DataRequired(), Length(min=8, max=128)])
    confirm_password = PasswordField(
        "Confirmar senha",
        validators=[DataRequired(), EqualTo("password")],
    )
    submit = SubmitField("Criar conta")


class ProfileForm(FlaskForm):
    name = StringField("Nome", validators=[DataRequired(), Length(min=3, max=120)])
    email = StringField("E-mail", validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField("Telefone", validators=[Length(max=20)])
    submit = SubmitField("Salvar perfil")


class PasswordChangeForm(FlaskForm):
    current_password = PasswordField("Senha atual", validators=[DataRequired()])
    new_password = PasswordField("Nova senha", validators=[DataRequired(), Length(min=8, max=128)])
    confirm_password = PasswordField(
        "Confirmar nova senha",
        validators=[DataRequired(), EqualTo("new_password")],
    )
    submit = SubmitField("Atualizar senha")
