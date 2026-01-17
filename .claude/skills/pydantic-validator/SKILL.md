---
name: pydantic-validator
description: Intelligence layer - ensures all AI agent outputs are structured and validated. Use when defining AI agent prompts or output schemas.
---

# Pydantic Validation Standards (The Intelligence Layer)

This skill governs the "Analyst" loop, ensuring that AI Agent outputs are always structured, valid, and actionable.

## Trigger
Automatically applies when:
- Defining AI agent prompts or system messages
- Creating output schemas for LLM responses
- Working on `backend/app/agents/` or `backend/app/schemas/`

## Rules

### 1. Mandatory Pydantic Validation
- Every LLM response MUST be validated against a Pydantic V2 model
- NEVER accept raw string outputs from AI agents
- Use structured output extraction (PydanticAI, Instructor, or similar)

### 2. Rich Field Descriptions
- Use `Field(description=...)` for EVERY attribute
- Descriptions guide the LLM to produce better outputs
- Example:
  ```python
  from pydantic import BaseModel, Field

  class InsightAnalysis(BaseModel):
      insight_text: str = Field(
          description="Core insight extracted from the content, 1-2 sentences"
      )
      market_fit_score: int = Field(
          ge=1, le=10,
          description="Market fit score from 1-10, where 10 = perfect PMF signal"
      )
      confidence: float = Field(
          ge=0.0, le=1.0,
          description="Confidence level in this analysis (0.0 to 1.0)"
      )
  ```

### 3. Required Insight Schema Fields
Every `Insight` schema must include:
- `market_fit_score` (int, 1-10): Quantified market fit signal
- `source_attribution` (list): URLs or references backing the insight
- `confidence` (float, 0-1): AI confidence in the analysis
- `category` (str): Classification (e.g., "pain_point", "solution", "trend")

Example:
```python
from pydantic import BaseModel, Field, HttpUrl
from typing import Literal

class Insight(BaseModel):
    insight_text: str = Field(
        description="The core insight, clearly stated"
    )
    market_fit_score: int = Field(
        ge=1, le=10,
        description="Market fit score: 1=weak signal, 10=strong PMF indicator"
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="AI confidence in this insight (0.0 to 1.0)"
    )
    category: Literal["pain_point", "solution", "trend", "opportunity", "risk"] = Field(
        description="Classification of the insight type"
    )
    source_attribution: list[HttpUrl] = Field(
        description="URLs or sources supporting this insight"
    )
    reasoning: str = Field(
        description="Brief explanation of why this insight matters"
    )
```

### 4. Validation Before Database Storage
- Always validate LLM output BEFORE saving to database
- Use `model.model_validate()` for Pydantic V2
- Example:
  ```python
  async def process_llm_response(raw_response: dict) -> Insight:
      try:
          validated_insight = Insight.model_validate(raw_response)
          # Now safe to store in database
          return validated_insight
      except ValidationError as e:
          logger.error(f"LLM output validation failed: {e}")
          raise
  ```

### 5. Constrained Generation
- Use Pydantic's validators and constraints to guide LLM behavior
- Example constraints:
  - `ge`, `le` for numeric ranges
  - `min_length`, `max_length` for strings
  - `Literal` for enum-like fields
  - `conlist` for list length constraints

## Standard AI Agent Output Template

```python
from pydantic import BaseModel, Field, HttpUrl, field_validator
from typing import Literal
from datetime import datetime

class AgentInsight(BaseModel):
    """Standard schema for all AI agent insights."""

    insight_text: str = Field(
        min_length=10,
        max_length=500,
        description="Core insight in 1-3 sentences"
    )

    market_fit_score: int = Field(
        ge=1, le=10,
        description="Market fit score: 1=weak, 10=strong PMF signal"
    )

    confidence: float = Field(
        ge=0.0, le=1.0,
        description="AI confidence in this analysis"
    )

    category: Literal[
        "pain_point",
        "solution",
        "trend",
        "opportunity",
        "risk",
        "user_feedback"
    ] = Field(description="Insight classification")

    source_attribution: list[HttpUrl] = Field(
        min_length=1,
        description="URLs or references backing this insight"
    )

    reasoning: str = Field(
        min_length=20,
        description="Why this insight matters for product decisions"
    )

    extracted_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of extraction"
    )

    @field_validator('insight_text')
    @classmethod
    def validate_insight_quality(cls, v: str) -> str:
        """Ensure insight is not generic."""
        generic_phrases = ['interesting', 'important', 'useful']
        if any(phrase in v.lower() for phrase in generic_phrases):
            raise ValueError("Insight too generic - be specific")
        return v
```

## Integration with PydanticAI

```python
from pydantic_ai import Agent
from pydantic import BaseModel

# Define structured output
class StartupAnalysis(BaseModel):
    market_fit_score: int = Field(ge=1, le=10)
    key_insights: list[str]
    confidence: float = Field(ge=0.0, le=1.0)

# Create agent with structured output
agent = Agent(
    model='claude-3-5-sonnet-20241022',
    result_type=StartupAnalysis,
    system_prompt="You are an expert startup analyst..."
)

# Agent automatically validates output
result = await agent.run("Analyze this startup...")
validated_output: StartupAnalysis = result.data
```

## Anti-Patterns to Avoid
- ❌ Accepting raw string outputs from LLMs
- ❌ Missing `Field(description=...)` annotations
- ❌ No `market_fit_score` in insight schemas
- ❌ No `source_attribution` for claims
- ❌ Using Pydantic V1 syntax (`from_orm` instead of `model_validate`)

## Checklist
Before committing AI agent code, verify:
- [ ] All LLM outputs use Pydantic V2 models
- [ ] Every field has a `Field(description=...)`
- [ ] Insight schema includes `market_fit_score` and `source_attribution`
- [ ] Validation happens before database storage
- [ ] Uses `model_validate()` (not `from_orm`)
- [ ] Includes custom validators where needed
