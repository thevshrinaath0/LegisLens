import pandas as pd
import random

class RiskCalculator:
    def __init__(self):
        # Keywords that suggest high risk in specific categories
        self.risk_indicators = {
            "Financial": ["penalty", "indemnify", "liquidated damages", "reimburse", "fine", "cost", "jurmana", "harjana", "shulk", "vool"],
            "Legal": ["jurisdiction", "arbitration", "litigation", "court", "lawsuit", "dispute", "nyayalaya", "vivad", "madhyasthata", "kanooni"],
            "Operational": ["exclusive", "non-compete", "restrict", "prohibit", "consent required", "pratibandh", "anumati", "rok"],
            "Compliance": ["audit", "regulation", "gdpr", "statutory", "license", "niyam", "vidhan", "anupalan"],
            "Termination": ["terminate", "cause", "notice period", "immediate effect", "samapt", "notis"]
        }

    def calculate_risk_scores(self, text, llm_response=None):
        """
        Generates scores for the radar chart.
        Hybrid Approach: 
        1. Base usage on Keywords (fast, reliable baseline).
        2. Semantic Boost: If LLM identifies specific risks in clauses, boost those categories.
           This ensures the Graph matches the Text Analysis, even for Hindi documents.
        """
        text_lower = text.lower()
        scores = {}
        
        # 1. Keyword Baseline
        for category, keywords in self.risk_indicators.items():
            count = sum(text_lower.count(kw) for kw in keywords)
            # Normalize: Reduce multiplier to 5 to avoid false positives in long docs
            # CAP at 50 (Medium) so that only LLM can push it to High Risk (Red)
            score = min(count * 5, 50) 
            if score == 0:
                score = random.randint(5, 20) # Lower baseline noise
            scores[category] = score
            
        # 2. LLM Semantic Override (The "Smart" Layer)
        if llm_response and isinstance(llm_response, dict) and "clauses" in llm_response:
            for clause in llm_response["clauses"]:
                c_type = clause.get("type", "").lower()
                c_risk = clause.get("risk_level", "Low").lower()
                
                # Map clause types to categories
                cat_map = {
                    "indemnity": "Financial",
                    "penalty": "Financial",
                    "jurisdiction": "Legal",
                    "arbitration": "Legal",
                    "litigation": "Legal",
                    "termination": "Termination",
                    "non-compete": "Operational",
                    "ip": "Operational",
                    "audit": "Compliance"
                }
                
                # Find which category this clause belongs to
                target_cat = next((v for k, v in cat_map.items() if k in c_type), None)
                
                if target_cat and target_cat in scores:
                    # Boost score if risk is High/Medium
                    if c_risk == "high":
                        scores[target_cat] = max(scores[target_cat], 85)
                    elif c_risk == "medium":
                        scores[target_cat] = max(scores[target_cat], 60)

        # 3. GLOBAL SYNC (The "Silver Bullet" for Consistency)
        # If the LLM gives a Global Risk Score (e.g., 85), the Graph MUST reflect that overall intensity.
        # We scale the category scores so their weighted impact matches the LLM's verdict.
        if llm_response and "risk_score" in llm_response:
            target_global = llm_response["risk_score"]
            current_max = max(scores.values()) if scores.values() else 1
            
            # If the Graph looks "Safe" (e.g. 40) but AI says "High Risk" (e.g. 85)
            # We explicitly boost the highest risk categories to match the target.
            if target_global > current_max:
                diff = target_global - current_max
                for k, v in scores.items():
                    # Boost proportional to existing risk to keep the "shape" of the radar
                    # But ensure at least one category hits the target risk level
                    if v == current_max:
                        scores[k] = target_global
                    elif v > 30:
                        scores[k] = min(v + diff, target_global)
        
        return scores

    def get_radar_data(self, scores):
        """Returns a DataFrame suitable for Plotly Radar Chart."""
        df = pd.DataFrame(dict(
            r=list(scores.values()),
            theta=list(scores.keys())
        ))
        return df
