"""
Appointment Matching Engine
Intelligently matches patient symptoms/triage to optimal appointments
"""

from typing import List, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum


class TriageLevel(Enum):
    """5-level triage (from Infermedica)"""

    EMERGENCY_AMBULANCE = "emergency_ambulance"
    EMERGENCY = "emergency"
    CONSULTATION_24 = "consultation_24"
    CONSULTATION = "consultation"
    SELF_CARE = "self_care"


# Map Infermedica specialist IDs to our system
SPECIALIST_MAPPING = {
    "sp_1": "Primary Care",
    "sp_2": "Cardiology",
    "sp_3": "Dermatology",
    "sp_5": "Orthopedics",
    "sp_17": "Neurology",
    "sp_15": "Psychiatry",
    "sp_11": "Pediatrics",
}


@dataclass
class TriageResult:
    """Result from Infermedica triage"""

    triage_level: TriageLevel
    recommended_specialist: str  # "Cardiology", "Primary Care", etc.
    serious_observations: List[str]
    root_cause: str


@dataclass
class AppointmentScore:
    """Scored appointment recommendation"""

    slot: any  # AppointmentSlot from simulator
    total_score: float
    urgency_match_score: float
    specialist_match_score: float
    availability_score: float
    reasoning: str


class AppointmentMatcher:
    """Matches triage results to optimal appointments"""

    def __init__(self):
        # Urgency level weights (how important is each factor)
        self.weights = {
            "urgency_match": 0.5,  # 50% - Most important
            "specialist_match": 0.3,  # 30% - Very important
            "availability": 0.2,  # 20% - Nice to have
        }

    def match_appointments(
        self, triage_result: TriageResult, available_slots: List, max_results: int = 5
    ) -> List[AppointmentScore]:
        """
        Match triage to appointments and rank by fit

        Args:
            triage_result: Triage assessment from Infermedica
            available_slots: List of available appointment slots
            max_results: Maximum recommendations to return

        Returns:
            List of scored appointments, ranked best to worst
        """
        scored_appointments = []

        for slot in available_slots:
            if not slot.available:
                continue

            # Score this appointment
            score = self._score_appointment(triage_result, slot)
            scored_appointments.append(score)

        # Sort by total score (descending)
        scored_appointments.sort(key=lambda x: x.total_score, reverse=True)

        return scored_appointments[:max_results]

    def _score_appointment(self, triage: TriageResult, slot) -> AppointmentScore:
        """Score a single appointment slot"""

        # 1. Urgency Match Score
        urgency_score = self._calculate_urgency_match(
            triage.triage_level, slot.datetime, slot.appointment_type
        )

        # 2. Specialist Match Score
        specialist_score = self._calculate_specialist_match(
            triage.recommended_specialist, slot.provider.specialty.value
        )

        # 3. Availability Score (sooner is better for urgent cases)
        availability_score = self._calculate_availability_score(
            triage.triage_level, slot.datetime
        )

        # Calculate weighted total
        total_score = (
            urgency_score * self.weights["urgency_match"]
            + specialist_score * self.weights["specialist_match"]
            + availability_score * self.weights["availability"]
        )

        # Generate reasoning
        reasoning = self._generate_reasoning(
            triage, slot, urgency_score, specialist_score, availability_score
        )

        return AppointmentScore(
            slot=slot,
            total_score=total_score,
            urgency_match_score=urgency_score,
            specialist_match_score=specialist_score,
            availability_score=availability_score,
            reasoning=reasoning,
        )

    def _calculate_urgency_match(
        self, triage_level: TriageLevel, slot_datetime: datetime, appointment_type
    ) -> float:
        """
        Score how well appointment timing matches urgency

        Returns: 0.0 to 1.0 (1.0 = perfect match)
        """
        days_until = (slot_datetime - datetime.now()).days
        hours_until = (slot_datetime - datetime.now()).total_seconds() / 3600

        # Define urgency requirements , these all need updating
        urgency_requirements = {
            TriageLevel.EMERGENCY_AMBULANCE: {
                "max_hours": 0,  # Need immediate care
                "required_type": "URGENT",
            },
            TriageLevel.EMERGENCY: {
                "max_hours": 1,  # Need care within 24 hours
                "required_type": "URGENT",
            },
            TriageLevel.CONSULTATION_24: {
                "max_hours": 24,  # Need care within 2 days
                "required_type": None,
            },
            TriageLevel.CONSULTATION: {
                "max_days": 7,  # Need care within 2 weeks
                "required_type": None,
            },
            TriageLevel.SELF_CARE: {
                "max_days": 30,  # Follow-up acceptable
                "required_type": None,
            },
        }

        req = urgency_requirements[triage_level]

        # Emergency levels
        if triage_level in [TriageLevel.EMERGENCY_AMBULANCE, TriageLevel.EMERGENCY]:
            if hours_until <= req["max_hours"]:
                return 1.0
            elif days_until <= 1:
                return 0.7
            elif days_until <= 2:
                return 0.4
            else:
                return 0.1  # Too far out for emergency

        # Consultation within 24 hours
        elif triage_level == TriageLevel.CONSULTATION_24:
            if days_until <= 1:
                return 1.0
            elif days_until <= 2:
                return 0.8
            elif days_until <= 7:
                return 0.5
            else:
                return 0.3

        # Regular consultation
        elif triage_level == TriageLevel.CONSULTATION:
            if days_until <= 7:
                return 1.0
            elif days_until <= 14:
                return 0.8
            else:
                return 0.6

        # Self-care
        else:
            if days_until <= 30:
                return 1.0
            else:
                return 0.8

    def _calculate_specialist_match(
        self, recommended: str, provider_specialty: str
    ) -> float:
        """
        Score how well provider specialty matches recommendation

        Returns: 0.0 to 1.0 (1.0 = perfect match)
        """
        # Exact match
        if recommended.lower() == provider_specialty.lower():
            return 1.0

        # Primary care can handle many things
        if provider_specialty == "Primary Care":
            return 0.7  # Good fallback

        # Partial match (e.g., "Cardiology" vs "Cardiac Surgery")
        if (
            recommended.lower() in provider_specialty.lower()
            or provider_specialty.lower() in recommended.lower()
        ):
            return 0.8

        # No match
        return 0.3

    def _calculate_availability_score(
        self, triage_level: TriageLevel, slot_datetime: datetime
    ) -> float:
        """
        Score based on how soon appointment is available

        For urgent cases: sooner = much better
        For routine cases: timing less critical

        Returns: 0.0 to 1.0
        """
        days_until = (slot_datetime - datetime.now()).days

        # Emergency: sooner is critical
        if triage_level in [TriageLevel.EMERGENCY_AMBULANCE, TriageLevel.EMERGENCY]:
            if days_until == 0:
                return 1.0
            elif days_until == 1:
                return 0.5
            else:
                return 0.2

        # Consultation within 24 hours: soon is important
        elif triage_level == TriageLevel.CONSULTATION_24:
            if days_until <= 1:
                return 1.0
            elif days_until <= 3:
                return 0.7
            else:
                return 0.5

        # Regular consultation: reasonable timeframe
        elif triage_level == TriageLevel.CONSULTATION:
            if days_until <= 7:
                return 1.0
            elif days_until <= 14:
                return 0.9
            else:
                return 0.7

        # Self-care: timing flexible
        else:
            return 0.8  # Consistent score, timing not critical

    def _generate_reasoning(
        self,
        triage: TriageResult,
        slot,
        urgency_score: float,
        specialist_score: float,
        availability_score: float,
    ) -> str:
        """Generate human-readable reasoning for recommendation"""
        reasons = []

        # Urgency reasoning
        if urgency_score >= 0.8:
            reasons.append("✓ Timing matches your urgency level")
        elif urgency_score >= 0.5:
            reasons.append("⚠ Timing acceptable but not ideal for urgency")
        else:
            reasons.append("⚠ Timing may be too far out for your urgency")

        # Specialist reasoning
        if specialist_score >= 0.9:
            reasons.append(
                f"✓ {slot.provider.specialty.value} matches recommended specialist"
            )
        elif specialist_score >= 0.7:
            reasons.append(f"⚠ {slot.provider.specialty.value} can handle your case")
        else:
            reasons.append(f"⚠ Different specialty than recommended")

        # Availability reasoning
        days_until = (slot.datetime - datetime.now()).days
        if days_until == 0:
            reasons.append("✓ Available today")
        elif days_until == 1:
            reasons.append("✓ Available tomorrow")
        elif days_until <= 7:
            reasons.append(f"✓ Available in {days_until} days")
        else:
            reasons.append(f"Available in {days_until} days")

        return "\n".join(reasons)

    def get_alternative_options(self, triage_result: TriageResult) -> List[Dict]:
        """
        Get alternative care options based on triage
        (ER, urgent care, telemedicine, etc.)
        """
        alternatives = []

        # Emergency Department
        if triage_result.triage_level in [
            TriageLevel.EMERGENCY_AMBULANCE,
            TriageLevel.EMERGENCY,
        ]:
            alternatives.append(
                {
                    "type": "Emergency Department",
                    "availability": "Immediate",
                    "cost_range": (1500, 3000),
                    "wait_time": "< 1 hour",
                    "icon": "🚨",
                }
            )

        # Urgent Care
        if triage_result.triage_level in [
            TriageLevel.EMERGENCY,
            TriageLevel.CONSULTATION_24,
        ]:
            alternatives.append(
                {
                    "type": "Urgent Care Center",
                    "availability": "Walk-in (within 1 hour)",
                    "cost_range": (150, 300),
                    "wait_time": "30-60 minutes",
                    "icon": "🏥",
                }
            )

        # Telemedicine
        if triage_result.triage_level != TriageLevel.EMERGENCY_AMBULANCE:
            alternatives.append(
                {
                    "type": "Telemedicine Visit",
                    "availability": "Within 2-4 hours",
                    "cost_range": (40, 75),
                    "wait_time": "2-4 hours",
                    "icon": "💻",
                }
            )

        # Self-care
        if triage_result.triage_level == TriageLevel.SELF_CARE:
            alternatives.append(
                {
                    "type": "Self-Care & Monitoring",
                    "availability": "Immediate",
                    "cost_range": (0, 20),
                    "wait_time": "None",
                    "icon": "🏠",
                }
            )

        return alternatives


