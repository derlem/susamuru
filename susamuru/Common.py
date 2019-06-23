# This file contains the shared variables/constants. 

# ======== WIKIBOT CONFIGS ========
LANGUAGE = "tr" # Global language config
FAMILY = "wikipedia" # Don't change it unless necessary 

# FOLDERS
OUTPUT_FOLDER = "./output"
DUMP_FOLDER = "./dumps"
CSV_SUFFIX = ".csv"

# FILES
AT_VDT_SENTENCE_FILENAME = "at_vdt_sentence"
AT_DTCS_FILENAME = "at_dtcs"
AT_VDTS_FILENAME = "at_vdts"
AT_VDT_ETH_FILENAME = "at_vdt_eth"
AT_VDT_ETG_FILENAME = "at_vdt_etg"
AT_VDT_TAG_FILENAME = "at_vdt_tag"
WIKIDATA_CACHE_FILENAME = "wikidata_cache.json"

# ==== ENTITY TYPE GRAPH CONFIGS ====
TAG_LIST = ['person : Q215627', 'organization : Q43229', 'location : Q17334923']


# CSV WRITER
DELIMITER = ","
QUOTE_CHAR = '"'
ETG_QUOTE_CHAR = "'"

# ========== CONFIG ==========
A_START_INDEX = 160
DEBUG = False
LIMIT = 100
DISAMBIGUATION_REFERENCE = "(anlam ayrımı)"
VERBOSE = True
DUMPFILE = "./dumps/trwiki-20190401-pages-articles-multistream.xml"
BLACKLIST = ["{{","}}","\n","style=\"","YÖNLENDİR","[[Dosya:"]
TOTAL_PAGE_COUNT = 909107

# Final Data
final_filename = "output"
finalfile_delimiter = "\t"
finalfile_quote_char = "\""

# CoNNL
CoNNL_B = "B-"
CoNNL_I = "I-"
CoNNL_O = "O"
seperator_row = [" "," "," "," "," "," "," "," "," "," "]

unknown_tags =["UNK1","UNK2"]

# Sentences
total_sentence_count = 366321

# Flags
write_no_tag_sentences = False