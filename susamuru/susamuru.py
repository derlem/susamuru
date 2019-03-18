import pywikibot
import re
import utils 


import nltk
nltk.download('punkt')

print("You should set CODE accordingly default is 'tr' for Turkish")
print("You should set FAMILY accordingly default is 'wikipedia' for wikipedia")
print("You should set DISAMBIGUATION accordingly default is '(anlam ayrımı)'")
print()
CODE = "tr"
FAMILY = "wikipedia"
SITE = pywikibot.Site(CODE, FAMILY)
DISAMBIGUATION = "(anlam ayrımı)"
INSTANCE_OF_PROPERTY_CODE = "P31"
SUBCLASS_PROPERTY_CODE = "P279"


'''
Templates and Config for mediawiki-parser 
'''
templates = {}

from mediawiki_parser.preprocessor import make_parser
preprocessor = make_parser(templates)

from mediawiki_parser.text import make_parser
parser = make_parser()

def parse_wiki_text(wiki_text):
    preprocessed_text = preprocessor.parse(wiki_text)
    print("Type of preprocessed text: ", type(preprocessed_text))
    
    output = parser.parse(preprocessed_text.leaves())
    print("Type of output: ", type(output))
    return output

def get_ambiguous_term_generator():
    return SITE.disambcategory().articles()


def get_ambiguous_terms(limit=None):
    generator = get_ambiguous_term_generator()
    pages = []
    for page in generator:
        pages.append(page)
        #break  # DEBUG for test purposes
        if limit is not None and len(pages) > limit: break  # DEBUG
    return pages


def get_candidates(disamb_page):
    """Candidate is a page that its title includes the ambiguous term.
    This function looks for candidates in disamb_page.linkedPages().

    Arguments:
        disamb_page {pywikibot.Page()} -- a disambiguation page

    Returns:
        list -- list of pywikikbot.Page() that are candidates
    """

    # Filter out the disambiguation string i.e (anlam ayrımı) from title.
    title = utils.strip_ambiguous_term(disamb_page.title(),
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
    terms = get_ambiguous_terms(limit)
    disambiguation_map = {}
    for term in terms:
        term_title = utils.strip_ambiguous_term(term.title(),
                                                     DISAMBIGUATION)
        disambiguation_map[term_title] = get_candidates(term)
    return disambiguation_map


def extract_sentences_from_referenced_pages(page):  # incomplete
    refs = list(page.getReferences(namespaces=FAMILY))
    # TODO: for now gets just title of the page. it does not work
    # TODO: it should be improved, probably with 'nltk'
    sentences = []
    for ref in refs:
        if not ref.isDisambig():
            page_text = ref.text
            parsed_page_text = parse_wiki_text(page_text)

            page_sentences = nltk.sent_tokenize(parsed_page_text)
            #print("Page sentences: ", page_sentences)
            sentences.append(page_sentences)
    return sentences


def collect(limit=None):
    disamb_map = get_disambiguation_map(limit)
    entities = []
    #print("Map", disamb_map)
    for disamb_term, candidates in disamb_map.items():
        for candidate in candidates:
            class_path = extract_class_path(candidate)  # TODO: Should its NER TAG using wikidata
            sentences = extract_sentences_from_referenced_pages(candidate)
            entity = [disamb_term, candidate.title(), sentences, class_path]
            entities.append(entity)
    return entities

def extract_class_path(page):
    try:
        wd_page = pywikibot.ItemPage.fromPage(page)
    except pywikibot.exceptions.NoPage:
        # This means wikidata page does not exists for this wikipedia page
        return None
    curr_page = wd_page
    claims = curr_page.text["claims"]
    class_path = []
    # Find instance of if exists else just continue with subclasses
    if INSTANCE_OF_PROPERTY_CODE in claims:
        claim = claims[INSTANCE_OF_PROPERTY_CODE][0]
        curr_page = claim.target
        class_path.append(curr_page.text["labels"]["en"])
        claims = curr_page.text["claims"]
    while SUBCLASS_PROPERTY_CODE in claims:
        claim = claims[SUBCLASS_PROPERTY_CODE][0]
        curr_page = claim.target
        claims = curr_page.text["claims"]
        class_path.append(curr_page.text["labels"]["en"])
    return class_path

collect(limit=2)
# from susamuru.susamuru import *
# from datetime import datetime
# begin = datetime.now()
# map = get_disambiguation_map()
# end = datetime.now()
# end - begin
# terms = get_ambiguous_terms(5)
# get_candidates(terms[0])
