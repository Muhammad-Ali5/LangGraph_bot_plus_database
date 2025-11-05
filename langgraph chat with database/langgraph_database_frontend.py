import streamlit as st
from langgraph_database_backend import chatbot, retrieve_all_threads
from langchain_core.messages import HumanMessage
import uuid

# ===================Thread_id=========================
def generate_thread_id():
    thread_id = uuid.uuid4()
    return thread_id

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state["thread_id"] = thread_id
    add_thread(st.session_state["thread_id"])
    st.session_state["message_history"] = []  

def add_thread(thread_id):
    if thread_id not in st.session_state["chat_threads"]:
        st.session_state["chat_threads"].append(thread_id)

def load_thread(thread_id):
    # Placeholder for loading thread-specific history if needed
    return chatbot.get_state(config={"configurable": {"thread_id": thread_id}}).values["messages"]

# =====================Session Setups=======================
if "message_history" not in st.session_state:
    st.session_state["message_history"] = []

if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = generate_thread_id()

if "chat_threads" not in st.session_state:
    st.session_state["chat_threads"] = retrieve_all_threads()

add_thread(st.session_state["thread_id"])

# =======================Siderbar UI=====================
st.sidebar.title("LangGraph Chatbot")
if st.sidebar.button("New Chat"):
    reset_chat()

st.sidebar.header("Conversation History")

for thread_id in st.session_state["chat_threads"]:
    if st.sidebar.button(str(thread_id), key=str(thread_id)):
        st.session_state["thread_id"] = thread_id
        messages  = load_thread(thread_id)

        temp_history = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                role="user"
            else:
                role="assistant"
            temp_history.append({"role": role, "content": msg.content})
        
        st.session_state["message_history"] = temp_history

# =====================Main UI======================
# Display chat history
for message in st.session_state["message_history"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input("Type here")

if user_input:
    # Add user message to history and display
    st.session_state["message_history"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # ============================================
    CONFIG = {"configurable": {"thread_id": st.session_state["thread_id"]}}

    # Stream AI response
    with st.chat_message("assistant"):
        response_container = st.empty()
        response_container.markdown("Assistant is typing...")
        full_response = ""
        
        try:
            # Stream the response with stream_mode="messages" for token-by-token
            for message_chunk, metadata in chatbot.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode="messages"
            ):
                if message_chunk.content:
                    chunk_text = message_chunk.content
                    full_response += chunk_text
                    response_container.markdown(full_response)
        except Exception as e:
            response_container.markdown(f"Error generating response: {str(e)}")
        
        # Save the full response to history
        st.session_state["message_history"].append({"role": "assistant", "content": full_response})