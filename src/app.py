import asyncio
import time

import streamlit as st

from conversation import (
    ConversationState,
    add_assistant_message,
    add_user_message,
    get_conversation_history,
)
from orchestrator import (
    execute_capabilities,
    generate_answer,
    resolve_request_dates,
    validate_capability_parameters,
)
from preference_extractor import extract_preferences
from request_parameters import extract_parameters
from router import route_question


WELCOME_MESSAGE = "Hello! Ask me anything about Singapore."


def apply_theme() -> None:
    """Apply the application's focused travel-planning visual theme."""
    st.markdown(
        """
        <style>
        :root {
            --background: #07111f;
            --surface: #10233a;
            --surface-raised: #172f4b;
            --border: #2a4a6d;
            --text: #e6eef8;
            --muted: #adc2d9;
            --accent: #38bdf8;
            --accent-soft: #0e7490;
        }

        [data-testid="stAppViewContainer"],
        [data-testid="stAppViewContainer"] .stApp {
            background: radial-gradient(circle at top, #132d4a 0%, var(--background) 52%);
            color: var(--text);
        }

        .stApp,
        .stApp p,
        .stApp li,
        .stApp label,
        [data-testid="stMarkdownContainer"] {
            color: var(--text);
        }

        [data-testid="stHeader"] {
            background: var(--background);
        }

        h1 {
            color: #f8fafc;
            font-weight: 700;
            letter-spacing: -0.03em;
        }

        [data-testid="stChatMessage"] {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 14px;
            box-shadow: 0 6px 18px rgba(0, 0, 0, 0.2);
            color: var(--text);
        }

        [data-testid="stChatMessage"] p,
        [data-testid="stChatMessage"] li,
        [data-testid="stChatMessage"] strong {
            color: var(--text);
        }

        .stApp a {
            color: #7dd3fc;
        }

        [data-testid="stChatInput"] {
            background: transparent;
            border: 0;
            box-shadow: none;
        }

        [data-testid="stChatInput"] > div,
        [data-testid="stChatInput"] [data-baseweb="textarea"] {
            background: #0d1b2d;
            border: 1px solid #29435f;
            border-radius: 12px;
            box-shadow: none;
        }

        [data-testid="stChatInput"] textarea {
            background: transparent;
            border: 0;
            box-shadow: none;
            color: var(--text);
        }

        [data-testid="stChatInput"] textarea::placeholder {
            color: var(--muted);
        }

        [data-testid="stChatInput"] [data-baseweb="textarea"]:focus-within {
            border-color: #3b82a8;
            box-shadow: 0 0 0 2px rgba(59, 130, 168, 0.12);
        }

        [data-testid="stChatInput"] button {
            background: #20354e;
            border-radius: 9px;
            color: #b9d8ec;
        }

        [data-testid="stChatInput"] button:disabled {
            background: #18293d;
            color: var(--muted);
        }

        .initial-loader {
            align-items: center;
            color: var(--muted);
            display: flex;
            flex-direction: column;
            justify-content: center;
            min-height: 70vh;
        }

        .loader {
            animation: spin 0.8s linear infinite;
            border: 3px solid var(--surface-raised);
            border-radius: 50%;
            border-top-color: var(--accent);
            height: 32px;
            width: 32px;
        }

        .message-loader {
            align-items: center;
            color: var(--muted);
            display: flex;
            font-size: 0.85rem;
            gap: 0.5rem;
            justify-content: flex-end;
            margin: 0.35rem 1rem 0.75rem 0;
        }

        .message-loader .loader {
            border-width: 2px;
            height: 16px;
            width: 16px;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def initialize_session_state() -> None:
    """Initialize chat state once per Streamlit browser session."""
    if "conversation_state" not in st.session_state:
        st.session_state.conversation_state = ConversationState()
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": WELCOME_MESSAGE}
        ]
        add_assistant_message(
            st.session_state.conversation_state,
            WELCOME_MESSAGE,
        )
    if "is_processing" not in st.session_state:
        st.session_state.is_processing = False
    if "pending_question" not in st.session_state:
        st.session_state.pending_question = None
    if "initial_load_complete" not in st.session_state:
        st.session_state.initial_load_complete = False


def process_question(question: str, conversation_state: ConversationState) -> str:
    """Run the existing orchestration flow for one chat message."""
    add_user_message(conversation_state, question)
    for preference in extract_preferences(question):
        if preference not in conversation_state.preferences:
            conversation_state.preferences.append(preference)

    decision = route_question(question)
    extracted_parameters = extract_parameters(question)
    parameters, date_clarification = resolve_request_dates(extracted_parameters)
    clarification = date_clarification or validate_capability_parameters(
        decision.capabilities, parameters
    )
    if clarification is not None:
        answer = clarification
    else:
        evidence = asyncio.run(
            execute_capabilities(question, decision.capabilities, parameters)
        )
        answer = generate_answer(
            question,
            evidence,
            get_conversation_history(conversation_state),
        )

    add_assistant_message(conversation_state, answer)
    return answer


def main() -> None:
    st.set_page_config(page_title="Singapore Travel Assistant")
    initialize_session_state()
    apply_theme()
    st.title("Singapore Travel Assistant")

    if not st.session_state.initial_load_complete:
        st.markdown(
            """
            <div class="initial-loader">
                <div class="loader"></div>
                <p>Preparing your travel assistant...</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        time.sleep(0.8)
        st.session_state.initial_load_complete = True
        st.rerun()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    prompt = st.chat_input(
        "Ask about Singapore...",
        disabled=st.session_state.is_processing,
    )
    if st.session_state.is_processing:
        question = st.session_state.pending_question
        if question is None:
            raise RuntimeError("A pending question is required while processing.")

        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.write(question)
        st.markdown(
            """
            <div class="message-loader">
                <span>Finding your answer</span><span class="loader"></span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        try:
            answer = process_question(question, st.session_state.conversation_state)
        finally:
            st.session_state.is_processing = False
            st.session_state.pending_question = None

        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.rerun()

    if prompt is not None:
        st.session_state.pending_question = prompt
        st.session_state.is_processing = True
        st.rerun()


if __name__ == "__main__":
    main()
