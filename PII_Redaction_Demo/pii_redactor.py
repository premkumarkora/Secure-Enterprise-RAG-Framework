"""
PII Redaction Demo for Healthcare AI
Demonstrates automatic detection and redaction of sensitive information
using Microsoft Presidio before data enters AI systems.
"""

import json
import sys
import subprocess
from datetime import datetime
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from colorama import init, Fore, Back, Style
from tabulate import tabulate

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Ensure spacy model is installed
def ensure_spacy_model():
    """Download spacy model if not already installed"""
    try:
        import spacy
        spacy.load("en_core_web_sm")
    except (OSError, ImportError):
        print(f"{Fore.YELLOW}Downloading spaCy language model (en_core_web_sm)...")
        import spacy.cli
        spacy.cli.download("en_core_web_sm")

ensure_spacy_model()


class PIIRedactor:
    """Main class for PII detection and redaction"""
    
    def __init__(self):
        """Initialize Presidio analyzer and anonymizer engines"""
        # Create NLP engine
        configuration = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
        }
        
        provider = NlpEngineProvider(nlp_configuration=configuration)
        nlp_engine = provider.create_engine()
        
        # Initialize analyzer with NLP engine
        self.analyzer = AnalyzerEngine(nlp_engine=nlp_engine)
        self.anonymizer = AnonymizerEngine()
        
        # Supported entity types
        self.entity_types = [
            "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD",
            "IBAN_CODE", "DATE_TIME", "LOCATION", "MEDICAL_LICENSE",
            "URL", "IP_ADDRESS"
        ]
    
    def analyze(self, text, language='en'):
        """
        Analyze text and detect PII entities
        
        Args:
            text: Input text to analyze
            language: Language code (default: 'en')
            
        Returns:
            List of detected PII entities with scores
        """
        results = self.analyzer.analyze(
            text=text,
            language=language,
            entities=self.entity_types
        )
        return results
    
    def redact(self, text, language='en'):
        """
        Redact PII from text using tokenization
        
        Args:
            text: Input text to redact
            language: Language code (default: 'en')
            
        Returns:
            Tuple of (redacted_text, detected_entities)
        """
        # Analyze text
        results = self.analyze(text, language)
        
        # Anonymize with tokens
        anonymized_result = self.anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators={
                "DEFAULT": OperatorConfig("replace", {"new_value": "<REDACTED>"}),
                "PERSON": OperatorConfig("replace", {"new_value": "<PERSON>"}),
                "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "<EMAIL>"}),
                "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "<PHONE>"}),
                "CREDIT_CARD": OperatorConfig("replace", {"new_value": "<CREDIT_CARD>"}),
                "DATE_TIME": OperatorConfig("replace", {"new_value": "<DATE>"}),
                "LOCATION": OperatorConfig("replace", {"new_value": "<LOCATION>"}),
            }
        )
        
        return anonymized_result.text, results
    
    def get_entity_summary(self, results):
        """
        Generate summary statistics of detected entities
        
        Args:
            results: List of detected entities from analyzer
            
        Returns:
            Dictionary with entity counts and confidence scores
        """
        summary = {}
        for result in results:
            entity_type = result.entity_type
            if entity_type not in summary:
                summary[entity_type] = {
                    'count': 0,
                    'avg_confidence': 0,
                    'confidences': []
                }
            summary[entity_type]['count'] += 1
            summary[entity_type]['confidences'].append(result.score)
        
        # Calculate average confidence
        for entity_type in summary:
            confidences = summary[entity_type]['confidences']
            summary[entity_type]['avg_confidence'] = sum(confidences) / len(confidences)
        
        return summary


def print_colored_comparison(original, redacted, entities):
    """Print side-by-side comparison with highlighting"""
    
    print("\n" + "="*80)
    print(f"{Fore.CYAN}{Style.BRIGHT}PII REDACTION COMPARISON")
    print("="*80 + "\n")
    
    # Original text
    print(f"{Fore.YELLOW}{Style.BRIGHT}ORIGINAL TEXT (WITH PII):")
    print(f"{Fore.RED}{Back.BLACK}{original}")
    
    print("\n" + "-"*80 + "\n")
    
    # Redacted text
    print(f"{Fore.GREEN}{Style.BRIGHT}REDACTED TEXT (PII PROTECTED):")
    print(f"{Fore.GREEN}{redacted}")
    
    print("\n" + "="*80 + "\n")


