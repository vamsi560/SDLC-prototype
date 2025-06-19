import streamlit as st
import json
import time # To simulate API calls
from collections import OrderedDict # To maintain order of agents in workflow
import pandas as pd # For mock data in dashboard
import numpy as np # For mock data in dashboard

# --- Global Data Structures ---
# Define agent data with their roles, technologies, and sample LLM interaction types
# IMPORTANT: Added 'id' key to each agent dictionary.
# Added 'workflow_steps' for internal agent breadcrumbs and an indicator 'llm_step_index'
# to know at which step the LLM interaction happens.
# Added 'activates_agents' to explicitly show connections for the prototype.
agent_data = {
    1: {'id': 1, 'name': 'BA Agent', 'description': 'Translates business requirements into detailed technical specifications.', 'tech': 'Gemini 2.0 Flash', 'icon': '&#128221;', 'llm_feature': 'trd_generation', 'receives_input_from': [],
        'workflow_steps': [
            "Input: PO provides requirements (e.g., MS-Word, PDF)",
            "Step 1: Extract content and images",
            "Step 2: Process & categorize content",
            "Step 3: Call LLM to generate TRD", # LLM interaction happens here
            "Step 4: Create/Update release backlog",
            "Output: Present for review and approvals"
        ], 'llm_step_index': 3, 'activates_agents': ['Architect Agent', 'Evaluator Agent']
    },
    2: {'id': 2, 'name': 'Planner Agent', 'description': 'Picks items from Release backlog, schedules for Sprint, creates tasks.', 'tech': 'Gemini 2.0 Flash', 'icon': '&#128197;', 'llm_feature': 'sprint_summary', 'receives_input_from': ['Architect Agent'], # Planner now receives from Architect
        'workflow_steps': [
            "Input: Receive items from Release Backlog",
            "Step 1: Analyze complexity & dependencies",
            "Step 2: Estimate effort/capacity",
            "Step 3: Call LLM to generate Sprint Goal & Summary", # LLM interaction happens here
            "Step 4: Create detailed tasks for scrum team",
            "Output: Update project management system"
        ], 'llm_step_index': 3, 'activates_agents': ['Developer Agent', 'Evaluator Agent']
    },
    3: {'id': 3, 'name': 'Architect Agent', 'description': 'Sets up solution structure, creates Architecture and Solution diagrams, HLD.', 'tech': 'OpenAI 4.1, ArchitectGPT', 'icon': '&#127959;&#65039;', 'llm_feature': 'arch_pattern_suggestion', 'receives_input_from': ['BA Agent'],
        'workflow_steps': [
            "Input: Review high-level requirements (HLRs) & NFRs",
            "Step 1: Setup solution structure",
            "Step 2: Create conceptual architecture diagrams",
            "Step 3: Call LLM to suggest Architectural Patterns", # LLM interaction happens here
            "Step 4: Define technology stack & design patterns",
            "Output: Generate High-Level Design (HLD) document"
        ], 'llm_step_index': 3, 'activates_agents': ['Planner Agent', 'Evaluator Agent']
    },
    4: {'id': 4, 'name': 'Developer Agent', 'description': 'Writes code, unit tests, conducts unit testing.', 'tech': 'Gemini 2.0 Flash', 'icon': '&#128187;', 'llm_feature': 'code_generation', 'receives_input_from': ['Architect Agent', 'Planner Agent'],
        'workflow_steps': [
            "Input: Receive sprint tasks/user stories",
            "Step 1: Analyze requirements and designs",
            "Step 2: Call LLM to generate code snippets", # LLM interaction happens here
            "Step 3: Write and refine code (adhere to standards)",
            "Step 4: Write unit tests",
            "Output: Check-in code & manage merges"
        ], 'llm_step_index': 2, 'activates_agents': ['Functional Tester Agent', 'DevOps Agent', 'Evaluator Agent']
    },
    5: {'id': 5, 'name': 'Functional Tester Agent', 'description': 'Reviews user stories, writes functional test cases, automates, executes, logs defects.', 'tech': 'OpenAI 4.1', 'icon': '&#128270;', 'llm_feature': 'test_case_generation', 'receives_input_from': ['Developer Agent'],
        'workflow_steps': [
            "Input: Review user stories and acceptance criteria",
            "Step 1: Call LLM to generate functional test cases", # LLM interaction happens here
            "Step 2: Identify regression candidates for automation",
            "Step 3: Automate test cases",
            "Step 4: Execute automated tests",
            "Output: Log defects with reproduction steps"
        ], 'llm_step_index': 1, 'activates_agents': ['Evaluator Agent']
    },
    6: {'id': 6, 'name': 'DevOps Agent', 'description': 'Invokes CI/CD pipeline, manages deployments, infrastructure as code.', 'tech': 'Gemini 2.0 Flash', 'icon': '&#128640;', 'llm_feature': 'deployment_suggestion', 'receives_input_from': ['Developer Agent'],
        'workflow_steps': [
            "Input: Monitor code check-ins for changes",
            "Step 1: Trigger CI/CD pipeline execution",
            "Step 2: Perform build and packaging",
            "Step 3: Call LLM to suggest Deployment Strategy", # LLM interaction happens here
            "Step 4: Execute defined deployment strategy",
            "Output: Provision/manage infrastructure as code (IaC)"
        ], 'llm_step_index': 3, 'activates_agents': ['Ops Engineer Agent', 'FinOps Agent', 'Evaluator Agent']
    },
    7: {'id': 7, 'name': 'Ops Engineer Agent', 'description': 'Configures alerts, reviews logs, performs RCA.', 'tech': 'Gemini 2.0 Flash', 'icon': '&#128200;', 'llm_feature': 'rca_assistant', 'receives_input_from': ['DevOps Agent'],
        'workflow_steps': [
            "Input: Monitor system health and performance metrics",
            "Step 1: Configure and manage alerts",
            "Step 2: Review service logs for anomalies",
            "Step 3: Call LLM for Root Cause Analysis (RCA) assistance", # LLM interaction happens here
            "Step 4: Implement or trigger self-healing actions",
            "Output: Propose AIOps enhancements"
        ], 'llm_step_index': 3, 'activates_agents': ['FinOps Agent', 'Evaluator Agent']
    },
    8: {'id': 8, 'name': 'Evaluator Agent', 'description': 'Provides confidence score, validates action for each agent.', 'tech': 'OpenAI 4.1, Gemini 2.0 Flash', 'icon': '&#129513;', 'llm_feature': 'eval_rationale', 'receives_input_from': ['BA Agent', 'Planner Agent', 'Architect Agent', 'Developer Agent', 'Functional Tester Agent', 'DevOps Agent', 'Ops Engineer Agent'],
        'workflow_steps': [
            "Input: Receive agent action or output for review",
            "Step 1: Apply evaluation criteria and rubrics",
            "Step 2: Validate adherence to standards",
            "Step 3: Call LLM to generate Confidence Score Rationale", # LLM interaction happens here
            "Step 4: Flag discrepancies or potential errors",
            "Output: Provide structured feedback"
        ], 'llm_step_index': 3, 'activates_agents': []
    }, # Evaluator typically provides feedback back to source or reports
    9: {'id': 9, 'name': 'Memory Agent', 'description': 'Provides access to enterprise standards, guidelines, and historical data.', 'tech': 'ChromaDB', 'icon': '&#128210;', 'llm_feature': 'simulated_retrieval', 'receives_input_from': [],
        'workflow_steps': [
            "Input: Receive query for enterprise knowledge/context",
            "Step 1: Search internal knowledge base (ChromaDB)",
            "Step 2: Call LLM to interpret query/summarize retrieved documents", # LLM interaction happens here for complex queries/summaries
            "Output: Retrieve relevant documents/templates/data"
        ], 'llm_step_index': 2, 'activates_agents': []
    }, # Memory Agent usually just serves data on request
    10: {'id': 10, 'name': 'FinOps Agent', 'description': 'Cost optimization, Cost reports, Recommendations for cloud resource optimization.', 'tech': 'Gemini 2.0 Flash', 'icon': '&#128176;', 'llm_feature': 'finops_rationale', 'receives_input_from': ['DevOps Agent', 'Ops Engineer Agent'],
        'workflow_steps': [
            "Input: Collect cloud resource usage and spending data",
            "Step 1: Generate detailed cost reports",
            "Step 2: Analyze spending patterns",
            "Step 3: Call LLM to generate Cost Optimization Rationale", # LLM interaction happens here
            "Step 4: Identify optimization opportunities",
            "Output: Provide actionable recommendations"
        ], 'llm_step_index': 3, 'activates_agents': []
    } # FinOps provides reports/recommendations, doesn't typically activate next SDLC phase
}

