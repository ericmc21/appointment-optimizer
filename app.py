"""
Streamlit UI for Intelligent Appointment Optimizer
"""

import streamlit as st
from datetime import datetime
from appointment_optimizer import AppointmentOptimizer, PatientInfo, OptimizationResult
from infermedica_client import InfermedicaClient

# Page config
st.set_page_config(
    page_title="Appointment Optimizer",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .appointment-card {
        border: 2px solid #e0e0e0;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .best-match {
        border-color: #4CAF50;
        background-color: #f1f8f4;
    }
    .urgency-emergency {
        color: #d32f2f;
        font-weight: bold;
    }
    .urgency-consultation {
        color: #ff9800;
        font-weight: bold;
    }
    .urgency-self-care {
        color: #4caf50;
        font-weight: bold;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Initialize session state
if "optimization_result" not in st.session_state:
    st.session_state.optimization_result = None
if "show_details" not in st.session_state:
    st.session_state.show_details = False

# Header
st.markdown(
    '<p class="main-header">🏥 Intelligent Appointment Optimizer</p>',
    unsafe_allow_html=True,
)
st.markdown(
    "AI-powered system that matches your symptoms to the optimal healthcare appointment"
)

# Sidebar - Patient Information
with st.sidebar:
    st.header("👤 Patient Information")

    age = st.number_input(
        "Age", min_value=0, max_value=120, value=30, help="Patient's age in years"
    )

    sex = st.selectbox(
        "Sex assigned at birth",
        options=["male", "female"],
        help="Required for accurate symptom assessment",
    )

    st.divider()

    # Example symptoms
    with st.expander("📝 Example Symptoms"):
        st.markdown(
            """
        **Emergency examples:**
        - "I have chest pain and feel dizzy when I stand up"
        - "Severe headache with vision changes"
        
        **Routine examples:**
        - "I have a cold and fever for 3 days"
        - "My knee hurts when I walk"
        - "Persistent cough for 2 weeks"
        """
        )

    # System info
    with st.expander("ℹ️ How it works"):
        st.markdown(
            """
        1. **Analyze** symptoms using AI
        2. **Assess** urgency level
        3. **Match** to optimal appointments
        4. **Recommend** best provider & timing
        """
        )

# Main content area
tab1, tab2 = st.tabs(["🔍 Find Appointment", "📊 About"])

with tab1:
    # Symptom input
    st.subheader("What symptoms are you experiencing?")

    symptom_text = st.text_area(
        "Describe your symptoms",
        placeholder="e.g., I have chest pain and feel dizzy when I stand up",
        height=100,
        help="Describe your symptoms in your own words. Be specific about location, duration, and severity.",
    )

    # Action buttons
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        search_button = st.button(
            "🔍 Find Optimal Appointment", type="primary", use_container_width=True
        )

    with col2:
        if st.session_state.optimization_result:
            clear_button = st.button("🔄 Clear", use_container_width=True)
            if clear_button:
                st.session_state.optimization_result = None
                st.rerun()

    # Process search
    if search_button:
        if not symptom_text.strip():
            st.error("⚠️ Please describe your symptoms")
        else:
            try:
                with st.spinner("🔄 Analyzing symptoms and finding appointments..."):
                    # Create patient info
                    patient = PatientInfo(age=age, sex=sex, symptom_text=symptom_text)

                    # Run optimization
                    optimizer = AppointmentOptimizer()
                    result = optimizer.optimize(patient)

                    # Store in session state
                    st.session_state.optimization_result = result
                    st.success("✅ Analysis complete!")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.info(
                    "💡 Note: This requires Infermedica API credentials. Add INFERMEDICA_APP_ID and INFERMEDICA_APP_KEY to your .env file."
                )

    # Display results
    if st.session_state.optimization_result:
        result = st.session_state.optimization_result

        st.divider()

        # Triage Assessment
        st.subheader("📋 Clinical Assessment")

        col1, col2, col3 = st.columns(3)

        with col1:
            urgency = result.triage.triage_level.value
            urgency_display = urgency.replace("_", " ").title()

            # Color code by urgency
            if "emergency" in urgency:
                urgency_class = "urgency-emergency"
                urgency_icon = "🚨"
            elif "consultation" in urgency:
                urgency_class = "urgency-consultation"
                urgency_icon = "⚠️"
            else:
                urgency_class = "urgency-self-care"
                urgency_icon = "✅"

            st.markdown(
                f'<div class="metric-card"><p style="color: #666; font-size: 0.9rem;">Urgency Level</p><p class="{urgency_class}" style="font-size: 1.5rem;">{urgency_icon} {urgency_display}</p></div>',
                unsafe_allow_html=True,
            )

        with col2:
            st.markdown(
                f'<div class="metric-card"><p style="color: #666; font-size: 0.9rem;">Recommended Specialist</p><p style="font-size: 1.2rem; font-weight: bold;">🩺 {result.triage.recommended_specialist_name}</p></div>',
                unsafe_allow_html=True,
            )

        with col3:
            st.markdown(
                f'<div class="metric-card"><p style="color: #666; font-size: 0.9rem;">Parsed Symptoms</p><p style="font-size: 1.2rem; font-weight: bold;">📝 {len(result.parsed_symptoms)}</p></div>',
                unsafe_allow_html=True,
            )

        # Show parsed symptoms
        if st.checkbox("Show parsed symptoms", value=False):
            st.write("**Identified symptoms:**")
            for symptom in result.parsed_symptoms:
                st.write(f"• {symptom.common_name}")

        st.divider()

        # Appointments
        st.subheader("🎯 Recommended Appointments")

        if result.recommended_appointments:
            # Best match highlight
            best = result.recommended_appointments[0]

            with st.container():
                st.markdown(
                    f"""
                <div class="appointment-card best-match">
                    <h4>🏆 BEST MATCH - Fit Score: {int(best.total_score * 100)}/100</h4>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"### {best.slot.provider.name}")
                    st.markdown(f"**{best.slot.provider.specialty.value}**")
                    st.markdown(f"📍 {best.slot.provider.location}")

                    if best.slot.provider.rating:
                        stars = "⭐" * int(best.slot.provider.rating)
                        st.markdown(
                            f"{stars} {best.slot.provider.rating}/5.0 ({best.slot.provider.years_experience} years experience)"
                        )

                with col2:
                    st.markdown(f"#### 📅 {best.slot.datetime.strftime('%A, %B %d')}")
                    st.markdown(f"#### 🕐 {best.slot.datetime.strftime('%I:%M %p')}")
                    st.markdown(f"#### 💰 ${best.slot.cost_estimate}")
                    st.markdown(f"⏱️ {best.slot.duration_minutes} minutes")

                st.markdown("**Why this is recommended:**")
                for line in best.reasoning.split("\n"):
                    if line.strip():
                        st.markdown(f"{line}")

                st.button(
                    "📅 Schedule Appointment", type="primary", key="schedule_best"
                )

            # Other options
            if len(result.recommended_appointments) > 1:
                st.markdown("### Alternative Options")

                for i, rec in enumerate(result.recommended_appointments[1:4], 2):
                    with st.expander(
                        f"{i}. {rec.slot.provider.name} - {rec.slot.provider.specialty.value} (Score: {int(rec.total_score * 100)}/100)"
                    ):
                        col1, col2 = st.columns([2, 1])

                        with col1:
                            st.write(f"**Provider:** {rec.slot.provider.name}")
                            st.write(
                                f"**Specialty:** {rec.slot.provider.specialty.value}"
                            )
                            st.write(f"**Location:** {rec.slot.provider.location}")
                            if rec.slot.provider.rating:
                                st.write(f"**Rating:** {rec.slot.provider.rating}/5.0")

                        with col2:
                            st.write(
                                f"**Date:** {rec.slot.datetime.strftime('%A, %B %d')}"
                            )
                            st.write(
                                f"**Time:** {rec.slot.datetime.strftime('%I:%M %p')}"
                            )
                            st.write(f"**Cost:** ${rec.slot.cost_estimate}")
                            st.write(f"**Duration:** {rec.slot.duration_minutes} min")

                        st.markdown("**Reasoning:**")
                        for line in rec.reasoning.split("\n"):
                            if line.strip():
                                st.write(line)

                        st.button(f"📅 Schedule", key=f"schedule_{i}")

        else:
            st.warning("No appointments found matching your criteria")

        # Alternative care options
        if result.alternative_options:
            st.divider()
            st.subheader("💡 Alternative Care Options")

            cols = st.columns(len(result.alternative_options))

            for idx, alt in enumerate(result.alternative_options):
                with cols[idx]:
                    cost_min, cost_max = alt["cost_range"]

                    st.markdown(
                        f"""
                    <div class="metric-card">
                        <h4>{alt['icon']} {alt['type']}</h4>
                        <p><strong>Available:</strong> {alt['availability']}</p>
                        <p><strong>Cost:</strong> ${cost_min}-${cost_max}</p>
                        <p><strong>Wait:</strong> {alt['wait_time']}</p>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

with tab2:
    st.subheader("About This System")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
        ### 🎯 What It Does
        
        This AI-powered system combines clinical triage with intelligent 
        appointment matching to route patients to the right care at the right time.
        
        **Key Features:**
        - 🩺 Medical-grade symptom assessment (Infermedica AI)
        - ⚡ 5-level urgency triage
        - 🎯 Smart appointment matching algorithm
        - 💰 Cost transparency
        - 📊 Alternative care options
        
        ### 🔬 Technology Stack
        
        - **Clinical AI:** Infermedica Engine API
        - **Matching:** Custom scoring algorithm
        - **Backend:** Python, FastAPI
        - **Frontend:** Streamlit
        """
        )

    with col2:
        st.markdown(
            """
        ### 📈 How Matching Works
        
        Appointments are scored based on three factors:
        
        **1. Urgency Match (50%)**
        - Emergency → Must be within 24 hours
        - Consultation → Within 2 weeks acceptable
        
        **2. Specialist Match (30%)**
        - Exact specialty match = 1.0
        - Primary care fallback = 0.7
        
        **3. Availability (20%)**
        - Sooner is better for urgent cases
        - Flexible for routine care
        
        ### 🔐 Privacy & Security
        
        - No personal data stored
        - HIPAA-compliant architecture ready
        - Secure API communication
        - Session-based processing
        
        ### 📧 Contact
        
        **Eric McLean**  
        Senior Delivery Manager | Healthcare AI  
        [eric-mclean.com](https://eric-mclean.com)
        """
        )

    st.divider()

    st.info(
        """
    **Note:** This is a demonstration system using simulated appointment data. 
    Production deployment would integrate with real EHR systems (Epic FHIR, Cerner) 
    and provider scheduling databases.
    """
    )

# Footer
st.divider()
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("🏥 **Intelligent Appointment Optimizer**")

with col2:
    st.markdown("Built with Infermedica AI")

with col3:
    st.markdown(f"© 2025 | [Portfolio](https://eric-mclean.com)")