def print_entity_details(entities, summary):
    """Print detailed table of detected entities"""
    
    print(f"{Fore.CYAN}{Style.BRIGHT}DETECTED PII ENTITIES:\n")
    
    # Create table data
    table_data = []
    for entity in entities:
        table_data.append([
            entity.entity_type,
            entity.start,
            entity.end,
            f"{entity.score:.2%}",
            entity.recognition_metadata.get('recognizer_name', 'N/A')
        ])
    
    headers = ["Entity Type", "Start", "End", "Confidence", "Recognizer"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    print(f"\n{Fore.CYAN}{Style.BRIGHT}SUMMARY STATISTICS:\n")
    
    # Summary table
    summary_data = []
    for entity_type, stats in summary.items():
        summary_data.append([
            entity_type,
            stats['count'],
            f"{stats['avg_confidence']:.2%}"
        ])
    
    summary_headers = ["Entity Type", "Count", "Avg Confidence"]
    print(tabulate(summary_data, headers=summary_headers, tablefmt="grid"))


def process_claims_batch(claims_file='data/sample_claims.json'):
    """Process multiple claims and generate statistics"""
    
    redactor = PIIRedactor()
    
    # Load claims
    with open(claims_file, 'r') as f:
        claims = json.load(f)
    
    print(f"\n{Fore.MAGENTA}{Style.BRIGHT}Processing {len(claims)} medical claims...")
    print("="*80 + "\n")
    
    total_entities = 0
    all_entity_types = set()
    
    for i, claim in enumerate(claims, 1):
        print(f"{Fore.CYAN}Processing Claim {i}/{len(claims)}: {claim['claim_id']}")
        
        # Redact PII
        redacted_text, entities = redactor.redact(claim['text'])
        summary = redactor.get_entity_summary(entities)
        
        # Update statistics
        total_entities += len(entities)
        all_entity_types.update(summary.keys())
        
        # Print comparison
        print_colored_comparison(claim['text'], redacted_text, entities)
        print_entity_details(entities, summary)
        
        print("\n" + "="*80 + "\n")
    
    # Final summary
    print(f"{Fore.MAGENTA}{Style.BRIGHT}BATCH PROCESSING COMPLETE")
    print(f"Total Claims Processed: {len(claims)}")
    print(f"Total PII Entities Detected: {total_entities}")
    print(f"Unique Entity Types Found: {', '.join(sorted(all_entity_types))}")
    print("="*80 + "\n")


def demo_single_claim():
    """Quick demo with a single claim"""
    
    redactor = PIIRedactor()
    
    # Sample claim
    sample_text = """Claim ID: CLM-2024-8472
Patient: Ahmed Al-Mansouri, Emirates ID: 784-1985-1234567-8
DOB: 15/03/1985
Diagnosis: Type 2 Diabetes with complications
Physician: Dr. Sarah Johnson
Hospital: Burjeel Medical City, Abu Dhabi
Phone: +971-50-123-4567
Email: ahmed.almansouri@email.ae
Claim Amount: AED 45,000
Notes: Patient hospitalized on 12/01/2024 for insulin management.
Credit Card: 4532-1234-5678-9010"""
    
    print(f"\n{Fore.MAGENTA}{Style.BRIGHT}QUICK DEMO - Single Claim Processing")
    print("="*80 + "\n")
    
    # Process
    redacted_text, entities = redactor.redact(sample_text)
    summary = redactor.get_entity_summary(entities)
    
    # Display results
    print_colored_comparison(sample_text, redacted_text, entities)
    print_entity_details(entities, summary)


if __name__ == "__main__":
    import sys
    
    print(f"""
{Fore.CYAN}{Style.BRIGHT}
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║        PII REDACTION DEMO FOR HEALTHCARE AI SYSTEMS              ║
║                                                                   ║
║        Protecting Patient Privacy Before AI Processing           ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}
    """)
    
    print("Choose demo mode:")
    print("1. Quick Demo (single claim)")
    print("2. Batch Processing (all 10 sample claims)")
    print("3. Exit")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        demo_single_claim()
    elif choice == "2":
        process_claims_batch()
    elif choice == "3":
        print("Exiting...")
        sys.exit(0)
    else:
        print("Invalid choice. Running quick demo by default...")
        demo_single_claim()
    
    print(f"\n{Fore.GREEN}Demo completed successfully!")
    print(f"{Fore.CYAN}Check out the code at: https://github.com/yourusername/pii-redaction-demo")