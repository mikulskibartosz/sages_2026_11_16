import asyncio
import streamlit as st

import ai_client

st.set_page_config(page_title="LOT Booking Assistant", page_icon="✈️")
st.title("✈️ LOT Booking Assistant")

# --- Session state setup ---
if "agent" not in st.session_state:
    st.session_state.agent = ai_client.build_agent()
if "chat_log" not in st.session_state:
    st.session_state.chat_log = []          # for rendering: list of {"role", "content"}
if "message_history" not in st.session_state:
    st.session_state.message_history = None  # PydanticAI's own message history
if "pending" not in st.session_state:
    st.session_state.pending = None          # DeferredToolRequests, if a turn is paused


def run_async(coro):
    return asyncio.run(coro)


def render_chat_log():
    for entry in st.session_state.chat_log:
        with st.chat_message(entry["role"]):
            st.markdown(entry["content"])


def handle_turn_result(result: ai_client.TurnResult):
    st.session_state.message_history = result.messages
    if result.pending is not None:
        st.session_state.pending = result.pending
    else:
        st.session_state.pending = None
        st.session_state.chat_log.append({"role": "assistant", "content": result.text})


render_chat_log()

# --- Approval UI: shown only when a run is paused waiting for a human ---
if st.session_state.pending is not None:
    st.warning("⚠️ Wymagane zatwierdzenie przed kontynuacją:")
    decisions: dict[str, bool] = {}

    for call in st.session_state.pending.approvals:
        with st.container(border=True):
            st.write(f"**Narzędzie:** `{call.tool_name}`")
            st.json(call.args)
            col1, col2 = st.columns(2)
            with col1:
                approve = st.button("✅ Zatwierdź", key=f"approve_{call.tool_call_id}")
            with col2:
                deny = st.button("❌ Odrzuć", key=f"deny_{call.tool_call_id}")

            if approve:
                decisions[call.tool_call_id] = True
            elif deny:
                decisions[call.tool_call_id] = False

    if decisions:
        deferred_results = ai_client.build_deferred_results(decisions)
        with st.spinner("Przetwarzanie decyzji..."):
            result = run_async(
                ai_client.send_message(
                    st.session_state.agent,
                    user_message=None,
                    message_history=st.session_state.message_history,
                    deferred_tool_results=deferred_results,
                )
            )
        handle_turn_result(result)
        st.rerun()

# --- Normal chat input, disabled while a decision is pending ---
else:
    user_input = st.chat_input("Zapytaj o loty LOT...")
    if user_input:
        st.session_state.chat_log.append({"role": "user", "content": user_input})
        with st.spinner("Przetwarzanie..."):
            result = run_async(
                ai_client.send_message(
                    st.session_state.agent,
                    user_message=user_input,
                    message_history=st.session_state.message_history,
                )
            )
        handle_turn_result(result)
        st.rerun()
