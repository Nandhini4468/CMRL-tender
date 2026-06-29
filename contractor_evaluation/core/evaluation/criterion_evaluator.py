import json
import re
import time
from typing import List, Dict, Optional, Callable
import pandas as pd
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from core.rag.retriever import BidderRetriever


SCORING_SYSTEM = """You are an expert procurement evaluator.
Score the bidder against the given evaluation criterion using ONLY the retrieved document evidence.

Respond with a valid JSON object only. No markdown. No extra text.
Keys:
- awarded_score: numeric score awarded (must not exceed maximum_score)
- evidence_text: exact quote from retrieved documents supporting the score (empty string if none)
- source_file: filename where evidence was found (empty string if none)
- page: page number as integer (0 if unknown)
- reasoning: brief explanation of how you determined the score
- evidence_found: true if supporting evidence was found, false otherwise
- retrieval_confidence: integer 0-100 (how well the retrieved text matched the query)
- evaluation_confidence: integer 0-100 (how confident you are in the score you assigned)

STRICT RULES:
- awarded_score MUST be 0 if no evidence is found
- Never invent evidence
- Never award more than maximum_score
- Apply scoring_rules exactly as specified
- If partial scoring applies, use the exact ranges/conditions given
"""


def evaluate_criterion(
    bidder_name: str,
    criterion: pd.Series,
    retriever: BidderRetriever,
    groq_api_key: str,
    model: str,
    on_rate_limit: Optional[Callable[[str], None]] = None,
) -> Dict:
    """Evaluate a single criterion for a single bidder."""
    llm = ChatGroq(api_key=groq_api_key, model_name=model, temperature=0)

    query = f"{criterion.get('criterion_description', '')} {criterion.get('supporting_evidence', '')}"
    chunks = retriever.retrieve(query, n_results=6)
    context = _format_context(chunks)

    avg_retrieval_sim = (
        sum(c["similarity"] for c in chunks) / len(chunks) if chunks else 0.0
    )

    user_msg = (
        f"CRITERION ID: {criterion.get('criteria_id', '')}\n"
        f"CRITERION DESCRIPTION: {criterion.get('criterion_description', '')}\n"
        f"MAXIMUM SCORE: {criterion.get('maximum_score', 0)}\n"
        f"SCORING RULES: {criterion.get('scoring_rules', 'Binary: full score if met, 0 if not')}\n"
        f"REQUIRED EVIDENCE: {criterion.get('supporting_evidence', '')}\n\n"
        f"RETRIEVED EVIDENCE FROM BIDDER DOCUMENTS:\n{context}"
    )

    result = _call_llm(llm, SCORING_SYSTEM, user_msg, on_rate_limit=on_rate_limit)
    result["criteria_id"] = criterion.get("criteria_id", "")
    result["criterion_description"] = criterion.get("criterion_description", "")
    result["maximum_score"] = criterion.get("maximum_score", 0)
    result["bidder"] = bidder_name
    result["avg_retrieval_similarity"] = round(avg_retrieval_sim, 2)

    # Enforce score limits
    max_score = float(criterion.get("maximum_score", 0))
    awarded = float(result.get("awarded_score", 0))
    result["awarded_score"] = min(awarded, max_score)

    if not result.get("evidence_found", False):
        result["awarded_score"] = 0
        result["evidence_text"] = ""

    return result


def evaluate_all_criteria(
    bidder_name: str,
    evaluation_df: pd.DataFrame,
    retriever: BidderRetriever,
    groq_api_key: str,
    model: str,
    on_rate_limit: Optional[Callable[[str], None]] = None,
) -> List[Dict]:
    """Evaluate all approved criteria for one bidder."""
    results = []
    for i, (_, criterion) in enumerate(evaluation_df.iterrows()):
        if i > 0:
            time.sleep(2)  # proactive pacing to stay under Groq free-tier rate limits
        result = evaluate_criterion(bidder_name, criterion, retriever, groq_api_key, model, on_rate_limit=on_rate_limit)
        results.append(result)
    return results


def _format_context(chunks: List[Dict]) -> str:
    if not chunks:
        return "No relevant evidence retrieved from bidder documents."
    parts = []
    for c in chunks:
        parts.append(
            f"[File: {c['source_file']}, Page: {c['page']}, Similarity: {c['similarity']}%]\n{c['text']}"
        )
    return "\n\n---\n\n".join(parts)


def _call_llm(
    llm: ChatGroq,
    system: str,
    user: str,
    on_rate_limit: Optional[Callable[[str], None]] = None,
) -> Dict:
    default = {
        "awarded_score": 0, "evidence_text": "", "source_file": "",
        "page": 0, "reasoning": "LLM error", "evidence_found": False,
        "retrieval_confidence": 0, "evaluation_confidence": 0,
    }
    max_retries = 6
    for attempt in range(max_retries):
        try:
            messages = [SystemMessage(content=system), HumanMessage(content=user)]
            response = llm.invoke(messages)
            raw = response.content.strip()
            raw = re.sub(r"```(?:json)?", "", raw).replace("```", "").strip()
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            return default
        except Exception as e:
            err = str(e)
            is_rate_limit = (
                "429" in err
                or "rate_limit" in err.lower()
                or "rate limit" in err.lower()
                or "too many requests" in err.lower()
            )
            if is_rate_limit and attempt < max_retries - 1:
                wait_match = re.search(r"try again in (\d+(?:\.\d+)?)s", err, re.IGNORECASE)
                wait_secs = float(wait_match.group(1)) + 3 if wait_match else min(30 * (attempt + 1), 120)
                msg = f"Groq rate limit hit — waiting {wait_secs:.0f}s before retry (attempt {attempt + 1}/{max_retries - 1})..."
                if on_rate_limit:
                    on_rate_limit(msg)
                else:
                    print(msg)
                time.sleep(wait_secs)
                continue
            break
    return default
