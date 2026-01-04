"""
Interactive Multi-Turn Streamlit UI for Appointment Optimizer
Implements full Infermedica interview flow with state management
"""

import streamlit as st
from interview_manager import InterviewManager, InterviewStage
from infermedica_client import InfermedicaClient
from appointment_optimizer import AppointmentOptimizer

# Page config
st.set_page_config(
    page_title="Appointment Optimizer - Full Interview", page_icon="🏥", layout="wide"
)

# Custom CSS
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .stage-header {
        font-size: 1.8rem;
        color: #2c5282;
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding: 0.5rem;
        background-color: #e6f2ff;
        border-left: 4px solid #1f77b4;
    }
    .question-card {
        padding: 1.5rem;
        background-color: #f8f9fa;
        border-radius: 8px;
        margin: 1rem 0;
        border: 1px solid #dee2e6;
    }
    .red-flag {
        color: #dc3545;
        font-weight: bold;
    }
    .progress-text {
        font-size: 1.1rem;
        color: #495057;
        margin: 0.5rem 0;
    }
    .complete-box {
        padding: 2rem;
        background-color: #d4edda;
        border: 2px solid #28a745;
        border-radius: 8px;
        margin: 2rem 0;
    }
</style>
""",
    unsafe_allow_html=True,
)


def initialize_session_state():
    """Initialize session state variables"""
    if "client" not in st.session_state:
        st.session_state.client = None
        st.session_state.manager = None
        st.session_state.patient_age = 30
        st.session_state.patient_sex = "male"
        st.session_state.symptom_text = ""
        st.session_state.parsed_symptoms = None

        # Stage-specific data
        st.session_state.pending_risk_factors = []
        st.session_state.pending_related_symptoms = []
        st.session_state.pending_red_flags = []
        st.session_state.current_question = None

        # Final results
        st.session_state.final_results = None
        st.session_state.appointment_results = None


def render_header():
    """Render page header"""
    st.markdown(
        '<div class="main-header">🏥 Appointment Optimizer</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        "**Full Diagnostic Interview Flow with Intelligent Appointment Matching**"
    )
    st.markdown("---")


def render_sidebar():
    """Render sidebar with patient info and progress"""
    with st.sidebar:
        st.header("Patient Information")

        # Only allow editing if interview hasn't started
        disabled = st.session_state.manager is not None

        age = st.number_input(
            "Age",
            min_value=0,
            max_value=120,
            value=st.session_state.patient_age,
            disabled=disabled,
        )

        sex = st.selectbox(
            "Sex",
            ["male", "female"],
            index=0 if st.session_state.patient_sex == "male" else 1,
            disabled=disabled,
        )

        if not disabled:
            st.session_state.patient_age = age
            st.session_state.patient_sex = sex

        st.markdown("---")

        # Show progress if interview started
        if st.session_state.manager:
            st.header("Interview Progress")
            progress = st.session_state.manager.get_progress()

            st.metric("Stage", progress["stage"].replace("_", " ").title())
            st.metric("Questions Asked", progress["questions_asked"])
            st.metric("Evidence Collected", progress["evidence_count"])

            # Progress bar
            if progress["stage"] == "complete":
                st.progress(100)
            else:
                # Estimate progress based on stage
                stage_progress = {
                    "initial_symptoms": 10,
                    "risk_factors": 30,
                    "related_symptoms": 50,
                    "red_flags": 70,
                    "interview_loop": 85,
                    "complete": 100,
                }
                st.progress(stage_progress.get(progress["stage"], 0))

        st.markdown("---")

        # How it works
        with st.expander("ℹ️ How It Works"):
            st.markdown(
                """
            **Interview Stages:**
            1. Initial Symptoms
            2. Risk Factors
            3. Related Symptoms
            4. Red Flags (Safety)
            5. Diagnosis Questions
            6. Final Results
            
            **Full Infermedica Flow:**
            Uses the recommended interview process for maximum accuracy.
            """
            )

        # Reset button
        if st.session_state.manager:
            st.markdown("---")
            if st.button("🔄 Start New Interview", type="secondary"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()


def render_stage_1_initial_symptoms():
    """Stage 1: Collect initial symptoms"""
    st.markdown(
        '<div class="stage-header">Step 1: Describe Your Symptoms</div>',
        unsafe_allow_html=True,
    )

    symptom_text = st.text_area(
        "What symptoms are you experiencing?",
        value=st.session_state.symptom_text,
        height=100,
        placeholder="Example: I have chest pain and shortness of breath",
        help="Describe your symptoms in your own words",
    )

    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("🔍 Start Interview", type="primary", use_container_width=True):
            if not symptom_text.strip():
                st.error("Please describe your symptoms")
                return

            # Initialize client and manager
            try:
                st.session_state.client = InfermedicaClient()
                st.session_state.symptom_text = symptom_text

                # Parse symptoms
                with st.spinner("Analyzing symptoms..."):
                    parsed = st.session_state.client.parse_symptoms(
                        symptom_text,
                        st.session_state.patient_age,
                        st.session_state.patient_sex,
                    )
                    st.session_state.parsed_symptoms = parsed

                    # Create manager and start interview
                    st.session_state.manager = InterviewManager(
                        st.session_state.client,
                        st.session_state.patient_age,
                        st.session_state.patient_sex,
                    )
                    st.session_state.manager.start_interview(parsed)

                st.success(f"✓ Parsed {len(parsed)} symptoms")
                st.rerun()

            except Exception as e:
                st.error(f"Error: {e}")
                st.info(
                    "Make sure you have valid Infermedica API credentials in .env file"
                )

    with col2:
        if st.session_state.symptom_text:
            if st.button("Clear", use_container_width=True):
                st.session_state.symptom_text = ""
                st.rerun()

    # Show examples
    with st.expander("💡 Example Symptoms"):
        st.markdown(
            """
        **Emergency Examples:**
        - "I have severe chest pain and feel dizzy"
        - "Sudden severe headache with vision problems"
        
        **Routine Examples:**
        - "I have a cold and fever for 3 days"
        - "My knee hurts when I walk"
        - "I have a persistent cough"
        """
        )


def render_stage_2_risk_factors():
    """Stage 2: Collect risk factors"""
    st.markdown(
        '<div class="stage-header">Step 2: Demographic Risk Factors</div>',
        unsafe_allow_html=True,
    )

    manager = st.session_state.manager

    # Load risk factors if not already loaded
    if not st.session_state.pending_risk_factors:
        with st.spinner("Checking risk factors..."):
            risk_factors = manager.collect_risk_factors()
            st.session_state.pending_risk_factors = risk_factors

    risk_factors = st.session_state.pending_risk_factors

    if not risk_factors:
        st.info("No risk factors to check")
        if st.button("Continue →"):
            st.session_state.pending_risk_factors = []
            st.rerun()
        return

    st.markdown(
        """
