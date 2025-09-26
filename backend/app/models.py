from pydantic import BaseModel
from typing import Optional, Dict, Any

class Article(BaseModel):
    title: str
    url: str
    source: str
    summary: str
    bias_analysis: Optional[Dict[str, Any]] = None

class BiasAnalysis(BaseModel):
    bias_score: float
    bias_category: str
    confidence: float
    details: Dict[str, Any]

class BalancedDietRequest(BaseModel):
    target_balance: Optional[Dict[str, int]] = None
    category: Optional[str] = "all"
