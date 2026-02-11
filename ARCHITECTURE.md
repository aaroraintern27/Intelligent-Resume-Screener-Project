# Architecture & Code Organization

## File Structure (Industry Standard)

```
├── config.py           # Environment configuration
├── resume_parser.py    # Document parsing layer
├── ai_service.py       # AI business logic
├── app.py              # Presentation layer (Streamlit UI)
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
├── style.css           # UI styling
├── SETUP.md            # Setup instructions
└── ARCHITECTURE.md     # This file
```

---

## Design Principles Applied

### 1. Separation of Concerns
Each module has a **single, clear responsibility**:

| Module | Responsibility | Why Separate? |
|--------|---------------|---------------|
| `config.py` | Environment configuration | Centralized settings, easy environment switching |
| `resume_parser.py` | Document text extraction | Pure data transformation, no business logic |
| `ai_service.py` | AI prompts + API calls | Business logic for AI inference |
| `app.py` | User interface | Presentation separated from logic |

### 2. Tight Coupling Where Appropriate
**Prompts and AI calls are in the same module** (`ai_service.py`) because:
- They serve the same business purpose (AI inference)
- The prompt is required to make the API call
- Separating them would create unnecessary dependencies
- This follows patterns in LangChain, Haystack, and other AI frameworks

### 3. No Mock/Test Data in Production Code
- All mock responses removed
- Fail-fast approach: raise clear errors if API keys missing
- Follows production-readiness best practices

---

## Module Details

### config.py
**Purpose:** Centralized environment configuration

**Contents:**
- Load `.env` file
- Define AI provider settings (Groq/Gemini)
- Export configuration constants

**Pattern:** Configuration module (12-factor app principle)

```python
# Other modules import from here
from config import AI_PROVIDER, GROQ_API_KEY, GROQ_MODEL
```

---

### resume_parser.py
**Purpose:** Document parsing and text extraction

**Responsibilities:**
- Extract text from PDF files
- Parallel processing for multiple files
- Return standardized JSON format: `{"R-001": "text...", "R-002": "text..."}`

**Pattern:** Data transformation layer (ETL pattern)

**Future additions:**
- DOCX parsing
- Error handling for corrupted files
- Text cleaning/normalization

---

### ai_service.py
**Purpose:** AI inference business logic

**Responsibilities:**
1. **Prompt Building:**
   - Compose three-layer prompt (system + context + query)
   - Add candidate separators with JSON identifiers
   - Enforce output schema instructions

2. **AI Client Calls:**
   - Route to appropriate provider (Groq/Gemini)
   - Handle API calls with proper error handling
   - Parse and return JSON responses

**Pattern:** Service layer (domain logic)

**Why prompts and API calls are together:**
- They're tightly coupled (prompt → API call)
- Same business purpose (AI inference)
- Avoids circular dependencies
- Industry standard (LangChain, Haystack, etc.)

---

### app.py
**Purpose:** User interface and presentation

**Responsibilities:**
- Render Streamlit UI
- Handle user interactions (upload, submit)
- Display progress messages
- Show results

**Pattern:** Presentation layer (MVC pattern)

**Flow:**
1. User uploads PDFs → sidebar
2. User enters JD → text area
3. User clicks "Final Submit" → triggers processing
4. Progress shown → below text area
5. Results displayed → JSON output

---

## Data Flow

```
┌─────────────┐
│   app.py    │  User uploads PDFs + enters JD
│  (UI Layer) │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ resume_parser.py│  Extracts text in parallel
│  (Data Layer)   │  Returns: {"R-001": "...", "R-002": "..."}
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  ai_service.py  │  Composes prompt (3-layer design)
│ (Business Logic)│
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  ai_service.py  │  Calls Groq/Gemini API
│  (API Client)   │  Returns: {"candidates": [...], "ranking": [...]}
└──────┬──────────┘
       │
       ▼
┌─────────────┐
│   app.py    │  Displays results in UI
│  (UI Layer) │
└─────────────┘
```

---

## Why This Structure?

### Industry Standards Followed

1. **12-Factor App**: Configuration in environment variables
2. **Separation of Concerns**: Each module has one job
3. **Dependency Inversion**: High-level modules don't depend on low-level details
4. **Single Responsibility Principle**: Each file has one reason to change
5. **Clean Architecture**: Layers depend inward (UI → Service → Data)

### Scalability Considerations

This structure supports future growth:

**Easy to add:**
- ✅ New document types (DOCX, TXT) → Add to `resume_parser.py`
- ✅ New AI providers (Claude, OpenAI) → Add to `ai_service.py`
- ✅ New UI pages (history, settings) → Add to `app.py`
- ✅ New environments (dev, staging, prod) → Update `config.py`

**Easy to test:**
- ✅ Unit test parsers independently
- ✅ Mock AI calls in tests
- ✅ Test UI without hitting APIs

---

## What We Didn't Split (and Why)

### Prompts + AI Calls (kept together in ai_service.py)
**Reason:** They're tightly coupled and serve the same purpose.

**Alternative (rejected):**
```
prompt_builder.py  → Build prompt
ai_client.py       → Call API
```
**Why rejected:**
- Creates artificial boundary
- Adds import complexity
- Over-engineering for this project size
- Goes against common AI framework patterns

---

## Comparison: Before vs After

### Before (Initial Attempt)
```
helper.py           # PDF parsing
config.py           # Configuration
prompt_builder.py   # Prompt building
ai_client.py        # AI API calls (EMPTY FILE - bug!)
app.py              # UI
```
**Issues:**
- 5 files for a medium-sized project (overkill)
- Empty file created by mistake
- Prompts separated from AI calls (artificial boundary)

### After (Current)
```
config.py           # Configuration
resume_parser.py    # PDF parsing (renamed from helper.py)
ai_service.py       # Prompts + AI calls (merged)
app.py              # UI
```
**Benefits:**
- 4 files, clear responsibilities
- No empty/unused files
- Logical grouping (prompts + AI calls together)
- Industry standard structure

---

## References & Best Practices

This architecture follows patterns from:

- **LangChain**: Services combine prompts + model calls
- **Haystack**: Pipelines group related AI operations
- **FastAPI**: Config separate, services cohesive
- **12-Factor App**: Configuration management
- **Clean Architecture**: Dependency rules

---

## Future Improvements

### Short-term
- [ ] Add DOCX parsing to `resume_parser.py`
- [ ] Add caching layer for repeated JD queries
- [ ] Add logging (structured logs)
- [ ] Add input validation (file size, text length limits)

### Long-term
- [ ] Database layer for history/audit logs
- [ ] Authentication/authorization (multi-user)
- [ ] API layer (REST/GraphQL) for programmatic access
- [ ] Background job queue for large batches
- [ ] Vector database for semantic search across past resumes

---

## Conclusion

**Question:** Should we split `ai_service.py`?

**Answer:** ✅ YES - but we did it strategically:
- Split out **config** (separate concern)
- Kept **prompts + AI calls** together (cohesive)
- Removed **mock code** (production-ready)
- Followed **industry standards** (proven patterns)

This structure is **clean, scalable, and maintainable** without being over-engineered.
