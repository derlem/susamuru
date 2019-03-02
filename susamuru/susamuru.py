import pywikibot
import re
from . import utils

print("You should set CODE accordingly default is 'tr' for Turkish")
print("You should set FAMILY accordingly default is 'wikipedia' for wikipedia")
print("You should set DISAMBIGUATION accordingly default is '(anlam ayrımı)'")
print()
CODE = "tr"
FAMILY = "wikipedia"
SITE = pywikibot.Site(CODE, FAMILY)
DISAMBIGUATION = "(anlam ayrımı)"


def get_disambiguation_term_generator():
    return SITE.disambcategory().articles()


def get_disambiguation_terms(limit=None):
    generator = get_disambiguation_term_generator()
    pages = []
    for page in generator:
        pages.append(page)
        # break  # DEBUG for test purposes
        if limit is not None and len(pages) > limit: break  # DEBUG
    return pages


def get_candidates(disamb_page):
    """Candidate is a page that its title includes the disabiguation term.
    This function looks for candidates in disamb_page.linkedPages().

    Arguments:
        disamb_page {pywikibot.Page()} -- a disambiguation page

    Returns:
        list -- list of pywikikbot.Page() that are candidates
    """

    # Filter out the disambiguation string i.e (anlam ayrımı) from title.
    title = utils.strip_disambiguation_term(disamb_page.title(),
                                            DISAMBIGUATION)

    candidates = []
    # Traverse all links in the disambiguation page
    for page in disamb_page.linkedPages():
        if title in page.title().lower():
            # if link's title includes the disambiguation page's title then
            # then we include this to the candidates.
            candidates.append(page)

    return candidates


def get_disambiguation_map(limit=None):
    terms = get_disambiguation_terms(limit)
    disambiguation_map = {}
    for term in terms:
        term_title = utils.strip_disambiguation_term(term.title(),
                                                     DISAMBIGUATION)
        disambiguation_map[term_title] = get_candidates(term)
    return disambiguation_map


def extract_sentences_from_referenced_pages(page):  # incomplete
    refs = list(page.getReferences(namespaces=FAMILY))
    sentences = []
    # TODO: for now gets just title of the page. it does not work
    # TODO: it should be improved, probably with 'nltk'
    title = page.title()
    for ref in refs:
        if not ref.isDisambig():
            sentences.append(ref.title())
    return sentences


def collect(limit=None):
    disamb_map = get_disambiguation_map(limit)
    entities = []
    for disamb_term, candidates in disamb_map.items():
        for candidate in candidates:
            tag = 0  # TODO: Should its NER TAG using wikidata
            sentences = extract_sentences_from_referenced_pages(candidate)
            entity = [disamb_term, candidate.title(), sentences, tag]
            entities.append(entity)
    return entities

# from susamuru.susamuru import *
# from datetime import datetime
# begin = datetime.now()
# map = get_disambiguation_map()
# end = datetime.now()
# end - begin
# terms = get_disambiguation_terms(5)
# get_candidates(terms[0])
