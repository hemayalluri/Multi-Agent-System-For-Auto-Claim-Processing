import os
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from snowflake_tool import search_insurance_policy
from dotenv import load_dotenv

# Loading secure keys from the .env file
load_dotenv()

# 1. Defining the UNIFIED State (The shared memory)
class AgentState(TypedDict):
    claim_id: str
    claim_text: str
    verification_result: Optional[str]
    risk_assessment: Optional[str]   
    fraud_analysis: Optional[str]    
    final_summary: Optional[str]     # final joint conclusion

# 2. Connecting to Bedrock (Azure OpenAI)
llm = AzureChatOpenAI(
    azure_deployment=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    temperature=0 
)

# 3. Defining the Agents (The processing nodes)
def verification_agent(state: AgentState):
    print(f"\n--- Verification Agent Processing Claim: {state['claim_id']} ---")
    
    # 1. THE RAG RETRIEVAL: Fetch the rules from Snowflake!
    print(">> Reaching into Snowflake to fetch policy rules...")
    retrieved_rules = search_insurance_policy(state['claim_text'])
    
    # 2. THE RAG AUGMENTATION: Inject the rules into the System Message
    sys_msg = SystemMessage(content=f"""You are an expert insurance verification agent. Analyze the provided claim text STRICTLY using the following Delverisk Policy Rules:
    
    POLICY RULES: {retrieved_rules}
    Summarize the incident, state if it is covered under the retrieved rules, and provide a Conclusion.
    """)
    
    user_msg = HumanMessage(content=state['claim_text'])
    
    # 3. GENERATION: Send the augmented prompt to the Brain
    response = llm.invoke([sys_msg, user_msg])
    
    return {"verification_result": response.content}

def risk_agent(state: AgentState):
    print("--- Risk Agent Processing ---")
    sys_msg = SystemMessage(content="You are a Risk Assessment Agent. Analyze the insurance claim for risk factors such as weather conditions, severity of damage, and potential liability. Be concise and objective.")
    human_msg = HumanMessage(content=f"Claim: {state['claim_text']}\nVerification Notes: {state.get('verification_result', 'None')}")
    response = llm.invoke([sys_msg, human_msg])
    return {"risk_assessment": response.content}

def fraud_agent(state: AgentState):
    print("--- Fraud Agent Processing ---")
    sys_msg = SystemMessage(content="You are a Fraud Detection Agent. Review the claim details, verification notes, and risk assessment. Look for any inconsistencies, suspicious details, or red flags that indicate potential fraud. Conclude with a 'Fraud Probability: LOW, MEDIUM, or HIGH'. ")
    human_msg = HumanMessage(content=f"Claim: {state['claim_text']}\nVerification Notes: {state.get('verification_result', 'None')}\nRisk Notes: {state.get('risk_assessment', 'None')}")
    response = llm.invoke([sys_msg, human_msg])
    return {"fraud_analysis": response.content}

def summary_agent(state: AgentState):
    print("--- Lead Adjuster (Summary) Agent Processing ---")
    sys_msg = SystemMessage(content="""
    You are a Lead Claims Adjuster. Review the findings from the Verification, Risk, and Fraud AI agents. 
    Write a 'Joint Conclusion and Suggestion Note'. 
    This should be a highly concise, 3-4 sentence summary of the overall claim status followed by a definitive next-step recommendation (e.g., 'APPROVE', 'DENY', or 'FLAG FOR HUMAN INVESTIGATION').
    """)
    human_msg = HumanMessage(content=f"""
    Verification Agent Findings: {state.get('verification_result')}
    Risk Agent Findings: {state.get('risk_assessment')}
    Fraud Agent Findings: {state.get('fraud_analysis')}
    """)
    response = llm.invoke([sys_msg, human_msg])
    return {"final_summary": response.content}

# 4. Build the Graph (The Orchestration)
workflow = StateGraph(AgentState)

# Add nodes to the graph
workflow.add_node("verify", verification_agent)
workflow.add_node("risk", risk_agent)       
workflow.add_node("fraud", fraud_agent)
workflow.add_node("summary", summary_agent) 

# Set the start and end points of the pipeline
workflow.set_entry_point("verify")
workflow.add_edge("verify", "risk")
workflow.add_edge("risk", "fraud")
workflow.add_edge("fraud", "summary")      
workflow.add_edge("summary", END)           # <-- End after summary

# Compile the orchestration engine
app = workflow.compile()

# 5. Run a Test Execution!
if __name__ == "__main__":
    test_state = {
        "claim_id": "CLM-TEST-001",
        "claim_text": "I was driving on I-95 and a tree branch fell on my car during a storm, causing significant damage to the roof and windshield. I have photos of the damage and a police report confirming the incident."
    }
    
    print("Starting LangGraph Orchestration...\n")
    result = app.invoke(test_state)
    
    # Print just the final executive summary
    print("\n================ JOINT CONCLUSION & SUGGESTION ================\n")
    print(result.get('final_summary'))
    print("\n===============================================================")