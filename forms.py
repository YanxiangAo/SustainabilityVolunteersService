from dataclasses import dataclass
from typing import Optional

@dataclass
class LoginForm:
    username_or_email: str
    password: str
    user_type: str

@dataclass
class RegisterForm:
    username: str
    email: str
    password: str
    user_type: str

def parse_login_form(request) -> LoginForm:
    return LoginForm(
        username_or_email=(request.form.get('username') or '').strip(),
        password=(request.form.get('password') or '').strip(),
        user_type=((request.form.get('user_type') or '').strip().lower()),
    )

def parse_register_form(request) -> RegisterForm:
    return RegisterForm(
        username=(request.form.get('username') or '').strip(),
        email=(request.form.get('email') or '').strip(),
        password=(request.form.get('password') or '').strip(),
        user_type=((request.form.get('user_type') or '').strip().lower()),
    )
