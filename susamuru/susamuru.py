
import sys
import json
import os
import pprint
import re
import csv
import datetime

import mwparserfromhell
import nltk
import pywikibot

import utils


# Added to be able to read the large csv fields.
maxInt = sys.maxsize
while True:
    # decrease the maxInt value by factor 10 
    # as long as the OverflowError occurs.
    try:
        csv.field_size_limit(maxInt)
        break
    except OverflowError:
        maxInt = int(maxInt/10)


nltk.download('punkt')

LIMIT = 1
A_START_INDEX = 160

print("You should set CODE accordingly default is 'tr' for Turkish")
print("You should set FAMILY accordingly default is 'wikipedia' for wikipedia")
print("You should set DISAMBIGUATION accordingly default is '(anlam ayrımı)'")
print()
CODE = "tr"
FAMILY = "wikipedia"
SITE = pywikibot.Site(CODE, FAMILY)
DISAMBIGUATION_REFERENCE = "(anlam ayrımı)"
INSTANCE_OF_PROPERTY_CODE = "P31"
SUBCLASS_PROPERTY_CODE = "P279"

# In case it didn't work, put tab character
DELIMITER = ","
QUOTE_CHAR = '"'

# All Ambiguous Terms and their all disambiguation term candidates are found in this file
AT_DTCS_FILENAME = "./dataset/at_dtcs.csv"  
AT_VDTS_FILENAME = "./dataset/at_vdts.csv"
AT_VDT_ETH_FILENAME = "./dataset/at_vdt_eth.csv"
WIKIDATA_CACHE_FILENAME = "./dataset/wikidata_cache.json"
AT_VDT_RPTS_FILENAME = "./dataset/at_vdt_rpts.csv"

def get_salt_text(wiki_text):
    wikicode = mwparserfromhell.parse(wiki_text)
    return wikicode.strip_code()

def get_ambiguous_term_generator():
    return SITE.disambcategory().articles()

def get_ambiguous_terms(limit=None):
    print("Getting all ambiguous terms...")
    generator = get_ambiguous_term_generator()

    # Convert to list 
    generator = list(generator)
    generator = generator[A_START_INDEX:]
    pages = []
    for page in generator:
        pages.append(page)
        #break  # DEBUG for test purposes
        if limit is not None and len(pages) > limit: break  # DEBUG
    print("Finished getting all disambiguation terms.")
    return pages


def get_disamb_term_candidates(disamb_page):
    """
    Candidate is a page that its title includes the ambiguous term.
    This function looks for candidates in disamb_page.linkedPages().

    Arguments:
        disamb_page {pywikibot.Page()} -- a disambiguation page

    Returns:
        list -- list of pywikibot.Page() candidates list for a given page.
    """

    # Traverse all links in the disambiguation page
    candidates = [disamb_candidate for disamb_candidate in disamb_page.linkedPages()]
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


