import streamlit as st
import json
import time # To simulate API calls
from collections import OrderedDict # To maintain order of agents in workflow

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
        ], 'llm_step_index': 3, 'activates_agents': ['Planner Agent', 'Architect Agent']},
    2: {'id': 2, 'name': 'Planner Agent', 'description': 'Picks items from Release backlog, schedules for Sprint, creates tasks.', 'tech': 'Gemini 2.0 Flash', 'icon': '&#128197;', 'llm_feature': 'sprint_summary', 'receives_input_from': ['BA Agent'],
        'workflow_steps': [
            "Input: Receive items from Release Backlog",
            "Step 1: Analyze complexity & dependencies",
            "Step 2: Estimate effort/capacity",
            "Step 3: Call LLM to generate Sprint Goal & Summary", # LLM interaction happens here
            "Step 4: Create detailed tasks for scrum team",
            "Output: Update project management system"
        ], 'llm_step_index': 3, 'activates_agents': ['Developer Agent']},
    3: {'id': 3, 'name': 'Architect Agent', 'description': 'Sets up solution structure, creates Architecture and Solution diagrams, HLD.', 'tech': 'OpenAI 4.1, ArchitectGPT', 'icon': '&#127959;&#65039;', 'llm_feature': 'arch_pattern_suggestion', 'receives_input_from': ['BA Agent'],
        'workflow_steps': [
            "Input: Review high-level requirements (HLRs) & NFRs",
            "Step 1: Setup solution structure",
            "Step 2: Create conceptual architecture diagrams",
            "Step 3: Call LLM to suggest Architectural Patterns", # LLM interaction happens here
            "Step 4: Define technology stack & design patterns",
            "Output: Generate High-Level Design (HLD) document"
        ], 'llm_step_index': 3, 'activates_agents': ['Developer Agent']},
    4: {'id': 4, 'name': 'Developer Agent', 'description': 'Writes code, unit tests, conducts unit testing.', 'tech': 'Gemini 2.0 Flash', 'icon': '&#128187;', 'llm_feature': 'code_generation', 'receives_input_from': ['Architect Agent', 'Planner Agent'],
        'workflow_steps': [
            "Input: Receive sprint tasks/user stories",
            "Step 1: Analyze requirements and designs",
            "Step 2: Call LLM to generate code snippets", # LLM interaction happens here
            "Step 3: Write and refine code (adhere to standards)",
            "Step 4: Write unit tests",
            "Output: Check-in code & manage merges"
        ], 'llm_step_index': 2, 'activates_agents': ['Functional Tester Agent', 'DevOps Agent', 'Evaluator Agent']},
    5: {'id': 5, 'name': 'Functional Tester Agent', 'description': 'Reviews user stories, writes functional test cases, automates, executes, logs defects.', 'tech': 'OpenAI 4.1', 'icon': '&#128270;', 'llm_feature': 'test_case_generation', 'receives_input_from': ['Developer Agent'],
        'workflow_steps': [
            "Input: Review user stories and acceptance criteria",
            "Step 1: Call LLM to generate functional test cases", # LLM interaction happens here
            "Step 2: Identify regression candidates for automation",
            "Step 3: Automate test cases",
            "Step 4: Execute automated tests",
            "Output: Log defects with reproduction steps"
        ], 'llm_step_index': 1, 'activates_agents': ['Evaluator Agent']},
    6: {'id': 6, 'name': 'DevOps Agent', 'description': 'Invokes CI/CD pipeline, manages deployments, infrastructure as code.', 'tech': 'Gemini 2.0 Flash', 'icon': '&#128640;', 'llm_feature': 'deployment_suggestion', 'receives_input_from': ['Developer Agent'],
        'workflow_steps': [
            "Input: Monitor code check-ins for changes",
            "Step 1: Trigger CI/CD pipeline execution",
            "Step 2: Perform build and packaging",
            "Step 3: Call LLM to suggest Deployment Strategy", # LLM interaction happens here
            "Step 4: Execute defined deployment strategy",
            "Output: Provision/manage infrastructure as code (IaC)"
        ], 'llm_step_index': 3, 'activates_agents': ['Ops Engineer Agent', 'FinOps Agent', 'Evaluator Agent']},
    7: {'id': 7, 'name': 'Ops Engineer Agent', 'description': 'Configures alerts, reviews logs, performs RCA.', 'tech': 'Gemini 2.0 Flash', 'icon': '&#128200;', 'llm_feature': 'rca_assistant', 'receives_input_from': ['DevOps Agent'],
        'workflow_steps': [
            "Input: Monitor system health and performance metrics",
            "Step 1: Configure and manage alerts",
            "Step 2: Review service logs for anomalies",
            "Step 3: Call LLM for Root Cause Analysis (RCA) assistance", # LLM interaction happens here
            "Step 4: Implement or trigger self-healing actions",
            "Output: Propose AIOps enhancements"
        ], 'llm_step_index': 3, 'activates_agents': ['FinOps Agent', 'Evaluator Agent']},
    8: {'id': 8, 'name': 'Evaluator Agent', 'description': 'Provides confidence score, validates action for each agent.', 'tech': 'OpenAI 4.1, Gemini 2.0 Flash', 'icon': '&#129513;', 'llm_feature': 'eval_rationale', 'receives_input_from': ['BA Agent', 'Planner Agent', 'Architect Agent', 'Developer Agent', 'Functional Tester Agent', 'DevOps Agent', 'Ops Engineer Agent'],
        'workflow_steps': [
            "Input: Receive agent action or output for review",
            "Step 1: Apply evaluation criteria and rubrics",
            "Step 2: Validate adherence to standards",
            "Step 3: Call LLM to generate Confidence Score Rationale", # LLM interaction happens here
            "Step 4: Flag discrepancies or potential errors",
            "Output: Provide structured feedback"
        ], 'llm_step_index': 3, 'activates_agents': []}, # Evaluator typically provides feedback back to source or reports
    9: {'id': 9, 'name': 'Memory Agent', 'description': 'Provides access to enterprise standards, guidelines, and historical data.', 'tech': 'ChromaDB', 'icon': '&#128210;', 'llm_feature': 'simulated_retrieval', 'receives_input_from': [],
        'workflow_steps': [
            "Input: Receive query for enterprise knowledge/context",
            "Step 1: Search internal knowledge base (ChromaDB)",
            "Step 2: Call LLM to interpret query/summarize retrieved documents", # LLM interaction happens here for complex queries/summaries
            "Output: Retrieve relevant documents/templates/data"
        ], 'llm_step_index': 2, 'activates_agents': []}, # Memory Agent usually just serves data on request
    10: {'id': 10, 'name': 'FinOps Agent', 'description': 'Cost optimization, Cost reports, Recommendations for cloud resource optimization.', 'tech': 'Gemini 2.0 Flash', 'icon': '&#128176;', 'llm_feature': 'finops_rationale', 'receives_input_from': ['DevOps Agent', 'Ops Engineer Agent'],
        'workflow_steps': [
            "Input: Collect cloud resource usage and spending data",
            "Step 1: Generate detailed cost reports",
            "Step 2: Analyze spending patterns",
            "Step 3: Call LLM to generate Cost Optimization Rationale", # LLM interaction happens here
            "Step 4: Identify optimization opportunities",
            "Output: Provide actionable recommendations"
        ], 'llm_step_index': 3, 'activates_agents': []} # FinOps provides reports/recommendations, doesn't typically activate next SDLC phase
}

