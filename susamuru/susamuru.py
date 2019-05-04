
import csv
import datetime
import json
import os
import pprint
import re
import sys

import mwparserfromhell
import nltk
import pywikibot
from networkx import (DiGraph, all_simple_paths, draw, generate_graphml,
                      relabel_nodes, similarity, spring_layout)
from networkx.readwrite.graphml import read_graphml, write_graphml
from pywikibot import pagegenerators
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from SPARQLWrapper import JSON, SPARQLWrapper

import dataset_manager
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

'''
print("You should set CODE accordingly default is 'tr' for Turkish")
print("You should set FAMILY accordingly default is 'wikipedia' for wikipedia")
print("You should set DISAMBIGUATION accordingly default is '(anlam ayrımı)'")
print()
'''

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
AT_DTCS_FILENAME = "./output/at_dtcs.csv"  
AT_VDTS_FILENAME = "./output/at_vdts.csv"
AT_VDT_ETH_FILENAME = "./output/at_vdt_eth.csv"
AT_VDT_ETG_FILENAME = "./output/at_vdt_etg.csv"
WIKIDATA_CACHE_FILENAME = "./dataset/wikidata_cache.json"



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

def get_etg(page):
    etg = DiGraph()
    if(page.isDisambig()):
        return etg
    try:
        wd_page = pywikibot.ItemPage.fromPage(page)
    except:
        return etg
    q_code = wd_page.title()
    endpoint_url = "https://query.wikidata.org/sparql"
    query_head = """#class
    SELECT ?superclass ?superclass2 ?superclassLabel ?superclass2Label
    WHERE 
    {
      wd:""" 
    query_foot = """ wdt:P31 ?class.
      ?class wdt:P279* ?superclass.
      ?superclass wdt:P279 ?superclass2.
      SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
    }"""
    q_code ="P31"
    query = query_head + q_code + query_foot
    sparql = SPARQLWrapper(endpoint_url)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    for result in results["results"]["bindings"]:
        first_node_label = result["superclassLabel"]["value"]
        second_node_label = result["superclass2Label"]["value"]
        first_node_q_code = result["superclass"]["value"].split("/")[-1]
        second_node_q_code = result["superclass2"]["value"].split("/")[-1].split("/")[-1]
        first_node = first_node_label + " : " + first_node_q_code
        second_node = second_node_label + " : " + second_node_q_code
        etg.add_edge(first_node, second_node)
    return etg

def at_vdt_etg(limit=None):
    at_vdts_map = construct_at_dt_map_from_file(AT_VDTS_FILENAME)
    with open(AT_VDT_ETG_FILENAME, mode='w') as at_vdt_eth_file:
        etg_quote_char = "'"
        writer = csv.writer(at_vdt_eth_file, delimiter=DELIMITER, quotechar=etg_quote_char, quoting=csv.QUOTE_MINIMAL)
        for ambiguation_term_title,valid_disambiguation_terms in at_vdts_map.items():            
            row_items = []
            for vdt in valid_disambiguation_terms:
                row_items.append(ambiguation_term_title)
                row_items.append(vdt.title())
                etg = get_etg(vdt)
                etg_grapml = list(generate_graphml(etg, prettyprint=False))[0]
                
                row_items.append(etg_grapml)
                writer.writerow(row_items)
                row_items = []
# at_dtcs()
# at_vdts()
#dataset_manager.generate_at_vdt_sentence_start_end_csv()
# at_vdt_eth(limit=LIMIT)
