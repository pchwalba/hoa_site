from django.core.exceptions import ValidationError


def file_extension_validator(value):
    ext = value.name.split('.')[-1]
    if ext != 'xlsx':
        raise ValidationError('Niepoprawne rozszerzenie pliku')


def phone_number_validator(value):
    if 999999999 < value < 100000000:
        raise ValidationError("Niepoprawny numer telefonu")
