from flask_marshmallow import Marshmallow
from marshmallow import fields, validates_schema, ValidationError, validate, EXCLUDE

# Global Marshmallow instance, initialized with the Flask app in app.py
ma = Marshmallow()


class ProjectCreateSchema(ma.Schema):
    """Schema for validating project creation payloads (organization publish form)."""
    title = fields.Str(required=True, validate=validate.Length(min=3, max=200))
    description = fields.Str(required=True, validate=validate.Length(min=1))
    category = fields.Str(required=False, allow_none=True)
    date = fields.Date(required=True, format="%Y-%m-%d")
    location = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    max_participants = fields.Int(required=False, load_default=10, validate=validate.Range(min=1))
    min_participants = fields.Int(required=False, load_default=1, validate=validate.Range(min=1))
    duration = fields.Float(required=False, load_default=0.0, validate=validate.Range(min=0.0, min_inclusive=False))
    points = fields.Int(required=False, load_default=0, validate=validate.Range(min=0))
    requirements = fields.Str(required=False, allow_none=True)

    @validates_schema
    def validate_participant_range(self, data, **kwargs):
        """
        Cross-field validation:
        Ensure min_participants is not greater than max_participants.
        Uses default values (10 / 1) when fields are omitted from the payload.
        """
        max_p = data.get('max_participants', 10)
        min_p = data.get('min_participants', 1)
        if min_p is not None and max_p is not None and min_p > max_p:
            raise ValidationError(
                {'min_participants': ['Minimum participants cannot be greater than maximum participants.']}
            )


class ProjectUpdateSchema(ma.Schema):
    """Schema for validating partial project updates (PATCH endpoint)."""
    title = fields.Str(required=False, validate=validate.Length(min=3, max=200))
    description = fields.Str(required=False, validate=validate.Length(min=1))
    category = fields.Str(required=False, allow_none=True)
    date = fields.Date(required=False, format="%Y-%m-%d")
    location = fields.Str(required=False, validate=validate.Length(min=1, max=200))
    max_participants = fields.Int(required=False, validate=validate.Range(min=1))
    min_participants = fields.Int(required=False, validate=validate.Range(min=1))
    duration = fields.Float(required=False, validate=validate.Range(min=0.0, min_inclusive=False))
    points = fields.Int(required=False, validate=validate.Range(min=0))
    requirements = fields.Str(required=False, allow_none=True)

    @validates_schema
    def validate_participant_range(self, data, **kwargs):
        """
        Cross-field validation for PATCH:
        Only enforce the participant range rule when both fields are provided
        in the same request body.
        """
        if 'min_participants' in data and 'max_participants' in data:
            if data['min_participants'] > data['max_participants']:
                raise ValidationError(
                    {'min_participants': ['Minimum participants cannot be greater than maximum participants.']}
                )



