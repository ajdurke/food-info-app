import re
import inflect

p = inflect.engine()

DESCRIPTORS = {
    "fresh", "frozen", "dried", "chopped", "sliced", "grated", "minced",
    "shredded", "cooked", "raw", "large", "small", "extra", "extra-virgin",
    "organic", "peeled", "unsalted", "salted", "finely", "coarsely",
    "thinly", "thickly", "trimmed", "melted", "optional", "diagonal"
}

def normalize_food_name(text):
    if not text:
        return ""
    text = re.sub(r"\(.*?\)", "", text)       # remove parentheticals
    text = re.sub(r",.*", "", text)           # remove trailing notes
    words = text.lower().split()
    words = [w for w in words if w not in DESCRIPTORS]
    singular_words = [p.singular_noun(w) or w for w in words]
    return " ".join(singular_words).strip()
