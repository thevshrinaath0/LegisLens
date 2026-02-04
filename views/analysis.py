import streamlit as st
import json
from utils.nlp_engine import NLPEngine

def show(analysis_result):
    st.header("Detailed Clause Analysis")
    
    nlp = NLPEngine()
    
    if not analysis_result or "clauses" not in analysis_result:
        st.warning("No clause analysis available yet. Go to Dashboard to process.")
        return

    # Helper function for risk colors
    def get_risk_color(level):
        if level.lower() == "high": return "red"
        if level.lower() == "medium": return "orange"
        return "green"

    for idx, clause in enumerate(analysis_result["clauses"]):
        risk = clause.get("risk_level", "Low")
        color = get_risk_color(risk)
        
        with st.expander(f"Clause {idx+1}: {clause.get('type', 'Standard')} ({risk} Risk)"):
            st.markdown(f"**Original Text:**\n> {clause.get('text')}")
            st.markdown(f"**Plain Language:**\n{clause.get('explanation')}")
            
            if risk.lower() in ["high", "medium"]:
                col_a, col_b = st.columns([1, 3])
                with col_a:
                    st.error(f"Risk: {risk}")
                with col_b:
                    if st.button(f"Negotiate Clause {idx+1}", key=f"btn_{idx}"):
                        st.session_state[f"negotiate_{idx}"] = True
                
                if st.session_state.get(f"negotiate_{idx}"):
                    with st.form(key=f"form_{idx}"):
                        st.write("Generating draft email...")
                        issue_context = f"The user considers this {clause.get('type')} clause too risky."
                        draft = nlp.draft_negotiation_email(clause.get("text"), issue_context)
                        st.text_area("Draft Email", value=draft, height=200)
                        st.form_submit_button("Copy to Clipboard")
