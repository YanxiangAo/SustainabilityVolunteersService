"""Server-side form validation using WTForms."""
from wtforms import Form, StringField, PasswordField, SelectField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo, AnyOf


def _strip_filter(value: str | None) -> str | None:
    if value is None:
        return None
    return value.strip()


USER_TYPE_CHOICES = ('participant', 'organization', 'admin')


class LoginForm(Form):
    user_type = SelectField(
        'User Type',
        choices=[(choice, choice.capitalize()) for choice in USER_TYPE_CHOICES],
        validators=[DataRequired(message='User type is required'),
                    AnyOf(USER_TYPE_CHOICES, message='Unknown user type')],
    )
    username = StringField(
        'Username or Email',
        validators=[
            DataRequired(message='Username or email is required'),
            Length(max=120, message='Username or email must be under 120 characters'),
        ],
        filters=[_strip_filter],
    )
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message='Password is required'),
            Length(min=6, max=128, message='Password must be between 6 and 128 characters'),
        ],
    )
    remember = BooleanField('Remember Me', default=False)


class RegisterForm(Form):
    user_type = SelectField(
        'User Type',
        choices=[(choice, choice.capitalize()) for choice in USER_TYPE_CHOICES if choice != 'admin'],
        validators=[DataRequired(message='User type is required'),
                    AnyOf(('participant', 'organization'), message='Invalid user type')],
    )
    username = StringField(
        'Username',
        validators=[
            DataRequired(message='Username is required'),
            Length(min=3, max=50, message='Username must be between 3 and 50 characters'),
        ],
        filters=[_strip_filter],
    )
    email = StringField(
        'Email',
        validators=[
            DataRequired(message='Email is required'),
            Email(message='Invalid email address'),
            Length(max=120, message='Email must be under 120 characters'),
        ],
        filters=[_strip_filter],
    )
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message='Password is required'),
            Length(min=6, max=128, message='Password must be between 6 and 128 characters'),
        ],
    )
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(message='Please confirm your password'),
            EqualTo('password', message='Passwords must match'),
        ],
    )