def collect(limit=None, directory="./dataset"):
    if not os.path.isdir(directory):
        os.mkdir(directory)

    disamb_map = get_disambiguation_map(limit)
    disamb_term_number = 0
    candidate_number = 0
    sentence_number = 0
    for disamb_term, candidates in disamb_map.items():

        disamb_term_dir_name = "".join(x for x in disamb_term if x.isalnum())
        # Create ambigous term directory
        ambiguous_term_directory = directory + "/" + disamb_term_dir_name
        if not disamb_term_dir_name:  # empty file name
            ambiguous_term_directory = directory + "/" + "illegal_ambiguous_term_name"

        i = 1  # for preventing duplicate dir names
        while os.path.isdir(ambiguous_term_directory):
            ambiguous_term_directory = ambiguous_term_directory + "_" + str(i)
            i += 1

        print(disamb_term)
        os.mkdir(ambiguous_term_directory)
        disamb_term_number += 1

        disamb_term_sentence_number = 0
        for candidate in candidates["candidates"]:
            entities = []
            class_path = extract_class_path(candidate)  # TODO: Should its NER TAG using wikidata
            page_sentences = extract_sentences_from_referenced_pages(candidate)
        

            candidate_file_name = "".join(x for x in candidate.title() if x.isalnum())
            # Create candidate file

            
            candidate_file_path = ambiguous_term_directory + "/" + candidate_file_name + ".csv"
            i = 1  # for preventing duplicate filenames
            while os.path.isfile(candidate_file_path):
                candidate_file_path = ambiguous_term_directory + "/" + candidate_file_name + "_" + str(i) + ".csv"
                i += 1

            print(candidate_file_path)
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

            with open(candidate_file_path, 'a',  newline='') as candidate_file:
                wr = csv.writer(candidate_file, quoting=csv.QUOTE_ALL, lineterminator='\n')
                wr.writerows(entities)
    
            disamb_term_sentence_number += len(useful_sentences)
            candidate_number += 1
        
        with open(ambiguous_term_directory + "/statistics.json", "a") as f:
            candidates["statistics"]["sentences_number"] = disamb_term_sentence_number
            candidates["statistics"]["ambiguous_term"] = disamb_term

            json.dump(candidates["statistics"], f)
            sentence_number += disamb_term_sentence_number

    with open(directory + "/statistics.json", "a") as f:
        stat_dict = {"disamb_term_number": disamb_term_number,
                    "candidate_number": candidate_number,
                    "sentence_number": sentence_number}
        json.dump(stat_dict, f)


def extract_class_path(page, cache):
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
            entity_type = curr_page.text["labels"]["en"]
            class_path.append(entity_type)
            # Check Cache
            if entity_type in cache:
                rest = cache[entity_type]
                class_path.extend(rest)
                return class_path
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
            entity_type = curr_page.text["labels"]["en"]
            class_path.append(entity_type)
            # Check Cache
            if entity_type in cache:
                rest = cache[entity_type]
                class_path.extend(rest)
                return class_path
    return class_path

# =========================================================================== 
'''
    Methods that we used to collect the data step by step.
    
    1st Step: at_dtcs 
    --------------
    Get all the ambiguous terms from disambiguation page
    Get all the links in those pages. Put them in rows in the following format:
    ambiguation_term,link1,link2,link3
    Beşiktaş,Beşiktaş Semti,Beşiktaş Futbol Takımı etc.
    Write all to a file.
    ---------------

    2nd Step: at_vdts
    ---------------
    Filters the candidates. Candidates that includes the ambiguous 
    term is accepted as a valid disambiguation term. Others are discarded.
    Uses the csv file that is created with the 1st method's.

    3rd Step: at_vdt_eth
    ---------------
    Gets the entity type hierarchy (list) of the given 
    (ambiguous term, valid disambiguation term) pair. Uses the information 
    that is in at_vdts.csv file.

    4th Step: at_vdt_rpts
    ---------------
    Gets the all (ambiguous term, valid disambiguation term) pairs from 
    at_vdts.csv file.
    Query every vdt page to find the pages that they are referenced from.
    Get all the texts in wikidata syntax from those pages. Put them in a list
    construct the following data type 
    (at,vdt,[rpt_1,rpt_2,rpt_3, ...])
    rpt = (vdt) referencing page text.
    
    5th Step: at_vdt_ss
    ---------------
    Get the sentences in raw format that include the vdt.
    Hash the wiki syntaxed text links, change the links to hashed versions. 
    Seperate the sentences with nltk, change the hashed value to original value. 
    Construct the tuple. s being the sentence.
    (at,vdt,s)

'''
def at_dtcs(limit=None):
    # Get every ambiguation term.
    print("\nStarting 1st Step...")
    ambiguous_terms = get_ambiguous_terms(limit)

    with open(AT_DTCS_FILENAME, mode='w') as at_dtcs_file:
        writer = csv.writer(at_dtcs_file, delimiter=DELIMITER,quotechar=QUOTE_CHAR, quoting=csv.QUOTE_MINIMAL)
        
        for ambiguation_term in ambiguous_terms:
            candidates = [disamb_candidate for disamb_candidate in ambiguation_term.linkedPages()]
            disamb_candidate_titles = [candidate.title() for candidate in candidates]
            
            # Strip "anlam ayrımı" from ambiguation page title.
            ambiguation_term_title = utils.strip_disambiguation_reference(ambiguation_term.title(), DISAMBIGUATION_REFERENCE)

            # Items that are going to be printed.
            row_items = []
            row_items = disamb_candidate_titles
            row_items.insert(0,ambiguation_term_title)
            writer.writerow(row_items)
    print("1st Step is complete [ at_dcts.csv is ready ]\n")

