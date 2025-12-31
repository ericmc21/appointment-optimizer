"""
Appointment Optimization Flow
Complete pipeline: Symptoms → Triage → Appointment Matching
"""

from typing import Dict, List
from dataclasses import dataclass
from infermedica_client import InfermedicaClient, ParsedSymptom, TriageResult
from appointment_simulator import AppointmentSimulator, SpecialtyType
from appointment_matcher import (
    AppointmentMatcher,
    AppointmentScore,
    TriageLevel as MatcherTriageLevel,
)


@dataclass
class PatientInfo:
    """Patient demographic information"""

    age: int
    sex: str  # "male" or "female"
    symptom_text: str


@dataclass
class OptimizationResult:
    """Complete result with triage + appointments"""

    patient: PatientInfo
    parsed_symptoms: List[ParsedSymptom]
    triage: TriageResult
    recommended_appointments: List[AppointmentScore]
    alternative_options: List[Dict]


class AppointmentOptimizer:
    """
    Main orchestrator for appointment optimization
    """

    def __init__(self):
        self.infermedica = InfermedicaClient()
        self.simulator = AppointmentSimulator()
        self.matcher = AppointmentMatcher()

    def optimize(self, patient: PatientInfo) -> OptimizationResult:
        """
        Complete optimization flow

        Args:
            patient: Patient information and symptoms

        Returns:
            Complete optimization result with recommendations
        """
        print("=" * 60)
        print("🔍 Starting Appointment Optimization")
        print("=" * 60)

        # Step 1: Parse symptoms
        print(f"\n1️⃣ Parsing symptoms: '{patient.symptom_text}'")
        symptoms = self.infermedica.parse_symptoms(
            text=patient.symptom_text, age=patient.age, sex=patient.sex
        )

        print(f"   ✓ Found {len(symptoms)} symptoms:")
        for symptom in symptoms:
            print(f"     • {symptom.common_name}")

        # Step 2: Run triage
        print(f"\n2️⃣ Running clinical triage...")
        triage = self.infermedica.run_triage(
            symptoms=symptoms, age=patient.age, sex=patient.sex
        )

        print(f"   ✓ Urgency: {triage.triage_level.value}")
        print(f"   ✓ Recommended: {triage.recommended_specialist_name}")

        # Step 3: Generate appointment slots
        print(f"\n3️⃣ Finding available appointments...")

        # Map Infermedica specialist to our specialty types
        specialty = self._map_specialist_to_specialty(
            triage.recommended_specialist_name
        )

        # Get slots (filter by specialty if urgent)
        if triage.triage_level.value in ["emergency", "emergency_ambulance"]:
            slots = self.simulator.get_urgent_slots(specialty)
        else:
            slots = self.simulator.generate_slots(specialty=specialty, days_ahead=14)

        print(f"   ✓ Found {len([s for s in slots if s.available])} available slots")

        # Step 4: Match appointments
        print(f"\n4️⃣ Matching optimal appointments...")

        # Convert Infermedica triage to matcher format
        matcher_triage = self._convert_triage_for_matcher(triage)

        recommendations = self.matcher.match_appointments(
            triage_result=matcher_triage, available_slots=slots, max_results=5
        )

        print(f"   ✓ Ranked {len(recommendations)} appointments by fit")

        # Step 5: Get alternative options
        alternatives = self.matcher.get_alternative_options(matcher_triage)

        print("\n" + "=" * 60)
        print("✓ Optimization Complete")
        print("=" * 60)

        return OptimizationResult(
            patient=patient,
            parsed_symptoms=symptoms,
            triage=triage,
            recommended_appointments=recommendations,
            alternative_options=alternatives,
        )

    def _map_specialist_to_specialty(self, specialist_name: str) -> SpecialtyType:
        """Map Infermedica specialist name to our specialty enum"""
        mapping = {
            "general practitioner": SpecialtyType.PRIMARY_CARE,
            "primary care": SpecialtyType.PRIMARY_CARE,
            "cardiologist": SpecialtyType.CARDIOLOGY,
            "cardiology": SpecialtyType.CARDIOLOGY,
            "dermatologist": SpecialtyType.DERMATOLOGY,
            "orthopedist": SpecialtyType.ORTHOPEDICS,
            "orthopedics": SpecialtyType.ORTHOPEDICS,
            "neurologist": SpecialtyType.NEUROLOGY,
            "psychiatrist": SpecialtyType.PSYCHIATRY,
            "pediatrician": SpecialtyType.PEDIATRICS,
        }

        specialist_lower = specialist_name.lower()
        return mapping.get(specialist_lower, SpecialtyType.PRIMARY_CARE)

    def _convert_triage_for_matcher(self, triage: TriageResult):
        """Convert Infermedica triage to matcher's expected format"""
        from appointment_matcher import TriageResult as MatcherTriage

        # Map Infermedica triage levels to matcher enum
        level_map = {
            "emergency_ambulance": MatcherTriageLevel.EMERGENCY_AMBULANCE,
            "emergency": MatcherTriageLevel.EMERGENCY,
            "consultation_24": MatcherTriageLevel.CONSULTATION_24,
            "consultation": MatcherTriageLevel.CONSULTATION,
            "self_care": MatcherTriageLevel.SELF_CARE,
        }

        return MatcherTriage(
            triage_level=level_map[triage.triage_level.value],
            recommended_specialist=triage.recommended_specialist_name,
            serious_observations=[
                obs.get("name", "") for obs in triage.serious_observations
            ],
            root_cause=triage.root_cause,
        )

    def display_results(self, result: OptimizationResult):
        """Display results in a user-friendly format"""
        print("\n" + "=" * 60)
        print("📊 APPOINTMENT RECOMMENDATIONS")
        print("=" * 60)

        # Patient info
        print(f"\n👤 Patient: {result.patient.age}yo {result.patient.sex}")
        print(f'💬 Complaint: "{result.patient.symptom_text}"')

        # Triage summary
        print(f"\n📋 Assessment:")
        print(f"   Urgency: {result.triage.triage_level.value.upper()}")
        print(f"   Recommended: {result.triage.recommended_specialist_name}")

        # Top recommendations
        print(f"\n🎯 RECOMMENDED APPOINTMENTS:\n")

        for i, rec in enumerate(result.recommended_appointments[:3], 1):
            slot = rec.slot
            score_pct = int(rec.total_score * 100)

            print(f"{i}. {slot.provider.name} - {slot.provider.specialty.value}")
            print(f"   ⭐ Fit Score: {score_pct}/100")
            print(f"   📅 {slot.datetime.strftime('%A, %B %d at %I:%M %p')}")
            print(f"   💰 ${slot.cost_estimate} • ⏱️ {slot.duration_minutes} min")
            print(f"   📍 {slot.provider.location}")

            if slot.provider.rating:
                print(f"   ⭐ Provider Rating: {slot.provider.rating}/5.0")

            print(f"\n   Why recommended:")
            for line in rec.reasoning.split("\n"):
                print(f"   {line}")
            print()

        # Alternative options
        if result.alternative_options:
            print(f"\n💡 ALTERNATIVE CARE OPTIONS:\n")

            for alt in result.alternative_options:
                cost_min, cost_max = alt["cost_range"]
                print(f"{alt['icon']} {alt['type']}")
                print(f"   Available: {alt['availability']}")
                print(f"   Cost: ${cost_min}-${cost_max}")
                print(f"   Wait: {alt['wait_time']}")
                print()


def demo_optimization():
    """Demo the complete optimization flow"""
    print("=" * 60)
    print("🏥 APPOINTMENT OPTIMIZATION SYSTEM DEMO")
    print("=" * 60)

    # Example scenarios
    scenarios = [
        PatientInfo(
            age=45,
            sex="male",
            symptom_text="I have chest pain and feel dizzy when I stand up",
        ),
        PatientInfo(
            age=28, sex="female", symptom_text="I have a cold and fever for 3 days"
        ),
        PatientInfo(age=62, sex="male", symptom_text="My knee hurts when I walk"),
    ]

    optimizer = AppointmentOptimizer()

    # Run first scenario
    patient = scenarios[0]

    print(f"\n📝 Scenario: {patient.age}yo {patient.sex}")
    print(f'Symptoms: "{patient.symptom_text}"')

    try:
        result = optimizer.optimize(patient)
        optimizer.display_results(result)

        print("\n" + "=" * 60)
        print("✓ Demo Complete!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Demo failed: {e}")
        print("\nNote: This demo requires Infermedica API credentials.")
        print("Add INFERMEDICA_APP_ID and INFERMEDICA_APP_KEY to .env")
        raise


if __name__ == "__main__":
    demo_optimization()
