from langchain_core.output_parsers import StrOutputParser, SimpleJsonOutputParser
from langchain.prompts import PromptTemplate
from langchain_community.llms import Ollama

import os
import re
import json


# https://cau-git.rz.uni-kiel.de/MIKI/impetus/llm-utils/-/blob/main/reformatting.py
def clean_string(input_string):
    # Note order at which string is cleaned matters!

    # Remove strange characters
    cleaned_string = re.sub(r'[¶]', '', input_string)

    # Remove "\m..." or "\mG..."
    cleaned_string = re.sub(r'\\m\d+', '', cleaned_string)
    cleaned_string = re.sub(r'\\mG\d+', '', cleaned_string)

    # Remove "\y:575\"
    cleaned_string = re.sub(r'\\y:\d+\\', '', cleaned_string)

    # Remove "\a:575\"
    cleaned_string = re.sub(r'\\a:\d+\\', '', cleaned_string)

    # Remove "\f:****\" or "\c:****\" where **** is any integer
    cleaned_string = re.sub(r'\\f:\d+\\', '', cleaned_string)
    cleaned_string = re.sub(r'\\c:\d+\\', '', cleaned_string)

    # Remove "\f:-\" or "\c:-\"
    cleaned_string = re.sub(r'\\f:-\\', '', cleaned_string)
    cleaned_string = re.sub(r'\\c:-\\', '', cleaned_string)

    # Remove any other non-alphanumeric escape sequences
    cleaned_string = re.sub(r'\\[^\w\s]', '', cleaned_string)

    # Replace sequences of \r and \n (including combinations and multiples) with a single line break
    cleaned_string = re.sub(r'(\\r\s*|\\n\s*)+', "\n", cleaned_string)

    # Test - remove control characters (like ASCII control characters)
    cleaned_string = re.sub(r'[\x00-\x09\x0B-\x1F\x7F]', '', cleaned_string)

    return cleaned_string


def get_text(incoming_text):
    return clean_string(incoming_text)


def run_text(llm_model, document_id, text, prompt_model):
    prompt_template = get_prompt_template()

    json_schema_list = []
    for data_model in prompt_model:
        json_schema = get_json_schema(data_model)
        json_schema_list.append(json_schema)

    llm_outputs = run_llm(
        prompt_template,
        prompt_variables_list=[
            {
                "documents": text,
                "json_schema": schema,
                "begin_tokens": "[INST]",
                "end_tokens": "[/INST]",
            }
            for schema in json_schema_list
        ],
        model=llm_model,
    )

    res = dict()
    res['id'] = document_id
    res['text'] = text
    res['outcomes'] = llm_outputs
    return res


def run_llm(prompt_template: PromptTemplate, prompt_variables_list: list[dict], model: str | None = None):
    ollama_host = os.getenv('OLLAMA_HOST')
    llm = Ollama(format="json", temperature=0.1, base_url=ollama_host, model=model)
    llm_chain = prompt_template | llm | SimpleJsonOutputParser()

    responses = []
    for prompt_variables in prompt_variables_list:
        resp = llm_chain.invoke(prompt_variables)
        responses.append(resp)

    return responses


# https://github.com/MouYongli/MIE2024/blob/jonathan/pipeline_stages/_3_json_schema.py
def simplify_schema(schema):
    def replace_ref(obj):
        if isinstance(obj, dict):
            if "$ref" in obj:
                ref_path = obj["$ref"]
                def_name = ref_path.split("/")[-1]
                definition = schema["$defs"][def_name]
                definition.pop("title", None)
                return definition
            else:
                new_obj = {k: replace_ref(v) for k, v in obj.items()}
                new_obj.pop("title", None)
                if "allOf" in new_obj:
                    enum_details = new_obj["allOf"][0]
                    if "enum" in enum_details:
                        new_obj.update(enum_details)
                        del new_obj["allOf"]
                return new_obj
        elif isinstance(obj, list):
            return [replace_ref(i) for i in obj]
        else:
            return obj

    inlined_schema = replace_ref(schema)
    if "$defs" in inlined_schema:
        del inlined_schema["$defs"]
    return inlined_schema


def get_json_schema(data_model):
    schema = simplify_schema(data_model.model_json_schema())
    return json.dumps(schema, indent=4, ensure_ascii=False)


def get_prompt_template():
    prompt_template_text = """{begin_tokens}Ich werde dir im Folgenden ein Dokument übergeben, welches sich auf die Anamnese eines Patient bezieht.
    Deine Antwort soll aus einem JSON-Objekt bestehen, dass die gemeinsamen Informationen aus dem Dokument enthält.

    Das JSON-Objekt soll folgendem JSON-Schema entsprechen, wobei immer nur Werte ermittelt werden dürfen, die in dem jeweiligen Datentypen erlaubt sind. 
    Also wenn z.B. der Datentyp im JSON-Schema string ist, dann darf der Wert ein beliebiger String sein.
    Wenn allerdings der Datentyp enum ist mit einer Liste von möglichen Werten, darf nur ein Wert aus dieser Liste genommen werden!
    Nimm also dann immer den wahrscheinlichsten Wert aus der Liste. Wenn bei einem Feld kein Wert sicher ermittelt werden kann, ist das Feld wegzulassen.
    In der 'description' erkläre ich dir jeweils, wie du den richtigen Wert ermittelst. Hier ist das JSON-Schema:

    {json_schema}

    Dies ist das Dokument:

    {documents}

    Bitte beachte, dass deine Antwort das gesuchte JSON-Objekt sein soll und keine weiteren Informationen wie erklärenden Text beinhalten darf.
    Deine Antwort muss sich also direkt gegen das obige Schema validieren lassen.{end_tokens}"""

    prompt_template = PromptTemplate(
        template=prompt_template_text,
        input_variables=["json_schema", "documents", "begin_tokens", "end_tokens"],
    )

    return prompt_template