# This method constructs the at_dtcs map from the at_dtcs.csv file.
def construct_at_dt_map_from_file(filename):
    at_dt_map = {}
    with open(filename, newline='') as csvfile:
        reader = csv.reader(csvfile,delimiter=DELIMITER,quotechar=QUOTE_CHAR)
        for row in reader:
            
            # Put the pages into the map.
            pages = [pywikibot.Page(SITE,page_name) for page_name in row[1:]]
            at_dt_map[row[0]] = pages
        return at_dt_map

def get_valid_candidates(ambiguation_term_title,candidates):
    valid_candidates = []
    for c in candidates:
        if ambiguation_term_title in c.title().lower():
            valid_candidates.append(c)
    return valid_candidates

def at_vdts(limit=None):
    print("\nStarting 2nd Step...")
    at_dtcs_map = construct_at_dt_map_from_file(AT_DTCS_FILENAME)

    with open(AT_VDTS_FILENAME, mode='w') as at_vdts_file:
        writer = csv.writer(at_vdts_file, delimiter=DELIMITER,quotechar=QUOTE_CHAR, quoting=csv.QUOTE_MINIMAL)

        for ambiguation_term,candidates in at_dtcs_map.items():
            ambiguation_term_title = utils.strip_disambiguation_reference(ambiguation_term.title(), DISAMBIGUATION_REFERENCE)
            valid_candidates = get_valid_candidates(ambiguation_term_title,candidates)
            valid_candidate_titles = [vc.title() for vc in valid_candidates]

            # Items that are going to be printed.
            row_items = []
            row_items = valid_candidate_titles
            row_items.insert(0, ambiguation_term_title)
            writer.writerow(row_items)
    print("2nd Step is complete. [ at_vdts.csv is ready ].\n")

# This method gets the entity type hierarchy for each (at,vdt) pair.
# (AT,VDT,[ET1,ET2,ET3,ET4..])
# This works but takes a long time, querying wikidata takes a lot of time.
# We can maybe first flatten all the disambiguate terms and then query wikidata 
# and save it to a file for future usage.
def at_vdt_eth(limit=None):
    at_vdts_map = construct_at_dt_map_from_file(AT_VDTS_FILENAME)
    if not os.path.isfile(WIKIDATA_CACHE_FILENAME):
        wikidata_cache_file = open(WIKIDATA_CACHE_FILENAME, 'w+')
        wikidata_cache_dict = {}
        wikidata_cache_file.close()
    else:
        wikidata_cache_file = open(WIKIDATA_CACHE_FILENAME, 'r')
        wikidata_cache_dict = json.load(wikidata_cache_file)
        wikidata_cache_file.close()
    with open(AT_VDT_ETH_FILENAME, mode='w') as at_vdt_eth_file:
        writer = csv.writer(at_vdt_eth_file, delimiter=DELIMITER,quotechar=QUOTE_CHAR, quoting=csv.QUOTE_MINIMAL)
        for ambiguation_term_title,valid_disambiguation_terms in at_vdts_map.items():            
            row_items = []
            for vdt in valid_disambiguation_terms:
                row_items.append(ambiguation_term_title)
                row_items.append(vdt.title())
                eth = extract_class_path(vdt, cache=wikidata_cache_dict)
                # TODO: Some of the vdt's doesn't have a page in wikidata.
                if eth is not None:
                    # Write Cache
                    for i in range(len(eth)):
                        if eth[i] not in wikidata_cache_dict:
                            wikidata_cache_dict[eth[i]] = eth[i+1:]
                    for et in eth:
                        row_items.append(et)
                    writer.writerow(row_items)
                row_items = []
    
    wikidata_cache_file = open(WIKIDATA_CACHE_FILENAME, 'w+')
    json.dump(wikidata_cache_dict, wikidata_cache_file)
    wikidata_cache_file.close()

