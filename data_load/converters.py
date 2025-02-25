import re
from django.urls import register_converter

class FloatUrlParameterConverter:
    regex = '[+-]?([0-9]*[.])?[0-9]+'  # Regex for matching float numbers

    def to_python(self, value):
        return float(value)  # Convert the matched string to a float

    def to_url(self, value):
        return str(value)  # Convert the float back to string for URL

# Register the converter
register_converter(FloatUrlParameterConverter, 'float')