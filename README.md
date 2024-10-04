# Allergy Extraction using LLMs

This study explores the use of Large Language Models (LLMs) in extracting and structuring allergic reaction data from non-English clinical free texts.

The used dataset was a collection of 500 anamneses sections of discharge letters from the University Hospital Schleswig-Holstein.

The allergies and reactions are automatically mapped to SNOMED CT codes and tranformed into HL7 FHIR AllergyIntolerance resources.

## Requirements
Requires access to server with Ollama installed, along with required models 

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/IMIS-MIKI/LLM-Allergy-Extraction.git
   cd llm-allergy-extraction
   ```

2. Edit env.
   - Copy and complete the env.template with required credentials and OLLAMA host
   - Rename it to `.env`

3. Running locally
   1. Install requirements
       ```bash
      conda env create -f environment.yml
      conda activate allergy-extraction
      ```

   2. Feed Input folder
   3. Run experiment file
      ```bash
      python3 run_experiment.py
      ```

4. Run as Service
   1. Start Service - Build image and run it
       ```bash
      docker build -t allergy-extraction-service .
      docker-compose up -d
      ```

