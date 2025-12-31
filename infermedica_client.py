"""
Infermedica API Client
Handles authentication, symptom parsing, and triage
"""

import os
import requests
from typing import Dict, List, Optional
from dotenv import load_dotenv
from dataclasses import dataclass
from enum import Enum

load_dotenv()


class TriageLevel(Enum):
    """5-level triage from Infermedica"""

    EMERGENCY_AMBULANCE = "emergency_ambulance"
    EMERGENCY = "emergency"
    CONSULTATION_24 = "consultation_24"
    CONSULTATION = "consultation"
    SELF_CARE = "self_care"


@dataclass
class ParsedSymptom:
    """Symptom parsed from text"""

    id: str
    name: str
    common_name: str
    choice_id: str = "present"  # present, absent, unknown


@dataclass
class TriageResult:
    """Result from triage endpoint"""

    triage_level: TriageLevel
    recommended_specialist_id: str
    recommended_specialist_name: str
    recommended_channel: str
    serious_observations: List[Dict]
    root_cause: str


class InfermedicaClient:
    """
    Client for Infermedica Platform/Engine API
    Handles symptom parsing and triage
    """

    def __init__(self):
        self.app_id = os.getenv("INFERMEDICA_APP_ID")
        self.app_key = os.getenv("INFERMEDICA_APP_KEY")
        self.base_url = os.getenv(
            "INFERMEDICA_BASE_URL", "https://api.infermedica.com/v3"
        )

        if not self.app_id or not self.app_key:
            raise ValueError(
                "INFERMEDICA_APP_ID and INFERMEDICA_APP_KEY required in .env"
            )

        self.headers = {
            "App-Id": self.app_id,
            "App-Key": self.app_key,
            "Content-Type": "application/json",
        }

    def parse_symptoms(
        self, text: str, age: int, sex: str, include_tokens: bool = False
    ) -> List[ParsedSymptom]:
        """
        Parse free text into structured symptoms using Infermedica NLP

        Args:
            text: Patient's symptom description (e.g., "I have a cold and fever")
            age: Patient age
            sex: "male" or "female"
            include_tokens: Whether to include token-level analysis

        Returns:
            List of parsed symptoms with IDs

        Example:
            >>> parse_symptoms("I have a cold and fever", 30, "male")
            [
                ParsedSymptom(id="s_99", name="Fever", common_name="Fever"),
                ParsedSymptom(id="s_1962", name="Nasal congestion", ...)
            ]
        """
        url = f"{self.base_url}/parse"

        payload = {
            "text": text,
            "age": {"value": age},
            "sex": sex,
            "include_tokens": include_tokens,
        }

        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()

            # Extract mentions (symptoms found in text)
            symptoms = []
            for mention in data.get("mentions", []):
                symptom = ParsedSymptom(
                    id=mention["id"],
                    name=mention["name"],
                    common_name=mention.get("common_name", mention["name"]),
                    choice_id="present",
                )
                symptoms.append(symptom)

            return symptoms

        except requests.exceptions.RequestException as e:
            print(f"✗ Infermedica parse failed: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"Response: {e.response.text}")
            raise

    def suggest_symptoms(
        self, text: str, age: int, sex: str, max_results: int = 8
    ) -> List[ParsedSymptom]:
        """
        Suggest symptoms based on partial text (autocomplete-style)

        Args:
            text: Partial symptom text (e.g., "head")
            age: Patient age
            sex: "male" or "female"
            max_results: Maximum suggestions to return

        Returns:
            List of suggested symptoms
        """
        url = f"{self.base_url}/suggest"

        payload = {
            "text": text,
            "age": {"value": age},
            "sex": sex,
            "max_results": max_results,
        }

        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()

            suggestions = []
            for item in data:
                symptom = ParsedSymptom(
                    id=item["id"],
                    name=item["name"],
                    common_name=item.get("common_name", item["name"]),
                )
                suggestions.append(symptom)

            return suggestions

        except requests.exceptions.RequestException as e:
            print(f"✗ Infermedica suggest failed: {e}")
            raise

    def run_triage(
        self,
        symptoms: List[ParsedSymptom],
        age: int,
        sex: str,
        risk_factors: Optional[List[Dict]] = None,
    ) -> TriageResult:
        """
        Run triage assessment based on symptoms

        Args:
            symptoms: List of symptoms (from parse or user selection)
            age: Patient age
            sex: "male" or "female"
            risk_factors: Optional risk factors (e.g., pregnancy, smoking)

        Returns:
            TriageResult with urgency level and recommendations
        """
        url = f"{self.base_url}/triage"

        # Build evidence list
        evidence = []
        for symptom in symptoms:
            evidence.append(
                {"id": symptom.id, "choice_id": symptom.choice_id, "source": "initial"}
            )

        # Add risk factors if provided
        if risk_factors:
            evidence.extend(risk_factors)

        payload = {"sex": sex, "age": {"value": age}, "evidence": evidence}

        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()

            return TriageResult(
                triage_level=TriageLevel(data["triage_level"]),
                recommended_specialist_id=data.get("recommended_specialist", {}).get(
                    "id", "sp_1"
                ),
                recommended_specialist_name=data.get("recommended_specialist", {}).get(
                    "name", "General Practitioner"
                ),
                recommended_channel=data.get("recommended_channel", "personal_visit"),
                serious_observations=data.get("serious", []),
                root_cause=data.get("root_cause", ""),
            )

        except requests.exceptions.RequestException as e:
            print(f"✗ Infermedica triage failed: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"Response: {e.response.text}")
            raise

    def get_specialist_info(self, specialist_id: str) -> Dict:
        """
        Get information about a specialist

        Args:
            specialist_id: Specialist ID (e.g., "sp_2")

        Returns:
            Specialist information
        """
        # Map common specialist IDs to names
        specialist_map = {
            "sp_1": {"name": "General Practitioner", "category": "Primary Care"},
            "sp_2": {"name": "Cardiologist", "category": "Cardiology"},
            "sp_3": {"name": "Dermatologist", "category": "Dermatology"},
            "sp_5": {"name": "Orthopedist", "category": "Orthopedics"},
            "sp_17": {"name": "Neurologist", "category": "Neurology"},
            "sp_15": {"name": "Psychiatrist", "category": "Psychiatry"},
            "sp_11": {"name": "Pediatrician", "category": "Pediatrics"},
        }

        return specialist_map.get(
            specialist_id, {"name": "Specialist", "category": "General"}
        )


def test_infermedica():
    """Test Infermedica integration"""
    print("=" * 60)
    print("Testing Infermedica Integration")
    print("=" * 60)

    try:
        client = InfermedicaClient()

        # Test 1: Parse symptoms from text
        print("\n1️⃣ Testing symptom parsing...")
        print("Input: 'I have a cold and fever'")

        symptoms = client.parse_symptoms(
            text="I have a cold and fever", age=30, sex="male"
        )

        print(f"\n✓ Parsed {len(symptoms)} symptoms:")
        for symptom in symptoms:
            print(f"  • {symptom.common_name} ({symptom.id})")

        # Test 2: Run triage
        print("\n2️⃣ Testing triage assessment...")

        triage = client.run_triage(symptoms=symptoms, age=30, sex="male")

        print(f"\n✓ Triage Result:")
        print(f"  Urgency: {triage.triage_level.value}")
        print(f"  Recommended: {triage.recommended_specialist_name}")
        print(f"  Channel: {triage.recommended_channel}")

        if triage.serious_observations:
            print(f"  Serious: {len(triage.serious_observations)} concerning findings")

        # Test 3: Suggest symptoms (autocomplete)
        print("\n3️⃣ Testing symptom suggestions...")
        print("Input: 'head'")

        suggestions = client.suggest_symptoms(
            text="head", age=30, sex="male", max_results=5
        )

        print(f"\n✓ Suggested {len(suggestions)} symptoms:")
        for suggestion in suggestions:
            print(f"  • {suggestion.common_name}")

        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        raise


if __name__ == "__main__":
    test_infermedica()
