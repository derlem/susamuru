# -*- coding: utf-8 -*-
#
from nltk.tokenize import sent_tokenize
import mwparserfromhell

from datetime import datetime
import mwxml
import csv
import re
import time
import hashlib
import gc

import os
import logging
from mem_top import mem_top

DELIMITER = ","
QUOTE_CHAR = '"'
AT_VDTS_FILENAME = "./dumps/at_vdts.csv"
IGNORED_SENTENCES_FILE = "./output/ignored_sentences/ignored_sentences_"
AT_VDT_SENTENCE_START_END_FILENAME = "./output/at_vdt_sentence_start_end_"
DISAMBIGUATION_REFERENCE = "(anlam ayrımı)"

BLACKLIST = ["{{", "}}", "\n", "style=\"", "YÖNLENDİR", "[[Dosya:"]

# This is just for debug.
TOTAL_PAGE_COUNT = 909107
TIME_SUFFIX = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')


def print_dict(map):
    for key, value in map.items():
        print("Key: ", str(key), " Value: ", value)
        print('-' * 50)


def print_list(l):
    for item in l:
        print(item)
        print("-" * 50)


def get_vdt_map():
    print("Starting to construct AT -> [VDT,VDT,VDT] map.")
    at_vdt_map = {}

    with open(AT_VDTS_FILENAME, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=DELIMITER, quotechar=QUOTE_CHAR)
        for row in reader:
            pages = row[1:]
            at_vdt_map[row[0]] = pages
        print("Finished constructing AT -> [VDT,VDT,VDT] map.")
        return at_vdt_map


# Not finished
def remove_references(wiki_syntaxed_text):
    link_regex = r'(^<ref>.*</ref>$)'
    matches = re.finditer(link_regex, wiki_syntaxed_text)
    if matches:
        for m in matches:
            pass


def prepare_text(wiki_text):
    wikicode = mwparserfromhell.parse(wiki_text)
    templates = wikicode.filter_templates()
    tags = wikicode.filter_tags()
    external_links = wikicode.filter_external_links()
    comments = wikicode.filter_arguments()
    headings = wikicode.filter_headings()

    final_wiki_text = wiki_text
    for template in templates:
        final_wiki_text.replace(str(template), '')

    for tag in tags:
        if '<ref' in str(tag) or '</ref>' in str(tag) or '<br' in str(tag):
            final_wiki_text.replace(str(tag), '')

    for heading in headings:
        final_wiki_text.replace(str(heading), '')

    for comment in comments:
        final_wiki_text.replace(str(comment), '')

    for link in external_links:
        final_wiki_text.replace(str(link), '')

    return final_wiki_text


def get_salt_text(wiki_text):
    wikicode = mwparserfromhell.parse(wiki_text)
    return wikicode.strip_code()


def replace_hash_values_with_seen_text(sentence, hashmap):
    normal_sentence = sentence
    for hash_value, text_map in hashmap.items():
        if hash_value in normal_sentence:
            normal_sentence = normal_sentence.replace(hash_value, text_map['seen_text'])
    return normal_sentence


def is_valid_sentence(sentence):
    for item in BLACKLIST:
        if item in sentence:
            return False
    return True


