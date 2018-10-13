import re


def snake_case(text):
    return re.sub('\W', '_', text.lower())
