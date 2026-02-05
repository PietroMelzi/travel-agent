import asyncio
import json
import logging
import weave
from collections import deque

import streamlit as st
from agents import Runner
from utils import build_message_with_history, load_agent
from agents.exceptions import InputGuardrailTripwireTriggered

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


try:
    weave.init("travel-agent")
except Exception as e:
    log.warning("Weave init skipped: %s", e)


def run_async(coro):
    """
    Safely run async code inside Streamlit.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    else:
        return loop.run_until_complete(coro)


st.set_page_config(page_title="Travel Agent", page_icon="✈️")
st.title("✈️ Travel Agent")
st.caption("Let's plan your travel!")

# --- session state ---
if "history" not in st.session_state:
    st.session_state.history = deque(maxlen=5)

if "agent" not in st.session_state:
    try:
        st.session_state.agent = load_agent()
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        st.error(f"Failed to load agent config: {e}")
        st.stop()

# --- display conversation ---
for user_msg, assistant_msg in st.session_state.history:
    with st.chat_message("user"):
        st.markdown(user_msg)
    with st.chat_message("assistant"):
        st.markdown(assistant_msg)

# --- input ---
user_input = st.chat_input("Ask a travel question...")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                message = build_message_with_history(
                    st.session_state.history, user_input
                )
                result = run_async(Runner.run(st.session_state.agent, message))
                assistant_output = result.final_output

            except InputGuardrailTripwireTriggered:
                assistant_output = (
                    "🚫 This request was blocked — it doesn't seem to be about travel."
                )

            except Exception as e:
                log.exception(f"Agent run failed: {e!s}")
                assistant_output = f"❌ Error. Please try again."

        st.markdown(assistant_output)

    st.session_state.history.append((user_input, assistant_output))