# p1=open('write_one_row_memory_profiler.log','w+')
# @profile(stream=fp1)
def get_all_pagename_sentences(dumpfile, vdt_map):
    print("Getting vdt & sentences map from the dump file...")
    dump = mwxml.Dump.from_file(open(dumpfile))
    total_sentence_count = 0
    page_count = 0
    ignored_sentence_count = 0
    valid_sentence_count = 0
    iteration = 0
    link_regex = r'(\[\[([a-zA-Z\u0080-\uFFFF ()]+)\]\]|\[\[([a-zA-Z\u0080-\uFFFF ()]+)\|([a-zA-Z\u0080-\uFFFF ]+)\]\])'

    for page in dump:

        # Ignore disambiguation pages.
        if DISAMBIGUATION_REFERENCE in page.title:
            continue

        percentage = (page_count * 100.0) / TOTAL_PAGE_COUNT
        page_links_hashes = {}
        page_count += 1
        if iteration > 10000:
            print(iteration)
            print("==================== Before Garbage Collection ====================")
            print(mem_top())

            gc.collect()
            print("==================== After Garbage Collection ====================")
            print(mem_top())

            iteration = 0

        for revision in page:

            iteration += 1
            # print(iteration)

            if isinstance(revision.text, str):
                # Get the matched strings.
                wiki_syntaxed_text = prepare_text(revision.text)
                matches = re.finditer(link_regex, wiki_syntaxed_text)
                if matches:
                    for m in matches:
                        # Get the hash of a matched link.
                        hash_of_link = hashlib.sha256(m.group(1).encode('utf-8')).hexdigest()

                        seen_text = m.group(4)
                        if seen_text is None:
                            seen_text = m.group(2)

                        page_name = m.group(2)
                        if page_name is None:
                            page_name = m.group(3)

                        page_links_hashes[hash_of_link] = {'wiki_text': m.group(1), 'page_name': page_name,
                                                           'seen_text': seen_text}
                # print_dict(page_links_hashes)

                # Change the wiki_text in the text with the hash
                hash_replaced_text = wiki_syntaxed_text
                for hash_value, text_map in page_links_hashes.items():
                    hash_replaced_text = hash_replaced_text.replace(text_map['wiki_text'], hash_value)

                # Get rid of tables and other wiki syntax objects.
                # hash_replaced_text = get_salt_text(hash_replaced_text)

                # Separate sentences with nltk
                sentences_with_hash = sent_tokenize(hash_replaced_text)

                # Find the sentences with the hashes and replace the hash with the seen_text. Save starting and
                # ending positions.

                for hash_value_, text_map_ in page_links_hashes.items():
                    for sentence in sentences_with_hash:
                        if hash_value_ in sentence:
                            # Check for unwanted text parts.

                            normal_sentence = replace_hash_values_with_seen_text(sentence, page_links_hashes)
                            normal_sentence = get_salt_text(normal_sentence)
                            if not is_valid_sentence(sentence):
                                continue

                            total_sentence_count += 1
                            try:
                                vdt_start_index = normal_sentence.index(text_map_['seen_text'])
                                vdt_end_index = vdt_start_index + len(text_map_['seen_text'])

                                # Increase total sentence count.
                                valid_sentence_count += 1
                                write_one_row(percentage, vdt_map, text_map_['page_name'], normal_sentence,
                                              vdt_start_index, vdt_end_index)
                            except Exception as e:
                                print(e)
                        # write_ignored_sentence(page.title,normal_sentence)
        #print("% [", percentage, "] of pages processed. From page: [", page.title, "] Found: [", len(page_links_hashes),"] pagelinks.")

    print("Finished getting all sentences. (@_@)")
    print("Total Sentence Count: ", total_sentence_count)
    print("Ignored Sentence Count: ", ignored_sentence_count)
    print("Valid Sentence Count: ", valid_sentence_count)
    print("Valid/Total Ratio: ", (valid_sentence_count * 100.0) / total_sentence_count)


def find_at(vdt_map, vdt):
    for at, vdts in vdt_map.items():
        if vdt in vdts:
            return at
    return None


def write_ignored_sentence(title, sentence):
    with open(IGNORED_SENTENCES_FILE + str(TIME_SUFFIX) + ".txt", mode='a') as ignored_file:
        ignored_file.write(title)
        ignored_file.write(sentence)
        ignored_file.write("\n")
        ignored_file.write("#" * 50)
        ignored_file.write("\n")


def write_one_row(percentage, vdt_map, vdt, sentence, start, end):
    # Determine the filename to write the data.
    # Distribute pages equally to 3 pieces
    filename = AT_VDT_SENTENCE_START_END_FILENAME + str(TIME_SUFFIX) + "_PART_1.csv"
    if percentage > 66.6:
        filename = AT_VDT_SENTENCE_START_END_FILENAME + str(TIME_SUFFIX) + "_PART_3.csv"
    elif percentage > 33.3:
        filename = AT_VDT_SENTENCE_START_END_FILENAME + str(TIME_SUFFIX) + "_PART_2.csv"

    with open(filename, mode='a') as final_csv:
        writer = csv.writer(final_csv, delimiter=DELIMITER, quotechar=QUOTE_CHAR, quoting=csv.QUOTE_MINIMAL)
        at = find_at(vdt_map, vdt)
        if at is not None:
            row_items = list()
            row_items.append(at)
            row_items.append(vdt)
            row_items.append(sentence)
            row_items.append(start)
            row_items.append(end)
            writer.writerow(row_items)


def generate_at_vdt_sentence_start_end_csv(dumpfile="./dumps/trwiki-20190401-pages-articles-multistream.xml"):
    vdt_map = get_vdt_map()

    start_time = time.time()
    print(TIME_SUFFIX)
    get_all_pagename_sentences(dumpfile, vdt_map)
    end_time = time.time()

    print("Total execution took [", (end_time - start_time), "] seconds.")
