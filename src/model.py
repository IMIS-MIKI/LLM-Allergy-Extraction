from pydantic import BaseModel, Field
from typing import List

import enum
import json


SUBSTANCE_CODE_PATH = "codes/substance.json"
FINDING_CODE_PATH = "codes/finding.json"


def get_all_substances_from_csv():
    with open(SUBSTANCE_CODE_PATH, 'r') as file:
        codes = json.load(file)
    return codes


def get_all_findings_from_csv():
    with open(FINDING_CODE_PATH, 'r') as file:
        codes = json.load(file)
    return codes


class AllergyIntolerance_DE(BaseModel):
    allergies: List[str] = Field(description=""" 
    
    Aufgabe: Übersetze den folgenden medizinischen Text in Englische und bestimme, ob der Patient Allergien hat. Falls Allergien erwähnt werden, liste alle englischen Allergien auf. 
    Falls keine Allergien erwähnt werden, gib nichts aus.

    Beispieltext: "Der Patient hat bekannte Allergien gegen Iod, Pollen und Hausstaubmilben."
    Antwort: Iodine, Pollen, House dust mites

    Ziel: Übersetze den Text in Englische und bestimme anhand der Informationen im Text, ob der Patient Allergien hat und gibt die Allergien als Liste aus. 
    Wenn keine Allergien erwähnt werden, gib nichts aus. Falls du Abkürzungen findest, schreibe sie aus.
      
    """)


def get_AllergyExtraction():
    return [AllergyIntoleranceExtraction]


class AllergyIntoleranceExtraction(BaseModel):
    allergies: List[str] = Field(description=""" 

    Task: Translate the following medical text into English and determine whether the patient has allergies. If allergies are mentioned, list all found allergies in English. 
    If no allergies are mentioned, do not provide any outcome. If you find abbreviations for the allergies, write them also out.

    Example text 1: "Der Patient hat bekannte Allergien gegen Iod, Pollen und Hausstaubmilben."
    Answer 1: Iodine, Pollen, House dust mites
    
    Example text 2: "Der Patient hat keine Allergien."
    Answer 2: 

    Example text 3: "Allergien: Mausepithel, Morphium-."
    Answer 3: Mouse epithelium, Morphium
    
    Objective: Translate the text into English and use the information in the text to determine whether the patient has allergies and output the allergies as a list.
    If no allergies are mentioned, do not provide any outcome.
    """)


def get_SubstanceIdentification():
    return [SubstanceIdentification]


class SubstanceIdentification(BaseModel):
    substance: List[str] = Field(description=""" 

    Task: The main substance and a list of substances will be given as text. From the list of substances identify the one the main substance corresponds to.
    If none of the substances in the list is the main substance return nothing. Should account for abbreviations or small typos. Should give priority to english versions.
    Results should exactly match the entry in the list which matched the main substance or return nothing if substance not found.

    Example text 1: "Main substance: 'dapsone' List of substances: ['Damson', 'Dapson', 'Dalapon', 'Gasoline', 'Dipyrone', 'Diflorasone', 'Decapase', 'DNase', 'Dental stone', 'Opicapone']"
    Answer 1: Dapson
    
    Example text 2: "Main substance: 'brown band-aid' List of substances: ['brown seeds', 'brown plant', 'banana', 'DNase']"
    Answer 2: 

    Example text 3: "Main substance: 'Nitro' List of substances: ['Sodium nitrite', 'Nitrite', 'Nitrogen compound', 'Organic nitrogen compound', 'Nitrosomonas communis']"
    Answer 3: Nitrogen compound

    Objective: Identify a substance in a list of substances and if it exists return the target substance from the list.
    """)


def get_SubstanceClassification():
    return [SubstanceClassification]


class SubstanceClassification(BaseModel):
    substance_type: List[str] = Field(description=""" 

    Task: A substance will be given. Classify the given substance into one of the following categories: food | medication | environment | biologic.

    Example text: "Walnut"
    Answer: food

    Objective: Classify a substance into one of the following categories food | medication | environment | biologic.
    """)


def get_SubstanceGatekeeper():
    return [SubstanceGatekeeper]