# Define workflow phases, mapping to primary agents (using agent_data keys)
workflow_data = [
    {'phase_id': 'req_planning', 'name': '1. Requirements & Planning', 'description': 'Business requirements are transformed into detailed specifications.', 'primary_agent_id': 1}, # BA Agent
    {'phase_id': 'design_arch', 'name': '2. Design & Architecture', 'description': 'Solution blueprints and high-level designs are created.', 'primary_agent_id': 3}, # Architect Agent
    {'phase_id': 'sprint_planning', 'name': '3. Sprint Planning & Task Creation', 'description': 'Release backlog items are scheduled, and detailed tasks are created for sprints.', 'primary_agent_id': 2}, # Planner Agent (new phase order)
    {'phase_id': 'development', 'name': '4. Development', 'description': 'Code is generated, written, unit tested, and refined.', 'primary_agent_id': 4}, # Developer Agent
    {'phase_id': 'testing', 'name': '5. Testing & Validation', 'description': 'Functional test cases are generated, automated, and executed; defects are logged.', 'primary_agent_id': 5}, # Functional Tester Agent
    {'phase_id': 'ci_cd_deploy', 'name': '6. CI/CD & Deployment', 'description': 'Continuous integration, delivery, and automated deployments are orchestrated.', 'primary_agent_id': 6}, # DevOps Agent
    {'phase_id': 'operations', 'name': '7. Operations & Monitoring', 'description': 'Production systems are monitored, and incidents are managed with RCA.', 'primary_agent_id': 7}, # Ops Engineer Agent
    {'phase_id': 'cross_cutting_eval', 'name': '8. Cross-Cutting: Evaluation', 'description': 'The Evaluator agent assesses quality and provides feedback across the SDLC.', 'primary_agent_id': 8}, # Evaluator Agent
    {'phase_id': 'cross_cutting_finops', 'name': '9. Cross-Cutting: FinOps', 'description': 'The FinOps agent focuses on cloud cost optimization and financial insights.', 'primary_agent_id': 10} # FinOps Agent
]

# Custom order for agents in sidebar and main display (all agents for admin view)
all_agent_display_order = [1, 3, 2, 4, 5, 6, 7, 8, 10, 9] # BA, Architect, Planner, Developer, FT, DevOps, Ops, Evaluator, FinOps, Memory

# --- Hardcoded User Credentials and Role-to-Agent Mapping (for prototype demonstration) ---
USER_CREDENTIALS = {
    "admin": "adminpass",
    "ba_user": "bapass",
    "architect_user": "archpass",
    "planner_user": "planpass",
    "dev_user": "devpass",
    "qa_user": "qapass",
    "devops_user": "devopspass",
    "ops_user": "opspass",
}

# Map roles to a list of agent IDs they can access
ROLE_AGENT_ACCESS = {
    "admin": [agent['id'] for agent in agent_data.values()], # Admin sees all
    "ba_user": [1], # BA Agent only
    "architect_user": [3], # Architect Agent only
    "planner_user": [2], # Planner Agent only
    "dev_user": [4], # Developer Agent only
    "qa_user": [5], # Functional Tester only
    "devops_user": [6], # DevOps only
    "ops_user": [7], # Ops Engineer only
}

# --- Streamlit Session State Initialization ---
def initialize_session_state():
    st.session_state.current_phase_index = 0
    st.session_state.completed_phases_outputs = OrderedDict()
    st.session_state.agent_detailed_view = None
    st.session_state.current_agent_step_index = 0
    st.session_state.last_agent_output_for_phase_completion = None
    st.session_state.started = False
    st.session_state.is_authenticated = False
    st.session_state.logged_in_user_role = None
    st.session_state.current_view = 'agent_overview' # 'agent_overview', 'agent_detail', or 'dashboard'

if 'current_phase_index' not in st.session_state:
    initialize_session_state()

