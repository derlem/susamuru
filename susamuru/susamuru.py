import json
import os
import pprint
import re

import mwparserfromhell
import nltk
import pywikibot

import utils

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
        dict -- list of pywikikbot.Page() that are candidates and statistics.
    """

    # Filter out the disambiguation string i.e (anlam ayrımı) from title.
    title = utils.strip_ambiguous_term(disamb_page.title(),
                                            DISAMBIGUATION)

    candidates = []
    # Traverse all links in the disambiguation page
    all_pages_number = 0
    candidate_pages_number = 0
    for page in disamb_page.linkedPages():
        all_pages_number += 1
        if title in page.title().lower():
            # if link's title includes the disambiguation page's title then
            # then we include this to the candidates.
            candidate_pages_number += 1
            candidates.append(page)
    returned_dict = {"candidates": candidates,
                     "statistics": {"all_pages": all_pages_number,
                                    "candidate_pages": candidate_pages_number}}
    return returned_dict


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


def collect(limit=None, directory="./dataset"):
    if not os.path.isdir(directory):
        os.mkdir(directory)

    disamb_map = get_disambiguation_map(limit)
    disamb_term_number = 0
    candidate_number = 0
    sentence_number = 0
    for disamb_term, candidates in disamb_map.items():

        # Create letter directory
        first_letter = disamb_term[0]
        letter_directory = directory + "/'" + first_letter + "'"
        if not os.path.isdir(letter_directory):
            print(first_letter)
            os.mkdir(letter_directory) 

        # Create ambigous term directory
        ambiguous_term_directory = letter_directory + "/'" + disamb_term + "'"
        if not os.path.isdir(ambiguous_term_directory):
            print(disamb_term)
            os.mkdir(ambiguous_term_directory)
            disamb_term_number += 1

        disamb_term_sentence_number = 0
        for candidate in candidates["candidates"]:
            entities = []
            class_path = extract_class_path(candidate)  # TODO: Should its NER TAG using wikidata
            page_sentences = extract_sentences_from_referenced_pages(candidate)
        
            # Create candidate file
            candidate_file_name = ambiguous_term_directory + "/'" + candidate.title() + "'.json"
            candidate_file = open(candidate_file_name, "w")


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

            disamb_term_sentence_number += len(useful_sentences)
            json.dump(entities, candidate_file) 
            candidate_file.flush()
            candidate_file.close()
            candidate_number += 1
        
        with open(ambiguous_term_directory + "/statistics.json", "w") as f:
            candidates["statistics"]["sentences_number"] = disamb_term_sentence_number
            json.dump(candidates["statistics"], f)
            sentence_number += disamb_term_sentence_number

    with open(directory + "/statistics.json", "w") as f:
        stat_dict = {"disamb_term_number": disamb_term_number,
                    "candidate_number": candidate_number,
                    "sentence_number": sentence_number}
        json.dump(stat_dict, f)


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
        if "labels" in curr_page.text and "en" in curr_page.text["labels"]:
            class_path.append(curr_page.text["labels"]["en"])
        if "claims" in curr_page.text:
            claims = curr_page.text["claims"]
        else:
            return class_path
    while SUBCLASS_PROPERTY_CODE in claims:
        claim = claims[SUBCLASS_PROPERTY_CODE][0]
        curr_page = claim.target
        if "claims" in curr_page.text:
            claims = curr_page.text["claims"]
        else:
            break
        if "labels" in curr_page.text and "en" in curr_page.text["labels"]:
            class_path.append(curr_page.text["labels"]["en"])
    return class_path

# from susamuru.susamuru import *
# from datetime import datetime
# begin = datetime.now()
# map = get_disambiguation_map()
# end = datetime.now()
# end - begin
# terms = get_ambiguous_terms(5)
# get_candidates(terms[0])