class SubstanceGatekeeper(BaseModel):
    check: List[str] = Field(description=""" 

    Task: Two substances will be given. Return True if they are both the same substance and False otherwise.

    Example text 1: Iod | Iodide
    Answer 1: False
    
    Example text 2: House dust mites | House dust (substance)
    Answer 2: True
    
    Example text 3: Mausepithel | Mouse epithelium
    Answer 3: True

    Objective: Identify if two substances are the same
    """)


def get_SubstanceIdentClass():
    return [SubstanceIdentClass]


class SubstanceIdentClass(BaseModel):
    substance: List[str] = Field(description=""" 

    Task: Task: The main substance of interest and a list of substances will be given as text. From the list of substances identify the one the main substance corresponds to.
    If none of the substances in the list match the main substance return nothing. Should account for abbreviations or small typos. Should give priority to english versions.
    Results should exactly match the corresponding entry in the list or return nothing if substance was not present in list.
    Then classify the given substance into one of the following categories: food | medication | environment | biologic.

    Example text: "Main substance: 'dapsone' List of substances: ['Damson', 'Dapson', 'Dalapon', 'Gasoline', 'Dipyrone', 'Diflorasone', 'Decapase', 'DNase', 'Dental stone', 'Opicapone']"
    Answer: [Dapson, medication]

    Objective: Identify a substance in a list of substances and if it exists return the target substance from the list along with its classifification as one of the following categories
     food | medication | environment | biologic.
    """)


# REACTIONS
def get_ReactionExtraction():
    return [ReactionExtraction]


class ReactionExtraction(BaseModel):
    reactions: List[str] = Field(description=""" 
    Task: You will be provided with a substance and a text in the format "substance | text".

    Your goal is to identify only the reactions that are explicitly associated with an allergy or intolerance to the given substance in the text.

    Rules:
    - Only return reactions that are directly linked to the specified substance.
    - Do not return reactions associated with any other substances.
    - If no reactions are found for the specified substance, return nothing.
    - Translate all reactions to English.

    Examples:

    Example 1:
    Input: Mouse Epithelium | OP bei Katarakt 2023. Allergien: Paracetamol + Mausepithel (jeweils Exanthem/Erythem, Dyspnoe, Krankheitsgefühl), Nickel
    Output: Exanthema, Erythema, Dyspnoea, Feeling ill

    Example 2:
    Input: Nickel | OP bei Katarakt 2023. Allergien: Paracetamol + Mausepithel (jeweils Exanthem/Erythem, Dyspnoe, Krankheitsgefühl), Nickel
    Output: 

    Example 3:
    Input: Paracetamol | OP bei Katarakt 2023. Allergien: Paracetamol + Mausepithel (jeweils Exanthem/Erythem, Dyspnoe, Krankheitsgefühl), Nickel
    Output: 

    Example 4:
    Input: Paracetamol | Haut kühl und trocken. Kein Ikterus, keine Zyanose, keine Ödeme. Allergien: Morphium- (Krankheitsgefühl), Paracetamol (Dyspnoe).
    Output: Dyspnoea
    """)


def get_ReactionIdentification():
    return [ReactionIdentification]


class ReactionIdentification(BaseModel):
    reaction: List[str] = Field(description=""" 

    Task: The main reaction and a list of reactions will be given as text. From the list of reactions identify the one the main reaction corresponds to.
    If none of the reactions in the list is the main reaction return nothing. Should account for abbreviations or small typos. Should give priority to english versions.
    Results should exactly match the entry in the list which matched the main reaction or return nothing if reaction not found.

    Example text 1: "Main reaction: 'exanthema' List of reactions: ['Exanthem', 'Exanthem subitum', 'Erythem', 'Drug exanthem', 'Exanthema subitum', 'Bullöses Exanthem', 'Viral exanthem']"
    Answer 1: Exanthem

    Objective: Identify a reaction in a list of reactions and if it exists return the target reaction from the list.
    """)


def get_ReactionSeverity():
    return [ReactionSeverity]


