import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from utils.risk_calculator import RiskCalculator

def show(contract_text, analysis_result):
    st.header("Contract Health Dashboard")
    
    # 1. Top Level Metrics
    col1, col2 = st.columns(2)
    
    risk_score = 0
    if analysis_result and isinstance(analysis_result, dict):
        risk_score = analysis_result.get("risk_score", 50)
    
    with col1:
        # Strict Threshold: > 60 is considered High Risk for SMEs
        st.metric("Overall Risk Score", f"{risk_score}/100", delta="-High Risk" if risk_score > 75 else "Safe")
    with col2:
        st.metric("Total Clauses (Approx)", len(contract_text.split('.')) // 2)
        
    st.divider()
    
    # 2. Risk Radar
    st.subheader("Risk Dimensions")
    calculator = RiskCalculator()
    scores = calculator.calculate_risk_scores(contract_text, analysis_result)
    
    # Create Radar Chart
    categories = list(scores.keys())
    values = list(scores.values())
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='Contract Risk',
        line_color='#FF4B4B'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 3. High Level Summary
    if analysis_result and "summary" in analysis_result:
        st.info(f"**Executive Summary**: {analysis_result['summary']}")
