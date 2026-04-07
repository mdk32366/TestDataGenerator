"""
fsc_agent_chat.py — Agentic Chat Panel for FSC Insurance Test Data Generator
Drop-in module: imported and called from fsc_data_generator_v2.py

Drop-in usage (add to bottom of fsc_data_generator_v2.py):
    from fsc_agent_chat import render_agent_chat
    render_agent_chat()

Requires: ANTHROPIC_API_KEY in environment or .env
Model:    claude-haiku-4-5-20251001  (fast, cheap, FSC-aware)
"""

from __future__ import annotations

import os
import json
import textwrap
from datetime import datetime
from typing import Any

import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# LAZY IMPORT — anthropic only needed when chat is used
# ─────────────────────────────────────────────────────────────────────────────
def _get_client():
    try:
        import anthropic
    except ImportError:
        st.error("Install the Anthropic SDK:  pip install anthropic")
        st.stop()
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        # Try .env fallback
        try:
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        except ImportError:
            pass
    if not api_key:
        return None, "ANTHROPIC_API_KEY not found. Set it in your .env file."
    return anthropic.Anthropic(api_key=api_key), None


# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT — FSC-aware, knows about current dataset state
# ─────────────────────────────────────────────────────────────────────────────
_SYSTEM_BASE = textwrap.dedent("""
You are **FSC Data Assistant**, an expert Salesforce Financial Services Cloud (FSC) \
data engineer embedded inside the FSC Insurance Test Data Generator application.

## Your role
You help the user understand, configure, troubleshoot, and get the most out of the \
FSC Insurance Test Data Generator. You have deep knowledge of:
- Salesforce FSC Insurance objects: Campaign, Lead, Account, Contact, Opportunity, InsurancePolicy
- Salesforce API limits, composite collections, and bulk loading best practices
- The Salesforce Connected App credential model (username + password + security token)
- Sandbox vs. production environments
- Common upload failure patterns and how to resolve them
- FSC Insurance Cloud object relationships and required fields
- The app's current dataset state (injected below)

## Personality
Professional but direct. You give concrete, actionable answers. You never hallucinate \
Salesforce field names — if you're unsure about a specific API name, you say so and \
recommend checking Object Manager. You speak fluently about Applied Epic, Cosmos DB, \
Azure ADF, Snowflake, and the broader integration stack this app feeds into.

## Current dataset state
{dataset_state}

## Rules
- Keep replies concise. Use bullet points for lists of steps. Use code blocks for SOQL, JSON, Python.
- If the user asks you to generate or modify data, remind them the sidebar controls do that — \
  your job is to advise and explain, not to re-run generators.
- Never suggest they paste credentials into the chat. Always point to the sidebar Salesforce Connection form.
- If the user is clearly debugging a load failure, walk through the error systematically: \
  field validation → API limits → permission sets → object accessibility.
""").strip()


def _build_system_prompt() -> str:
    """Inject live dataset stats into the system prompt."""
    ss = st.session_state
    if not ss.get("generated"):
        state_block = "No dataset has been generated yet in this session."
    else:
        dfs = {
            "Campaigns":  ss.get("df_campaigns"),
            "Leads":      ss.get("df_leads"),
            "Accounts":   ss.get("df_accounts"),
            "Contacts":   ss.get("df_contacts"),
            "Opportunities": ss.get("df_opps"),
            "Insurance Policies": ss.get("df_policies"),
        }
        lines = []
        for name, df in dfs.items():
            if df is not None:
                lines.append(f"  - {name}: {len(df):,} rows, {len(df.columns)} columns")
        seed  = ss.get("_seed_used", "unknown")
        state_block = f"Seed: {seed}\n" + "\n".join(lines)
        # Add SF connection status
        if ss.get("sf_connected"):
            state_block += f"\n  - Salesforce: CONNECTED ({ss.get('sf_org_name','')})"
        else:
            state_block += "\n  - Salesforce: not connected"
        # Add any load results
        load_res = ss.get("load_results", {})
        if load_res:
            state_block += "\n  - Last load results: " + ", ".join(
                f"{obj}: {r.get('inserted',0)}/{r.get('total',0)} inserted"
                for obj, r in load_res.items()
            )
    return _SYSTEM_BASE.format(dataset_state=state_block)


# ─────────────────────────────────────────────────────────────────────────────
# QUICK-ACTION BUTTONS
# ─────────────────────────────────────────────────────────────────────────────
_QUICK_ACTIONS = [
    ("🔢 How many records?",       "Summarise the current dataset: how many records are in each object and what is the total?"),
    ("⚠️ Why did my upload fail?", "Walk me through the most common reasons an InsurancePolicy upload fails and how to fix each one."),
    ("🔑 Security token help",     "Explain what a Salesforce security token is, when it's required, and how to reset it."),
    ("📋 Required fields?",        "What are the required fields for each of the six FSC Insurance objects this app generates?"),
    ("🏦 Sandbox vs Prod",         "What are the key differences I should know between loading test data into a Salesforce sandbox versus production?"),
    ("🧹 Clean up loaded data",    "Give me a SOQL strategy and delete approach to remove the test records this app loaded into my org."),
]


