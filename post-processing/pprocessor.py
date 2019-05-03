import sys, getopt
import csv

DELIMITER = ","
QUOTE_CHAR = "\""

BLACKLIST = ["REDIRECT","</ref>",""]

if __name__ == '__main__':
	main(sys.argv[1:])

def is_useful_sentence(sentence):
	for item in BLACKLIST:
		if item in sentence:
			return False
	return True

def write_to_outputfile(items):
	with open(outputfile, mode='w') as f:
		writer = csv.writer(f, delimiter=DELIMITER,quotechar=QUOTE_CHAR, quoting=csv.QUOTE_MINIMAL)
		writer.writerow(items)

def main(argv):
	inputfile = ''
	outputfile = ''
	
	try:
		opts, args = getopt.getopt(argv,"hi:o:",["ifile=","ofile="])
	except getopt.GetoptError:
		print 'pprocessor.py -i <inputfile> -o <outputfile>'
		sys.exit(2)
	for opt, arg in opts:
		if opt == '-h':
			print 'pprocessor.py -i <inputfile> -o <outputfile>'
			sys.exit()
		elif opt in ("-i", "--ifile"):
			inputfile = arg
		elif opt in ("-o", "--ofile"):
			outputfile = arg
		else:
			outputfile = inputfile.replace('.csv','') + "_processed.csv"

	print('Input file is "', inputfile)
	print('Output file is "', outputfile)
	print("Starting to process the file...")

    with open(inputfile, newline='') as csvfile:
        reader = csv.reader(csvfile,delimiter=DELIMITER,quotechar=QUOTE_CHAR)
        for row in reader:
            is_useful = is_useful_sentence(row[2])
            if is_useful:
            	write_to_outputfile(row)
	print("Past processing is complete.")
	print("Sentences that include ",BLACKLIST," have been deleted.")