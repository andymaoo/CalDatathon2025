"""
Bill Processing Pipeline

Purpose: Extract text and structured parameters from bill PDFs
"""

import pdfplumber
import re
import spacy
import os
import json
from pathlib import Path
from typing import Dict, Optional, List, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.warning("spaCy model 'en_core_web_sm' not found. Install with: python -m spacy download en_core_web_sm")
    nlp = None


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from PDF using pdfplumber.
    
    Args:
        pdf_path: Path to PDF file
    
    Returns:
        Extracted text
    """
    try:
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        logger.info(f"Extracted {len(text)} characters from PDF")
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        return ""


def clean_bill_text(text: str) -> str:
    """
    Clean bill text: remove headers/footers, normalize whitespace, handle hyphenation.
    
    Args:
        text: Raw extracted text
    
    Returns:
        Cleaned text
    """
    # Remove page numbers and common headers/footers
    text = re.sub(r"Page \d+ of \d+", "", text)
    text = re.sub(r"Senate Bill \d+|House Bill \d+|Assembly Bill \d+", "", text)
    
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\n\s*\n", "\n", text)
    
    # Handle hyphenation across line breaks
    text = re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1\2", text)
    
    return text.strip()


def extract_money_amounts(text: str) -> List[float]:
    """
    Extract money amounts from text.
    
    Args:
        text: Bill text
    
    Returns:
        List of dollar amounts
    """
    # Pattern: $X, $X.X, $X million, $X billion
    pattern = r'\$[\d,]+(?:\.\d{2})?(?:\s*(?:million|billion|M|B))?'
    matches = re.findall(pattern, text, re.IGNORECASE)
    
    amounts = []
    for match in matches:
        # Remove $ and commas
        amount_str = match.replace("$", "").replace(",", "").strip()
        
        # Handle millions/billions
        multiplier = 1
        if "million" in match.lower() or "M" in match:
            multiplier = 1_000_000
        elif "billion" in match.lower() or "B" in match:
            multiplier = 1_000_000_000
        
        try:
            amount = float(re.sub(r'[^\d.]', '', amount_str)) * multiplier
            amounts.append(amount)
        except ValueError:
            continue
    
    return amounts


def extract_percentages(text: str) -> List[float]:
    """
    Extract percentages from text.
    
    Args:
        text: Bill text
    
    Returns:
        List of percentage values
    """
    # Pattern: X%, X percent, X percentage points
    pattern = r'(\d+(?:\.\d+)?)\s*(?:percent|%|percentage points?)'
    matches = re.findall(pattern, text, re.IGNORECASE)
    
    percentages = []
    for match in matches:
        try:
            pct = float(match)
            percentages.append(pct)
        except ValueError:
            continue
    
    return percentages


def extract_funding_changes(text: str) -> Optional[float]:
    """
    Extract funding change percentage from context around "funding" keywords.
    
    Args:
        text: Bill text
    
    Returns:
        Funding change percentage, or None
    """
    # Look for context around "funding"
    funding_pattern = r'(?:funding|appropriation|budget|allocation).{0,100}(?:cut|reduce|decrease|increase|boost|raise|add)'
    matches = re.findall(funding_pattern, text, re.IGNORECASE)
    
    for match in matches:
        # Look for percentages in the context
        percentages = extract_percentages(match)
        if percentages:
            # Check for negative keywords
            if any(word in match.lower() for word in ["cut", "reduce", "decrease", "reduction"]):
                return -abs(percentages[0])
            elif any(word in match.lower() for word in ["increase", "boost", "raise", "add"]):
                return abs(percentages[0])
    
    return None


def extract_institution_types(text: str) -> List[str]:
    """
    Extract affected institution types from keywords.
    
    Args:
        text: Bill text
    
    Returns:
        List of institution types
    """
    types = []
    text_lower = text.lower()
    
    if any(keyword in text_lower for keyword in ["public university", "public college", "state university"]):
        types.append("public")
    if any(keyword in text_lower for keyword in ["private university", "private college", "private institution"]):
        types.append("private")
    if any(keyword in text_lower for keyword in ["community college", "community colleges"]):
        types.append("community")
    
    # If no specific types found, assume all
    if not types:
        types = ["public", "private", "community"]
    
    return types


def extract_with_spacy(text: str) -> Dict:
    """
    Use spaCy NER to extract entities.
    
    Args:
        text: Bill text
    
    Returns:
        Dict with extracted entities
    """
    if nlp is None:
        return {}
    
    doc = nlp(text[:10000])  # Limit to first 10k chars for speed
    
    entities = {
        "money": [],
        "percent": [],
        "orgs": [],
        "states": []
    }
    
    for ent in doc.ents:
        if ent.label_ == "MONEY":
            entities["money"].append(ent.text)
        elif ent.label_ == "PERCENT":
            entities["percent"].append(ent.text)
        elif ent.label_ == "ORG":
            entities["orgs"].append(ent.text)
        elif ent.label_ == "GPE":  # Geopolitical entity (states)
            entities["states"].append(ent.text)
    
    return entities


def rule_based_extraction(text: str) -> Tuple[Dict, float]:
    """
    Fast, deterministic extraction using regex + spaCy.
    
    Args:
        text: Bill text
    
    Returns:
        Tuple of (params dict, confidence score)
    """
    params = {
        "funding_change_pct": None,
        "min_wage_change": None,
        "childcare_subsidy": None,
        "tuition_cap_pct": None,
        "affected_types": [],
        "confidence_score": 0.0
    }
    
    # Extract funding changes
    funding_change = extract_funding_changes(text)
    if funding_change is not None:
        params["funding_change_pct"] = funding_change
    
    # Extract minimum wage changes
    wage_pattern = r'(?:minimum wage|min wage|wage).{0,100}(?:increase|raise|to|set to|change to)'
    wage_matches = re.findall(wage_pattern, text, re.IGNORECASE)
    for match in wage_matches:
        amounts = extract_money_amounts(match)
        if amounts:
            params["min_wage_change"] = amounts[0]
            break
    
    # Extract childcare subsidies
    childcare_pattern = r'(?:childcare|child care|child-care).{0,100}(?:subsidy|grant|assistance|support)'
    childcare_matches = re.findall(childcare_pattern, text, re.IGNORECASE)
    for match in childcare_matches:
        amounts = extract_money_amounts(match)
        if amounts:
            params["childcare_subsidy"] = amounts[0]
            break
    
    # Extract tuition caps
    tuition_pattern = r'(?:tuition cap|tuition limit|tuition increase limit)'
    if re.search(tuition_pattern, text, re.IGNORECASE):
        percentages = extract_percentages(text)
        if percentages:
            params["tuition_cap_pct"] = percentages[0]
    
    # Extract institution types
    params["affected_types"] = extract_institution_types(text)
    
    # Calculate confidence score
    confidence = 0.0
    if params["funding_change_pct"] is not None:
        confidence += 30
    if params["min_wage_change"] is not None:
        confidence += 20
    if params["childcare_subsidy"] is not None:
        confidence += 20
    if params["tuition_cap_pct"] is not None:
        confidence += 10
    if params["affected_types"]:
        confidence += 20
    
    params["confidence_score"] = min(100, confidence)
    
    return params, params["confidence_score"]


def llm_fallback_extraction(text: str, api_key: Optional[str] = None) -> Optional[Dict]:
    """
    Handle complex/ambiguous bills using Claude API.
    
    Args:
        text: Bill text (first 2000 chars)
        api_key: Anthropic API key
    
    Returns:
        Enhanced params dict, or None if unavailable
    """
    if api_key is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        logger.warning("Anthropic API key not found. LLM extraction unavailable.")
        return None
    
    try:
        from anthropic import Anthropic
        
        client = Anthropic(api_key=api_key)
        
        # Use first 2000 chars
        text_sample = text[:2000]
        
        prompt = f"""Extract policy parameters from this education bill text. Return ONLY valid JSON with these keys:
- funding_change_pct: float (percentage change, negative for cuts)
- min_wage_change: float (dollar change)
- childcare_subsidy: float (dollar amount)
- tuition_cap_pct: float (percentage cap)
- affected_types: list of strings (["public", "private", "community"])

Example output:
{{"funding_change_pct": -10.0, "min_wage_change": 2.0, "childcare_subsidy": 3000.0, "tuition_cap_pct": 5.0, "affected_types": ["public", "community"]}}

Bill text:
{text_sample}

Return ONLY the JSON object, no markdown, no explanations:"""

        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Extract JSON from response
        response_text = response.content[0].text.strip()
        
        # Remove markdown code blocks if present
        response_text = re.sub(r'```json\s*', '', response_text)
        response_text = re.sub(r'```\s*', '', response_text)
        
        params = json.loads(response_text)
        logger.info("LLM extraction successful")
        return params
        
    except Exception as e:
        logger.error(f"LLM extraction failed: {e}")
        return None


def process_bill(
    pdf_path: str,
    use_llm_fallback: bool = True,
    confidence_threshold: float = 60.0
) -> Dict:
    """
    Main function to process a bill PDF and extract parameters.
    
    Args:
        pdf_path: Path to bill PDF
        use_llm_fallback: Whether to use LLM if confidence is low
        confidence_threshold: Minimum confidence to skip LLM fallback
    
    Returns:
        Dict with extracted parameters
    """
    logger.info(f"Processing bill: {pdf_path}")
    
    # Extract text
    text = extract_text_from_pdf(pdf_path)
    if not text:
        logger.error("Failed to extract text from PDF")
        return {}
    
    # Clean text
    text = clean_bill_text(text)
    
    # Rule-based extraction
    params, confidence = rule_based_extraction(text)
    
    logger.info(f"Rule-based extraction confidence: {confidence}%")
    
    # LLM fallback if confidence is low
    if use_llm_fallback and confidence < confidence_threshold:
        logger.info("Confidence low, attempting LLM extraction...")
        llm_params = llm_fallback_extraction(text)
        
        if llm_params:
            # Merge LLM results (LLM takes precedence)
            for key, value in llm_params.items():
                if value is not None and value != []:
                    params[key] = value
            params["confidence_score"] = 85.0  # Higher confidence after LLM
            logger.info("LLM extraction completed")
    
    # Add metadata
    params["bill_text_sample"] = text[:500]  # First 500 chars for summaries
    params["extraction_method"] = "llm" if use_llm_fallback and confidence < confidence_threshold else "rule_based"
    
    logger.info(f"Extraction complete. Parameters: {params}")
    return params


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        params = process_bill(pdf_path)
        print(json.dumps(params, indent=2))

