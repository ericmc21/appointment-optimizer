"""
Appointment Simulator
Generates realistic provider schedules and availability for demo purposes
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict
from dataclasses import dataclass
from enum import Enum


class SpecialtyType(Enum):
    """Medical specialties"""

    PRIMARY_CARE = "Primary Care"
    CARDIOLOGY = "Cardiology"
    DERMATOLOGY = "Dermatology"
    ORTHOPEDICS = "Orthopedics"
    NEUROLOGY = "Neurology"
    PSYCHIATRY = "Psychiatry"
    PEDIATRICS = "Pediatrics"


class AppointmentType(Enum):
    """Types of appointments"""

    NEW_PATIENT = "New Patient"
    FOLLOW_UP = "Follow-up"
    URGENT = "Urgent Care"
    ANNUAL_PHYSICAL = "Annual Physical"
    PROCEDURE = "Procedure"


class TimeSlot(Enum):
    """Time slots"""

    MORNING = "Morning (8:00 AM - 12:00 PM)"
    AFTERNOON = "Afternoon (12:00 PM - 5:00 PM)"
    EVENING = "Evening (5:00 PM - 8:00 PM)"


@dataclass
class Provider:
    """Healthcare provider"""

    id: str
    name: str
    specialty: SpecialtyType
    location: str
    in_network: bool = True
    rating: float = 4.5
    years_experience: int = 10


@dataclass
class AppointmentSlot:
    """Available appointment slot"""

    id: str
    provider: Provider
    datetime: datetime
    appointment_type: AppointmentType
    duration_minutes: int
    cost_estimate: int
    available: bool = True


class AppointmentSimulator:
    """Simulates realistic appointment availability"""

    def __init__(self):
        self.providers = self._generate_providers()

    def _generate_providers(self) -> List[Provider]:
        """Generate sample providers"""
        providers = [
            # Primary Care
            Provider(
                "prov_001",
                "Dr. Emily Rodriguez",
                SpecialtyType.PRIMARY_CARE,
                "Main Campus - Building A",
                True,
                4.8,
                15,
            ),
            Provider(
                "prov_002",
                "Dr. Michael Chen",
                SpecialtyType.PRIMARY_CARE,
                "North Clinic",
                True,
                4.6,
                8,
            ),
            # Cardiology
            Provider(
                "prov_003",
                "Dr. Sarah Chen",
                SpecialtyType.CARDIOLOGY,
                "Main Campus Cardiology",
                True,
                4.9,
                20,
            ),
            Provider(
                "prov_004",
                "Dr. James Wilson",
                SpecialtyType.CARDIOLOGY,
                "Heart Center",
                True,
                4.7,
                12,
            ),
            # Dermatology
            Provider(
                "prov_005",
                "Dr. Lisa Anderson",
                SpecialtyType.DERMATOLOGY,
                "Dermatology Clinic",
                True,
                4.8,
                18,
            ),
            # Orthopedics
            Provider(
                "prov_006",
                "Dr. Robert Martinez",
                SpecialtyType.ORTHOPEDICS,
                "Sports Medicine Center",
                True,
                4.7,
                15,
            ),
            # Neurology
            Provider(
                "prov_007",
                "Dr. Patricia Kumar",
                SpecialtyType.NEUROLOGY,
                "Neurology Center",
                True,
                4.9,
                22,
            ),
            # Psychiatry
            Provider(
                "prov_008",
                "Dr. David Thompson",
                SpecialtyType.PSYCHIATRY,
                "Behavioral Health",
                True,
                4.6,
                10,
            ),
        ]
        return providers

    def generate_slots(
        self,
        specialty: SpecialtyType = None,
        days_ahead: int = 14,
        appointment_type: AppointmentType = None,
    ) -> List[AppointmentSlot]:
        """
        Generate appointment slots

        Args:
            specialty: Filter by specialty
            days_ahead: Number of days to generate slots for
            appointment_type: Filter by appointment type

        Returns:
            List of available appointment slots
        """
        slots = []

        # Filter providers by specialty if specified
        providers = self.providers
        if specialty:
            providers = [p for p in providers if p.specialty == specialty]

        for provider in providers:
            # Generate slots for each day
            for day_offset in range(days_ahead):
                date = datetime.now() + timedelta(days=day_offset)

                # Skip weekends (simple logic)
                if date.weekday() >= 5:
                    continue

                # Generate 2-4 slots per day per provider
                num_slots = random.randint(2, 4)

                for _ in range(num_slots):
                    slot = self._generate_slot(provider, date, appointment_type)
                    if slot:
                        slots.append(slot)

        return sorted(slots, key=lambda x: x.datetime)

    def _generate_slot(
        self,
        provider: Provider,
        date: datetime,
        appointment_type: AppointmentType = None,
    ) -> AppointmentSlot:
        """Generate a single appointment slot"""

        # Random time slot
        time_slot = random.choice(list(TimeSlot))

        # Map time slot to hour
        hour_ranges = {
            TimeSlot.MORNING: (8, 12),
            TimeSlot.AFTERNOON: (12, 17),
            TimeSlot.EVENING: (17, 20),
        }

        start_hour, end_hour = hour_ranges[time_slot]
        hour = random.randint(start_hour, end_hour - 1)
        minute = random.choice([0, 15, 30, 45])

        slot_datetime = date.replace(hour=hour, minute=minute, second=0)

        # Determine appointment type
        if appointment_type is None:
            appointment_type = random.choice(list(AppointmentType))

        # Determine duration and cost based on type
        duration_cost = {
            AppointmentType.NEW_PATIENT: (60, 250),
            AppointmentType.FOLLOW_UP: (30, 150),
            AppointmentType.URGENT: (20, 200),
            AppointmentType.ANNUAL_PHYSICAL: (45, 200),
            AppointmentType.PROCEDURE: (90, 500),
        }

        duration, base_cost = duration_cost[appointment_type]

        # Adjust cost by specialty
        specialty_multipliers = {
            SpecialtyType.PRIMARY_CARE: 1.0,
            SpecialtyType.CARDIOLOGY: 1.5,
            SpecialtyType.DERMATOLOGY: 1.2,
            SpecialtyType.ORTHOPEDICS: 1.4,
            SpecialtyType.NEUROLOGY: 1.6,
            SpecialtyType.PSYCHIATRY: 1.3,
            SpecialtyType.PEDIATRICS: 0.9,
        }

        cost = int(base_cost * specialty_multipliers[provider.specialty])

        # 80% of slots are available (simulate some bookings)
        available = random.random() < 0.8

        slot_id = f"slot_{provider.id}_{slot_datetime.strftime('%Y%m%d%H%M')}"

        return AppointmentSlot(
            id=slot_id,
            provider=provider,
            datetime=slot_datetime,
            appointment_type=appointment_type,
            duration_minutes=duration,
            cost_estimate=cost,
            available=available,
        )

    def get_provider_by_specialty(self, specialty: SpecialtyType) -> List[Provider]:
        """Get providers by specialty"""
        return [p for p in self.providers if p.specialty == specialty]

    def get_urgent_slots(
        self, specialty: SpecialtyType = None
    ) -> List[AppointmentSlot]:
        """Get urgent care slots (within 48 hours)"""
        slots = self.generate_slots(
            specialty=specialty, days_ahead=2, appointment_type=AppointmentType.URGENT
        )
        return [s for s in slots if s.available]


def demo_simulator():
    """Demo the appointment simulator"""
    simulator = AppointmentSimulator()

    print("=" * 60)
    print("Appointment Simulator Demo")
    print("=" * 60)

    # Show cardiology slots
    print("\n🫀 Cardiology Appointments (Next 7 days):")
    cardio_slots = simulator.generate_slots(
        specialty=SpecialtyType.CARDIOLOGY, days_ahead=7
    )

    for slot in cardio_slots[:5]:
        if slot.available:
            print(f"\n  {slot.provider.name}")
            print(f"  📅 {slot.datetime.strftime('%A, %B %d at %I:%M %p')}")
            print(f"  💰 ${slot.cost_estimate}")
            print(f"  ⏱️ {slot.duration_minutes} minutes")

    # Show urgent slots
    print("\n\n🚨 Urgent Care Slots (Next 48 hours):")
    urgent_slots = simulator.get_urgent_slots()

    for slot in urgent_slots[:3]:
        print(f"\n  {slot.provider.name} - {slot.provider.specialty.value}")
        print(f"  📅 {slot.datetime.strftime('%A, %B %d at %I:%M %p')}")
        print(f"  💰 ${slot.cost_estimate}")


if __name__ == "__main__":
    demo_simulator()
