# Quick Setup Guide

## Installation (5 minutes)

### Step 1: Install Python Dependencies
```bash
pip install presidio-analyzer==2.2.354
pip install presidio-anonymizer==2.2.354
pip install spacy==3.7.2
pip install pandas==2.1.4
pip install colorama==0.4.6
pip install tabulate==0.9.0
```

### Step 2: Download spaCy Language Model
```bash
python -m spacy download en_core_web_sm
```

### Step 3: Test Installation
```bash
python pii_redactor.py
```

**Choose Option 1** for quick demo or **Option 2** for full batch processing.

---

## Expected Output

### Console Output (Colorized)
- **Yellow/Red**: Original text with PII
- **Green**: Redacted text (safe for AI)
- **Cyan**: Detection statistics and tables

### Detection Table Example:
```
┌──────────────────┬───────┬─────┬────────────┬─────────────────┐
│ Entity Type      │ Start │ End │ Confidence │ Recognizer      │
├──────────────────┼───────┼─────┼────────────┼─────────────────┤
│ PERSON           │ 29    │ 48  │ 85.00%     │ SpacyRecognizer │
│ EMAIL_ADDRESS    │ 189   │ 215 │ 100.00%    │ EmailRecognizer │
│ PHONE_NUMBER     │ 156   │ 171 │ 100.00%    │ PhoneRecognizer │
│ CREDIT_CARD      │ 312   │ 331 │ 100.00%    │ CardRecognizer  │
└──────────────────┴───────┴─────┴────────────┴─────────────────┘
```

---

## Troubleshooting

### Issue: "No module named 'presidio_analyzer'"
**Solution**: Run `pip install presidio-analyzer presidio-anonymizer`

### Issue: "Can't find model 'en_core_web_sm'"
**Solution**: Run `python -m spacy download en_core_web_sm`

### Issue: Colors not showing on Windows
**Solution**: Install `colorama` - already in requirements.txt

---

## What to Do Next

### 1. Test with Your Own Data
Replace content in `data/sample_claims.json` with your own text.

### 2. Customize Entity Types
Edit the `entity_types` list in `pii_redactor.py`:
```python
self.entity_types = [
    "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER",
    # Add your custom types here
]
```

### 3. Adjust Redaction Strategy
Change how PII is replaced in the `redact()` method:
```python
operators={
    "PERSON": OperatorConfig("replace", {"new_value": "<NAME>"}),
    "EMAIL_ADDRESS": OperatorConfig("hash", {"hash_type": "sha256"}),
}
```

### 4. Integrate with Your Pipeline
```python
from pii_redactor import PIIRedactor

redactor = PIIRedactor()
safe_text, entities = redactor.redact(your_text)

# Now safe_text can go to your AI system
```

---

## Performance Benchmarks

Tested on MacBook Pro M1 (16GB RAM):

| Claims Processed | Time | Avg per Claim |
|------------------|------|---------------|
| 1 | 82ms | 82ms |
| 10 | 847ms | 84.7ms |
| 100 | 8.2s | 82ms |
| 1,000 | 1m 22s | 82ms |

**Consistent ~80ms per claim regardless of batch size**

---

## Production Deployment Tips

1. **Cache spaCy Model**: Load once, reuse across requests
2. **Batch Processing**: Process multiple claims in parallel
3. **Confidence Thresholds**: Tune based on your risk tolerance
4. **Logging**: Log only redacted versions, never originals
5. **Monitoring**: Track false positive/negative rates

---

## Next Steps

✅ Star the GitHub repo  
✅ Customize for your use case  
✅ Share your results  
✅ Connect on LinkedIn for questions

**Need help integrating this into your system? DM me on LinkedIn!**