# Define workflow phases, mapping to primary agents (using agent_data keys)
workflow_data = [
    {'phase_id': 'req_planning', 'name': '1. Requirements & Planning', 'description': 'Business requirements are transformed into detailed specifications and an agile sprint plan.', 'primary_agent_id': 1}, # BA Agent
    {'phase_id': 'design_arch', 'name': '2. Design & Architecture', 'description': 'Solution blueprints and high-level designs are created.', 'primary_agent_id': 3}, # Architect Agent
    {'phase_id': 'development', 'name': '3. Development', 'description': 'Code is generated, written, unit tested, and refined.', 'primary_agent_id': 4}, # Developer Agent
    {'phase_id': 'testing', 'name': '4. Testing & Validation', 'description': 'Functional test cases are generated, automated, and executed; defects are logged.', 'primary_agent_id': 5}, # Functional Tester Agent
    {'phase_id': 'ci_cd_deploy', 'name': '5. CI/CD & Deployment', 'description': 'Continuous integration, delivery, and automated deployments are orchestrated.', 'primary_agent_id': 6}, # DevOps Agent
    {'phase_id': 'operations', 'name': '6. Operations & Monitoring', 'description': 'Production systems are monitored, and incidents are managed with RCA.', 'primary_agent_id': 7}, # Ops Engineer Agent
    {'phase_id': 'cross_cutting_eval', 'name': '7. Cross-Cutting: Evaluation', 'description': 'The Evaluator agent assesses quality and provides feedback across the SDLC.', 'primary_agent_id': 8}, # Evaluator Agent
    {'phase_id': 'cross_cutting_finops', 'name': '8. Cross-Cutting: FinOps', 'description': 'The FinOps agent focuses on cloud cost optimization and financial insights.', 'primary_agent_id': 10} # FinOps Agent
]

