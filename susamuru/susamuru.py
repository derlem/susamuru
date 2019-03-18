import pywikibot
import re
import utils 
import mwparserfromhell
import pprint

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

def get_salt_text(wiki_text):
    wikicode = mwparserfromhell.parse(wiki_text)
    return wikicode.strip_code()

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
    sentences = []
    for ref in refs:
        if not ref.isDisambig():
            page_text = ref.text
            page_sentences = nltk.sent_tokenize(page_text)
            
            sentences.append(page_sentences)
    
    flat_sentences_list = [item for sublist in sentences for item in sublist]
    return flat_sentences_list


def collect(limit=None):
    disamb_map = get_disambiguation_map(limit)
    entities = []
    for disamb_term, candidates in disamb_map.items():
        for candidate in candidates:
            class_path = extract_class_path(candidate)  # TODO: Should its NER TAG using wikidata
            page_sentences = extract_sentences_from_referenced_pages(candidate)
            
            # Here get the important sentences and create the entity
            # Use the candidate title to get the sentence
            # search_item = "Beşiktaş (kadın basketbol takımı)"
            search_item = candidate.title()
            useful_sentences = []

            for sentence in page_sentences:
                wikicode = mwparserfromhell.parse(sentence)
                links_in_sentence = wikicode.filter_wikilinks()
                for link in links_in_sentence:
                    if search_item in link:
                        # print("Found one sentence for candidate: ", candidate.title(), " Sentence: ", wikicode.strip_code())
                        useful_sentences.append(wikicode.strip_code())

            for useful_sentence in useful_sentences:
                entity = [disamb_term, candidate.title(), useful_sentence, class_path]
                entities.append(entity)

    print("**********************************")
    pprint.pprint(entities)
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

collect(limit=5)
# from susamuru.susamuru import *
# from datetime import datetime
# begin = datetime.now()
# map = get_disambiguation_map()
# end = datetime.now()
# end - begin
# terms = get_ambiguous_terms(5)
# get_candidates(terms[0])
