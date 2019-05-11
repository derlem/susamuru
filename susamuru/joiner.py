import csv
import Common
import datetime

TIME_SUFFIX = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

def get_word_location(words,sub_word):
    for i,word in enumerate(words):
        if sub_word in word:
            return i
    return -1

def tag_sentence(sentence,vdt_index_map):
    words = sentence.split(" ")
    tags = ["O" for i in words]
    
    for _,(start,end,tag) in vdt_index_map.items():
        vdt_in_text = sentence[start:end]
        
        vdt_parts = vdt_in_text.split(" ")
        loc_of_the_begining = get_word_location(words,vdt_parts[0])
        if tag == Common.CoNNL_O:
            tags[loc_of_the_begining] = Common.CoNNL_O    
        else:
            tags[loc_of_the_begining] = Common.CoNNL_B + tag

            if len(vdt_parts) > 1:
                for part in vdt_parts[1:]:
                    location_ = get_word_location(words,part)
                    tags[location_] = Common.CoNNL_I + tag
    res = [words,tags]
    
    # Return the transposed version
    return [[x[0],"-","-","-","-","-","-","-","-",x[1]] for x in zip(*res)]

def join():
    print("Starting to join the sentences")
    tag_map = construct_tag_map()

    with open(Common.at_vdt_sentence_start_end_filename) as f:
        reader = csv.reader(f, delimiter=Common.delimiter,
                            quotechar=Common.quote_char)

        prev_sentence = ""
        is_first = True
        vdt_start_end_map = {}
        count = 0
        for row in reader:
            
            percentage = count*100.0/Common.total_sentence_count
            print("% [", percentage, "] of sentences processed.")
            
            vdt = row[1]
            sentence = row[2]
            start = int(row[3])
            end = int(row[4])

            if ((prev_sentence != sentence) and (not is_first)):
                # Get the words in the sentence.
                sentence_rows = tag_sentence(prev_sentence, vdt_start_end_map)
                write_to_final_file(sentence_rows)
                vdt_start_end_map = {} 
            
            is_first = False
            tag = tag_map[vdt]
            vdt_start_end_map[vdt] = (start, end, tag)
            prev_sentence = sentence

            count+=1


def write_to_final_file(sentence_rows):
    with open(Common.final_filename + '_' + TIME_SUFFIX + '.csv', mode='a') as f:
        writer = csv.writer(f, delimiter=Common.finalfile_delimiter,
                            quotechar=Common.finalfile_quote_char)
        writer.writerows(sentence_rows)
        writer.writerow(Common.seperator_row)

def construct_tag_map():
    tag_map = {}
    with open(Common.at_vdt_tag_filename) as f:
        reader = csv.reader(f, delimiter=Common.delimiter,
                            quotechar=Common.quote_char)
        for row in reader:
            if row[2] in Common.unknown_tags:
                tag_map[row[1]] = Common.CoNNL_O
            else:
                tag_map[row[1]] = row[2]

        return tag_map

if __name__ == "__main__":
    join()