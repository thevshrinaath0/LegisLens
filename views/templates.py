import streamlit as st
from utils.nlp_engine import NLPEngine

def show(nlp_engine=None):
    st.header("📝 Standardized Contract Templates")
    st.markdown("Generate professional legal agreements in seconds using AI.")
    
    if nlp_engine is None:
        nlp_engine = NLPEngine()
        
    contract_types = [
        "Employment Agreement",
        "Non-Disclosure Agreement (NDA)",
        "Rental Agreement",
        "Vendor Service Agreement",
        "Freelance Contract"
    ]
    
    selected_type = st.selectbox("Select Contract Type", contract_types)
    
    st.subheader("Contract Details")
    
    params = {}
    
    col1, col2 = st.columns(2)
    
    with col1:
        params["party_a_name"] = st.text_input("Party A Name (Employer/Landlord)", placeholder="e.g. Acme Corp")
        params["party_a_address"] = st.text_input("Party A Address")
    
    with col2:
        params["party_b_name"] = st.text_input("Party B Name (Employee/Tenant)", placeholder="e.g. John Doe")
        params["party_b_address"] = st.text_input("Party B Address")
        
    st.divider()
    
    # Dynamic fields based on type
    if "Employment" in selected_type:
        c1, c2 = st.columns(2)
        params["role"] = c1.text_input("Job Role/Title")
        params["salary"] = c2.text_input("Monthly Salary (INR)")
        params["start_date"] = st.date_input("Start Date")
        
    elif "Rental" in selected_type:
        c1, c2 = st.columns(2)
        params["property_address"] = st.text_input("Property Address")
        params["monthly_rent"] = c1.text_input("Monthly Rent (INR)")
        params["security_deposit"] = c2.text_input("Security Deposit (INR)")
        
    else:
        params["scope"] = st.text_area("Scope of Work / Purpose", placeholder="Describe the services or confidential information...")
        params["payment_terms"] = st.text_input("Payment Terms", placeholder="e.g. 50% advance, 50% on completion")

    if st.button("Generate Contract Draft", type="primary"):
        if not params["party_a_name"] or not params["party_b_name"]:
            st.error("Please fill in at least the party names.")
        else:
            with st.spinner(f"Drafting your {selected_type}..."):
                draft = nlp_engine.generate_contract_template(selected_type, params)
                st.session_state["generated_template"] = draft
                st.success("Draft Generated Successfully!")
                
    if "generated_template" in st.session_state:
        st.divider()
        st.subheader("Generated Draft")
        st.markdown("Review and copy the draft below.")
        st.text_area("Contract Text", value=st.session_state["generated_template"], height=600)
        st.download_button(
            label="Download as Text File",
            data=st.session_state["generated_template"],
            file_name=f"{selected_type.replace(' ', '_')}.txt",
            mime="text/plain"
        )
