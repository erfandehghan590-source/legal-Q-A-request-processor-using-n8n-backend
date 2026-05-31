<img width="1729" height="1156" alt="image" src="https://github.com/user-attachments/assets/5f1af879-6b81-4a62-86ac-6d222895fbf6" />

## Intelligent Legal Data Generation Pipeline

An end-to-end AI pipeline for transforming raw statutory text into structured, multi-level legal question-answer datasets for chatbot, LLM, and RAG evaluation.

## Overview

This project automates the generation, processing, and standardization of legal evaluation data from unstructured law documents. It combines **Python orchestration**, **n8n workflow automation**, and **Gemini LLM-based prompt execution** to produce structured outputs in **TXT, XLSX, and JSON** formats.

The system was designed to address a common challenge in legal AI: the lack of scalable, high-quality evaluation datasets for testing the factual accuracy, reasoning ability, and reliability of language models in legal contexts.

## Problem Statement

Legal text is difficult for general-purpose LLMs because it is:

- highly specialized in terminology
- structurally complex
- sensitive to wording and legal nuance
- prone to hallucination when interpreted without grounding

Manual creation of legal QA datasets is expensive, slow, and difficult to scale. This project was built to industrialize that process through an automated and modular pipeline.

## Objectives

- Convert raw legal text into structured evaluation datasets
- Generate legal QA pairs across multiple reasoning levels
- Standardize outputs for both human review and downstream system use
- Improve reproducibility, scalability, and maintainability of legal data generation
- Enable future use in chatbot benchmarking, RAG evaluation, and legal AI testing workflows

## Key Features

- **End-to-end automation** from raw law documents to final JSON outputs
- **Multi-level question generation** across 4 complexity levels
- **Prompt engineering framework** for different legal reasoning tasks
- **Modular architecture** separating business logic from execution logic
- **Automated format conversion** from TXT to XLSX to JSON
- **Aggregation layer** for unified Excel-based human review
- **Multi-stage quality control**
- **Logging and execution monitoring**
- **Token usage optimization** for cost-sensitive LLM workflows

## System Architecture

The architecture is built around two core components:

### 1. Logic Layer: n8n Workflow
The n8n workflow serves as the system’s orchestration and prompt-engineering layer. It is responsible for:

- receiving requests via webhook
- selecting the correct prompt based on question level
- injecting legal terminology when needed
- routing requests to the LLM
- post-processing model outputs into structured responses

### 2. Execution Layer: Python Pipeline
The Python modules serve as the execution arm of the system. They are responsible for:

- reading legal text files
- sending requests to n8n
- saving raw outputs
- converting text tables to Excel
- aggregating structured files
- converting outputs into final JSON datasets
- validating and logging execution steps

## Design Philosophy

A major architectural decision in this project was the separation of:

- **business logic / prompt logic** → managed in n8n
- **execution / file processing / ETL tasks** → managed in Python

This separation improves:

- maintainability
- modularity
- scalability
- flexibility for replacing the underlying LLM
- ease of prompt iteration without redeploying Python code

