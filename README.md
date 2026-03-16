# Children's Story Generation Pipeline - User Guide

A multi-stage LLM pipeline that generates culturally authentic English stories for Indian children (Grades 3-6) using Google's Gemini API. Built for Stanford's GC Lab ESL curriculum integration.

## How It Works

The pipeline generates stories through 5 stages:

```
Input (location, culture, grade)
  → Outline Generation (2 API calls)
  → Human Review (approve/edit/reject the outline)
  → Story Generation (2 versions at different temperatures)
  → Critique (LLM-as-Judge scores each version)
  → Revision (applies critique feedback)
  → Safety Check + Readability Scoring
  → Best story selected and saved
```

Total: **9 API calls per story**

---

## Initial Setup

### 1. Prerequisites

- Python 3.10 or higher
- A Google AI Studio account (free)

### 2. Clone the Repository

```bash
git clone https://github.com/kothari1/Story-Pipeline-v2.git
cd Story-Pipeline-v2
```

### 3. Install Dependencies

```bash
pip install -e ".[dev]"
```

### 4. Get a Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Click **Create API Key**
3. Copy the key

### 5. Set Up Your API Key

```bash
cp .env.example .env
```

Open `.env` and paste your key:

```
GOOGLE_API_KEY=your_key_here
```

### 6. Verify Installation

```bash
pytest tests/ -k "not slow"
```

All 23 tests should pass.

---

## Usage

### Basic Command

```bash
python -m src.cli.app generate \
    --location "a village near Satara, in the state of Maharashtra" \
    --culture "Marathi speaking community, with major occupation being farming" \
    --grade 4 \
    --fast
```

### Command Options

| Flag | Required | Description |
|------|----------|-------------|
| `--location` | Yes (new run) | Where the story is set |
| `--culture` | Yes (new run) | Cultural context for authentic details |
| `--grade` | No (default: 4) | Target grade level: 3, 4, 5, or 6 |
| `--fast` | No | Use Flash for all stages (recommended on free tier) |
| `--no-review` | No | Skip the outline review step |
| `--resume RUN_ID` | No | Resume a crashed/interrupted run |
| `--config-dir` | No | Path to config directory (default: `config/`) |
| `--log-level` | No | Logging level: DEBUG, INFO, WARNING (default: INFO) |

### During the Outline Review

After the outline is generated, you'll see it displayed with characters, cultural elements, and plot. You have three options:

- **`a`** - Approve the outline and continue
- **`e`** - Edit the outline (opens JSON in your default `$EDITOR`)
- **`r`** - Reject and regenerate (uses 2 more API calls)

### Resuming a Crashed Run

If the pipeline crashes mid-run (e.g., due to rate limits), you can resume:

```bash
# Find your run ID
ls output/

# Resume from where it stopped
python -m src.cli.app generate --fast --resume 20260315_173702_335dec6c
```

The pipeline detects which stages are already complete and skips them.

---

## Free Tier Rate Limits

The Gemini free tier has strict limits:

| Model | Requests/Minute | Requests/Day |
|-------|-----------------|--------------|
| Gemini 2.5 Flash | 5 | 20 |
| Gemini 2.5 Pro | 0 | 0 (often unavailable) |

**What this means:**
- You can generate **~2 stories per day** on the free tier
- Always use `--fast` flag (it uses Flash for everything)
- If you hit a rate limit, the pipeline retries automatically (waits ~30-60s)
- If all retries fail, use `--resume` to pick up later

To check your current usage: [Google AI Studio Rate Limits](https://ai.dev/rate-limit)

### Updating Rate Limits

If your account has different limits (e.g., paid tier), edit `config/models.yaml`:

```yaml
models:
  flash:
    rpm: 5      # Change to your RPM limit
    rpd: 20     # Change to your RPD limit
```

---

## Output Structure

Each run creates a timestamped directory under `output/`:

```
output/20260315_173702_335dec6c/
├── outline.json              # Raw generated outline
├── outline_approved.json     # Outline after human review
├── versions/
│   ├── story_v1.json         # Story version 1 (temp=0.7)
│   └── story_v2.json         # Story version 2 (temp=0.9)
├── critiques/
│   ├── critique_v1.json      # Critique for version 1
│   └── critique_v2.json      # Critique for version 2
├── revised/
│   ├── story_v1_revised.json # Revised version 1
│   └── story_v2_revised.json # Revised version 2
├── safety/
│   └── safety_report.json    # Safety check results
└── final/
    └── story_final.json      # Best story (final output)
```

### Reading the Final Story

The final story JSON contains:

```json
{
  "title": "The Village Kitten",
  "sections": [
    {"heading": "Beginning", "content": "..."},
    {"heading": "Middle", "content": "..."},
    {"heading": "End", "content": "..."}
  ],
  "characters": [{"name": "Meera", "role": "protagonist"}],
  "vocabulary_words": [
    {"word": "determined", "context_sentence": "...", "simple_definition": "..."}
  ],
  "word_count": 650,
  "moral_lesson": "Kindness spreads to everyone around"
}
```

---

## Configuration

### Prompt Templates (`config/prompts_v1.yaml`)

All LLM prompts are versioned in YAML. To experiment with different prompts:

1. Copy `prompts_v1.yaml` to `prompts_v2.yaml`
2. Edit your new prompts
3. Update `prompt_version` in `config/pipeline.yaml`:
   ```yaml
   prompt_version: v2
   ```

### Pipeline Settings (`config/pipeline.yaml`)

```yaml
generation:
  num_versions: 2           # Number of story versions to generate
  temperatures: [0.7, 0.9]  # Temperature for each version
  word_count_min: 500
  word_count_max: 800
```

---

## Example Inputs

Here are some location/culture combinations to try:

```bash
# Coastal Karnataka fishing village
--location "a village near Mangalore in coastal Karnataka"
--culture "Tulu-speaking fishing community"

# Punjab farming community
--location "a village near Amritsar in Punjab"
--culture "Punjabi-speaking farming community, wheat and mustard cultivation"

# Kerala backwaters
--location "a village near Alleppey in Kerala"
--culture "Malayalam-speaking community, houseboat tourism and coir-making"

# Rajasthan desert town
--location "a small town near Jaisalmer in Rajasthan"
--culture "Rajasthani community, camel herding and folk music traditions"
```

---

## Running Tests

```bash
# Unit tests (no API key needed)
pytest tests/ -k "not slow"

# Integration test (needs API key, uses real API calls)
pytest tests/test_integration.py -m slow
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `GOOGLE_API_KEY not set` | Create `.env` file with your API key |
| `429 RESOURCE_EXHAUSTED` | You've hit the daily limit. Wait for reset or resume tomorrow with `--resume` |
| `ValidationError` on model response | The LLM returned unexpected JSON structure. Try running again — responses vary |
| Pipeline hangs at "Choice (a, e, r)" | Type `a` then press Enter to approve the outline |
| `ModuleNotFoundError` | Run `pip install -e ".[dev]"` from the project root |
