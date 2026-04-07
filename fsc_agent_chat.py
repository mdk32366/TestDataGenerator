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
from pathlib import Path

import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG MANAGEMENT — Import from main app or define locally
# ─────────────────────────────────────────────────────────────────────────────
CONFIG_DIR = Path("./.fsc_configs")
CONFIG_DIR.mkdir(exist_ok=True)

def load_config_for_chat(config_name: str) -> tuple[bool, dict, str]:
    """Load a configuration. Returns (success, config_dict, message)."""
    try:
        config_file = CONFIG_DIR / f"{config_name}.json"
        if not config_file.exists():
            return False, {}, f"Config '{config_name}' not found."
        with open(config_file, "r") as f:
            config_data = json.load(f)
        return True, config_data, f"✅ Config '{config_name}' loaded."
    except Exception as e:
        return False, {}, f"❌ Failed to load config: {e}"

def list_configs_for_chat() -> list[str]:
    """List all available saved configurations."""
    return sorted([f.stem for f in CONFIG_DIR.glob("*.json")])

def save_config_for_chat(config_name: str, config_data: dict) -> tuple[bool, str]:
    """Save a configuration to disk. Returns (success, message)."""
    try:
        config_file = CONFIG_DIR / f"{config_name}.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f, indent=2)
        return True, f"✅ Config '{config_name}' saved successfully."
    except Exception as e:
        return False, f"❌ Failed to save config: {e}"

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
            try:
                load_dotenv(encoding='utf-8-sig')
            except (UnicodeDecodeError, Exception):
                # If .env file is corrupted, try without specifying encoding or skip it
                try:
                    load_dotenv()
                except Exception:
                    pass  # silently skip if .env is unreadable
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
- The app's current dataset state and saved configurations (injected below)
- Saving and loading dataset configurations for fast reuse

## Your Actions
You can perform the following actions directly with this assistant:
- **Auto-Configure Datasets** — If the user describes a desired dataset (e.g., "I want 100 accounts \
in California, insurance industry, with Home and Auto policies"), the system will intelligently parse \
their request using Claude and auto-configure all the sidebar parameters. The user then just needs to \
click **Generate Dataset** in the middle column. This is the recommended workflow!
- **New Chat** — Click the **📝 New Chat** button to start fresh with a brand new conversation. Chat \
history will be cleared, allowing you to ask about a completely different dataset.
- **Generate CSV files** — If the user asks you to "generate csv", "create csv", or "download csv", \
the system will automatically create downloadable CSVs for all six objects. You can trigger this by \
mentioning it naturally in the chat, OR the user can click the button. Simply respond that you've \
triggered the action.
- **Save Configuration** — If the user asks to "save config", "save configuration", or "save current config", \
the system will automatically save the current dataset configuration with an auto-generated name and \
store it for later reuse. The chat will confirm the saved config name.
- **Combined Actions** — The user can ask to "save config and generate csv" or similar, and both \
actions will be triggered in sequence.
- **Describe → Configure → Generate → Save → Export Workflow** — User can now say something like: \
"I want 500 accounts across CA, OR, WA for the insurance industry. Save as 'Pacific Northwest dataset' \
and generate the CSVs." The system will configure, then on the next request generate CSVs.

## What you do NOT do
- **DO NOT attempt to connect to Salesforce.** If the user asks you to load data to Salesforce, \
explain the process and direct them to use the sidebar Salesforce Connection form and Bulk Loader.
- **DO NOT store or transmit credentials.** Never ask for or accept Salesforce credentials in the chat.
- **DO NOT modify the app's configuration or settings.** Those are controlled via the sidebar.

## Configuration Management
The app supports saving and reloading dataset configurations. You can:
- List available saved configs (e.g., "show available saved configs")
- Ask the user to load a config and generate (e.g., "Generate from West Coast Dataset")
- Explain how the save/load feature works and why it's useful

Available configs: {available_configs}

## Current dataset state
{dataset_state}

## Personality
Professional but direct. You give concrete, actionable answers. You never hallucinate \
Salesforce field names — if you're unsure about a specific API name, you say so and \
recommend checking Object Manager. You speak fluently about Applied Epic, Cosmos DB, \
Azure ADF, Snowflake, and the broader integration stack this app feeds into.

## Rules
- Keep replies concise. Use bullet points for lists of steps. Use code blocks for SOQL, JSON, Python.
- If the user asks you to generate or modify data, remind them the sidebar controls do that — \
  your job is to advise and explain, not to re-run generators.
