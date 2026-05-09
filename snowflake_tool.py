import os
import snowflake.connector
from dotenv import load_dotenv

# Load credentials
load_dotenv()

def search_insurance_policy(query: str) -> str:
    """
    This is the tool the AI will use to search the Snowflake Vector Database.
    """
    print(f"\n[SYSTEM] Executing Snowflake Semantic Search for: '{query}'...")
    # Ask for the 6-digit code right in the VS Code terminal
    mfa_code = input("\nEnter your 6-digit Snowflake Authenticator code: ")

    # 1. Connect to Snowflake
    conn = snowflake.connector.connect(
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
        passcode=mfa_code
    )
    
    cursor = conn.cursor()
    
    # 2. The Vector Search SQL Query
    # We embed the agent's question, and compare it to the embeddings in our table!
    sql = f"""
        SELECT CHUNK_TEXT 
        FROM POLICY_CHUNKS
        ORDER BY VECTOR_COSINE_SIMILARITY(
            EMBEDDING, 
            SNOWFLAKE.CORTEX.EMBED_TEXT_768('e5-base-v2', '{query}')
        ) DESC
        LIMIT 1;
    """
    
    try:
        cursor.execute(sql)
        result = cursor.fetchone()
        
        if result:
            print("[SYSTEM] Match Found in Snowflake!")
            return result[0] # Return the exact policy text
        else:
            return "No matching policy rules found."
            
    finally:
        cursor.close()
        conn.close()

# Let's test the tool directly!
if __name__ == "__main__":
    test_question = "Are collisions with animals like deer covered?"
    found_rule = search_insurance_policy(test_question)
    
    print("\n--- RETRIEVED RULE FROM SNOWFLAKE ---")
    print(found_rule)
    print("-------------------------------------\n")