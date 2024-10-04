from fhir.resources.bundle import Bundle, BundleEntry, BundleEntryRequest
from fhir.resources.observation import Observation
from fhir.resources.allergyintolerance import AllergyIntolerance, AllergyIntoleranceReaction
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.identifier import Identifier
from fhir.resources.reference import Reference
from fhir.resources.annotation import Annotation
from fhir.resources.codeablereference import CodeableReference

import uuid


def export(patient_id, document_id, substances, reactions):
    bundle = Bundle.construct()
    bundle.type = 'transaction'
    bundle.entry = []
    allergy_bundle_request = BundleEntryRequest.construct(url='AllergyIntolerance', method='POST')
    obs_bundle_request = BundleEntryRequest.construct(url='Observation', method='POST')

    for key in substances:
        allergy_entry = BundleEntry.construct()
        allergy, reactions_obs = create_allergy(patient_id, document_id, key, substances[key], reactions[key])
        allergy_entry.resource = allergy
        allergy_entry.request = allergy_bundle_request
        allergy_entry.fullUrl = str(uuid.uuid4())
        bundle.entry.append(allergy_entry)
        for entry in reactions_obs.keys():
            obs_entry = BundleEntry.construct()
            obs_entry.resource = reactions_obs[entry]
            obs_entry.request = obs_bundle_request
            obs_entry.fullUrl = str(entry)
            bundle.entry.append(obs_entry)
    return bundle


def create_observation(patient_id, reaction):
    observation = Observation.construct()
    observation.status = "final"
    observation_code = CodeableConcept.construct()
    observation_code.coding = list()
    observation_code.coding.append({"system": "http://hl7.org/fhir/ValueSet/observation-codes",
                                    "code": reaction.code,
                                    "display": reaction.display})
    observation.code = observation_code
    pat_ref = Reference.construct()
    pat_ref.reference = "https://medic.uksh.de/orbis/" + str(patient_id)
    observation.subject = pat_ref
    return observation


def create_allergy(patient_id, document_id, note, substance, reactions):
    allergy = AllergyIntolerance.construct()

    identifier = Identifier.construct()
    identifier.system = "https://lake.medic.uksh.de/document/"
    identifier.value = document_id
    allergy.identifier = [identifier]

    clinical_status = CodeableConcept.construct()
    clinical_status.coding = list()
    clinical_status.coding.append({"system": "http://hl7.org/fhir/ValueSet/allergyintolerance-clinical",
                                   "code": "active",
                                   "display": "Active"})
    allergy.clinicalStatus = clinical_status

    verification_status = CodeableConcept.construct()
    verification_status.coding = list()
    verification_status.coding.append({"system": "http://hl7.org/fhir/ValueSet/allergyintolerance-verification",
                                       "code": "unconfirmed",
                                       "display": "Unconfirmed"})
    allergy.verificationStatus = verification_status
    allergy.criticality = 'unable-to-assess'

    if substance:
        code = CodeableConcept.construct()
        code.coding = list()
        code.coding.append({"system": "http://hl7.org/fhir/ValueSet/allergyintolerance-code",
                            "code": substance.code,
                            "display": substance.display})
        allergy.code = code

        if substance.mechanism != "undefined":
            allergy_type = CodeableConcept.construct()
            allergy_type.coding = list()
            allergy_type.coding.append({"system": "http://hl7.org/fhir/ValueSet/allergy-intolerance-type",
                                        "code": substance.mechanism,
                                        "display": substance.mechanism.capitalize()})
            allergy.type = allergy_type

        if substance.category:
            allergy.category = [substance.category]

    else:
        allergy_note = Annotation.construct()
        allergy_note.text = note
        allergy.note = [allergy_note]

    reactions_list = []
    observations_dict = dict()
    for reaction in reactions:
        allergy_intol_reaction = AllergyIntoleranceReaction.construct()

        obs_uuid = str(uuid.uuid4())
        obs = create_observation(patient_id, reaction)
        observations_dict[obs_uuid] = obs

        reaction_ref = Reference.construct()
        reaction_ref.reference = obs_uuid

        manifestation = CodeableReference.construct()
        manifestation.reference = reaction_ref
        allergy_intol_reaction.manifestation = [manifestation]

        reaction_note = Annotation.construct()
        reaction_note.text = reaction.display + " | " + reaction.code
        allergy_intol_reaction.note = [reaction_note]

        if reaction.severity != "undefined":
            allergy_intol_reaction.severity = reaction.severity

        reactions_list.append(allergy_intol_reaction)

    if reactions_list:
        allergy.reaction = reactions_list

    pat_ref = Reference.construct()
    pat_ref.reference = "https://medic.uksh.de/orbis/" + str(patient_id)
    allergy.patient = pat_ref
    return allergy, observations_dict
