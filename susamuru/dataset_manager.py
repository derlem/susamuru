import mwxml

def create_dataset(page_limit_per_at=None, dumpfile="./dataset/trwiki-20190401-pages-articles-multistream.xml"):   
	dump = mwxml.Dump.from_file(open(dumpfile))

	count = 0
	for page in dump:
		print(page)