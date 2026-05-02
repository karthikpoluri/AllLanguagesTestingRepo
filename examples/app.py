import os
import time
from datetime import datetime
from dotenv import load_dotenv
import streamlit as st
 
# Set page config FIRST - must be the first Streamlit command
st.set_page_config(
    page_title="Banking Chatbot",
    layout="wide",
    page_icon="🏦"
)
 
# Now load other dependencies after page config
from retriever import execute_rag_agent
from pandas_agent import get_upcoming_tx_details, get_df_info
from sql_agent_2 import get_customer_details, get_table_info
from langgraph_supervisor import create_supervisor
from langgraph.prebuilt import create_react_agent
from langchain.chat_models import init_chat_model
from langchain_openai import AzureChatOpenAI
 
# Load environment variables
load_dotenv()
 
# Configuration
def setup_config():
    langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_API_KEY"] = langsmith_api_key
    os.environ["USER_AGENT"] = "banking"
   
    today = datetime.now().strftime("%d/%m/%Y")
    google_api_key = os.getenv("GOOGLE_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
   
    return today, google_api_key, openai_api_key
 
today, google_api_key, openai_api_key = setup_config()
 
# Initialize models with caching
@st.cache_resource
def load_models():
    llm = init_chat_model(
        "gemini-1.5-pro",
        model_provider="google_genai",
        api_key=google_api_key
    )
 
    llm_thinking = AzureChatOpenAI(
        deployment_name="gpt-4o",
        model_name="gpt-4o",
        azure_endpoint="https://gpt-4-main.openai.azure.com/",
        api_key=openai_api_key,
        api_version="2024-12-01-preview",
        temperature=None,
    )
    return llm, llm_thinking
 
llm, llm_thinking = load_models()
 
# Retrieve necessary data with caching
@st.cache_data(ttl=3600)
def load_data():
    df_columns = get_df_info()
    schema = get_table_info()
    return df_columns, schema
 
df_columns, schema = load_data()
 
# Available users (modify as needed)
AVAILABLE_USERS = {
    "Jane": "customer_123",
    "John": "customer_456",
    "Eva": "customer_789"
}
 
# Tools with user context
def get_interest_rates_tool(query: str) -> list[str]:
    """Retrieves interest rates from the vector store."""
    st.session_state.tool_used = "Interest Rates"
    if "user_id" in st.session_state:
        query = f"{query} (for user {st.session_state.user_id})"
    documents = execute_rag_agent(query)
    return documents
 
def get_upcoming_tx_tool(query: str) -> str:
    """Retrieve upcoming transactions details."""
    st.session_state.tool_used = "Upcoming Transactions"
    if "user_id" in st.session_state:
        query = f"{query} for customer {st.session_state.user_id}"
    response = get_upcoming_tx_details(query)
    return response
 
def get_customer_details_tool(query: str) -> str:
    """Retrieve customer details."""
    st.session_state.tool_used = "Customer Details"
    if "user_id" in st.session_state:
        query = f"{query} for customer {st.session_state.user_id}"
    response = get_customer_details(query)
    return response
 
# Create agents with caching
@st.cache_resource
def setup_agents():
    interest_rate_agent = create_react_agent(
        model=llm,
        tools=[get_interest_rates_tool],
        name="interest_rate_agent",
        prompt="You are an interest rate agent. Use the tools provided to retrieve the interest rates.",
    )
 
    upcoming_tx_agent = create_react_agent(
        model=llm_thinking,
        tools=[get_upcoming_tx_tool],
        name="upcoming_tx_agent",
        prompt=f"You are a pending transactions agent. The dataframe columns are: {df_columns}",
    )
 
    customer_details_agent = create_react_agent(
        model=llm_thinking,
        tools=[get_customer_details_tool],
        name="customer_details_agent",
        prompt=f"You are the customer details agent. The database schema is: {schema}",
    )
 
    workflow = create_supervisor(
        [interest_rate_agent, upcoming_tx_agent, customer_details_agent],
        model=llm_thinking,
        prompt=f"Supervisor Prompt. DF Columns: {df_columns}, Schema: {schema}",
    )
 
    return workflow.compile()
 
app = setup_agents()
 
# Main App
def main():
    # Sidebar for additional controls
    with st.sidebar:
        st.title("Banking Assistant Settings")
        st.markdown(f"**Current Date:** {today}")
       
        # User selection radio button
        selected_user = st.radio(
            "Select Customer:",
            options=list(AVAILABLE_USERS.keys()),
            index=0,
            key="user_selection"
        )
       
        # Store the selected user's ID in session state
        st.session_state.user_id = AVAILABLE_USERS[selected_user]
        st.markdown(f"Selected: **{selected_user}** (ID: {st.session_state.user_id})")
       
        st.divider()
       
        if st.button("Clear Conversation"):
            st.session_state.messages = []
            st.rerun()
           
        st.markdown("### Quick Actions")
        if st.button("Check Interest Rates"):
            st.session_state.messages.append({"role": "user", "content": "What are the current interest rates?"})
            st.rerun()
           
        if st.button("Upcoming Transactions"):
            st.session_state.messages.append({"role": "user", "content": "Show me my upcoming transactions"})
            st.rerun()
   
    # Main chat interface
    st.title("🏦 Banking Assistant")
    st.markdown(f"Currently assisting: **{selected_user}**")
    st.markdown("""
        I can help you with:
        - 💰 Interest rate inquiries
        - 🏦 Account details
        - 📅 Upcoming transactions
        - And more!
    """)
   
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "tool_used" not in st.session_state:
        st.session_state.tool_used = None
 
    # Display chat history with avatars
    for message in st.session_state.messages:
        avatar = "👤" if message["role"] == "user" else "🏦"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])
            if message["role"] == "assistant" and st.session_state.tool_used:
                st.caption(f"Retrieved using: {st.session_state.tool_used}")
                st.session_state.tool_used = None
 
    # User input with processing indicator
    if query := st.chat_input("Ask your banking question..."):
        st.session_state.messages.append({"role": "user", "content": query})
       
        # Display user message immediately
        with st.chat_message("user", avatar="👤"):
            st.markdown(query)
       
        # Create a placeholder for the assistant's response
        with st.chat_message("assistant", avatar="🏦"):
            response_placeholder = st.empty()
            with st.spinner("Processing your request..."):
                try:
                    start_time = time.time()
                   
                    # Process the query with user context
                    context_query = f"{query} (for customer {selected_user})"
                   
                    result_state = app.invoke(
                        {"messages": [{"role": "user", "content": context_query}]},
                        config={"configurable": {"thread_id": "7"}},
                    )
                    response = result_state["messages"][-1].content
                   
                    # Simulate typing effect
                    full_response = ""
                    for chunk in response.split():
                        full_response += chunk + " "
                        time.sleep(0.05)
                        response_placeholder.markdown(full_response + "▌")
                   
                    response_placeholder.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                   
                    # Performance metrics
                    processing_time = time.time() - start_time
                    st.caption(f"Processed in {processing_time:.2f} seconds")
                   
                except Exception as e:
                    error_message = "Sorry, I encountered an error processing your request. Please try again later."
                    response_placeholder.error(error_message)
                    st.session_state.messages.append({"role": "assistant", "content": error_message})
                    st.error(f"Error details: {str(e)}")


if __name__ == "__main__":
    main()
 