# ─────────────────────────────────────────────────────────────────────────────
# MAIN RENDER FUNCTION
# ─────────────────────────────────────────────────────────────────────────────
def render_agent_chat() -> None:
    """
    Renders the full agentic chat panel.
    Call this from fsc_data_generator_v2.py after the existing three-column layout.
    """

    # ── Session state init ────────────────────────────────────────────────
    if "agent_messages" not in st.session_state:
        st.session_state.agent_messages = []
    if "agent_input_key" not in st.session_state:
        st.session_state.agent_input_key = 0

    st.markdown("---")
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #0d1b2a 0%, #1a3a5c 100%);
        border-radius: 12px;
        padding: 1.5rem 2rem;
        margin-bottom: 1.5rem;
        border: 1px solid #2563a844;
    ">
        <h2 style="margin:0;color:#e8f4fd;font-size:1.4rem;font-weight:700;">
            🤖 FSC Data Assistant
        </h2>
        <p style="margin:0.3rem 0 0;color:#93c5fd;font-size:0.9rem;">
            Ask me anything about this dataset, Salesforce FSC Insurance objects, \
upload troubleshooting, or data strategy.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Two-column layout: chat | context panel ───────────────────────────
    chat_col, ctx_col = st.columns([3, 1], gap="large")

    with ctx_col:
        st.markdown("#### ⚡ Quick Actions")
        for label, prompt in _QUICK_ACTIONS:
            if st.button(label, use_container_width=True, key=f"qa_{label[:12]}"):
                _submit_message(prompt)
                st.rerun()

        st.markdown("---")
        st.markdown("#### 🗂 Session Context")
        ss = st.session_state
        if ss.get("generated"):
            dfs = {
                "Campaigns":     ss.get("df_campaigns"),
                "Leads":         ss.get("df_leads"),
                "Accounts":      ss.get("df_accounts"),
                "Contacts":      ss.get("df_contacts"),
                "Opportunities": ss.get("df_opps"),
                "Policies":      ss.get("df_policies"),
            }
            for name, df in dfs.items():
                if df is not None:
                    st.caption(f"**{name}**: {len(df):,} rows")
            st.caption(f"Seed: `{ss.get('_seed_used','—')}`")
        else:
            st.caption("No dataset generated yet.")

        sf_ok = ss.get("sf_connected", False)
        st.markdown(
            f"**SF:** {'🟢 ' + ss.get('sf_org_name','Connected') if sf_ok else '⚪ Not connected'}"
        )

        if st.session_state.agent_messages:
            st.markdown("---")
            if st.button("🗑 Clear chat", use_container_width=True):
                st.session_state.agent_messages = []
                st.rerun()

    with chat_col:
        # ── Chat history display ──────────────────────────────────────────
        history_container = st.container(height=480)
        with history_container:
            if not st.session_state.agent_messages:
                st.markdown("""
                <div style="text-align:center;padding:3rem 1rem;color:#64748b;">
                    <div style="font-size:2.5rem;margin-bottom:0.8rem">🏛️</div>
                    <div style="font-size:1rem;font-weight:600;color:#94a3b8;">
                        FSC Data Assistant is ready
                    </div>
                    <div style="font-size:0.85rem;margin-top:0.4rem;color:#64748b;">
                        Ask a question or use a Quick Action →
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                for msg in st.session_state.agent_messages:
                    with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "🤖"):
                        st.markdown(msg["content"])
                        st.caption(msg.get("ts", ""))

        # ── Input area ────────────────────────────────────────────────────
        user_input = st.chat_input(
            "Ask about FSC objects, upload errors, SOQL, field mappings…",
            key=f"agent_chat_input_{st.session_state.agent_input_key}",
        )

        if user_input and user_input.strip():
            _submit_message(user_input.strip())
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# MESSAGE HANDLING
# ─────────────────────────────────────────────────────────────────────────────
def _submit_message(user_text: str) -> None:
    """Add user message, call the API, append assistant reply."""
    ts = datetime.now().strftime("%H:%M")
    st.session_state.agent_messages.append({
        "role": "user",
        "content": user_text,
        "ts": ts,
    })

    client, err = _get_client()
    if err:
        st.session_state.agent_messages.append({
            "role": "assistant",
            "content": f"⚠️ **Configuration error:** {err}\n\nSet `ANTHROPIC_API_KEY` in your `.env` file and restart.",
            "ts": datetime.now().strftime("%H:%M"),
        })
        return

    # Build messages list (exclude ts field — not part of API schema)
    api_messages = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.agent_messages
    ]

    system_prompt = _build_system_prompt()

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=system_prompt,
            messages=api_messages,
        )
        reply = response.content[0].text
    except Exception as exc:
        reply = f"⚠️ **API error:** `{exc}`\n\nCheck your API key and network connection."

    st.session_state.agent_messages.append({
        "role": "assistant",
        "content": reply,
        "ts": datetime.now().strftime("%H:%M"),
    })
    # Bump input key so Streamlit clears the chat_input widget
    st.session_state.agent_input_key += 1
