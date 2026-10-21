
import streamlit as st
from langgraph_backend import chatbot
from langchain_core.messages import HumanMessage, AIMessage
import uuid

# --------------------------------------------------
# Utility functions
# --------------------------------------------------

def generate_thread_id():
    return str(uuid.uuid4())


def add_thread(thread_id):
    if thread_id not in st.session_state["chat_threads"]:
        st.session_state["chat_threads"].append(thread_id)


def reset_chat():
    thread_id = generate_thread_id()

    st.session_state["thread_id"] = thread_id
    st.session_state["message_history"] = []

    add_thread(thread_id)

    st.session_state["chat_titles"][thread_id] = "New Conversation"


def load_conversation(thread_id):
    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    state = chatbot.get_state(config=config)
    return state.values.get("messages", [])


def create_title(user_input):
    # Use the first user message as the conversation title
    title = " ".join(user_input.strip().split())

    if len(title) > 30:
        title = title[:30].rstrip() + "..."

    return title or "New Conversation"


def format_messages(messages):
    formatted_messages = []

    for message in messages:
        if isinstance(message, HumanMessage):
            role = "user"
        elif isinstance(message, AIMessage):
            role = "assistant"
        else:
            continue

        formatted_messages.append({
            "role": role,
            "content": message.content
            if isinstance(message.content, str)
            else str(message.content)
        })

    return formatted_messages


# --------------------------------------------------
# Initialize session state
# --------------------------------------------------

if "message_history" not in st.session_state:
    st.session_state["message_history"] = []

if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = generate_thread_id()

if "chat_threads" not in st.session_state:
    st.session_state["chat_threads"] = []

if "chat_titles" not in st.session_state:
    st.session_state["chat_titles"] = {}

# Register the current conversation
add_thread(st.session_state["thread_id"])

current_thread_id = st.session_state["thread_id"]

if current_thread_id not in st.session_state["chat_titles"]:
    st.session_state["chat_titles"][current_thread_id] = (
        "New Conversation"
    )


# --------------------------------------------------
# Sidebar UI
# --------------------------------------------------

st.sidebar.title("LangGraph Chatbot")

if st.sidebar.button("➕ New Chat", use_container_width=True):
    reset_chat()
    st.rerun()

st.sidebar.divider()
st.sidebar.header("My Conversations")

# Display newest conversations first
for thread_id in reversed(st.session_state["chat_threads"]):

    title = st.session_state["chat_titles"].get(
        thread_id, "New Conversation"
    )

    # Highlight the current conversation in its title
    if thread_id == st.session_state["thread_id"]:
        button_label = f"🟢 {title}"
    else:
        button_label = title

    if st.sidebar.button(
        button_label,
        key=f"chat_{thread_id}",
        use_container_width=True
    ):
        st.session_state["thread_id"] = thread_id

        messages = load_conversation(thread_id)
        st.session_state["message_history"] = format_messages(
            messages
        )

        st.rerun()


# --------------------------------------------------
# Main chat UI
# --------------------------------------------------

st.title(
    st.session_state["chat_titles"].get(
        st.session_state["thread_id"],
        "New Conversation"
    )
)

# Display conversation history
for message in st.session_state["message_history"]:
    with st.chat_message(message["role"]):
        st.write(message["content"])


# --------------------------------------------------
# User input and AI response
# --------------------------------------------------

user_input = st.chat_input("Type your message here...")

if user_input:
    thread_id = st.session_state["thread_id"]

    # Automatically name the chat from its first message
    if (
        st.session_state["chat_titles"].get(thread_id)
        == "New Conversation"
    ):
        title = create_title(user_input)
        st.session_state["chat_titles"][thread_id] = title

    # Display user message
    st.session_state["message_history"].append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        st.write(user_input)

    # LangGraph checkpoint configuration
    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    # Stream the assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response_text = st.write_stream(
                message_chunk.content
                for message_chunk, metadata in chatbot.stream(
                    {
                        "messages": [
                            HumanMessage(content=user_input)
                        ]
                    },
                    config=config,
                    stream_mode="messages"
                )
                if isinstance(message_chunk.content, str)
            )

    # Save assistant response in Streamlit history
    st.session_state["message_history"].append({
        "role": "assistant",
        "content": response_text
    })

    # Refresh to update the sidebar title and page heading
    st.rerun()