def get_referring_pages_and_texts(page):
    refs = list(page.getReferences())
    print("There are [ " + str(len(refs)) + " ] referring pages.")
    print("Getting pages and texts...")
    page_name_text_tuples = []
    for ref in refs:
        if not ref.isDisambig():
            page_text = ref.text
            page_text_tuple = (ref.title(),page_text)
            page_name_text_tuples.append(page_text_tuple)
    return page_name_text_tuples

def generate_filename(key,pagename):
    # Append the key to first name.
    pagename = pagename.replace('/','&')
    #at = str(key[0]).replace('/','&')
    #vdt = str(key[1]).replace('/','&')

    #filename = at + "_" + vdt + "_" + pagename
    filename = pagename

    # Add the time.
    now = datetime.datetime.now()
    filename += "_" + str(now) + ".md"
    filename = filename.replace(' ','_')
    return filename

def generate_foldername(at_title,vdt_title):
    foldername = "./dataset/pages/" + at_title + "_" + vdt_title
    return foldername.replace(' ','_')

def at_vdt_rpts(limit=None):
    print("\nStarting 3rd Step...")
    at_vdts_map = construct_at_dt_map_from_file(AT_VDTS_FILENAME)

    with open(AT_VDT_RPTS_FILENAME, mode='w') as at_vdt_rpts_file:
        writer = csv.writer(at_vdt_rpts_file, delimiter=DELIMITER,quotechar=QUOTE_CHAR, quoting=csv.QUOTE_MINIMAL)

        for at_title,vdts in at_vdts_map.items():
            row_items = []    
            for vdt in vdts:
                vdt_title = vdt.title()

                row_items.append(at_title)
                row_items.append(vdt_title)
                
                print("\nProcessing referencing pages for AT: [ " + at_title +" ] and VDT: [ "+ vdt_title + " ]")
                rpts = get_referring_pages_and_texts(vdt)
                print("All references are fetched.")
                print("Starting to write the fetched texts to files...")
                
                for rpt in rpts:
                    # rpt[0]:referring page title 
                    # rpt[1]:referring page text 
                    foldername = generate_foldername(at_title,vdt_title)
                    filename = generate_filename((at_title,vdt_title), rpt[0])
                    filepath = foldername + "/" + filename
                    row_items.append(filepath)

                    if not os.path.exists(foldername):
                        os.mkdir(foldername)                    
                    
                    f = open(filepath,"w+")

                    # Write the text into the file.
                    f.write(rpt[1])
                    f.close()
                writer.writerow(row_items)
                row_items = []
                print("Writing operation completed.")
    print("3rd Step is complete. [ at_vdt_rpts.csv is ready ].\n")            
def construct_at_vdt_rpts_map_from_file(filename):
    at_vdt_rpts_map = {}
    with open(filename, newline='') as csvfile:
        reader = csv.reader(csvfile,delimiter=DELIMITER,quotechar=QUOTE_CHAR)
        for row in reader:
            key = (row[0],row[1])
            texts = [text for text in row[2:]]
            at_vdt_rpts_map[key] = texts
        return at_vdt_rpts_map

def at_vdt_ss(limit=None):
    at_vdt_rpts_map = construct_at_vdt_rpts_map_from_file(AT_VDT_RPTS_FILENAME)
    for key,value in at_vdt_rpts_map.items():
        print(key, len(value))

# at_dtcs()
# at_vdts()
# at_vdt_eth(limit=LIMIT)
# at_vdt_rpts()
# at_vdt_ss()