**How does each of these statements relate to you?**  
<small>Select one answer for each statement</small>
""",
        unsafe_allow_html=True,
    )

    # Create form for all risk factors
    with st.form("risk_factors_form"):
        responses = {}

        for i, rf in enumerate(risk_factors):
            st.markdown(f'<div class="question-card">', unsafe_allow_html=True)
            response = st.radio(
                f"**{i+1}. {rf.get('common_name')}**",
                ["Yes", "No", "Unknown"],
                index=1,  # Default to "No"
                key=f"rf_{rf.get('id')}",
                horizontal=True,
            )
            responses[rf.get("id")] = response
            st.markdown("</div>", unsafe_allow_html=True)

        submitted = st.form_submit_button("Continue →", type="primary")

        if submitted:
            # Add all responses
            for rf_id, response in responses.items():
                choice_map = {"Yes": "present", "No": "absent", "Unknown": "unknown"}
                manager.add_risk_factor_response(rf_id, choice_map[response])

            # Clear pending and move to next stage
            st.session_state.pending_risk_factors = []
            st.success(f"✓ Recorded {len(responses)} responses")
            st.rerun()


def render_stage_3_related_symptoms():
    """Stage 3: Collect related symptoms"""
    st.markdown(
        '<div class="stage-header">Step 3: Related Symptoms</div>',
        unsafe_allow_html=True,
    )

    manager = st.session_state.manager

    # Load related symptoms if not already loaded
    if not st.session_state.pending_related_symptoms:
        with st.spinner("Finding related symptoms..."):
            related = manager.collect_related_symptoms()
            st.session_state.pending_related_symptoms = related

    related = st.session_state.pending_related_symptoms

    if not related:
        st.info("No related symptoms to check")
        if st.button("Continue →"):
            st.session_state.pending_related_symptoms = []
            st.rerun()
        return

    st.markdown(
        """
