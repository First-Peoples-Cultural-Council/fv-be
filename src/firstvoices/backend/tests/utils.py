import random
import string


def generate_string(length):
    """Function to generate string of ascii characters (both upper and lower case) for the given length."""
    letters = string.ascii_letters
    return "".join(random.choice(letters) for i in range(length))
