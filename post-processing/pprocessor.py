import sys, getopt
import csv

DELIMITER = ","
QUOTE_CHAR = "\""

BLACKLIST = ["REDIRECT","</ref>","<ref","<small>","</small>","<small"]
def is_useful_sentence(sentence):
	for item in BLACKLIST:
		if item in sentence:
			return False
	return True

def write_to_outputfile(outputfile,items):
	with open(outputfile, mode='a') as f:
		writer = csv.writer(f, delimiter=DELIMITER,quotechar=QUOTE_CHAR, quoting=csv.QUOTE_MINIMAL)
		writer.writerow(items)

def main(argv):
	inputfile = ''
	outputfile = ''
	
	try:
		opts, args = getopt.getopt(argv,"hi:o:",["ifile=","ofile="])
	except getopt.GetoptError:
		print("pprocessor.py -i <inputfile> -o <outputfile>")
		sys.exit(2)
	
	# Parse opts and args
	for opt, arg in opts:
		if opt == '-h':
			print("pprocessor.py -i <inputfile> -o <outputfile>")
			sys.exit()
		elif opt in ("-i", "--ifile"):
			inputfile = arg
		elif opt in ("-o", "--ofile"):
			outputfile = arg
	
	if "-o" not in opts:
		outputfile = inputfile.replace('.csv','') +"_processed.csv"

	print('Input file is ', inputfile)
	print('Output file is ', outputfile)
	print("Processing the file...")
	
	total_count = 0
	deleted_count = 0
	
	with open(inputfile) as csvfile:
		reader = csv.reader(csvfile,delimiter=DELIMITER,quotechar=QUOTE_CHAR)
		for row in reader:
			total_count += 1
			is_useful = is_useful_sentence(row[2])
			if is_useful:
				write_to_outputfile(outputfile,row)
			else:
				deleted_count += 1
	
	print("Past processing is complete.\n")
	print("Sentences that include ",BLACKLIST," have been deleted.")
	print(deleted_count, " Sentences deleted.")
	print(total_count - deleted_count, " Sentences remained.")
if __name__ == '__main__':
	main(sys.argv[1:])