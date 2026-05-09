import streamlit as st
import uuid
from agent_graph import app as ai_engine # Importing your compiled LangGraph!

# Set up the visual configuration of the page
st.set_page_config(page_title="CLAIM PROCESSING ASSISTANT", page_icon="🛡️", layout="centered")

st.title(" AI CLAIMS PROCESSING ASSISTANT")
st.markdown("Enter the claim details below to run the Multi-Agent Verification, Risk, and Fraud pipeline.")

# Create a text area for the user to paste the claim
claim_text = st.text_area("Claim Description:", height=150, placeholder="e.g., I was driving on I-95 and hit a deer...")

# Create a button to trigger the AI
if st.button("Run AI Claim Analysis"):
    if not claim_text.strip():
        st.warning("Please enter a claim description.")
    else:
        with st.spinner("Agents are reviewing the policy and analyzing the claim..."):
            
            # 1. Package the state for LangGraph
            state_input = {
                "claim_id": f"CLM-{str(uuid.uuid4())[:8].upper()}",
                "claim_text": claim_text
            }
            
            # 2. Run the LangGraph Engine!
            try:
                result = ai_engine.invoke(state_input)
                
                # 3. Display the Results Beautifully
                st.success("Analysis Complete!")
                
                # Use tabs to organize the different agents' thoughts
                tab1, tab2, tab3, tab4 = st.tabs(["Final Summary", "Verification Notes", "Risk Notes", "Fraud Notes"])
                
                with tab1:
                    st.subheader("Executive Recommendation")
                    st.write(result.get('final_summary'))
                with tab2:
                    st.write(result.get('verification_result'))
                with tab3:
                    st.write(result.get('risk_assessment'))
                with tab4:
                    st.write(result.get('fraud_analysis'))
                    
            except Exception as e:
                st.error(f"An error occurred: {e}")