# --- LLM Call Simulation Function (Synchronous) ---
def call_llm_api(prompt):
    """
    Simulates a synchronous call to the Gemini API.
    In a real application, you would replace this with actual fetch/requests.
    """
    with st.spinner("Thinking... (Simulating LLM call)"): # Using spinner here
        time.sleep(2) # Simulate API latency

    # Placeholder for Gemini API Key - DO NOT HARDCODE IN PRODUCTION
    # The `apiKey` will be provided by the Canvas environment at runtime if left as ""
    apiKey = "" 
    apiUrl = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=" + apiKey

    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}]
    }

    try:
        # Mocking specific responses for the prototype
        if "Technical Requirements Document" in prompt:
            return "Generated TRD Snippet:\n\n*System Requirement:* User authentication via OAuth.\n*Functional Requirement:* Display order history.\n*Process Flow:* User clicks 'Login' -> redirected to OAuth provider -> authorizes app -> redirected back -> Session created."
        elif "sprint goal and a brief summary" in prompt:
            return "Sprint Goal: Successfully deliver essential user management and content creation features.\nKey Deliverables: User registration, login, profile management, basic article creation, and publishing."
        elif "architectural patterns" in prompt:
            return "Suggested Architectural Pattern: Microservices.\nPros: Scalability, fault isolation, technology diversity.\nCons: Operational complexity, distributed data management, inter-service communication overhead."
        elif "code snippet in a suitable language" in prompt:
            return "```python\ndef factorial(n):\n    if n == 0:\n        return 1\n    else:\n        return n * factorial(n-1)\n```"
        elif "functional test cases" in prompt:
            return "Test Cases for User Login:\n\n1. Valid credentials: User logs in successfully.\n2. Invalid password: Login fails, error message displayed.\n3. Invalid username: Login fails, error message displayed.\n4. Empty fields: Login fails, appropriate message shown."
        elif "deployment strategies" in prompt:
            return "Suggested Deployment Strategy: Blue-Green Deployment.\nPros: Zero downtime, easy rollback.\nCons: Requires double infrastructure, more complex setup."
        elif "root causes and initial diagnostic steps" in prompt:
            return "Potential Root Causes:\n1. High traffic/load exceeding capacity.\n2. Database connection pooling issues.\n3. Long-running queries.\nDiagnostic Steps:\n1. Check application metrics for peak usage times.\n2. Review database slow query logs.\n3. Analyze network latency between app and DB."
        elif "rationale for the confidence score" in prompt:
            return "Rationale: The score of X/10 is based on Y (e.g., completeness, adherence to standard, test pass rate). Strengths include A, B. Areas for improvement are C, D."
        elif "detailed explanation and rationale for the following cloud cost optimization recommendation" in prompt:
            return "Rationale for Right-sizing EC2 instances: This recommendation aims to align instance resources (CPU, memory) more closely with actual workload demands, reducing waste. Potential impact includes a 15-20% reduction in compute costs for underutilized instances."
        elif "Retrieve our enterprise coding standards" in prompt:
            return "Memory Agent Retrieval: Enterprise coding standards for Python require PEP 8 compliance, clear docstrings for all functions, and a max line length of 79 characters."
        else:
            return f"LLM Response to: '{prompt}'"
    except Exception as e:
        st.error(f"Error calling LLM: {e}")
        return f"Error calling LLM: {e}"

# --- UI Components ---

def display_agent_breadcrumbs(agent_id, current_step_index):
    agent = agent_data[agent_id]
    if not agent.get('workflow_steps'):
        return

    st.markdown(f"#### {agent['name']} Internal Workflow")
    cols = st.columns(len(agent['workflow_steps']))
    for i, step in enumerate(agent['workflow_steps']):
        with cols[i]:
            if i < current_step_index:
                st.markdown(f"""
                <div style="text-align: center; color: #94a3b8; opacity: 0.7;" title="Completed: {step}">
                    <span style="font-size: 1.5em;">&#10004;</span><br>
                    <small><s>{step}</s></small>
                </div>
                """, unsafe_allow_html=True)
            elif i == current_step_index:
                st.markdown(f"""
                <div style="text-align: center; color: #0369a1; font-weight: bold;" title="Current Step: {step}">
                    <span style="font-size: 1.5em;">&#9679;</span><br>
                    <small>{step}</small>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="text-align: center; color: #cbd5e1;" title="Upcoming Step: {step}">
                    <span style="font-size: 1.5em;">&#9675;</span><br>
                    <small>{step}</small>
                </div>
                """, unsafe_allow_html=True)
    st.markdown("---")


