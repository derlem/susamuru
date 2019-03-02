def strip_disambiguation_term(disamb_title, disambiguation):
    title = disamb_title.strip(" " + disambiguation).lower()
    if title == disamb_title:
        title = disamb_title.strip(disambiguation).lower()
    return title