**How does each of these statements relate to you?**  
<small>Select one answer for each statement</small>
""",
        unsafe_allow_html=True,
    )

    # Create form for all related symptoms
    with st.form("related_symptoms_form"):
        responses = {}

        for i, sym in enumerate(related):
            st.markdown(f'<div class="question-card">', unsafe_allow_html=True)
            response = st.radio(
                f"**{i+1}. {sym.get('common_name')}**",
                ["Yes", "No", "Unknown"],
                index=1,  # Default to "No"
                key=f"rs_{sym.get('id')}",
                horizontal=True,
            )
            responses[sym.get("id")] = response
            st.markdown("</div>", unsafe_allow_html=True)

        submitted = st.form_submit_button("Continue →", type="primary")

        if submitted:
            # Add all responses
            for sym_id, response in responses.items():
                choice_map = {"Yes": "present", "No": "absent", "Unknown": "unknown"}
                manager.add_related_symptom_response(sym_id, choice_map[response])

            # Clear pending and move to next stage
            st.session_state.pending_related_symptoms = []
            st.success(f"✓ Recorded {len(responses)} responses")
            st.rerun()


def render_stage_4_red_flags():
    """Stage 4: Check red flags (safety critical)"""
    st.markdown(
        '<div class="stage-header red-flag">⚠️ Step 4: Safety Check (Red Flags)</div>',
        unsafe_allow_html=True,
    )

    manager = st.session_state.manager

    # Load red flags if not already loaded
    if not st.session_state.pending_red_flags:
        with st.spinner("Checking for red flags..."):
            red_flags = manager.check_red_flags()
            st.session_state.pending_red_flags = red_flags

    red_flags = st.session_state.pending_red_flags

    if not red_flags:
        st.success("✓ No red flag symptoms detected")
        if st.button("Continue →"):
            st.session_state.pending_red_flags = []
            st.rerun()
        return

    st.warning(
        f"**Important: Please answer these {len(red_flags)} safety-critical questions:**"
    )

    # Create form for all red flags
    with st.form("red_flags_form"):
        responses = {}

        for i, rf in enumerate(red_flags):
            st.markdown(f'<div class="question-card">', unsafe_allow_html=True)
            response = st.radio(
                f"**⚠️ {i+1}. {rf.get('common_name')}**",
                ["Yes", "No", "Unknown"],
                index=1,  # Default to "No"
                key=f"redf_{rf.get('id')}",
                horizontal=True,
            )
            responses[rf.get("id")] = response
            st.markdown("</div>", unsafe_allow_html=True)

        submitted = st.form_submit_button("Continue →", type="primary")

        if submitted:
            # Add all responses
            for rf_id, response in responses.items():
                choice_map = {"Yes": "present", "No": "absent", "Unknown": "unknown"}
                manager.add_red_flag_response(rf_id, choice_map[response])

            # Clear pending and move to next stage
            st.session_state.pending_red_flags = []
            st.success(f"✓ Recorded {len(responses)} responses")
            st.rerun()


def render_stage_5_interview_loop():
    """Stage 5: Diagnosis interview loop"""
    st.markdown(
        '<div class="stage-header">Step 5: Diagnostic Interview</div>',
        unsafe_allow_html=True,
    )

    manager = st.session_state.manager

    # Get next question if we don't have one
    if not st.session_state.current_question and not manager.is_interview_complete():
        with st.spinner("Generating next question..."):
            question = manager.get_next_question()
            st.session_state.current_question = question

    # Check if interview is complete
    if manager.is_interview_complete():
        st.success("✓ Interview complete!")

        # Get final results
        if not st.session_state.final_results:
            st.session_state.final_results = manager.get_final_results()

        st.rerun()
        return

    question = st.session_state.current_question

    if not question:
        st.error("No question available")
        return

    # Show progress
    progress = manager.get_progress()
    st.markdown(
        f'<div class="progress-text">Question {progress["questions_asked"]} | Evidence: {progress["evidence_count"]} items</div>',
        unsafe_allow_html=True,
    )

    # Show question
    st.markdown(f'<div class="question-card">', unsafe_allow_html=True)
    st.markdown(f"**{question.question_text}**")

    # Show options based on question type
    if question.question_type == "single":
        # Single yes/no question
        item = question.items[0] if question.items else {}
        response = st.radio(
            f"{item.get('name', 'Symptom')}",
            ["Yes", "No", "Unknown"],
            key=f"q_{item.get('id')}",
            horizontal=True,
        )

        if st.button("Next Question →", type="primary"):
            choice_map = {"Yes": "present", "No": "absent", "Unknown": "unknown"}
            manager.answer_question(item.get("id"), choice_map[response])
            st.session_state.current_question = None
            st.rerun()

    else:
        # Group question - show first item for now (can be enhanced)
        item = question.items[0] if question.items else {}
        response = st.radio(
            f"{item.get('name', 'Symptom')}",
            ["Yes", "No", "Unknown"],
            key=f"q_{item.get('id')}",
            horizontal=True,
        )

        if st.button("Next Question →", type="primary"):
            choice_map = {"Yes": "present", "No": "absent", "Unknown": "unknown"}
            manager.answer_question(item.get("id"), choice_map[response])
            st.session_state.current_question = None
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def render_stage_6_results():
    """Stage 6: Show final results and appointments"""
    st.markdown('<div class="complete-box">', unsafe_allow_html=True)
    st.markdown("## ✅ Interview Complete!")
    st.markdown("</div>", unsafe_allow_html=True)

    results = st.session_state.final_results

    # Show top conditions
    st.markdown(
        '<div class="stage-header">Diagnostic Results</div>', unsafe_allow_html=True
    )

    if results.get("conditions"):
        st.write(f"**Top {min(5, len(results['conditions']))} Possible Conditions:**")

        for i, cond in enumerate(results["conditions"][:5], 1):
            prob = cond.get("probability", 0) * 100
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{i}. {cond.get('common_name')}**")
            with col2:
                st.metric("Probability", f"{prob:.1f}%")

    # Interview summary
    with st.expander("📋 Interview Summary"):
        st.write(f"**Interview ID:** {results.get('interview_id')}")
        st.write(f"**Questions Asked:** {results.get('questions_asked')}")
        st.write(f"**Evidence Collected:** {len(results.get('evidence', []))} items")

    # Find appointments button
    st.markdown("---")
    if st.button(
        "🔍 Find Optimal Appointments", type="primary", use_container_width=True
    ):
        st.info("Appointment matching coming in Phase 4!")
        # This will integrate with the appointment optimizer


def main():
    """Main app logic"""
    initialize_session_state()
    render_header()
    render_sidebar()

    # Determine which stage to show
    if not st.session_state.manager:
        # Stage 1: Initial symptoms
        render_stage_1_initial_symptoms()

    else:
        manager = st.session_state.manager
        stage = manager.state.stage

        if stage == InterviewStage.INITIAL_SYMPTOMS:
            render_stage_2_risk_factors()

        elif stage == InterviewStage.RISK_FACTORS:
            if st.session_state.pending_risk_factors:
                render_stage_2_risk_factors()
            else:
                render_stage_3_related_symptoms()

        elif stage == InterviewStage.RELATED_SYMPTOMS:
            if st.session_state.pending_related_symptoms:
                render_stage_3_related_symptoms()
            else:
                render_stage_4_red_flags()

        elif (
            stage == InterviewStage.RED_FLAGS or stage == InterviewStage.INTERVIEW_LOOP
        ):
            if not manager.is_interview_complete():
                render_stage_5_interview_loop()
            else:
                render_stage_6_results()

        elif stage == InterviewStage.COMPLETE:
            render_stage_6_results()


if __name__ == "__main__":
    main()