def display_agent_detail():
    if st.session_state.agent_detailed_view:
        agent_id = st.session_state.agent_detailed_view
        agent = agent_data.get(agent_id)
        
        if agent:
            st.subheader(f"{agent['icon']} {agent['name']} Details")
            st.markdown(f"**Role:** {agent['description']}")
            st.markdown(f"**Technology:** {agent['tech']}")
            
            # Agent internal breadcrumbs
            display_agent_breadcrumbs(agent_id, st.session_state.current_agent_step_index)

            # Initialize llm_output_key_for_agent at the beginning of the function
            llm_output_key_for_agent = f"llm_output_agent_{agent_id}_step_{agent.get('llm_step_index')}"


            if agent['receives_input_from']:
                st.markdown("#### Input Received (from previous agents in the SDLC flow):")
                for input_agent_name in agent['receives_input_from']:
                    input_received_content = "No input (or not applicable for this prototype step)."
                    
                    # Find the phase ID for the input agent
                    source_phase_id = None
                    # Search through all workflow phases to find the agent's primary phase
                    for p in workflow_data:
                        # Find agent ID by name
                        found_agent_id = next((aid for aid, ag in agent_data.items() if ag['name'] == input_agent_name), None)
                        if found_agent_id == p['primary_agent_id']:
                            source_phase_id = p['phase_id']
                            break

                    if source_phase_id and source_phase_id in st.session_state.completed_phases_outputs:
                        input_received_content = str(st.session_state.completed_phases_outputs[source_phase_id])
                    
                    if input_received_content != "No input (or not applicable for this prototype step).":
                         display_summary_content = input_received_content.splitlines()[0] + "..." if "\n" in input_received_content else input_received_content
                         
                         # Make the input content clickable to show full output (if applicable)
                         with st.expander(f"**From {input_agent_name}:** {display_summary_content}", expanded=False):
                             st.code(input_received_content, language='markdown') # Display full content in an expander

                    else:
                         st.markdown(f"<p style='color:#64748b; font-size:0.9em;'>From {input_agent_name}: (No relevant output yet from previous phase simulation)</p>", unsafe_allow_html=True)

            # --- LLM Interaction Section ---
            # Only show LLM interaction part if current_agent_step_index == agent.get('llm_step_index')
            if st.session_state.current_agent_step_index == agent.get('llm_step_index'):
                st.markdown("---")
                st.markdown(f"#### ✨ LLM Interaction: {agent['llm_feature'].replace('_', ' ').title()}")
                
                prompt_instructions = {
                    'trd_generation': "Enter a brief business requirement (e.g., 'User authentication via OAuth'):",
                    'sprint_summary': "Enter comma-separated sprint tasks (e.g., 'Implement user login, Design database schema'):",
                    'arch_pattern_suggestion': "Describe high-level requirements (e.g., 'Highly scalable, fault-tolerant'):",
                    'code_generation': "Describe a simple function to generate code for (e.g., 'Python function to calculate Fibonacci numbers'):",
                    'test_case_generation': "Enter a user story to generate test cases for (e.g., 'As a user, I can reset my password'):",
                    'deployment_suggestion': "Describe your application and environment for deployment suggestions (e.g., 'High-availability web app, zero downtime updates'):",
                    'rca_assistant': "Describe an incident or provide log snippets for RCA (e.g., 'High CPU usage, database timeouts'):",
                    'eval_rationale': "Describe the agent output and confidence score (e.g., 'TRD for login, Score: 8/10'):",
                    'simulated_retrieval': "Query for knowledge (e.g., 'Enterprise coding standards for Python'):",
                    'finops_rationale': "Describe a cost optimization recommendation (e.g., 'Switch from on-demand to reserved instances'):"
                }

                initial_input_values = {
                    'trd_generation': "As a user, I want to manage my profile.",
                    'sprint_summary': "Refactor legacy module, Integrate new payment gateway, Document API endpoints.",
                    'arch_pattern_suggestion': "Needs to support millions of users, be highly secure, and integrate with existing legacy systems.",
                    'code_generation': "A simple JavaScript function to reverse a string.",
                    'test_case_generation': "As an admin, I want to approve pending user registrations.",
                    'deployment_suggestion': "Microservices application, frequent updates, needs quick rollback capability.",
                    'rca_assistant': "Error: OutOfMemoryError in Java service 'billing-service' on production pod 'billing-xyz-123'.",
                    'eval_rationale': "Output: Test report showing 80% pass rate. Score: 8/10.",
                    'simulated_retrieval': "Retrieve our guidelines for microservice communication.",
                    'finops_rationale': "Consolidate unused S3 buckets to reduce storage costs."
                }

                # Use a unique key for the input text area based on agent ID and step
                current_input = st.text_area(prompt_instructions.get(agent['llm_feature'], "Enter input:"), 
                                            initial_input_values.get(agent['llm_feature'], ""), 
                                            key=f"agent_{agent_id}_step_{st.session_state.current_agent_step_index}_input")


                if st.button(f"Run {agent['name']} ({agent['llm_feature'].replace('_', ' ').title()})", 
                             key=f"run_agent_{agent_id}_step_{st.session_state.current_agent_step_index}"):
                    
                    # Store "Processing..." immediately
                    st.session_state[llm_output_key_for_agent] = "Processing..."
                    # Call synchronous LLM function (spinner handled inside call_llm_api)
                    response_text = call_llm_api(current_input) 
                    st.session_state[llm_output_key_for_agent] = response_text
                    # Store this LLM output for phase completion logic
                    st.session_state.last_agent_output_for_phase_completion = response_text
                    st.rerun() # Rerun to display output

                # Display LLM output if available for the current step
                if llm_output_key_for_agent in st.session_state and st.session_state[llm_output_key_for_agent] != "Processing...":
                    st.subheader("LLM Output:")
                    if agent['llm_feature'] == 'code_generation':
                        st.code(st.session_state[llm_output_key_for_agent], language='python')
                    else:
                        st.info(st.session_state[llm_output_key_for_agent])
                elif llm_output_key_for_agent in st.session_state and st.session_state[llm_output_key_for_agent] == "Processing...":
                     st.info("LLM is processing your request...")


            st.markdown("---")
            # Agent internal navigation buttons
            col_agent_nav1, col_agent_nav2 = st.columns(2)
            with col_agent_nav1:
                if st.session_state.current_agent_step_index > 0:
                    if st.button("Previous Agent Step", key=f"prev_agent_step_{agent_id}"):
                        st.session_state.current_agent_step_index -= 1
                        st.rerun()
            with col_agent_nav2:
                # Logic for automatic progression to the next agent/phase
                if st.session_state.current_agent_step_index < len(agent['workflow_steps']) - 1:
                    # If it's an LLM step, ensure LLM output is present before enabling next step
                    is_llm_step_and_output_ready = (st.session_state.current_agent_step_index == agent.get('llm_step_index')) and \
                                                   (llm_output_key_for_agent in st.session_state and \
                                                    st.session_state[llm_output_key_for_agent] not in ["Processing...", None])
                    
                    # Enable "Next Agent Step" if not an LLM step, or if it is and output is ready
                    can_go_next = (st.session_state.current_agent_step_index != agent.get('llm_step_index')) or is_llm_step_and_output_ready

                    if st.button("Next Agent Step", key=f"next_agent_step_{agent_id}", disabled=not can_go_next):
                        st.session_state.current_agent_step_index += 1
                        st.rerun()
                else:
                    # Logic when the last step of the agent's internal workflow is completed
                    st.success(f"You have completed {agent['name']}'s workflow!")
                    
                    st.markdown("#### Output Handoff & Agent Activation:")
                    st.markdown(f"The primary output of the {agent['name']} is: ")
                    if st.session_state.last_agent_output_for_phase_completion:
                        st.code(st.session_state.last_agent_output_for_phase_completion, language='markdown')
                    else:
                        st.info("No explicit LLM output was generated in this step, but the agent's tasks are considered complete.")

                    # --- New Logic for Role-Based Progression ---
                    if st.session_state.logged_in_user_role != 'admin':
                        st.info(f"Output from {agent['name']} has been saved to a shared memory for subsequent agents to consume.")
                        if st.button("Return to Agent Overview", key=f"return_overview_from_agent_{agent_id}"):
                            st.session_state.agent_detailed_view = None
                            st.session_state.current_agent_step_index = 0
                            st.session_state.last_agent_output_for_phase_completion = None
                            st.session_state.current_view = 'agent_overview'
                            st.rerun()
                    else: # Admin user retains direct progression capability
                        if agent['activates_agents']:
                            st.markdown(f"This output now **activates** the following agents:")
                            cols_activated = st.columns(len(agent['activates_agents']))
                            for i, activated_agent_name in enumerate(agent['activates_agents']):
                                with cols_activated[i]:
                                    activated_agent_id = next((aid for aid, ag in agent_data.items() if ag['name'] == activated_agent_name), None)
                                    if activated_agent_id:
                                        if st.button(f"Activate {activated_agent_name}", key=f"activate_{activated_agent_id}"):
                                            st.session_state.agent_detailed_view = activated_agent_id
                                            st.session_state.current_agent_step_index = 0
                                            st.session_state.last_agent_output_for_phase_completion = None
                                            st.rerun()

                        else:
                            st.markdown("This agent's output is for informational purposes or triggers downstream processes not directly represented as another agent in this prototype's linear flow.")

                        # Determine next automatic transition for primary phase agents (ONLY FOR ADMIN)
                        is_current_agent_primary_for_phase = (
                            st.session_state.current_phase_index < len(workflow_data) and
                            workflow_data[st.session_state.current_phase_index]['primary_agent_id'] == agent_id
                        )

                        if is_current_agent_primary_for_phase:
                            # Save the output for the completed phase
                            st.session_state.completed_phases_outputs[workflow_data[st.session_state.current_phase_index]['phase_id']] = \
                                st.session_state.get(llm_output_key_for_agent, "Agent ran but no specific output was generated.")

                            # If there's a next SDLC phase
                            if st.session_state.current_phase_index < len(workflow_data) - 1:
                                st.info(f"Automatically advancing to the next SDLC phase...")
                                st.session_state.current_phase_index += 1
                                next_primary_agent_id = workflow_data[st.session_state.current_phase_index]['primary_agent_id']
                                st.session_state.agent_detailed_view = next_primary_agent_id # Automatically open next primary agent
                                st.session_state.current_agent_step_index = 0 # Reset agent steps
                                st.session_state.last_agent_output_for_phase_completion = None # Clear output for new phase
                                st.rerun()
                            else:
                                st.success("You have completed the entire SDLC prototype workflow!")
                                st.balloons() # Add celebratory animation
                                if st.button("Return to Main View", key=f"return_main_from_agent_{agent_id}"):
                                    initialize_session_state() # Reset completely
                                    st.rerun()
                        else:
                            # If it's a cross-cutting agent or not the primary for its phase, just return to main phase view
                            st.info(f"Returning to the main SDLC workflow view.")
                            if st.button("Return to Main SDLC Workflow", key=f"return_workflow_from_agent_{agent_id}"):
                                st.session_state.agent_detailed_view = None
                                st.session_state.current_agent_step_index = 0
                                st.session_state.last_agent_output_for_phase_completion = None
                                st.session_state.current_view = 'agent_overview' # Ensure returning to agent overview
                                st.rerun()

            # Always provide a "Close Details" for manual exit
            # Only show if not auto-redirected, which means it's either the last phase or a non-primary agent
            # and the user hasn't chosen to return to the main view already.
            # This button will now also respect the admin/non-admin flow to avoid confusion
            if st.session_state.logged_in_user_role == 'admin':
                if not (st.session_state.current_agent_step_index == len(agent['workflow_steps']) -1 and is_current_agent_primary_for_phase):
                    st.button("Close Agent Details Manually", on_click=lambda: st.session_state.update(agent_detailed_view=None, current_agent_step_index=0, last_agent_output_for_phase_completion=None, current_view='agent_overview'))
            else: # For non-admin, always show return to overview
                 st.button("Close Agent Details Manually", on_click=lambda: st.session_state.update(agent_detailed_view=None, current_agent_step_index=0, last_agent_output_for_phase_completion=None, current_view='agent_overview'))