- Never suggest they paste credentials into the chat. Always point to the sidebar Salesforce Connection form.
- If the user is clearly debugging a load failure, walk through the error systematically: \
  field validation → API limits → permission sets → object accessibility.
- When discussing saved configs, always offer to help them load and generate from a specific config.
""").strip()


def _build_system_prompt() -> str:
    """Inject live dataset stats and available configs into the system prompt."""
    ss = st.session_state
    
    # Build config list
    available_configs = list_configs_for_chat()
    if available_configs:
        configs_block = "  - " + ", ".join(available_configs)
    else:
        configs_block = "  - (none saved yet)"
    
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
        # Add current loaded config
        if ss.get("loaded_config_name"):
            state_block += f"\n  - Current config: {ss.get('loaded_config_name')}"
    
    return _SYSTEM_BASE.format(dataset_state=state_block, available_configs=configs_block)


# ─────────────────────────────────────────────────────────────────────────────
# INTELLIGENT DATASET CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
def _parse_and_configure_dataset(user_request: str) -> str:
    """
    Use Claude to intelligently parse a dataset request and configure the app.
    Extracts: accounts, industries, regions, campaigns, etc.
    Returns a confirmation message.
    """
    client, err = _get_client()
    if err:
        return f"❌ Cannot parse request: {err}"
    
    # Use Claude to extract parameters with a simpler, clearer prompt
    extraction_prompt = f"""Extract parameters from this request: "{user_request}"

Return ONLY valid JSON. Null any field you cannot determine:

{{
  "num_accounts": null or a number,
  "industries": [] or list from [Insurance, Financial Services, Healthcare, Real Estate, Manufacturing, Technology, Retail, Hospitality],
  "region": null or one of [All 50 States, Northeast, Midwest, South, West, Custom],
  "custom_states": [] or [CA, OR, WA, etc.] if region is Custom,
  "num_campaigns": null or a number,
  "policy_types": [] or list from [Homeowners, Auto, Life, Commercial Property, General Liability, Workers Compensation, Umbrella],
  "carriers": [] or list of carrier names,
  "contacts_per_account": null or 1-5,
  "leads_per_campaign": null or a number
}}

Example input: "100 accounts in CA and OR, insurance industry"
Example output: {{"num_accounts": 100, "industries": ["Insurance"], "region": "Custom", "custom_states": ["CA", "OR"], "num_campaigns": null, "policy_types": [], "carriers": [], "contacts_per_account": null, "leads_per_campaign": null}}