def demo_matcher():
    """Demo the appointment matcher"""
    from appointment_simulator import AppointmentSimulator, SpecialtyType

    print("=" * 60)
    print("Appointment Matching Engine Demo")
    print("=" * 60)

    # Simulate a triage result
    triage = TriageResult(
        triage_level=TriageLevel.CONSULTATION_24,
        recommended_specialist="Cardiology",
        serious_observations=["Chest pain", "Shortness of breath"],
        root_cause="Cardiovascular symptoms require evaluation",
    )

    print(f"\n📋 Triage Result:")
    print(f"   Level: {triage.triage_level.value}")
    print(f"   Recommended: {triage.recommended_specialist}")

    # Get available slots
    simulator = AppointmentSimulator()
    slots = simulator.generate_slots(days_ahead=14)

    print(f"\n🔍 Found {len([s for s in slots if s.available])} available slots")

    # Match appointments
    matcher = AppointmentMatcher()
    recommendations = matcher.match_appointments(triage, slots, max_results=3)

    print(f"\n🎯 Top Recommendations:\n")

    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec.slot.provider.name} - {rec.slot.provider.specialty.value}")
        print(f"   📅 {rec.slot.datetime.strftime('%A, %B %d at %I:%M %p')}")
        print(f"   💰 ${rec.slot.cost_estimate}")
        print(f"   ⭐ Fit Score: {rec.total_score:.2f}/1.00")
        print(f"\n   Why recommended:")
        for line in rec.reasoning.split("\n"):
            print(f"   {line}")
        print()

    # Show alternatives
    alternatives = matcher.get_alternative_options(triage)
    print(f"\n💡 Alternative Care Options:\n")

    for alt in alternatives:
        print(f"{alt['icon']} {alt['type']}")
        print(f"   Available: {alt['availability']}")
        print(f"   Cost: ${alt['cost_range'][0]}-${alt['cost_range'][1]}")
        print()


if __name__ == "__main__":
    demo_matcher()