def display_dashboard():
    st.markdown("## AI Agent Performance Dashboard")
    st.markdown("""
        <p style='font-size:1.1em; color:#4a5568;'>
        Gain insights into the efficiency and impact of our AI agents through these simulated metrics and analytics.
        </p>
    """, unsafe_allow_html=True)

    user_role = st.session_state.logged_in_user_role

    if user_role == 'admin':
        # --- Admin Dashboard: Comprehensive View ---
        st.subheader("📊 Overall SDLC Performance Metrics (Admin View)")

        # Evaluator Agent Metrics (Admin's full view)
        st.markdown("### Evaluator Agent Metrics")
        confidence_data = {
            'Date': pd.to_datetime(['2025-01-01', '2025-01-15', '2025-02-01', '2025-02-15', '2025-03-01', '2025-03-15', '2025-04-01']),
            'Confidence Score': [7.5, 8.0, 8.2, 7.9, 8.5, 8.3, 8.7]
        }
        df_confidence = pd.DataFrame(confidence_data)
        st.line_chart(df_confidence.set_index('Date'))
        st.markdown("Historical trends of confidence scores provided by the Evaluator Agent for generated artifacts across all agents.")

        defect_data = {
            'Phase': ['Requirements', 'Design', 'Development', 'Testing', 'Deployment'],
            'Defects per KLOC': [0.5, 0.3, 1.2, 0.8, 0.1]
        }
        df_defect = pd.DataFrame(defect_data)
        st.bar_chart(df_defect.set_index('Phase'))
        st.markdown("Simulated defect density per thousand lines of code (KLOC) reported across SDLC phases.")
        
        validation_success_data = {
            'Agent Type': ['BA Agent', 'Architect Agent', 'Developer Agent', 'Functional Tester Agent', 'DevOps Agent'],
            'Success Rate (%)': [92, 88, 95, 98, 93]
        }
        df_validation_success = pd.DataFrame(validation_success_data)
        st.bar_chart(df_validation_success.set_index('Agent Type'))
        st.markdown("Percentage of outputs from various agents that successfully pass automated or human validation checks, indicating high quality and adherence to standards.")

        test_coverage_data = {
            'Component': ['User Auth', 'Order Mgmt', 'Reporting', 'Payment Gateway'],
            'Coverage (%)': [90, 85, 70, 95]
        }
        df_test_coverage = pd.DataFrame(test_coverage_data)
        st.bar_chart(df_test_coverage.set_index('Component'))
        st.markdown("Automated test coverage achieved for different application components, driven by Functional Tester Agent.")

        compliance_score = 91 # Example value
        st.metric(label="Average Compliance Score (Overall)", value=f"{compliance_score}%", delta="↑ 2% since last review")
        st.markdown("An aggregate score indicating adherence to regulatory and internal compliance standards across the board.")

        time_saved_hours = 1250 # Example total hours saved per month
        st.metric(label="Estimated Hours Saved Monthly (Overall)", value=f"{time_saved_hours} hrs", delta="↑ 150 hrs since last quarter")
        st.markdown("Aggregate estimated time saved across the SDLC due to AI agent automation.")

        error_reduction_rate = 35 # Example percentage
        st.metric(label="Overall Error Reduction Rate", value=f"{error_reduction_rate}%", delta="↓ 5% since last year")
        st.markdown("Overall reduction in critical errors and defects attributed to AI agent interventions.")
        
        mttd_hours = 0.5 # Example value in hours
        st.metric(label="Mean Time To Detect (MTTD) - Overall", value=f"{mttd_hours} hours", delta="↓ 0.2 hours this month")
        st.markdown("The average time taken to detect critical issues across the system.")


        # FinOps Agent Metrics (Admin's full view)
        st.markdown("### FinOps Agent Metrics")
        cost_savings_data = {
            'Optimization Type': ['Right-sizing Instances', 'Reserved Instances', 'Storage Tiering', 'Cloud Cleanup', 'Autoscaling Tuning'],
            'Estimated Savings ($)': [5000, 7000, 2000, 1000, 3500]
        }
        df_cost_savings = pd.DataFrame(cost_savings_data)
        st.bar_chart(df_cost_savings.set_index('Optimization Type'))
        st.markdown("Estimated monthly cost savings generated through FinOps Agent recommendations.")

        current_efficiency = 78 # Example value
        st.metric(label="Overall Cost Efficiency Score", value=f"{current_efficiency}%", delta="↑ 5% since last month")
        st.progress(current_efficiency / 100.0)
        st.markdown("A composite score reflecting overall cloud resource utilization and cost effectiveness.")

        # Memory Agent Insights (Admin Only)
        st.markdown("### Memory Agent Insights")
        st.info("The Memory Agent operates primarily as a backend knowledge retrieval service. Its effectiveness is reflected in the enhanced performance and accuracy of other agents, such as improved code generation or more precise architecture suggestions due to access to up-to-date enterprise standards and historical data.")
        retrieval_accuracy = 97
        st.metric(label="Knowledge Retrieval Accuracy", value=f"{retrieval_accuracy}%")
        st.markdown("Simulated accuracy of relevant knowledge retrieval for other agents.")


    elif user_role == 'ba_user':
        st.subheader("📝 BA Agent Dashboard: Requirements Quality")
        st.markdown("""
            <p style='font-size:0.9em; color:#64748b;'>
            Monitor the effectiveness of the BA Agent in translating business needs into clear, actionable requirements.
            </p>
        """, unsafe_allow_html=True)
        st.metric(label="Requirement Clarity Score", value="85%", delta="↑ 3% this sprint")
        st.markdown("Score reflecting the clarity and completeness of generated Technical Requirements Documents (TRDs).")
        st.metric(label="Traceability Linkage Rate", value="90%", delta="↑ 5% this release")
        st.markdown("Percentage of requirements successfully linked to corresponding design and development artifacts.")
        
        req_processed_data = pd.DataFrame({
            'Week': ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
            'Requirements Processed': [15, 18, 20, 17]
        }).set_index('Week')
        st.bar_chart(req_processed_data)
        st.markdown("Number of new business requirements processed and translated by the BA Agent per week.")

    elif user_role == 'architect_user':
        st.subheader("🏛️ Architect Agent Dashboard: Design Effectiveness")
        st.markdown("""
            <p style='font-size:0.9em; color:#64748b;'>
            Track the Architect Agent's impact on system design, pattern adoption, and long-term maintainability.
            </p>
        """, unsafe_allow_html=True)
        st.metric(label="Architectural Debt Index", value="1.5 (Lower is Better)", delta="↓ 0.2 points")
        st.markdown("Metric indicating the complexity and maintainability challenges within the system architecture.")
        st.metric(label="Reusable Component Identification Rate", value="70%", delta="↑ 8% this quarter")
        st.markdown("Percentage of new features that utilize existing reusable architectural components or patterns identified by the agent.")

        arch_decisions_data = pd.DataFrame({
            'Month': ['Jan', 'Feb', 'Mar', 'Apr'],
            'Architectural Decisions': [5, 7, 6, 8]
        }).set_index('Month')
        st.line_chart(arch_decisions_data)
        st.markdown("Trend of significant architectural decisions made and documented by the Architect Agent.")

    elif user_role == 'planner_user':
        st.subheader("🗓️ Planner Agent Dashboard: Sprint Management & Velocity")
        st.markdown("""
            <p style='font-size:0.9em; color:#64748b;'>
            Monitor the Planner Agent's performance in optimizing sprint planning, task breakdown, and commitment adherence.
            </p>
        """, unsafe_allow_html=True)
        st.metric(label="Sprint Commitment Adherence", value="90%", delta="↑ 2% last sprint")
        st.markdown("Percentage of committed sprint items successfully delivered by the team, influenced by Planner Agent's estimates.")
        st.metric(label="Task Granularity Score", value="4.2 / 5", delta="↑ 0.1 this sprint")
        st.markdown("Score reflecting how well large tasks are broken down into manageable, actionable units by the agent.")

        tasks_created_data = pd.DataFrame({
            'Sprint': ['S1', 'S2', 'S3', 'S4'],
            'Tasks Created': [120, 135, 140, 130]
        }).set_index('Sprint')
        st.bar_chart(tasks_created_data)
        st.markdown("Number of detailed tasks created by the Planner Agent for development teams per sprint.")

    elif user_role == 'dev_user':
        st.subheader("💻 Developer Agent Dashboard: Code Quality & Efficiency")
        st.markdown("""
            <p style='font-size:0.9em; color:#64748b;'>
            Gain insights into the Developer Agent's contribution to code generation, test coverage, and overall development velocity.
            </p>
        """, unsafe_allow_html=True)
        st.metric(label="Code Generation Efficiency", value="40%", delta="↑ 5% this month")
        st.markdown("Percentage of boilerplate or repetitive code generated directly by the Developer Agent, accelerating development.")
        st.metric(label="Unit Test Pass Rate", value="99.5%", delta="↑ 0.1% since last week")
        st.markdown("Rate at which automated unit tests (potentially generated or enhanced by the agent) are passing.")

        commits_data = pd.DataFrame({
            'Day': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
            'Code Commits': [10, 12, 9, 15, 8]
        }).set_index('Day')
        st.line_chart(commits_data)
        st.markdown("Daily frequency of code commits, indicating development activity supported by the agent.")

    elif user_role == 'qa_user':
        st.subheader("🔍 Functional Tester Agent Dashboard: Test Effectiveness")
        st.markdown("""
            <p style='font-size:0.9em; color:#64748b;'>
            Understand how the Functional Tester Agent contributes to test case generation, automation, and defect detection.
            </p>
        """, unsafe_allow_html=True)
        test_coverage_data_qa = {
            'Component': ['User Auth', 'Order Mgmt', 'Reporting', 'Payment Gateway'],
            'Coverage (%)': [90, 85, 70, 95]
        }
        df_test_coverage_qa = pd.DataFrame(test_coverage_data_qa)
        st.bar_chart(df_test_coverage_qa.set_index('Component'))
        st.markdown("Automated test coverage achieved for different application components, a key output of the Functional Tester Agent.")

        st.metric(label="Defect Escape Rate (Production)", value="2%", delta="↓ 1% this quarter")
        st.markdown("Percentage of defects that escape to production after the Functional Tester Agent's validation.")
        
        test_cases_automated_data = pd.DataFrame({
            'Week': ['W1', 'W2', 'W3', 'W4'],
            'Test Cases Automated': [25, 30, 28, 35]
        }).set_index('Week')
        st.bar_chart(test_cases_automated_data)
        st.markdown("Number of new automated test cases generated and implemented by the Functional Tester Agent per week.")

    elif user_role == 'devops_user':
        st.subheader("🚀 DevOps Agent Dashboard: Deployment & Release Efficiency")
        st.markdown("""
            <p style='font-size:0.9em; color:#64748b;'>
            Evaluate the DevOps Agent's impact on CI/CD pipeline efficiency, deployment frequency, and stability.
            </p>
        """, unsafe_allow_html=True)
        st.metric(label="Deployment Frequency", value="10 deployments/day", delta="↑ 2 deployments/day")
        st.markdown("The average number of successful deployments to production per day.")
        st.metric(label="Deployment Success Rate", value="99.5%", delta="↑ 0.2%")
        st.markdown("Percentage of deployments that complete without errors, thanks to robust automation.")

        mttr_hours_devops = 1.0 # Example value in hours
        st.metric(label="Mean Time To Recovery (MTTR)", value=f"{mttr_hours_devops} hours", delta="↓ 0.5 hours this month")
        st.markdown("Average time to restore service after an incident, improved by automated recovery mechanisms.")

        pipeline_runs_data = pd.DataFrame({
            'Day': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
            'Pipeline Runs': [50, 55, 48, 60, 45]
        }).set_index('Day')
        st.line_chart(pipeline_runs_data)
        st.markdown("Daily count of CI/CD pipeline executions managed by the DevOps Agent.")

    elif user_role == 'ops_user':
        st.subheader("📈 Ops Engineer Agent Dashboard: Proactive Operations & RCA")
        st.markdown("""
            <p style='font-size:0.9em; color:#64748b;'>
            Focus on the Ops Engineer Agent's ability to proactively detect issues, accelerate root cause analysis, and ensure system health.
            </p>
        """, unsafe_allow_html=True)
        mttd_hours_ops = 0.5 # Example value in hours
        st.metric(label="Mean Time To Detect (MTTD)", value=f"{mttd_hours_ops} hours", delta="↓ 0.2 hours this month")
        st.markdown("The average time taken to detect critical issues, significantly reduced by proactive monitoring.")
        st.metric(label="Incident Resolution Rate", value="95%", delta="↑ 3%")
        st.markdown("Percentage of detected incidents successfully resolved within defined SLAs, aided by RCA automation.")

        st.metric(label="Proactive Alerting Ratio", value="70%", delta="↑ 10% this quarter")
        st.markdown("Percentage of incidents detected via automated alerts before user impact, showcasing proactive capabilities.")
        
        incidents_data = pd.DataFrame({
            'Month': ['Jan', 'Feb', 'Mar', 'Apr'],
            'Incidents': [15, 12, 10, 8]
        }).set_index('Month')
        st.bar_chart(incidents_data)
        st.markdown("Monthly trend of incidents, showing the impact of Ops Engineer Agent in reducing occurrences.")

    else:
        st.info("Please select a specific user role from the sidebar or log in as 'admin' to view a tailored dashboard.")


