"""
Appointment Matcher
Scores and ranks appointments based on triage urgency and specialist match
"""

from datetime import datetime, timedelta
from typing import List, Dict
from dataclasses import dataclass
from appointment_simulator import AppointmentSlot


@dataclass
class AppointmentScore:
    """Scored appointment with reasoning"""

    provider_name: str
    specialty: str
    location: str
    appointment_datetime: datetime
    total_score: float
    urgency_match_score: float
    specialist_match_score: float
    availability_score: float
    reasoning: List[str]


class AppointmentMatcher:
    """
    Matches patient needs to appointments and scores by fit
    """

    def __init__(self):
        # Scoring weights (must sum to 1.0)
        self.weights = {
            "urgency_match": 0.5,  # 50% - Most important
            "specialist_match": 0.3,  # 30% - Important
            "availability": 0.2,  # 20% - Nice to have
        }

    def match_appointments(
        self,
        triage_level: str,
        specialist_name: str,
        available_slots: List[AppointmentSlot],
        max_results: int = 5,
    ) -> List[AppointmentScore]:
        """
        Match and rank appointments

        Args:
            triage_level: Urgency level (e.g., "emergency", "consultation")
            specialist_name: Recommended specialist
            available_slots: Available appointment slots
            max_results: Maximum recommendations to return

        Returns:
            List of scored appointments, ranked best to worst
        """
        scored_appointments = []

        for slot in available_slots:
            if not slot.available:
                continue

            # Score this appointment
            score = self._score_appointment(triage_level, specialist_name, slot)
            scored_appointments.append(score)

        # Sort by total score (highest first)
        scored_appointments.sort(key=lambda x: x.total_score, reverse=True)

        return scored_appointments[:max_results]

    def _score_appointment(
        self, triage_level: str, specialist_name: str, slot: AppointmentSlot
    ) -> AppointmentScore:
        """Score a single appointment"""

        # 1. Urgency Match Score
        urgency_score = self._calculate_urgency_match(triage_level, slot.datetime)

        # 2. Specialist Match Score
        specialist_score = self._calculate_specialist_match(
            specialist_name, slot.provider.specialty.value
        )

        # 3. Availability Score
        availability_score = self._calculate_availability_score(
            triage_level, slot.datetime
        )

        # Calculate weighted total
        total_score = (
            urgency_score * self.weights["urgency_match"]
            + specialist_score * self.weights["specialist_match"]
            + availability_score * self.weights["availability"]
        )

        # Generate reasoning
        reasoning = self._generate_reasoning(
            triage_level,
            specialist_name,
            slot,
            urgency_score,
            specialist_score,
            availability_score,
        )

        return AppointmentScore(
            provider_name=slot.provider.name,
            specialty=slot.provider.specialty.value,
            location=slot.provider.location,
            appointment_datetime=slot.datetime,
            total_score=total_score,
            urgency_match_score=urgency_score,
            specialist_match_score=specialist_score,
            availability_score=availability_score,
            reasoning=reasoning,
        )

    def _calculate_urgency_match(
        self, triage_level: str, slot_datetime: datetime
    ) -> float:
        """
        Score how well appointment timing matches urgency

        Returns: 0.0 to 1.0 (1.0 = perfect match)
        """
        days_until = (slot_datetime - datetime.now()).days
        hours_until = (slot_datetime - datetime.now()).total_seconds() / 3600

        # Emergency ambulance: immediate care needed
        if triage_level == "emergency_ambulance":
            if hours_until < 1:
                return 1.0
            elif days_until == 0:
                return 0.7
            elif days_until <= 2:
                return 0.3
            else:
                return 0.1

        # Emergency: within 24 hours
        elif triage_level == "emergency":
            if hours_until < 24:
                return 1.0
            elif hours_until < 48:
                return 0.7
            elif days_until <= 7:
                return 0.4
            else:
                return 0.2

        # Consultation within 24 hours
        elif triage_level == "consultation_24":
            if hours_until < 24:
                return 1.0
            elif hours_until < 48:
                return 0.8
            elif days_until <= 7:
                return 0.5
            else:
                return 0.3

        # Consultation: within a week is good
        elif triage_level == "consultation":
            if days_until <= 7:
                return 1.0
            elif days_until <= 14:
                return 0.8
            else:
                return 0.6

        # Self-care: timing flexible
        else:  # self_care
            if days_until <= 30:
                return 1.0
            else:
                return 0.8

    def _calculate_specialist_match(
        self, recommended_specialist: str, provider_specialty: str
    ) -> float:
        """
        Score how well provider specialty matches recommendation

        Returns: 0.0 to 1.0 (1.0 = perfect match)
        """
        recommended_lower = recommended_specialist.lower()
        provider_lower = provider_specialty.lower()

        # Exact match
        if recommended_lower == provider_lower:
            return 1.0

        # Partial match (e.g., "cardiologist" in "cardiology")
        if recommended_lower in provider_lower or provider_lower in recommended_lower:
            return 0.8

        # Primary care can handle general cases
        if provider_lower == "primary care":
            return 0.7

        # No match
        return 0.3

    def _calculate_availability_score(
        self, triage_level: str, slot_datetime: datetime
    ) -> float:
        """
        Score availability (sooner is better for urgent cases)

        Returns: 0.0 to 1.0 (1.0 = best availability)
        """
        hours_until = (slot_datetime - datetime.now()).total_seconds() / 3600

        # For emergencies, sooner is critical
        if triage_level in ["emergency_ambulance", "emergency"]:
            if hours_until < 2:
                return 1.0
            elif hours_until < 6:
                return 0.8
            elif hours_until < 24:
                return 0.5
            else:
                return 0.2

        # For routine care, sooner is nice but not critical
        else:
            max_hours = 14 * 24  # 14 days
            normalized = 1.0 - (hours_until / max_hours)
            return max(0.7, min(1.0, normalized))

    def _generate_reasoning(
        self,
        triage_level: str,
        specialist_name: str,
        slot: AppointmentSlot,
        urgency_score: float,
        specialist_score: float,
        availability_score: float,
    ) -> List[str]:
        """Generate human-readable reasoning"""
        reasons = []

        # Urgency reasoning
        hours_until = (slot.datetime - datetime.now()).total_seconds() / 3600
        days_until = (slot.datetime - datetime.now()).days

        if triage_level in ["emergency_ambulance", "emergency"]:
            if hours_until < 24:
                reasons.append(
                    f"✓ Available within {int(hours_until)} hours (urgent case)"
                )
            else:
                reasons.append(f"⚠ {days_until} days wait (urgent case needs sooner)")
        else:
            if days_until <= 7:
                reasons.append(f"✓ Available within {days_until} days")

        # Specialist reasoning
        if specialist_score >= 0.8:
            reasons.append(f"✓ Matches recommended specialist ({specialist_name})")
        elif specialist_score >= 0.7:
            reasons.append(f"✓ Primary care provider (can handle general cases)")
        else:
            reasons.append(f"⚠ Different specialty than recommended")

        # Availability reasoning
        if availability_score >= 0.9:
            reasons.append(f"✓ Excellent availability")
        elif availability_score >= 0.7:
            reasons.append(f"✓ Good availability")

        return reasons

    def get_alternative_options(self, triage_level: str) -> List[Dict]:
        """Get alternative care options with costs"""
        alternatives = [
            {
                "name": "Emergency Room",
                "cost_range": "$1,500 - $3,000",
                "availability": "24/7",
                "best_for": "Life-threatening emergencies",
                "recommended": triage_level in ["emergency_ambulance", "emergency"],
            },
            {
                "name": "Urgent Care",
                "cost_range": "$150 - $300",
                "availability": "Walk-in, 8am-8pm",
                "best_for": "Non-life-threatening urgent issues",
                "recommended": triage_level in ["consultation_24", "emergency"],
            },
            {
                "name": "Telemedicine",
                "cost_range": "$40 - $90",
                "availability": "2-4 hours",
                "best_for": "Non-urgent consultations",
                "recommended": triage_level in ["consultation", "self_care"],
            },
        ]

        return alternatives
