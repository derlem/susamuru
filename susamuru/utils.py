def strip_disambiguation_reference(disamb_title, disambiguation_reference):
    return disamb_title.replace(disambiguation_reference,'').lower().strip()
