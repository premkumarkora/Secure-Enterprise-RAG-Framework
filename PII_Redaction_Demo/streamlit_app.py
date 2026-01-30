"""
Streamlit UI for PII Redaction Demo
Visualize before/after PII redaction for healthcare data
"""

import streamlit as st
import json
from pathlib import Path

from presidio_analyzer import AnalyzerEngine, RecognizerResult, Pattern, PatternRecognizer
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

# Page configuration
st.set_page_config(
    page_title="PII Redaction Demo",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stMetric {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)


def create_custom_recognizers():
    """Create custom pattern recognizers for healthcare data"""
    # Hospital name recognizer - uses lookbehind to match only the hospital name
    hospital_pattern = Pattern(
        name="hospital_pattern",
        regex=r"(?<=Hospital:\s)[A-Za-z][A-Za-z0-9\s,\-\.]+?(?=\n|$)",
        score=0.9
    )
    hospital_recognizer = PatternRecognizer(
        supported_entity="LOCATION",
        patterns=[hospital_pattern],
        name="HospitalRecognizer"
    )

    # Physician name recognizer - uses lookbehind to match only the name after "Dr."
    physician_pattern = Pattern(
        name="physician_pattern",
        regex=r"(?<=Physician:\sDr\.\s)[A-Z][a-z]+(?:\s+[A-Z][a-z\-]+)+",
        score=0.9
    )
    physician_recognizer = PatternRecognizer(
        supported_entity="PERSON",
        patterns=[physician_pattern],
        name="PhysicianRecognizer"
    )

    return [hospital_recognizer, physician_recognizer]


@st.cache_resource
def load_pii_engine():
    """Initialize and cache Presidio engines"""
    configuration = {
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "en", "model_name": "en_core_web_lg"}],
    }
    provider = NlpEngineProvider(nlp_configuration=configuration)
    nlp_engine = provider.create_engine()
    analyzer = AnalyzerEngine(nlp_engine=nlp_engine)

    # Add custom recognizers
    for recognizer in create_custom_recognizers():
        analyzer.registry.add_recognizer(recognizer)

    anonymizer = AnonymizerEngine()
    return analyzer, anonymizer


def filter_bad_detections(text: str, results):
    """Filter out obvious misclassifications"""
    import re

    filtered = []
    for entity in results:
        detected_text = text[entity.start:entity.end]

        # Skip if PERSON detection looks like a date (e.g., "05/01/2024")
        if entity.entity_type == "PERSON":
            if re.match(r'^\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}$', detected_text):
                continue  # Skip this - it's a date, not a person

        # If entity spans across newlines, truncate to first line only
        if '\n' in detected_text:
            first_line = detected_text.split('\n')[0].strip()
            if len(first_line) < 2:  # Too short after truncation
                continue
            # Create new entity with truncated bounds
            new_end = entity.start + len(first_line)
            filtered.append(RecognizerResult(
                entity_type=entity.entity_type,
                start=entity.start,
                end=new_end,
                score=entity.score,
                analysis_explanation=entity.analysis_explanation,
                recognition_metadata=entity.recognition_metadata
            ))
        else:
            filtered.append(entity)

    return filtered


def analyze_and_redact(text: str, analyzer, anonymizer):
    """Analyze text for PII and redact it"""
    entity_types = [
        "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD",
        "IBAN_CODE", "DATE_TIME", "LOCATION", "MEDICAL_LICENSE",
        "URL", "IP_ADDRESS"
    ]

    # Analyze
    results = analyzer.analyze(text=text, language="en", entities=entity_types)

    # Filter out bad detections (e.g., dates detected as PERSON, entities spanning newlines)
    results = filter_bad_detections(text, results)

    # Anonymize
    anonymized = anonymizer.anonymize(
        text=text,
        analyzer_results=results,
        operators={
            "DEFAULT": OperatorConfig("replace", {"new_value": "[REDACTED_INFO]"}),
            "PERSON": OperatorConfig("replace", {"new_value": "[PERSON_NAME]"}),
            "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "[EMAIL_ADDRESS]"}),
            "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "[PHONE_NUMBER]"}),
            "CREDIT_CARD": OperatorConfig("replace", {"new_value": "[CREDIT_CARD_NUMBER]"}),
            "DATE_TIME": OperatorConfig("replace", {"new_value": "[DATE_TIME]"}),
            "LOCATION": OperatorConfig("replace", {"new_value": "[LOCATION_NAME]"}),
            "URL": OperatorConfig("replace", {"new_value": "[WEB_URL]"}),
            "IP_ADDRESS": OperatorConfig("replace", {"new_value": "[IP_ADDRESS]"}),
        }
    )

    return anonymized.text, results