## End-to-End Data Flow
```text
Raw Law Files
   ↓
main_pipeline.py
   ↓
n8n Webhook
   ↓
Gemini LLM
   ↓
Generated QA Table (TXT)
   ↓
Excel Conversion (XLSX)
   ↓
Aggregated Excel Output
   ↓
Structured JSON Files

## Reasoning Levels

The system generates legal QA data across four complexity levels:

### Level 1 — Direct Extraction
Focuses on explicit facts and direct retrieval from legal text.

Examples:
- identifying responsible entities
- extracting deadlines or quantities
- recognizing direct prohibitions or definitions

### Level 2 — Rewriting and Explanation
Focuses on paraphrasing, summarization, and plain-language explanation of legal content.

### Level 3 — Conditional and Procedural Reasoning
Focuses on:
- if/then logic
- step-by-step legal procedures
- distinguishing general rules from exceptions

### Level 4 — Cross-Article Synthesis
Focuses on combining information from multiple legal provisions to produce a single answer.

## Prompt Engineering Strategy

The prompt layer is one of the core assets of this project. Prompt templates were designed separately for each reasoning level to guide the LLM in producing legally grounded, structured outputs.

The prompts differ in terms of:
- extraction vs. synthesis requirements
- citation behavior
- quotation constraints
- use of legal terminology
- expected reasoning complexity

## Legal Terminology Dictionary

To improve the quality of outputs in higher-complexity levels, the system uses a legal terminology dictionary containing specialized legal terms and their simplified meanings.

This terminology is selectively injected into prompts to improve:
- legal precision
- consistency of explanations
- model understanding of domain-specific vocabulary

## Token Optimization Strategy

Because terminology injection increases token usage and cost, the system applies conditional logic:

- **Level 1** runs without the terminology dictionary
- **Levels 2–4** include the dictionary when deeper understanding is required

This design helps balance:
- cost efficiency
- response quality
- latency

## Python Modules

### `main_pipeline.py`
The orchestrator of the entire workflow.

Responsibilities:
- configuration management
- folder setup
- dependency checks
- sequential execution of all steps
- logging and failure control

### `legal_question_generator.py`
Handles communication with the n8n webhook.

Responsibilities:
- reading law text files
- sending POST requests to n8n
- receiving model outputs
- saving generated results

### `table_text_to_excel_converter.py`
Converts raw text table outputs into structured Excel files.

Responsibilities:
- parsing markdown-style tables
- cleaning rows and columns
- exporting standardized XLSX files

### `aggregate_xlsx_tables.py`
Aggregates multiple Excel files into a single reviewable dataset.

Responsibilities:
- standardizing column names
- enriching data with source metadata
- combining outputs across laws and levels

### `xlsx_to_json_converter.py`
Converts structured Excel files into JSON format for downstream use.

Responsibilities:
- filtering incomplete rows
- validating final records
- exporting machine-readable legal QA datasets

## Output Formats

The pipeline produces multiple output formats for different users and use cases:

- **TXT**: raw generated tables
- **XLSX**: structured files for human review
- **Aggregated XLSX**: unified dataset for product/legal analysis
- **JSON**: machine-readable format for backend systems, evaluation pipelines, or model testing

### Example JSON Record

json
{
  "question_id": "example_001",
  "question_txt": "Who is responsible for ...?",
  "correct_answer_txt": "According to Article ...",
  "level": 1,
  "pattern": "Actor Identification",
  "law_reference": "Article 12",
  "answer_reasoning": "The answer is directly stated in the law.",
  "source_file": "law_01_level_1.json"
}

## Quality Control

The project includes a multi-stage quality control layer across the pipeline:

- validation of expected response structure from n8n
- filtering malformed or incomplete text rows
- column standardization before aggregation
- removal of incomplete JSON records
- final execution summary and log-based monitoring

This QC design improves:
- output consistency
- traceability
- reliability for downstream evaluation tasks

## Logging and Monitoring

A structured logging system was implemented to replace ad hoc print-based debugging.

Logging covers:
- dependency checks
- folder preparation
- execution progress
- conversion summaries
- warnings for incomplete rows
- errors in network or file processing
- final pipeline execution summary

This makes the system easier to debug, maintain, and operate in batch workflows.

## Project Structure

text
Legal_QG_Pipeline/
├── laws/
├── output/
├── xlsx_output/
├── json_output/
├── pipeline.log
├── aggregated_legal_questions.xlsx
├── main_pipeline.py
├── legal_question_generator.py
├── table_text_to_excel_converter.py
├── aggregate_xlsx_tables.py
└── xlsx_to_json_converter.py

## Installation

### Requirements
- Python 3.6+
- pandas
- openpyxl
- requests

Install dependencies with:

bash
pip install pandas openpyxl requests

> Recommended future improvement: add a `requirements.txt` file for reproducible setup.

## How to Run

1. Place legal text files in the `laws/` folder  
2. Configure the pipeline settings in `main_pipeline.py`  
3. Run the pipeline:

bash
python main_pipeline.py

4. Review outputs in:
- `output/`
- `xlsx_output/`
- `json_output/`
- `aggregated_legal_questions.xlsx`

## Configuration

Key configuration options include:

- input/output folder paths
- defined reasoning levels
- execution mode (`manual` or `auto`)
- stop-on-failure behavior

## Execution Modes

### Manual Mode
The pipeline reads `.txt` law files from the local `laws/` folder and sends their contents to the n8n webhook.

### Auto Mode
The pipeline sends law identifiers to n8n and relies on preconfigured legal texts stored inside the workflow.

## Use Cases

This pipeline can support:

- legal chatbot evaluation
- legal RAG benchmarking
- structured dataset generation for LLM testing
- internal quality benchmarking for legal AI systems
- domain-specific data preparation workflows

## Development History

The current architecture evolved through iterative problem-solving around:

- request timeout issues
- output format limitations
- token cost management
- aggregation needs for human reviewers
- codebase cleanup and logging improvements

The result is a more mature and modular workflow than the original prototype.

## Future Improvements

Possible next steps include:

- adding `requirements.txt`
- introducing domain-based routing across multiple legal sectors
- improving file naming conventions
- redesigning the critic/validator stage as an error-reporting layer
- adding a simple user interface with Streamlit or Gradio
- extending support for alternative LLMs such as GPT-4 or Claude

## Tech Stack

- **Python**
- **n8n**
- **Google Gemini**
- **Pandas**
- **OpenPyXL**
- **REST/Webhooks**
- **JSON / Excel-based ETL**
