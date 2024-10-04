from tqdm import tqdm

import pandas as pd
import json
import os

from dotenv import load_dotenv

load_dotenv(verbose=True)
INPUT_PATH = os.environ['INPUT_PATH']
EXPERIMENT_PATH = os.environ['EXPERIMENT_PATH']
OLLAMA_MODEL = os.environ['OLLAMA_MODEL']

GT_FILE = 'codes/allergy-groundtruth.csv'

DATA_PATH = 'raw/'
OUT_PATH = 'out/'


def load_ground_truth():
    df = pd.read_csv(GT_FILE, delimiter=';')
    return df


def get_result_filename(document_id, model_name):
    return 'result_' + str(document_id) + '_' + model_name + '.json'


def get_bool_result(document_id, model='llama3.1:70b'):
    with open(EXPERIMENT_PATH + get_result_filename(document_id, model), 'r') as file:
        data = json.load(file)

    return 1 if len(data['outcomes'][0]['allergies']) > 0 else 0


def get_result_list(document_id, model='llama3.1:70b'):
    with open(EXPERIMENT_PATH + get_result_filename(document_id, model), 'r') as file:
        data = json.load(file)

    return data['allergies']


def convert_raws():
    files_list = os.listdir(DATA_PATH)
    if '.gitkeep' in files_list: files_list.remove('.gitkeep')
    if '.DS_Store' in files_list: files_list.remove('.DS_Store')

    for echo in tqdm(files_list):
        res = dict()
        with open(DATA_PATH + echo, 'r') as file:
            res['id'] = echo
            res['text'] = file.read()

        with open(INPUT_PATH + echo + '.json', 'w') as fp:
            json.dump(res, fp, ensure_ascii=False)


def evaluate_bool(model_name='llama3.1:70b'):
    gt = load_ground_truth()
    temp = []

    for index, row in gt.iterrows():
        temp.append(get_bool_result(row['filename'], model_name))

    y_pred = pd.Series(temp, name='Prediction')

    gt.insert(2, 'Prediction', temp, True)
    gt.to_csv(OUT_PATH + model_name + '_bool_out.csv', index=False)

    y_gt = pd.Series(gt['allergy_bool'], name='GT')

    df_confusion = pd.crosstab(y_gt, y_pred, rownames=['Ground Truth'], colnames=['Predicted'], margins=True)
    print(df_confusion)


def evaluate_coding(model_name='llama3.1:70b'):
    gt = load_ground_truth()

    temp = dict()

    for index, row in gt.iterrows():
        if row['allergy_bool'] == 1:
            temp[row['filename']] = get_result_list(row['filename'], model_name)

    with open('out/' + model_name + '.csv', 'w') as fp:

        for key in temp.keys():
            for entry in temp[key].keys():
                fp.write(key + ';' + entry + ';' + ';'.join(temp[key][entry]) + '\n')


def run_eval(model_name='llama3.1:70b'):
    evaluate_bool(model_name)
    evaluate_coding(model_name)


if __name__ == '__main__':
    run_eval(OLLAMA_MODEL)
