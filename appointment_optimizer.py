"""
Appointment Optimization Flow
Complete pipeline: Symptoms → Triage → Specialist → Appointment Matching
"""

from typing import Dict, List
from dataclasses import dataclass
from infermedica_client import (
    InfermedicaClient,
    ParsedSymptom,
    TriageResult,
    SpecialistRecommendation,
)
from appointment_simulator import AppointmentSimulator, SpecialtyType
from appointment_matcher import AppointmentMatcher, AppointmentScore


@dataclass
class PatientInfo:
    """Patient demographic information"""

    age: int
    sex: str  # "male" or "female"
    symptom_text: str


@dataclass
class OptimizationResult:
    """Complete result with triage + specialist + appointments"""

    patient: PatientInfo
    parsed_symptoms: List[ParsedSymptom]
    triage: TriageResult
    specialist: SpecialistRecommendation
    recommended_appointments: List[AppointmentScore]
    alternative_options: List[Dict]


class AppointmentOptimizer:
    """
    Main orchestrator for appointment optimization
    Calls /triage and /recommend_specialist separately
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

        # Step 2: Run triage (urgency level)
        print(f"\n2️⃣ Running clinical triage...")
        triage = self.infermedica.run_triage(
            symptoms=symptoms, age=patient.age, sex=patient.sex
        )

        print(f"   ✓ Urgency: {triage.triage_level.value}")
        print(f"   ✓ Channel: {triage.recommended_channel}")

        # Step 3: Get specialist recommendation (separate call)
        print(f"\n3️⃣ Getting specialist recommendation...")
        specialist = self.infermedica.recommend_specialist(
            symptoms=symptoms, age=patient.age, sex=patient.sex
        )

        print(f"   ✓ Specialist: {specialist.specialist_name}")
        print(f"   ✓ Category: {specialist.specialist_category}")

        # Step 4: Generate appointment slots
        print(f"\n4️⃣ Finding available appointments...")

        # Map specialist to our specialty types
        specialty = self._map_specialist_to_specialty(specialist.specialist_name)

        # Get slots (filter by specialty if urgent)
        if triage.triage_level.value in ["emergency", "emergency_ambulance"]:
            slots = self.simulator.get_urgent_slots(specialty)
        else:
            slots = self.simulator.generate_slots(specialty=specialty, days_ahead=14)

        print(f"   ✓ Found {len([s for s in slots if s.available])} available slots")

        # Step 5: Match appointments
        print(f"\n5️⃣ Matching optimal appointments...")

        recommendations = self.matcher.match_appointments(
            triage_level=triage.triage_level.value,
            specialist_name=specialist.specialist_name,
            available_slots=slots,
            max_results=5,
        )

        print(f"   ✓ Ranked {len(recommendations)} appointments by fit")

        # Step 6: Get alternative options
        alternatives = self.matcher.get_alternative_options(triage.triage_level.value)

        print("\n" + "=" * 60)
        print("✓ Optimization Complete")
        print("=" * 60)

        return OptimizationResult(
            patient=patient,
            parsed_symptoms=symptoms,
            triage=triage,
            specialist=specialist,
            recommended_appointments=recommendations,
            alternative_options=alternatives,
        )

    def _map_specialist_to_specialty(self, specialist_name: str) -> SpecialtyType:
        """Map specialist name to our specialty enum"""
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


def main():
    """Demo the optimizer"""
    optimizer = AppointmentOptimizer()

    # Test case: Chest pain
    patient = PatientInfo(
        age=45, sex="male", symptom_text="I have chest pain and shortness of breath"
    )

    result = optimizer.optimize(patient)

    print("\n" + "=" * 60)
    print("📊 RESULTS SUMMARY")
    print("=" * 60)
    print(f"\n🚨 Urgency: {result.triage.triage_level.value}")
    print(f"👨‍⚕️ Specialist: {result.specialist.specialist_name}")
    print(f"\n🗓️ Top Appointments:")
    for i, appt in enumerate(result.recommended_appointments[:3], 1):
        print(
            f"  {i}. {appt.provider_name} - {appt.appointment_datetime.strftime('%b %d at %I:%M %p')} (Score: {appt.total_score:.0%})"
        )


if __name__ == "__main__":
    main()
