import os
import json
import anthropic
import spacy
import PyPDF2
import docx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
                
class NLPEngine:
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)
        else:
            self.client = None
            
        # Specific model requested for cost efficiency
        self.model = "claude-3-haiku-20240307" 
        
        # Load small spacy model for fast entity extraction without LLM tokens
        # Note: Model must be installed via requirements.txt for cloud deployment
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            # On cloud, if requirements failed, we can't download at runtime due to permissions.
            # Use a blank model as fallback to prevent crash, but entity extraction will be limited.
            self.nlp = spacy.blank("en")

    def extract_text(self, uploaded_file):
        """Extracts text from PDF, DOCX, or TXT files."""
        text = ""
        try:
            if uploaded_file.name.endswith('.pdf'):
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            elif uploaded_file.name.endswith('.docx'):
                doc = docx.Document(uploaded_file)
                for para in doc.paragraphs:
                    text += para.text + "\n"
            else:
                # Assume text file
                text = uploaded_file.read().decode("utf-8")
        except Exception as e:
            return f"Error reading file: {str(e)}"
        
        return text

    def analyze_clause_risks(self, contract_text):
        """
        Uses Claude 3 Haiku to analyze risks in the contract.
        Returns a JSON structure with risk assessment.
        """
        if not self.client:
            return {"error": "API Key missing"}

        system_prompt = """You are a high-end legal assistant for Indian SMEs. 
        Analyze the contract text for risks (Employment, Vendor, Lease, etc.).
        
        CRITICAL INSTRUCTIONS FOR MULTILINGUAL INPUTS:
        1. If the contract is in HINDI (or any non-English language), first internally translate the full concept to English.
        2. Apply the EXACT SAME strict risk criteria as you would for an English contract. 
           (e.g. "Jurmana" == "Penalty". If > 5%, it is HIGH RISK).
        3. Do NOT illustrate translation leniency. A risky clause is risky in any language.
        
        OUTPUT REQUIREMENTS:
        1. You MUST extract at least 5 distinct clauses.
        2. Map every clause to one of these STANDARD TYPES:
           ["Termination", "Indemnity", "Payment/Rent", "Penalty", "Jurisdiction", "Confidentiality", "Non-Compete", "Notice Period", "Liability", "Force Majeure"].
           If a clause in Hindi is "Kiraya", map it to "Payment/Rent".
        3. Even if the contract is safe, list the key clauses with "Low" risk. DO NOT return an empty list.
        4. For Employment Agreements, specifically look for "Bond/Training Cost", "Notice Period", and "Non-Compete".
        
        RISK SCORING RULES:
        - Indemnity/Unlimited Liability: HIGH RISK (Score > 80)
        - Unilateral Termination without notice: HIGH RISK (Score > 75)
        - Mutual Termination: LOW RISK (Score < 30)
        - Strict Exclusive Jurisdiction (Foreign): HIGH
        - Penalties > 5%: HIGH
        
        Output valid JSON only with this structure:
        {
            "summary": "Brief summary...",
            "risk_score": 0-100 (Standard contracts should be 20-40. High Risk starts at 75),
            "clauses": [
                {"text": "original clause text...", "explanation": "simple explanation", "risk_level": "High/Medium/Low", "type": "Standard Type (e.g. Termination)"}
            ],
            "missing_clauses": ["List of standard clauses missing..."]
        }
        """

        try:
            message = self.client.messages.create(
                max_tokens=4000,
                temperature=0,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": f"Analyze this contract:\n\n{contract_text[:15000]}"} # Truncate for safety/cost
                ],
                model=self.model,
            )
            # Simplistic parsing - in production we'd use robust JSON extraction
            return message.content[0].text
        except Exception as e:
            return {"error": str(e)}

    def extract_entities(self, text):
        """Extracts parties and dates using spaCy to save LLM tokens."""
        doc = self.nlp(text)
        entities = {
            "ORG": [],
            "PERSON": [],
            "DATE": [],
            "GPE": []
        }
        for ent in doc.ents:
            if ent.label_ in entities:
                if ent.text not in entities[ent.label_]:
                    entities[ent.label_].append(ent.text)
        return entities

    def draft_negotiation_email(self, clause_text, issue_description):
        """Drafts a polite negotiation email for a specific clause."""
        if not self.client:
            return "Error: No API Key."
            
        prompt = f"""Draft a professional email for an SME owner to send to a vendor/landlord.
        Context: The contract clause says: "{clause_text}"
        Issue: {issue_description}
        Goal: Request a modification to make it fairer.
        Tone: Professional, firm but polite.
        """
        
        message = self.client.messages.create(
            max_tokens=1000,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}],
            model=self.model,
        )
        return message.content[0].text

    def generate_contract_template(self, template_type, params):
        """Generates a legal contract template based on user inputs."""
        if not self.client:
            return "Error: No API Key."
            
        system_prompt = "You are an expert legal drafter for Indian contracts. Your goal is to draft a 'Low Risk', 'Fair', and 'Balanced' agreement that protects both parties equally."
        
        user_prompt = f"""Draft a {template_type} based on these details:
        {json.dumps(params, indent=2, default=str)}
        
        CRITICAL INSTRUCTIONS FOR LOW RISK SCORING:
        1. TERMINATION: Must be MUTUAL. Both parties must have the same right to terminate without cause (e.g., 30 days notice). DO NOT allow unilateral termination by the Company/Landlord immediately without cause.
        2. INDEMNITY: If included, must be MUTUAL and CAPPED at the annual contract value. Uncapped or unilateral indemnity is HIGH RISK.
        3. JURISDICTION: Use "Courts in [City of Party B] or mutual agreed city". Avoid strict exclusive jurisdiction favoring one party.
        4. PENALTY/INTEREST: Any late fees/penalties must be < 5%. 
        5. TONE: Professional but fair. Avoid aggressive "Employer-friendly" or "Landlord-friendly" biases.
        
        Formatting Requirements:
        1. Use clear Markdown headers.
        2. Leave [Brackets] for unspecified details.
        """
        
        try:
            message = self.client.messages.create(
                max_tokens=2000,
                temperature=0.3,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                model=self.model,
            )
            return message.content[0].text
        except Exception as e:
            return f"Error generating template: {str(e)}"
