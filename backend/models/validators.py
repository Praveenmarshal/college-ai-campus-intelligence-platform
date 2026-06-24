"""
models/validators.py
Marshmallow schemas for request body validation.
Used by auth and user routes to validate incoming JSON payloads.
"""

import re
from marshmallow import Schema, fields, validate, validates, ValidationError, pre_load


PASSWORD_MIN = 8
PASSWORD_MAX = 72  # bcrypt limit


def _strong_password(value: str):
    """Require at least one letter and one digit."""
    if len(value) < PASSWORD_MIN:
        raise ValidationError(f"Password must be at least {PASSWORD_MIN} characters.")
    if len(value) > PASSWORD_MAX:
        raise ValidationError(f"Password must not exceed {PASSWORD_MAX} characters.")
    if not re.search(r"[A-Za-z]", value):
        raise ValidationError("Password must contain at least one letter.")
    if not re.search(r"\d", value):
        raise ValidationError("Password must contain at least one digit.")


# ── Auth schemas ──────────────────────────────────────────
class RegisterSchema(Schema):
    name = fields.Str(
        required=True,
        validate=validate.Length(min=2, max=80),
        error_messages={"required": "Name is required."},
    )
    email = fields.Email(
        required=True,
        error_messages={"required": "Email is required.", "invalid": "Invalid email address."},
    )
    password = fields.Str(
        required=True,
        load_only=True,
        validate=_strong_password,
        error_messages={"required": "Password is required."},
    )
    role = fields.Str(
        load_default="student",
        validate=validate.OneOf(["admin", "faculty", "student"]),
    )
    department = fields.Str(load_default="", validate=validate.Length(max=100))
    phone = fields.Str(load_default="", validate=validate.Length(max=20))

    @pre_load
    def strip_strings(self, data, **kwargs):
        return {k: v.strip() if isinstance(v, str) else v for k, v in data.items()}


class LoginSchema(Schema):
    email = fields.Email(required=True, error_messages={"required": "Email is required."})
    password = fields.Str(required=True, load_only=True,
                          error_messages={"required": "Password is required."})

    @pre_load
    def strip_strings(self, data, **kwargs):
        return {k: v.strip() if isinstance(v, str) else v for k, v in data.items()}


class ChangePasswordSchema(Schema):
    current_password = fields.Str(required=True, load_only=True)
    new_password = fields.Str(required=True, load_only=True, validate=_strong_password)

    @validates("new_password")
    def new_differs_from_current(self, value, **kwargs):
        # Cross-field check handled in the route
        pass


# ── User profile schema ────────────────────────────────────
class UpdateProfileSchema(Schema):
    name = fields.Str(validate=validate.Length(min=2, max=80))
    phone = fields.Str(validate=validate.Length(max=20))
    department = fields.Str(validate=validate.Length(max=100))

    @pre_load
    def strip_strings(self, data, **kwargs):
        return {k: v.strip() if isinstance(v, str) else v for k, v in data.items()}


# ── Admin schemas ──────────────────────────────────────────
class UpdateRoleSchema(Schema):
    role = fields.Str(
        required=True,
        validate=validate.OneOf(["admin", "faculty", "student"]),
    )


# ── Helper ────────────────────────────────────────────────
def validate_body(schema: Schema, data: dict) -> tuple[dict, dict]:
    """
    Validate data against a schema.
    Returns (valid_data, errors). errors is {} on success.
    """
    try:
        result = schema.load(data)
        return result, {}
    except ValidationError as exc:
        # Flatten nested error lists to a single string per field
        flat = {
            field: msgs[0] if isinstance(msgs, list) else str(msgs)
            for field, msgs in exc.messages.items()
        }
        return {}, flat
