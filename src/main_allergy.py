from src.pipeliner import *
from src.model import *
from fhir_exporter import export
from collections import namedtuple
import difflib
import os
import json

substance_types = ["food", "medication", "environment", "biologic"]
substance_tuple = namedtuple('Substance', ['code', 'display', 'category', 'mechanism'])
substances = get_all_substances_from_csv()
substances_keys = list(substances.keys())

mechanism_types = ["allergy", "intolerance", "undefined"]

findings = get_all_findings_from_csv()
findings_keys = list(findings.keys())
reaction_tuple = namedtuple('Reaction', ['code', 'display', 'severity'])
severity_types = ["mild", "moderate", "severe", "undefined"]

def get_substance_for_allergy(llm_model, allergy, document_id):
    # Get Substance
    matches = difflib.get_close_matches(allergy, substances_keys, cutoff=0.5, n=20)

    text_search_match = f"Main substance: '{allergy}' List of substances: {matches}"

    res_substance = run_text(llm_model=llm_model, document_id=document_id, text=text_search_match,
                             prompt_model=get_SubstanceIdentification())

    res_substance_key = res_substance["outcomes"][0]

    if not ("substance" in res_substance_key.keys() and len(res_substance_key["substance"]) > 0 and
            res_substance_key["substance"][0] in substances_keys):
        return []

    substance = res_substance_key["substance"][0]

    text_gatekeeper = substance + " | " + allergy

    res_gatekeeper = run_text(llm_model=llm_model, document_id=document_id, text=text_gatekeeper,
                              prompt_model=get_SubstanceGatekeeper())

    res_gatekeeper = res_gatekeeper["outcomes"][0]

    if not ("check" in res_gatekeeper.keys() and len(res_gatekeeper["check"]) > 0 and
            res_gatekeeper["check"][0]):
        return []

    # Get Mechanism (Allergy vs Intolerance)
    text_mechanism = substance + " | " + allergy

    res_mechanism = run_text(llm_model=llm_model, document_id=document_id, text=text_mechanism,
                              prompt_model=get_Mechanism())

    res_mechanism = res_mechanism["outcomes"][0]

    if not ("mechanism" in res_mechanism.keys() and len(
            res_mechanism["mechanism"]) > 0 and
            res_mechanism["mechanism"][0] in mechanism_types):
        res_mechanism["mechanism"] = ["undefined"]

    mechanism = res_mechanism["mechanism"][0]

    # Get Substance type

    text_subst_type = substance

    res_substance_type = run_text(llm_model=llm_model, document_id=document_id, text=text_subst_type,
                                  prompt_model=get_SubstanceClassification())

    res_substance_type_key = res_substance_type["outcomes"][0]

    if not ("substance_type" in res_substance_type_key.keys() and len(
            res_substance_type_key["substance_type"]) > 0 and
            res_substance_type_key["substance_type"][0] in substance_types):
        return substance_tuple(substances[substance], substance, None, mechanism)

    return substance_tuple(substances[substance], substance, res_substance_type_key["substance_type"][0], mechanism)


def get_reactions_for_substance(llm_model, text, allergy, document_id):

    text_reactions = allergy + " | " + text
    res_all_reactions = run_text(llm_model=llm_model, document_id=document_id, text=text_reactions,
                                 prompt_model=get_ReactionExtraction())

    result = []

    # Gwen2 returns empty dict if  no allergy is present.
    if not bool(res_all_reactions['outcomes'][0]):
        res_all_reactions['outcomes'][0]['reactions'] = list()

    for reaction in res_all_reactions['outcomes'][0]['reactions']:
        matches = difflib.get_close_matches(reaction, findings_keys, cutoff=0.5, n=20)

        text_search_match = f"Main reaction: '{reaction}' List of reactions: {matches}"

        res_reaction = run_text(llm_model=llm_model, document_id=document_id, text=text_search_match,
                                prompt_model=get_ReactionIdentification())

        res_reaction_key = res_reaction["outcomes"][0]

        if not ("reaction" in res_reaction_key.keys() and len(res_reaction_key["reaction"]) > 0 and
                res_reaction_key["reaction"][0] in findings_keys):
            continue

        target_reaction = res_reaction_key["reaction"][0]

        text_gatekeeper = reaction + " | " + target_reaction

        res_reaction_gatekeeper = run_text(llm_model=llm_model, document_id=document_id, text=text_gatekeeper,
                                           prompt_model=get_ReactionGatekeeper())

        res_reaction_gatekeeper = res_reaction_gatekeeper["outcomes"][0]

        if not ("check" in res_reaction_gatekeeper.keys() and len(res_reaction_gatekeeper["check"]) > 0 and
                res_reaction_gatekeeper["check"][0]):
            continue

        # Get Severity
        text_reaction_severity = allergy + " | " + target_reaction + " | " + text
        res_reaction_severity = run_text(llm_model=llm_model, document_id=document_id, text=text_reaction_severity,
                                         prompt_model=get_ReactionSeverity())

        res_reaction_severity_key = res_reaction_severity["outcomes"][0]

        if not ("severity" in res_reaction_severity_key.keys() and
                len(res_reaction_severity_key["severity"]) > 0 and
                res_reaction_severity_key["severity"][0] in severity_types):
            res_reaction_severity_key = {'severity': ['undefined']}

        severity_reaction = res_reaction_severity_key["severity"][0]
        result.append(reaction_tuple(findings[target_reaction], target_reaction, severity_reaction))  # ['code', 'display', 'severity'])

    return result


def run_llm_allergy(llm_model, text, patient_id, store_locally=False):

    result = run_text(llm_model=llm_model, document_id=patient_id, text=text, prompt_model=get_AllergyExtraction())

    result["allergies"] = dict()

    for allergy in result['outcomes'][0]['allergies']:
        result["allergies"][allergy] = get_substance_for_allergy(llm_model, allergy, patient_id)
        result["reactions"][allergy] = get_reactions_for_substance(llm_model, text, allergy, patient_id)

    if store_locally:
        with open('experiment/kafka_' + patient_id, 'w') as fp:
            json.dump(result, fp, ensure_ascii=False, indent=4)

    if result["allergies"]:
        bundle = export(patient_id, patient_id, result["allergies"], result["reactions"])

        if store_locally:
            with open('experiment/fhir_' + patient_id, 'w') as fp:
                json.dump(bundle.dict(), fp, ensure_ascii=False, indent=4)

        return bundle.dict()
