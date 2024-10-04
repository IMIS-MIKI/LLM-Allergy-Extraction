from tqdm import tqdm
from src.pipeliner import *
from csv import DictWriter
from pathlib import Path
from src.model import get_all_substances_from_csv, get_AllergyExtraction, get_SubstanceIdentification, \
    get_SubstanceClassification, get_SubstanceIdentClass, get_SubstanceGatekeeper, get_all_findings_from_csv
from src.main_allergy import get_substance_for_allergy, get_reactions_for_substance
from src.fhir_exporter import export
from src.evaluate import run_eval
from collections import namedtuple
import difflib
import os
import json
from dotenv import load_dotenv

load_dotenv(verbose=True)
INPUT_PATH = os.environ['INPUT_PATH']
EXPERIMENT_PATH = os.environ['EXPERIMENT_PATH']
OLLAMA_MODEL = os.environ['OLLAMA_MODEL']


def get_file_paths(amount=-1):
    echo_files = os.listdir(INPUT_PATH)
    if '.gitkeep' in echo_files: echo_files.remove('.gitkeep')
    if '.DS_Store' in echo_files: echo_files.remove('.DS_Store')
    if amount != -1:
        return echo_files[:amount]
    else:
        return echo_files


def get_file_name(doc_id, model_name):
    return 'result_' + str(doc_id) + '_' + str(model_name) + '.json'


if __name__ == '__main__':
    models = [OLLAMA_MODEL]

    files = get_file_paths()

    for f in tqdm(files):
        with open(INPUT_PATH + f, 'r') as file:
            data = json.load(file)

        text = data['text']
        document_id = data['id']

        for llm_model in models:
            file_name = get_file_name(doc_id=document_id, model_name=llm_model)
            if not Path(f'{EXPERIMENT_PATH}/{file_name}').is_file():

                result = run_text(llm_model=llm_model, document_id=document_id, text=text,
                                  prompt_model=get_AllergyExtraction())

                result["allergies"] = dict()
                result["reactions"] = dict()

                # Gwen2 returns empty dict if  no allergy is present.
                if not bool(result['outcomes'][0]):
                    result['outcomes'][0]['allergies'] = list()

                for allergy in result['outcomes'][0]['allergies']:
                    result["allergies"][allergy] = get_substance_for_allergy(llm_model, allergy, document_id)
                    result["reactions"][allergy] = get_reactions_for_substance(llm_model, text, allergy, document_id)

                if result["allergies"]:
                    bundle = export(document_id, document_id, result["allergies"], result["reactions"])

                    with open(f'{EXPERIMENT_PATH}/fhir_{file_name}', 'w') as fp:
                        json.dump(bundle.dict(), fp, ensure_ascii=False, indent=4)

                with open(f'{EXPERIMENT_PATH}/{file_name}', 'w') as fp:
                    json.dump(result, fp, ensure_ascii=False, indent=4)
