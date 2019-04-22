import mwxml
import csv


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

def get_map(dumpfile):
	res = {}
	dump = mwxml.Dump.from_file(open(dumpfile))

	for page in dump:
		for revision in page:
			res[page.title] = revision.text
			break
	return res

def get_page_text(dumpfile, page_title):
	dump = mwxml.Dump.from_file(open(dumpfile))

	for page in dump:
		if page.title == page_title:
			print(page)

def create_dataset(page_limit_per_at=None, dumpfile="./dataset/trwiki-20190401-pages-articles-multistream.xml"):   
	vdt_map = get_vdt_map()
	
	pages_map = get_map(dumpfile)
	for at,vdts in vdt_map.items():
		for vdt in vdts:
			print("Page: ", vdt)
			if vdt in pages_map:
				print(pages_map[vdt])