def load_sample_claims():
    """Load sample claims from JSON file"""
    claims_path = Path(__file__).parent / "data" / "sample_claims.json"
    if claims_path.exists():
        with open(claims_path, "r") as f:
            return json.load(f)
    return []


def main():
    # Header
    st.title("🔒 PII Redaction Demo")
    st.markdown("### Protecting Sensitive Information Before AI Processing")
    st.markdown("---")

    # Load engines
    with st.spinner("Loading PII detection engine..."):
        analyzer, anonymizer = load_pii_engine()

    # Sidebar
    with st.sidebar:
        st.markdown("### ℹ️ About")
        st.markdown("""
        This demo shows how PII (Personally Identifiable Information)
        is detected and redacted **before** data enters AI systems.

        **Key Benefits:**
        - 🛡️ Protects patient privacy
        - ✅ HIPAA/GDPR compliant
        - 🤖 Safe for AI processing
        """)

    # Main content - Sample Claims
    claims = load_sample_claims()

    if claims:
        claim_options = {f"{c['claim_id']}": c['text'] for c in claims}
        selected_claim = st.selectbox(
            "Select a sample claim:",
            options=list(claim_options.keys()),
            format_func=lambda x: f"📋 {x}"
        )
        input_text = claim_options[selected_claim]
    else:
        st.warning("No sample claims found. Using default example.")
        input_text = """Claim ID: CLM-2024-8472
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

    # Process button
    if st.button("🔍 Analyze & Redact PII", type="primary", use_container_width=True):
        if not input_text.strip():
            st.error("Please enter some text to analyze.")
            return

        with st.spinner("Analyzing text for PII..."):
            redacted_text, entities = analyze_and_redact(input_text, analyzer, anonymizer)

        # Show raw input text
        st.markdown("### 📄 Raw Input Data")
        st.code(input_text, language=None)

        # Detailed entity table
        st.markdown("### 📋 Detected Entities Details")

        # Mapping from entity type to replacement token
        replacement_tokens = {
            "PERSON": "[PERSON_NAME]",
            "EMAIL_ADDRESS": "[EMAIL_ADDRESS]",
            "PHONE_NUMBER": "[PHONE_NUMBER]",
            "CREDIT_CARD": "[CREDIT_CARD_NUMBER]",
            "DATE_TIME": "[DATE_TIME]",
            "LOCATION": "[LOCATION_NAME]",
            "URL": "[WEB_URL]",
            "IP_ADDRESS": "[IP_ADDRESS]",
            "IBAN_CODE": "[BANK_ACCOUNT]",
            "MEDICAL_LICENSE": "[MEDICAL_LICENSE]",
        }

        if entities:
            table_data = []
            for e in entities:
                original_value = input_text[e.start:e.end]
                replaced_with = replacement_tokens.get(e.entity_type, "[REDACTED_INFO]")
                table_data.append({
                    "Original Value": original_value,
                    "Entity Type": e.entity_type,
                    "Replaced With": replaced_with,
                })

            st.dataframe(
                table_data,
                use_container_width=True,
                column_config={
                    "Original Value": st.column_config.TextColumn("Original Value", width="large"),
                    "Entity Type": st.column_config.TextColumn("Entity Type", width="medium"),
                    "Replaced With": st.column_config.TextColumn("Replaced With", width="medium"),
                }
            )
        else:
            st.info("No PII entities detected in the provided text.")


if __name__ == "__main__":
    main()