IMPORTANT: Return ONLY the JSON object, starting with {{ and ending with }}, no other text.
"""
    
    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            messages=[{"role": "user", "content": extraction_prompt}]
        )
        
        json_str = response.content[0].text.strip()
        
        # Clean up the response in case there's extra text
        if json_str.startswith("```"):
            # Remove markdown code blocks if present
            json_str = json_str.split("```")[1]
            if json_str.startswith("json"):
                json_str = json_str[4:]
            json_str = json_str.strip()
        
        # Try to extract JSON if wrapped in other text
        if "{" in json_str and "}" in json_str:
            json_str = json_str[json_str.index("{"):json_str.rindex("}")+1]
        
        # Try to parse JSON
        try:
            params = json.loads(json_str)
        except json.JSONDecodeError as e:
            st.write(f"Debug: Claude returned: {json_str[:200]}")  # Debug output
            return f"⚠️ Parsing issue with your request. Please try: '100 accounts, insurance industry, CA and OR'"
        
        ss = st.session_state
        
        # Apply configuration
        config_summary = ["**✅ Configuring dataset:**"]
        
        if params.get("num_accounts"):
            ss["cfg_num_accounts"] = int(params["num_accounts"])
            config_summary.append(f"  • Accounts: {params['num_accounts']}")
        
        if params.get("industries"):
            valid_industries = ["Insurance", "Financial Services", "Healthcare", "Real Estate", "Manufacturing", "Technology", "Retail", "Hospitality"]
            industries = [ind for ind in params["industries"] if ind in valid_industries]
            if industries:
                ss["cfg_industries"] = industries
                config_summary.append(f"  • Industries: {', '.join(industries)}")
        
        if params.get("region"):
            region = params["region"]
            if region in ["Northeast", "Midwest", "South", "West", "All 50 States"]:
                ss["cfg_region"] = region
                config_summary.append(f"  • Region: {region}")
            elif region == "Custom" and params.get("custom_states"):
                ss["cfg_region"] = "Custom"
                ss["cfg_custom_states"] = params["custom_states"]
                config_summary.append(f"  • States: {', '.join(params['custom_states'])}")
        
        if params.get("num_campaigns"):
            ss["cfg_num_campaigns"] = int(params["num_campaigns"])
            config_summary.append(f"  • Campaigns: {params['num_campaigns']}")
        
        if params.get("policy_types"):
            valid_policies = ["Homeowners", "Auto", "Life", "Commercial Property", "General Liability", "Workers Compensation", "Umbrella"]
            policies = [p for p in params["policy_types"] if p in valid_policies]
            if policies:
                ss["cfg_policy_types"] = policies
                config_summary.append(f"  • Policy Types: {', '.join(policies)}")
        
        if params.get("contacts_per_account"):
            ss["cfg_contacts_per_account"] = min(5, max(1, int(params["contacts_per_account"])))
            config_summary.append(f"  • Contacts/Account: {ss['cfg_contacts_per_account']}")
        
        if params.get("leads_per_campaign"):
            ss["cfg_leads_per_campaign"] = int(params["leads_per_campaign"])
            config_summary.append(f"  • Leads/Campaign: {params['leads_per_campaign']}")
        
        if params.get("carriers"):
            ss["cfg_carriers"] = params["carriers"][:10]
            config_summary.append(f"  • Carriers: {', '.join(ss['cfg_carriers'])}")
        
        msg = "\n".join(config_summary)
        msg += "\n\n👉 **Next:** Click **⚡ Generate Dataset** in the middle column, then ask me to **save config and generate csv**"
        
        ss["_parsed_dataset_request"] = True
        return msg
        
    except Exception as e:
        return f"⚠️ Error: {str(e)[:100]}. Try being more specific: '100 accounts, insurance industry, CA and OR'"


# ─────────────────────────────────────────────────────────────────────────────
# CSV GENERATION ACTION
# ─────────────────────────────────────────────────────────────────────────────
def _generate_csv_files() -> str:
    """
    Generate CSV files from the current dataset and store them in session state.
    Returns a success/info message.
    """
    ss = st.session_state
    if not ss.get("generated"):
        return "❌ No dataset has been generated yet. Please generate a dataset first from the configuration panel."
    
    # Check that we have dataframes
    dfs = {
        "Campaigns": ss.get("df_campaigns"),
        "Leads": ss.get("df_leads"),
        "Accounts": ss.get("df_accounts"),
        "Contacts": ss.get("df_contacts"),
        "Opportunities": ss.get("df_opps"),
        "InsurancePolicies": ss.get("df_policies"),
    }
    
    csv_files = {}
    for name, df in dfs.items():
        if df is not None and len(df) > 0:
            try:
                csv_data = df.to_csv(index=False)
                csv_files[f"{name}.csv"] = csv_data
            except Exception as e:
                return f"❌ Error generating CSV for {name}: {e}"
    
    # Store in session state for download
    ss["csv_files_ready"] = csv_files
    ss["csv_generation_timestamp"] = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    count = len(csv_files)
    total_rows = sum(len(df) for df in dfs.values() if df is not None)
    return f"✅ **CSV files generated!** {count} files ready ({total_rows:,} total records). Scroll to the **{{ 📥 Download }}** section in the center column to download."


# ─────────────────────────────────────────────────────────────────────────────
# SAVE CONFIGURATION ACTION
# ─────────────────────────────────────────────────────────────────────────────
def _save_current_config() -> str:
    """
    Save the current dataset configuration from session state.
    Returns a success/info message and prompts to generate CSVs.
    """
    ss = st.session_state
    
    # Collect all current configuration values
    try:
        config_data = {
            "region": ss.get("cfg_region", "All 50 States"),
            "custom_states": ss.get("cfg_custom_states", []) if ss.get("cfg_region") == "Custom" else [],
            "num_campaigns": ss.get("cfg_num_campaigns", 0),
            "campaign_names": ss.get("cfg_campaign_names", ""),
            "campaign_type": ss.get("cfg_campaign_type", ""),
            "campaign_status": ss.get("cfg_campaign_status", []),
            "budget_range": ss.get("cfg_budget_range", [10, 50]),
            "revenue_range": ss.get("cfg_revenue_range", [100, 500]),
            "leads_per_campaign": ss.get("cfg_leads_per_campaign", 0),
            "num_accounts": ss.get("cfg_num_accounts", 0),
            "contacts_per_account": ss.get("cfg_contacts_per_account", 0),
            "industries": ss.get("cfg_industries", []),
            "acct_types": ss.get("cfg_acct_types", []),
            "acct_sources": ss.get("cfg_acct_sources", []),
            "contact_titles": ss.get("cfg_contact_titles", []),
            "closed_won_pct": ss.get("cfg_closed_won_pct", 0),
            "opp_amount_range": ss.get("cfg_opp_amount_range", [25, 300]),
            "closed_months_back": ss.get("cfg_closed_months_back", 0),
            "open_months_fwd": ss.get("cfg_open_months_fwd", 0),
            "opp_types": ss.get("cfg_opp_types", []),
            "policy_types": ss.get("cfg_policy_types", []),
            "carriers": ss.get("cfg_carriers", []),
            "premium_pct_range": ss.get("cfg_premium_pct_range", [3, 8]),
            "payment_methods": ss.get("cfg_payment_methods", []),
            "payment_freqs": ss.get("cfg_payment_freqs", []),
            "seed_val": ss.get("cfg_seed_val", 0),
            "saved_at": datetime.now().isoformat(),
        }
    except Exception as e:
        return f"❌ Error collecting configuration: {e}"
    
    # Generate a descriptive config name from the current settings
    region = config_data.get("region", "All 50 States")
    accounts = config_data.get("num_accounts", 0)
    timestamp = datetime.now().strftime("%m%d_%H%M")
    config_name = f"{region.replace(' ', '_')}_{accounts}accts_{timestamp}"
    
    # Save the configuration
    success, msg = save_config_for_chat(config_name, config_data)
    if not success:
        return f"❌ Failed to save configuration: {msg}"
    
    # Return success message and prompt for CSV generation
    ss["last_saved_config"] = config_name
    return f"✅ **Configuration saved as '{config_name}'**\n\nWould you like me to generate CSV files now? Click the **📥 Generate CSV files** button or let me know!"


# ─────────────────────────────────────────────────────────────────────────────
# QUICK-ACTION BUTTONS
# ─────────────────────────────────────────────────────────────────────────────
def _get_quick_actions():
    """Build quick action list, including saved configs."""
    actions = [
        ("🔢 How many records?",       "Summarise the current dataset: how many records are in each object and what is the total?"),
        ("� Save Current Config",     "_SAVE_CONFIG_ACTION_"),
        ("📥 Generate CSV files",      "_CSV_ACTION_"),
        ("⚠️ Why did my upload fail?", "Walk me through the most common reasons an InsurancePolicy upload fails and how to fix each one."),
        ("🔑 Security token help",     "Explain what a Salesforce security token is, when it's required, and how to reset it."),
        ("📋 Required fields?",        "What are the required fields for each of the six FSC Insurance objects this app generates?"),
        ("🏦 Sandbox vs Prod",         "What are the key differences I should know between loading test data into a Salesforce sandbox versus production?"),
        ("🧹 Clean up loaded data",    "Give me a SOQL strategy and delete approach to remove the test records this app loaded into my org."),
    ]
    
    # Add saved config actions
    configs = list_configs_for_chat()
    if configs:
        actions.insert(6, ("📂 Show saved configs", f"List my saved configurations: {', '.join(configs)}"))
    
    return actions


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
    chat_col, ctx_col = st.columns([3.5, 0.8], gap="medium")

    with ctx_col:
        st.markdown("#### ⚡ Quick Actions")
        quick_actions = _get_quick_actions()
        # Arrange quick actions in 2 columns
        for i in range(0, len(quick_actions), 2):
            qa_col1, qa_col2 = st.columns(2, gap="small")
            label1, prompt1 = quick_actions[i]
            # Handle save config action specially
            if prompt1 == "_SAVE_CONFIG_ACTION_":
                if qa_col1.button(label1, use_container_width=True, key=f"qa_{label1[:10]}"):
                    msg = _save_current_config()
                    st.session_state.agent_messages.append({
                        "role": "assistant",
                        "content": msg,
                        "ts": datetime.now().strftime("%H:%M"),
                    })
                    st.rerun()
            # Handle CSV action specially
            elif prompt1 == "_CSV_ACTION_":
                if qa_col1.button(label1, use_container_width=True, key=f"qa_{label1[:10]}"):
                    msg = _generate_csv_files()
                    st.session_state.agent_messages.append({
                        "role": "assistant",
                        "content": msg,
                        "ts": datetime.now().strftime("%H:%M"),
                    })
                    st.rerun()
            else:
                if qa_col1.button(label1, use_container_width=True, key=f"qa_{label1[:10]}"):
                    _submit_message(prompt1)
                    st.rerun()
            if i + 1 < len(quick_actions):
                label2, prompt2 = quick_actions[i + 1]
                # Handle save config action specially
                if prompt2 == "_SAVE_CONFIG_ACTION_":
                    if qa_col2.button(label2, use_container_width=True, key=f"qa_{label2[:10]}"):
                        msg = _save_current_config()
                        st.session_state.agent_messages.append({
                            "role": "assistant",
                            "content": msg,
                            "ts": datetime.now().strftime("%H:%M"),
                        })
                        st.rerun()
                # Handle CSV action specially
                elif prompt2 == "_CSV_ACTION_":
                    if qa_col2.button(label2, use_container_width=True, key=f"qa_{label2[:10]}"):
                        msg = _generate_csv_files()
                        st.session_state.agent_messages.append({
                            "role": "assistant",
                            "content": msg,
                            "ts": datetime.now().strftime("%H:%M"),
                        })
                        st.rerun()
                else:
                    if qa_col2.button(label2, use_container_width=True, key=f"qa_{label2[:10]}"):
                        _submit_message(prompt2)
                        st.rerun()
            else:
                qa_col2.empty()

        st.markdown("---")
        st.markdown("#### 📂 Configs")
        available_configs = list_configs_for_chat()
        if available_configs:
            st.caption(f"**{len(available_configs)} configs saved**")
            selected = st.selectbox(
                "Quick load:",
                ["— Select config —"] + available_configs,
                label_visibility="collapsed",
                key="chat_config_selector"
            )
            if selected != "— Select config —":
                if st.button("↻ Load & Generate", use_container_width=True, key=f"load_gen_{selected}"):
                    _load_and_generate_config(selected)
                    st.rerun()
        else:
            st.caption("No configs saved yet. Create one from the left panel!")

        st.markdown("---")
        st.markdown("#### � Context")
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
        # ── New Chat button ────────────────────────────────────────────────
        chat_controls = st.columns([2, 1])
        with chat_controls[1]:
            if st.button("📝 New Chat", use_container_width=True, type="secondary"):
                st.session_state.agent_messages = []
                st.session_state.agent_input_key += 1
                st.rerun()
        
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
def _load_and_generate_config(config_name: str) -> None:
    """Load a saved config and trigger dataset generation."""
    success, config_data, msg = load_config_for_chat(config_name)
    if not success:
        st.error(msg)
        return
    
    # Map config data to session state keys
    config_mapping = {
        "region": "cfg_region",
        "custom_states": "cfg_custom_states",
        "num_campaigns": "cfg_num_campaigns",
        "campaign_names": "cfg_campaign_names",
        "campaign_type": "cfg_campaign_type",
        "campaign_status": "cfg_campaign_status",
        "budget_range": "cfg_budget_range",
        "revenue_range": "cfg_revenue_range",
        "leads_per_campaign": "cfg_leads_per_campaign",
        "num_accounts": "cfg_num_accounts",
        "contacts_per_account": "cfg_contacts_per_account",
        "industries": "cfg_industries",
        "acct_types": "cfg_acct_types",
        "acct_sources": "cfg_acct_sources",
        "contact_titles": "cfg_contact_titles",
        "closed_won_pct": "cfg_closed_won_pct",
        "opp_amount_range": "cfg_opp_amount_range",
        "closed_months_back": "cfg_closed_months_back",
        "open_months_fwd": "cfg_open_months_fwd",
        "opp_types": "cfg_opp_types",
        "policy_types": "cfg_policy_types",
        "carriers": "cfg_carriers",
        "premium_pct_range": "cfg_premium_pct_range",
        "payment_methods": "cfg_payment_methods",
        "payment_freqs": "cfg_payment_freqs",
        "seed_val": "cfg_seed_val",
    }
    
    for cfg_key, state_key in config_mapping.items():
        if cfg_key in config_data:
            st.session_state[state_key] = config_data[cfg_key]
    
    st.session_state.loaded_config_name = config_name
    st.success(f"✅ Config '{config_name}' loaded! Scroll down to click **⚡ Generate Dataset** to create the data.")

def _trigger_generation() -> None:
    """Trigger dataset generation with current session state."""
    from pathlib import Path
    import random
    
    ss = st.session_state
    
    # Get region/states
    region = ss.get("cfg_region", "All 50 States")
    custom_states = ss.get("cfg_custom_states", [])
    
    # Import states_for_region from the main module (we need to replicate the logic)
    # For now, we'll use a simplified approach
    US_CITIES = {
        "AL": (["Birmingham","Montgomery","Huntsville","Mobile","Tuscaloosa","Hoover","Dothan","Auburn","Decatur","Madison"], "35"),
        "AK": (["Anchorage","Fairbanks","Juneau","Sitka","Ketchikan","Wasilla","Kenai","Kodiak","Palmer","Homer"], "99"),
        "AZ": (["Phoenix","Tucson","Mesa","Chandler","Scottsdale","Glendale","Gilbert","Tempe","Peoria","Surprise"], "85"),
    }
    
    # We can't actually run the generators from here (they're in the main file)
    # Instead, set a flag that the main app will see
    ss["trigger_generation_from_chat"] = True
    st.success(f"✅ Config '{ss.get('loaded_config_name')}' loaded! Scroll down to click **Generate Dataset**.")

def _detect_and_execute_actions(user_text: str) -> list[str]:
    """
    Detect action keywords in user message and execute corresponding actions.
    Returns list of messages to add to chat (empty if no actions matched).
    """
    user_lower = user_text.lower()
    messages = []
    ts = datetime.now().strftime("%H:%M")
    
    # Detect save config action
    save_keywords = ["save config", "save configuration", "save this config", "save current config", "save the config"]
    should_save = any(kw in user_lower for kw in save_keywords)
    
    # Detect CSV generation action
    csv_keywords = ["generate csv", "create csv", "make csv", "download csv", "create csvs", "generate csvs"]
    should_generate_csv = any(kw in user_lower for kw in csv_keywords)
    
    # Detect dataset configuration request (contains numbers + industry/region keywords)
    dataset_indicators = ["account", "accounts", "campaign", "campaigns", "industry", "industries", 
                         "state", "states", "region", "regions", "policy", "policies", "carrier"]
    has_number = any(char.isdigit() for char in user_text)
    has_dataset_keyword = any(kw in user_lower for kw in dataset_indicators)
    is_not_action_only = not any(kw in user_lower for kw in save_keywords + csv_keywords)
    
    should_configure = has_number and has_dataset_keyword and is_not_action_only and len(user_text.split()) > 3
    
    # Execute dataset configuration if detected
    if should_configure and not (should_save or should_generate_csv):
        msg = _parse_and_configure_dataset(user_text)
        messages.append({
            "role": "assistant",
            "content": msg,
            "ts": ts,
        })
        return messages  # Return early; don't combine with other actions
    
    # Execute save config if requested
    if should_save:
        msg = _save_current_config()
        messages.append({
            "role": "assistant",
            "content": msg,
            "ts": ts,
        })
    
    # Execute CSV generation if requested
    if should_generate_csv:
        msg = _generate_csv_files()
        messages.append({
            "role": "assistant",
            "content": msg,
            "ts": ts,
        })
    
    return messages


def _submit_message(user_text: str) -> None:
    """Add user message, check for actions, call the API, append assistant reply."""
    ts = datetime.now().strftime("%H:%M")
    st.session_state.agent_messages.append({
        "role": "user",
        "content": user_text,
        "ts": ts,
    })

    # Check for semantic actions (save config, generate csv, configure dataset, etc.)
    action_messages = _detect_and_execute_actions(user_text)
    if action_messages:
        # Add all action results to chat
        st.session_state.agent_messages.extend(action_messages)
        # If actions were executed, don't call Claude (unless user also asked a question)
        # Simple heuristic: if message is ONLY about actions, stop here
        simple_check = user_text.lower()
        has_dataset_indicators = any(kw in simple_check for kw in ["account", "accounts", "campaign", "campaigns", 
                                                                    "industry", "industries", "state", "states", 
                                                                    "region", "regions", "policy", "policies"])
        has_number = any(char.isdigit() for char in user_text)
        is_action_only = (any(kw in simple_check for kw in ["save config", "save configuration", "generate csv", 
                                                             "create csv", "make csv", "download csv"]) and len(user_text.split()) <= 5) \
                        or (has_number and has_dataset_indicators and len(user_text.split()) <= 15)
        
        if is_action_only:
            return  # Action executed, don't also call Claude
    
    # If no action-only message, proceed with Claude for advisory/conversational responses
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