# --- Streamlit Session State Initialization ---
def initialize_session_state():
    st.session_state.current_phase_index = 0
    st.session_state.completed_phases_outputs = OrderedDict()
    st.session_state.agent_detailed_view = None
    st.session_state.current_agent_step_index = 0
    st.session_state.last_agent_output_for_phase_completion = None

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

def display_breadcrumbs():
    st.markdown("### SDLC Flow Progress")
    cols = st.columns(len(workflow_data))
    for i, phase in enumerate(workflow_data):
        with cols[i]:
            # Tooltip content for completed phases
            output_summary = "No output yet."
            if phase['phase_id'] in st.session_state.completed_phases_outputs and \
               st.session_state.completed_phases_outputs[phase['phase_id']]:
                
                # Ensure the output is a string before splitting
                output_content = str(st.session_state.completed_phases_outputs[phase['phase_id']])
                output_summary = output_content.split('\n')[0] + "..." # Take first line

            if i < st.session_state.current_phase_index:
                # Completed phase: Greyed out, with checkmark and tooltip of output
                st.markdown(f"""
                <div style="text-align: center; color: #94a3b8; opacity: 0.7; cursor: pointer;" title="Completed: {output_summary}">
                    <span style="font-size: 2em;">&#10004;</span><br>
                    <small><s>{phase['name']}</s></small>
                </div>
                """, unsafe_allow_html=True)
            elif i == st.session_state.current_phase_index:
                # Current phase: Highlighted
                st.markdown(f"""
                <div style="text-align: center; color: #0369a1; font-weight: bold;" title="Current Phase: {phase['description']}">
                    <span style="font-size: 2em;">&#9679;</span><br>
                    <small>{phase['name']}</small>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Future phase: Standard
                st.markdown(f"""
                <div style="text-align: center; color: #cbd5e1;" title="Upcoming Phase: {phase['description']}">
                    <span style="font-size: 2em;">&#9675;</span><br>
                    <small>{phase['name']}</small>
                </div>
                """, unsafe_allow_html=True)
    st.markdown("---")

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
                    for p in workflow_data:
                        if agent_data[p['primary_agent_id']]['name'] == input_agent_name:
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
            # Only show LLM interaction part if current_agent_step_index matches llm_step_index
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

                    if agent['activates_agents']:
                        st.markdown(f"This output now **activates** the following agents: **{', '.join(agent['activates_agents'])}**.")
                    else:
                        st.markdown("This agent's output is for informational purposes or triggers downstream processes not directly represented as another agent in this prototype's linear flow.")

                    # Determine next automatic transition
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
                            st.rerun()

            # Always provide a "Close Details" for manual exit
            # Only show if not auto-redirected, which means it's either the last phase or a non-primary agent
            # and the user hasn't chosen to return to the main view already.
            if not (st.session_state.current_agent_step_index == len(agent['workflow_steps']) -1 and is_current_agent_primary_for_phase):
                 st.button("Close Agent Details Manually", on_click=lambda: st.session_state.update(agent_detailed_view=None, current_agent_step_index=0, last_agent_output_for_phase_completion=None))


# --- Main App Logic ---
st.set_page_config(layout="wide", page_title="Agentic AI SDLC Prototype")

st.title("Agentic AI SDLC Automation Prototype")
st.markdown("This prototype demonstrates the interaction and flow of specialized AI agents across the Software Development Lifecycle.")

# Sidebar for overall navigation and agent list
with st.sidebar:
    st.header("Prototype Controls")
    if st.button("Reset Prototype", help="Clear all progress and start from the beginning."):
        initialize_session_state()
        st.rerun()
    st.markdown("---")

    st.header("Overall SDLC Phases")
    # Using st.radio for main phase selection with native highlighting
    phase_options = [phase['name'] for phase in workflow_data]
    
    # Get the name of the currently active phase
    active_phase_name = workflow_data[st.session_state.current_phase_index]['name']
    
    # Set the index for st.radio to match the active phase
    try:
        current_radio_index = phase_options.index(active_phase_name)
    except ValueError:
        current_radio_index = 0 # Default to first if not found (shouldn't happen with correct logic)

    selected_phase_name = st.radio(
        "Select SDLC Phase:",
        options=phase_options,
        index=current_radio_index,
        key="sdlc_phase_radio",
        help="Navigate through the main phases of the Software Development Lifecycle."
    )
    
    # Update current_phase_index based on radio selection
    new_phase_index = phase_options.index(selected_phase_name)
    if new_phase_index != st.session_state.current_phase_index:
        st.session_state.current_phase_index = new_phase_index
        st.session_state.agent_detailed_view = None # Close detail view when navigating
        st.session_state.current_agent_step_index = 0 # Reset agent steps
        st.session_state.last_agent_output_for_phase_completion = None # Clear output for new phase
        st.rerun() # Rerun to update the UI
    
    st.markdown("---")
    st.header("Individual AI Agents")
    # Display agents in sidebar for quick detail access
    for agent_id, agent in agent_data.items():
        is_current_agent_view = (st.session_state.agent_detailed_view == agent_id)
        # Construct button label without unsafe_allow_html for the button itself
        button_label = f"{agent['icon']} {agent['name']}"
        
        if is_current_agent_view:
             # If this agent is active, use markdown to highlight the button
            st.markdown(f"**👉 {button_label}**")
        
        if st.button(button_label, 
                     key=f"agent_sidebar_{agent_id}", 
                     help=agent['description']): 
            st.session_state.agent_detailed_view = agent_id
            st.session_state.current_agent_step_index = 0 # Start from the beginning of agent's workflow
            st.session_state.last_agent_output_for_phase_completion = None # Clear output
            st.rerun()

# Main content area
if st.session_state.agent_detailed_view:
    display_agent_detail()
else:
    display_breadcrumbs()

    current_phase = workflow_data[st.session_state.current_phase_index]
    primary_agent = agent_data[current_phase['primary_agent_id']]

    st.header(f"Phase: {current_phase['name']}")
    st.markdown(f"<p class='text-lg'>{current_phase['description']}</p>", unsafe_allow_html=True)

    st.markdown("---")

    st.subheader(f"Primary Agent for this Phase: {primary_agent['icon']} {primary_agent['name']}")
    st.markdown(f"**Role:** {primary_agent['description']}")
    st.markdown(f"**Technology:** {primary_agent['tech']}")

    # Show inputs received from previous agents - for the main phase view
    if primary_agent['receives_input_from']:
        st.markdown("#### Input Received (from previous agents in the SDLC flow):")
        for input_agent_name in primary_agent['receives_input_from']:
            input_received_content = "No input (or not applicable for this prototype step)."
            
            # Find the phase ID for the input agent
            source_phase_id = None
            for p in workflow_data:
                if agent_data[p['primary_agent_id']]['name'] == input_agent_name:
                    source_phase_id = p['phase_id']
                    break

            if source_phase_id and source_phase_id in st.session_state.completed_phases_outputs:
                input_received_content = str(st.session_state.completed_phases_outputs[source_phase_id])
            
            if input_received_content != "No input (or not applicable for this prototype step).":
                 # Display only the first line of the received content as a summary, make full content visible via expander
                 display_summary_content = input_received_content.splitlines()[0] + "..." if "\n" in input_received_content else input_received_content
                 with st.expander(f"**From {input_agent_name}:** {display_summary_content}", expanded=False):
                     st.code(input_received_content, language='markdown') # Display full content in an expander
            else:
                 st.markdown(f"<p style='color:#64748b; font-size:0.9em;'>From {input_agent_name}: (No relevant output yet from previous phase simulation)</p>", unsafe_allow_html=True)
    else:
        st.info("This agent is a primary initiator or receives no direct upstream input in this simplified flow.")

    st.markdown("---")
    st.markdown("Click on the agent's name or icon to see its internal workflow and LLM interaction. Completing its workflow will automatically advance to the next primary agent.")

    if st.button(f"Explore {primary_agent['name']} Workflow", key=f"explore_agent_{primary_agent['id']}"): 
        st.session_state.agent_detailed_view = primary_agent['id']
        st.session_state.current_agent_step_index = 0 # Start from the first step of the agent's workflow
        st.session_state.last_agent_output_for_phase_completion = None # Clear output for agent exploration
        st.rerun()

    st.markdown("---")

    # This section is now purely informational as the automatic progression handles the "next phase"
    st.subheader("SDLC Phase Handoff & Next Agent Activation")
    
    # Check if the current phase's output is saved (meaning its primary agent's LLM step was completed)
    is_primary_agent_llm_completed_for_phase = current_phase['phase_id'] in st.session_state.completed_phases_outputs and \
                                               st.session_state.completed_phases_outputs[current_phase['phase_id']] not in ["Processing...", None, "Agent ran but no specific output was generated."]

    if is_primary_agent_llm_completed_for_phase:
        st.markdown(f"The **{primary_agent['name']}** for this phase has completed its LLM interaction. Its output serves as a key deliverable for the next stages.")
        st.markdown(f"Primary output of {primary_agent['name']}:")
        st.code(st.session_state.completed_phases_outputs[current_phase['phase_id']], language='markdown')
        
        if primary_agent['activates_agents']:
            st.markdown(f"This output typically **activates** the following agents: **{', '.join(primary_agent['activates_agents'])}**.")
        else:
            st.markdown(f"This agent ({primary_agent['name']}) completes a critical step, but its direct output might not immediately activate a new primary agent in the *linear* SDLC flow shown in this prototype.")
    else:
        st.info(f"Explore the '{primary_agent['name']}' agent's workflow by clicking the button above. Complete its internal steps to see its output and automatically advance the SDLC phase.")

    st.markdown("---")
    st.subheader("How Agents Connect in Real-Time (Production Environment)")
    st.markdown("""
    In a real-world Agentic AI SDLC automation system, the "activation" and "connection" between agents go beyond simple sequential steps:

    * **Orchestration Layer:** A central **Agent Orchestrator** (often an advanced LLM or a custom AI service) acts as the brain. It receives outputs from agents, evaluates them (potentially with the help of the `Evaluator Agent`), and determines the next logical step.
    * **Event-Driven Architecture:** Agents communicate via events. When one agent completes a task (e.g., BA Agent generates a TRD), it publishes an event to a message queue (e.g., Kafka, Pub/Sub).
    * **Message Queues:** Other agents subscribe to relevant events. For instance, the Planner Agent and Architect Agent would subscribe to "New Requirements Document" events.
    * **APIs and Webhooks:** Agents would invoke each other's APIs or trigger webhooks directly for synchronous operations or to push data.
    * **Shared Knowledge Base (`Memory Agent`):** Agents might not directly "send" output to the next. Instead, they might update a shared knowledge base or artifact repository. Downstream agents then query this knowledge base (`Memory Agent`) to pull the information they need.
    * **Continuous Feedback Loops:** The `Evaluator Agent` constantly monitors outputs, and if an output doesn't meet quality standards, it can trigger a rework loop, sending feedback (and the problematic artifact) back to the originating agent.
    * **Human-in-the-Loop:** For critical decisions or complex problems, the Orchestrator can route tasks to human experts, who then provide input back to the system.

    This prototype simplifies the flow for demonstration, but in reality, it would be a complex, dynamic, and event-driven ecosystem.
    """)
    st.markdown("<div style='text-align: center; color: #64748b; font-size: 0.9em; margin-top: 2em;'>© 2025 ValueMomentum. All rights reserved.</div>", unsafe_allow_html=True)