def display_agent_cards_overview():
    st.markdown("## Explore Our Intelligent Agents")
    st.markdown("""
        <p style='font-size:1.1em; color:#4a5568;'>
        Dive into the capabilities of each specialized AI agent. Select an agent from the sidebar on the left,
        or click on any card below, to view its detailed workflow and interactive LLM features.
        </p>
    """, unsafe_allow_html=True)
    
    # Filter agents based on logged-in user's role
    if st.session_state.logged_in_user_role == 'admin':
        # Admin gets to see all agents
        filtered_agent_display_order = all_agent_display_order
    else:
        # Other roles get a filtered list based on ROLE_AGENT_ACCESS
        allowed_agent_ids = ROLE_AGENT_ACCESS.get(st.session_state.logged_in_user_role, [])
        filtered_agent_display_order = [
            agent_id for agent_id in all_agent_display_order if agent_id in allowed_agent_ids
        ]

    # Display agent cards in a grid based on filtered order
    cols = st.columns(3)
    for idx, agent_id in enumerate(filtered_agent_display_order):
        agent = agent_data[agent_id]
        with cols[idx % 3]:
            # Using custom HTML for agent cards with a nested Streamlit button for functionality
            st.markdown(f"""
            <div class="agent-card">
                <div class="agent-icon">{agent['icon']}</div>
                <h3 class="agent-name">{agent['name']}</h3>
                <p class="agent-description">{agent['description']}</p>
                <p class="agent-tech"><b>Tech:</b> {agent['tech']}</p>
                <p class="agent-llm-feature"><b>LLM Feature:</b> {agent['llm_feature'].replace('_', ' ').title()}</p>
            </div>
            """, unsafe_allow_html=True)
            # This Streamlit button is placed right after the custom HTML for the card
            if st.button(f"Explore {agent['name']} 👉", key=f"explore_agent_btn_{agent_id}", use_container_width=True):
                st.session_state.agent_detailed_view = agent_id
                st.session_state.current_agent_step_index = 0
                st.session_state.last_agent_output_for_phase_completion = None
                st.session_state.current_view = 'agent_detail' # Switch to agent_detail view when selecting an agent
                st.rerun()

