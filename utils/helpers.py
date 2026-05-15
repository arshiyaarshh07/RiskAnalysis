import re

def clean_text(text):

    text = re.sub(r'\s+', ' ', text)

    text = re.sub(r'[^\x00-\x7F]+', ' ', text)

    return text.strip()


def segment_sections(text):

    sections = text.split(".")

    return [s.strip() for s in sections if len(s.strip()) > 20]