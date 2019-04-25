import mwxml
import csv
import re
import time
import hashlib

DELIMITER = ","
QUOTE_CHAR = '"'
AT_VDTS_FILENAME = "./dataset/at_vdts.csv"

def get_vdt_map():
    at_dt_map = {}
    with open(AT_VDTS_FILENAME, newline='') as csvfile:
        reader = csv.reader(csvfile,delimiter=DELIMITER,quotechar=QUOTE_CHAR)
        for row in reader:
            # Put the pages into the map.
            pages = row[1:]
            at_dt_map[row[0]] = pages
        return at_dt_map

def print_dict(map):
	for key,value in map.items():
		print("Key: ", str(key), " Value: ", value)

def get_page_information(dumpfile):
	
	print("Getting vdt & sentences map from the dump file...")
	vdt_sentences_map = {}
	dump = mwxml.Dump.from_file(open(dumpfile))

	for page in dump:
		page_links_hashes = {}
		for revision in page:
			link_regex = r'(\[\[([a-zA-Z\u0080-\uFFFF ]+)\]\]|\[\[([a-zA-Z\u0080-\uFFFF ]+)\|([a-zA-Z\u0080-\uFFFF ]+)\]\])'
			
			if isinstance(revision.text,str):
				
				# Get the matched strings.
				matches = re.finditer(link_regex,revision.text)
				if matches:
					for m in matches:
						# Get the hash of a matched link.
						hash_of_link = hashlib.sha256(m.group(0).encode('utf-8')).hexdigest()
						
						seen_text = m.group(4)
						if seen_text == None: seen_text = m.group(2)
						
						page_name = m.group(2)
						if page_name == None: page_name = m.group(3)

						page_links_hashes[hash_of_link] = {'wiki_text': m.group(1), 'page_name': page_name ,'seen_text': seen_text}
				print_dict(page_links_hashes)
		break
	print("Finished getting all the pages from the dump. Page count: ", len(vdt_sentences_map))
	return 0


def get_links_for_page(pagemap,linkname,sentence_limit=None):
	# Get the links from the page texts and return the sentences in a list. 
	# This is the part we need to traverse all pages.
	link_regex = r'\[\[('+ re.escape(str(linkname)) + r'|'+ re.escape(str(linkname)) + r'\|[^\]\]]*)\]\]'
	for page_title,page_info in pagemap.items():
		page_text = page_info['text']
		if isinstance(page_text,str):
			m = re.search(link_regex,page_text)

		# Find the linkname in this text. Regular expression.
		if m:
			print('In page: ', page_title, " found linkname: ", m.group(0))

def create_dataset(page_limit_per_at=None, dumpfile="./dataset/trwiki-20190401-pages-articles-multistream.xml"):   
	vdt_map = get_vdt_map()
	
	map_construction_start_time = time.time()
	pagetitle_page_map = get_page_information(dumpfile)
	map_construction_end_time = time.time()

	# Get the links from the page texts and put them in a map given as key: Linked page value: [sentence]
	
	start_time = time.time()
	#get_links_for_page(pagetitle_page_map,"Galatasaray")
	end_time = time.time()

	print("Map construction takes: ", (map_construction_end_time - map_construction_start_time), " seconds.")
	print("One vdt link search takes: ", (end_time - start_time), " seconds.")
	