# --- Login Logic ---
def login_page():
    st.title("Login to Agentic AI SDLC Prototype")
    st.markdown("---")

    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login", key="perform_login_btn"):
        if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
            st.session_state.is_authenticated = True
            st.session_state.logged_in_user_role = username # Use username as role for simplicity in prototype
            st.success(f"Logged in as {username}!")
            time.sleep(1) # Give time to read message
            st.rerun()
        else:
            st.error("Invalid username or password")
    
    st.markdown("---")
    st.markdown("#### Demo Users:")
    st.markdown("- **Admin:** `admin` / `adminpass`")
    st.markdown("- **BA:** `ba_user` / `bapass`")
    st.markdown("- **Architect:** `architect_user` / `archpass`")
    st.markdown("- **Planner:** `planner_user` / `planpass`")
    st.markdown("- **Developer:** `dev_user` / `devpass`")
    st.markdown("- **QA:** `qa_user` / `qapass`")
    st.markdown("- **DevOps:** `devops_user` / `devopspass`")
    st.markdown("- **Ops Engineer:** `ops_user` / `opspass`")


# --- Landing Page Logic ---
def show_landing_page():
    st.set_page_config(layout="wide", page_title="Agentic AI SDLC Prototype", initial_sidebar_state="collapsed")

    # Custom CSS for a more professional look
    st.markdown("""
    <style>
    /* General App Styling */
    .stApp {
        background: linear-gradient(to bottom right, #f0f2f6, #e6e9ef); /* Subtle background gradient */
        font-family: 'Inter', sans-serif;
        color: #333;
    }

    /* Titles and Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #1a202c;
    }

    .main-header {
        font-size: 3.5em;
        color: #1a202c;
        text-align: center;
        margin-top: 1em;
        margin-bottom: 0.5em;
        font-weight: 700;
        line-height: 1.2;
    }
    .subheader {
        font-size: 1.5em;
        color: #4a5568;
        text-align: center;
        margin-bottom: 2em;
    }
    .description-text {
        font-size: 1.1em;
        color: #4a5568;
        text-align: center;
        margin-bottom: 3em;
        max-width: 800px;
        margin-left: auto;
        margin-right: auto;
        line-height: 1.6;
    }

    /* Buttons */
    .stButton > button {
        background-color: #4CAF50; /* Green */
        color: white;
        padding: 15px 30px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 1.2em;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 12px;
        border: none;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: background-color 0.3s ease, transform 0.2s ease;
    }
    .stButton > button:hover {
        background-color: #45a049;
        transform: translateY(-2px);
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #ffffff; /* White sidebar background */
        padding: 20px;
        border-right: 1px solid #e2e8f0;
        box-shadow: 2px 0 5px rgba(0,0,0,0.05); /* Subtle shadow for depth */
    }

    /* Styling for Streamlit buttons in the sidebar to make them look like navigation links */
    [data-testid="stSidebar"] .stButton button {
        background-color: transparent; /* Transparent background by default */
        color: #1a202c; /* Darker text */
        text-align: left;
        padding: 10px 15px;
        font-size: 1em;
        border-radius: 8px;
        border: 1px solid transparent; /* Add a subtle border */
        box-shadow: none;
        transition: background-color 0.2s ease, color 0.2s ease, border-color 0.2s ease;
        width: 100%; /* Make buttons fill sidebar width */
        margin: 5px 0;
    }

    [data-testid="stSidebar"] .stButton button:hover {
        background-color: #e2e8f0; /* Light gray on hover */
        color: #1a202c;
        border-color: #cbd5e1; /* Subtle border on hover */
        transform: none; /* No lift effect on sidebar buttons */
    }
    
    /* Specific styling for the selected agent button in the sidebar */
    .stButtonSelectedInSidebar button {
        background-color: #0369a1 !important; /* Blue for selected button, !important to override */
        color: white !important;
        font-weight: bold !important;
        border-color: #0369a1 !important; /* Ensure border is also blue */
    }

    /* Agent Cards on Home Page */
    .agent-card {
        border: 1px solid #e2e8f0;
        border-radius: 12px; /* More rounded corners */
        padding: 25px; /* More padding */
        margin-bottom: 20px;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.08); /* Stronger shadow */
        background-color: white;
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        height: 100%; /* Ensure full height within grid cell */
        min-height: 320px; /* Set a minimum height for consistent alignment */
        justify-content: space-between; /* Distribute content vertically */
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .agent-card:hover {
        transform: translateY(-5px); /* Lift effect on hover */
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.15);
    }
    .agent-icon {
        font-size:3.5em; /* Larger icon */
        margin-bottom: 15px;
        color: #0369a1; /* Blue icon color */
    }
    .agent-name {
        margin-top:0;
        margin-bottom: 8px;
        color: #1a202c;
        font-weight: 600; /* Bolder name */
    }
    .agent-description {
        color:#64748b;
        font-size:0.95em; /* Slightly larger text */
        flex-grow: 1; /* Allow description to take available space */
        line-height: 1.5;
        margin-bottom: 15px; /* Space before tech details */
    }
    .agent-tech, .agent-llm-feature {
        color:#4a5568; /* Darker grey for tech details */
        font-size:0.88em;
        font-weight: 500;
        margin-top: 5px;
    }
    /* Style for the "Explore" button within agent cards */
    .agent-card-button button {
        background-color: #0369a1 !important; /* Primary blue color */
        color: white !important;
        padding: 10px 20px !important;
        font-size: 1em !important;
        border-radius: 8px !important;
        border: none !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
        transition: background-color 0.2s ease, transform 0.2s ease !important;
        width: 100% !important; /* Make button fill card width */
        margin-top: 15px; /* Space between content and button */
    }
    .agent-card-button button:hover {
        background-color: #025686 !important; /* Darker blue on hover */
        transform: translateY(-1px) !important;
    }


    /* Footer */
    .footer-container {
        width: 100%;
        text-align: center;
        padding-top: 2em; /* Add some padding at the top */
        padding-bottom: 1em; /* Add some padding at the bottom */
        color: #64748b;
        font-size: 0.9em;
        /* Position at the very bottom */
        position: fixed;
        left: 0;
        bottom: 0;
        background: linear-gradient(to top, #f0f2f6, #e6e9ef); /* Match app background with gradient */
        z-index: 100; /* Ensure it's above other content if scrolling */
    }

    /* Main App Title Separator */
    .main-app-title-separator {
        border-bottom: 2px solid #cbd5e1; /* Subtle line */
        width: 100%; /* Span full width */
        margin-top: 10px; /* Space below title */
        margin-bottom: 30px; /* Space before content */
    }
    </style>
    """, unsafe_allow_html=True)

    # Logo at the top of the landing page
    st.image("https://www.valuemomentum.com/wp-content/uploads/2024/01/ValueMomentum-Logo-1.png", width=200)
    
    st.markdown("<div class='main-header'>Welcome to Agentic AI SDLC Automation Prototype</div>", unsafe_allow_html=True)
    st.markdown("<div class='subheader'>Accelerate your SDLC with AI-powered agents</div>", unsafe_allow_html=True)
    st.markdown("""
        <div class='description-text'>
            Explore a revolutionary approach to software development where specialized AI agents collaborate seamlessly across
            the entire Software Development Lifecycle. From requirements analysis to deployment and operations,
            witness how intelligent automation can enhance efficiency, reduce errors, and foster innovation.
            This prototype offers a hands-on experience to understand the power of agentic AI workflows.
        </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Replaced "Start Exploring" with a call to the login page
    login_page()
            
    # Centered and "locked" footer using a container div
    st.markdown("<div class='footer-container'>© 2025 ValueMomentum. All rights reserved.</div>", unsafe_allow_html=True)

# --- Main App Logic Refactor ---
if not st.session_state.is_authenticated:
    show_landing_page()
else:
    st.set_page_config(layout="wide", page_title="Agentic AI SDLC Prototype", initial_sidebar_state="expanded")
    st.title("Agentic AI SDLC Automation Prototype")
    # Add a visual separator under the main title
    st.markdown("<div class='main-app-title-separator'></div>", unsafe_allow_html=True)

    # Sidebar for navigation and agent list
    with st.sidebar:
        st.header("Prototype Controls")
        # Navigation buttons for main content views
        if st.button("Agent Overview", key="nav_agent_overview", help="View the accessible AI agents and their roles.",
                     type="primary" if st.session_state.current_view == 'agent_overview' else "secondary"):
            st.session_state.current_view = 'agent_overview'
            st.session_state.agent_detailed_view = None # Exit agent detail view if switching to agent overview
            st.rerun()

        if st.button("Dashboard", key="nav_dashboard", help="Explore performance metrics tailored to your role.",
                     type="primary" if st.session_state.current_view == 'dashboard' else "secondary"):
            st.session_state.current_view = 'dashboard'
            st.session_state.agent_detailed_view = None # Exit agent detail view if switching to dashboard
            st.rerun()

        st.markdown("---")
        st.header(f"Your Agents ({st.session_state.logged_in_user_role.replace('_user', '').title()})")
        
        # Filter sidebar agents based on logged-in user's role
        if st.session_state.logged_in_user_role == 'admin':
            display_order_sidebar = all_agent_display_order
        else:
            display_order_sidebar = [
                agent_id for agent_id in all_agent_display_order if agent_id in ROLE_AGENT_ACCESS.get(st.session_state.logged_in_user_role, [])
            ]

        # Iterate through the custom display order for sidebar buttons
        for agent_id in display_order_sidebar:
            agent = agent_data[agent_id]
            # Highlight if the detailed view of this agent is active AND we are in 'agent_detail' view
            is_current_agent_view = (st.session_state.agent_detailed_view == agent_id) and (st.session_state.current_view == 'agent_detail') 
            button_label = f"{agent['name']}" 
            
            # Use a div with a class to apply conditional styling for the selected button
            if is_current_agent_view:
                st.markdown(f"""
                <div class="stButtonSelectedInSidebar">
                    <button style="display: block; width: 100%; text-align: left; padding: 10px 15px; border-radius: 8px; border: none; cursor: default;">
                        👉 {button_label}
                    </button>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Regular Streamlit button for non-selected agents, which will pick up the general sidebar button styling
                if st.button(button_label, key=f"agent_sidebar_{agent_id}", help=agent['description']):
                    st.session_state.agent_detailed_view = agent_id
                    st.session_state.current_agent_step_index = 0
                    st.session_state.last_agent_output_for_phase_completion = None
                    st.session_state.current_view = 'agent_detail' # Switch to agent_detail view when selecting an agent from sidebar
                    st.rerun()
        st.markdown("---")
        if st.button("Logout", key="logout_sidebar_btn", help="Log out of the application."):
            initialize_session_state() # Reset state on logout
            st.rerun()

    # Main content area based on current_view
    if st.session_state.current_view == 'dashboard':
        display_dashboard()
    elif st.session_state.current_view == 'agent_detail':
        display_agent_detail()
    else: # Default to agent_overview if no agent is selected and not in dashboard view
        display_agent_cards_overview()
    st.markdown("<div class='footer-container'>© 2025 ValueMomentum. All rights reserved.</div>", unsafe_allow_html=True)