class ReactionSeverity(BaseModel):
    severity: List[str] = Field(description=""" 

    Task: The substance a patient is allergic to, a reaction to said substance and a text are provided. From the text identify the severity of the reaction of the patient when subjected to specified substance.
    Classify the severity into one of the following categories: mild | moderate | severe | undefined. If no severity is specified for this exactly the combination of substance and reaction return undefined. Avoid mixing severities from other reactions or allergies

    Example text 1: "'Aktuell: gering aktiv (MCP2-3 re. radiologischer Progress) unter  halbjährlich RTX (2x1g)  und MTX;DAS28-CRP: 2,63. Dosiserhöhung MTX von 7,5 auf 10 mg/Wo. empfohlen. Spirometrie mit Diffusion zum ILD-Screening zum 23.10. um 11:30 geplant, ggf HRCT Lunge empfohlen ). Weitere Diagnosen:. Allergien:  Adalimumab (Exanthem), Heuschnupfen (Hautausschläge, kritisch)\\rHypothyreose\\rBipolare Störung\\rdegenerativ: 4 mm  Ventrolisthese in Segment LWK 4/5. Linkskonvexe Skoliose der LWS'"
    Answer 1: undefined
    
    Example text 2: "'Hay Fever | Skin rashes | MTX seit 04/24 von 15 auf 7,5 mg s.c./Wo. (Transaminasenerhöhung) 07/23 add. Sulfasalazin (Aufdosierung). Aktuell: gering aktiv (MCP2-3 re. radiologischer Progress) unter  halbjährlich RTX (2x1g)  und MTX;DAS28-CRP: 2,63. Dosiserhöhung MTX von 7,5 auf 10 mg/Wo. empfohlen. Spirometrie mit Diffusion zum ILD-Screening zum 23.10. um 11:30 geplant, ggf HRCT Lunge empfohlen ). Weitere Diagnosen:. Allergien:  Adalimumab (Imraldi) (Exanthem), Heuschnupfen (Hautausschläge, kritisch)\\rHypothyreose\\rBipolare Störung\\rdegenerativ: 4 mm  Ventrolisthese in Segment LWK 4/5. Linkskonvexe Skoliose der LWS'"
    Answer 2: severe
    
    Objective: Identify the severity of the reaction the patient has towards a substance when in contact with a specific substance, if not explicit return undefined.
    """)


def get_ReactionGatekeeper():
    return [ReactionGatekeeper]


class ReactionGatekeeper(BaseModel):
    check: List[str] = Field(description=""" 

    Task: Two concepts will be given. Return True if they are both the same and False otherwise.

    Example text 1: Exanthem | Exanthem
    Answer 1: True

    Example text 2: Skin rashes | Hautausschläge
    Answer 2: True

    Example text 3: Abdominal lump | Abdominal migraine
    Answer 3: False

    Objective: Identify if two concepts are the same
    """)


# Allergy vs Intolerance
def get_Mechanism():
    return [Mechanism]


class Mechanism(BaseModel):
    mechanism: List[str] = Field(description=""" 

    Task: A substance and a text will be provided (substance | text). Identify in the text if it is explicitly mentioned whether the patient suffers an allergy or intolerance to the provided substance.
    If specified return the type as allergy | intolerance | undefined.

    Example text 1: "Mouse Epitheleum | OP bei Katarakt 2023. Allergien: Paracetamol + Mausepithel (jeweils Exanthem/Erythem, Dyspnoe, Krankheitsgefühl), Nickel"
    Answer 1: allergy

    Example text 2: "Nickel | OP bei Katarakt 2023. Allergien: Paracetamol + Mausepithel (jeweils Exanthem/Erythem, Dyspnoe, Krankheitsgefühl), Nickel"
    Answer 2: allergy

    Example text 3: "Lactose | OP bei Katarakt 2023. Allergien: Lactose intolerance + Mausepithel (jeweils Exanthem/Erythem, Dyspnoe, Krankheitsgefühl), Nickel"
    Answer 3: intolerance

    Example text 4: "Paracetamol | Haut kühl und trocken. Kein Ikterus, keine Zyanose, keine Ödeme. Allergien: Morphium- (Krankheitsgefühl), Paracetamol (Dyspnoe)."
    Answer 4: allergy

    Objective: Extract from the text whether the patiend has allergy | intolerance | undefined towards a specified substance.
    """)
