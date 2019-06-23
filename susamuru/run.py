from susamuru import at_dtcs as get_disambiguation_terms
from susamuru import at_vdts as get_valid_disambiguation_terms
from susamuru import at_vdt_etg as get_etg
from susamuru import at_vdt_tag as step_3_5
from dataset_manager import generate_at_vdt_sentence_start_end_csv as get_sentences

if __name__ == '__main__':
  # fire.Fire()
  # get_disambiguation_terms()
  # get_valid_disambiguation_terms()
  # get_etg()
  get_sentences()