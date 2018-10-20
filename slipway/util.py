import re


def snake_case(text):
    """
    Used for converting paths and such to a snake case format.
    """
    no_symbol = re.sub('[^A-Za-z0-9]', '_', text)
    no_duplicate = re.sub('[_]{2,}', '_', no_symbol.lower())
    return re.sub('(^_|_$)', '', no_duplicate)
