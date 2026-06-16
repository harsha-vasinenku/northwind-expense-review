# Eval Harness

## Setup

```bash
# From project root, with backend dependencies installed and server running:
cd backend
uvicorn app.main:app &   # start server in background

# Run eval against local server
python ../eval/harness.py --fixture ../eval/fixtures/expected_outcomes_sample.json

# Run against deployed URL
python ../eval/harness.py \
  --fixture ../eval/fixtures/expected_outcomes_sample.json \
  --base-url https://your-deployment.railway.app
```

## Fixture Format

```json
{
  "test_cases": [
    {
      "id": "tc_001",
      "type": "verdict",
      "submission_folder": "03_dinner_over_cap",
      "receipt_filename": "04_dinner_alinea.pdf",
      "expected": {
        "verdict": "flagged",
        "flags_should_include": ["over_meal_cap"],
        "cited_clause_should_contain": "meal",
        "confidence_min": 0.5
      }
    },
    {
      "id": "tc_oos_001",
      "type": "policy_qa_refusal",
      "question": "What is the CEO's salary?",
      "expected": { "should_refuse": true }
    }
  ]
}
```

## Test Case Types

- `verdict` — uploads a real receipt PDF, checks verdict/flags/citations
- `policy_qa_refusal` — verifies the Q&A correctly refuses out-of-scope questions
- `policy_qa_answer` — verifies the Q&A answers correctly with citations

## Metrics Output

```
Verdict Accuracy        5/5  (100%)
  - Correctly flagged:  2/2  (100%)
  - Correctly compliant: 3/3 (100%)

Citation Faithfulness   2/2  (100%)
Refusal Rate (OOS)      2/2  (100%)
Q&A Answer Quality      1/1  (100%)

Overall Score: 100.0%
```
