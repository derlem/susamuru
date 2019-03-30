def strip_disambiguation_reference(disamb_title, disambiguation_reference):
    title = disamb_title.strip(" " + disambiguation_reference).lower()
    if title == disamb_title:
        title = disamb_title.strip(disambiguation_reference).lower()
    return title
