"""
Infermedica API Client
Handles authentication, symptom parsing, triage, and specialist recommendation
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
    """Result from /triage endpoint - urgency only"""

    triage_level: TriageLevel
    recommended_channel: str
    serious_observations: List[Dict]
    root_cause: str


@dataclass
class SpecialistRecommendation:
    """Result from /recommend_specialist endpoint"""

    specialist_id: str
    specialist_name: str
    specialist_category: str


@dataclass
class DiagnosisQuestion:
    """Question from diagnosis endpoint (for full interview flow)"""

    question_type: str  # single, group_single, group_multiple
    question_text: str
    items: List[Dict]  # List of symptoms/conditions to ask about
    question_id: Optional[str] = None


@dataclass
class DiagnosisResult:
    """Result from diagnosis endpoint (for full interview flow)"""

    question: Optional[DiagnosisQuestion]
    should_stop: bool
    conditions: List[Dict]
    extras: Dict


class InfermedicaClient:
    """
    Client for Infermedica Platform/Engine API
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
        """Parse free text into structured symptoms"""
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
            print(f"✗ Parse failed: {e}")
            raise

    def run_triage(
        self, symptoms: List[ParsedSymptom], age: int, sex: str
    ) -> TriageResult:
        """
        Get urgency level from /triage endpoint
        Does NOT return specialist - use recommend_specialist() for that
        """
        url = f"{self.base_url}/triage"

        evidence = [
            {"id": s.id, "choice_id": s.choice_id, "source": "initial"}
            for s in symptoms
        ]

        payload = {"sex": sex, "age": {"value": age}, "evidence": evidence}

        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()

            return TriageResult(
                triage_level=TriageLevel(data["triage_level"]),
                recommended_channel=data.get("recommended_channel", "personal_visit"),
                serious_observations=data.get("serious", []),
                root_cause=data.get("root_cause", ""),
            )

        except requests.exceptions.RequestException as e:
            print(f"✗ Triage failed: {e}")
            raise

    def recommend_specialist(
        self, symptoms: List[ParsedSymptom], age: int, sex: str
    ) -> SpecialistRecommendation:
        """Get specialist recommendation from /recommend_specialist endpoint"""
        url = f"{self.base_url}/recommend_specialist"

        evidence = [
            {"id": s.id, "choice_id": s.choice_id, "source": "initial"}
            for s in symptoms
        ]

        payload = {"sex": sex, "age": {"value": age}, "evidence": evidence}

        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()

            specialist = data.get("recommended_specialist", {})

            return SpecialistRecommendation(
                specialist_id=specialist.get("id", "sp_1"),
                specialist_name=specialist.get("name", "General Practitioner"),
                specialist_category=specialist.get("category", "Primary Care"),
            )

        except requests.exceptions.RequestException as e:
            print(f"✗ Specialist recommendation failed: {e}")
            # Return safe default
            return SpecialistRecommendation(
                specialist_id="sp_1",
                specialist_name="General Practitioner",
                specialist_category="Primary Care",
            )

    def suggest_risk_factors(
        self, age: int, sex: str, interview_id: Optional[str] = None
    ) -> List[Dict]:
        """Get demographic risk factors"""
        url = f"{self.base_url}/suggest"

        payload = {
            "sex": sex,
            "age": {"value": age},
            "suggest_method": "demographic_risk_factors",
        }

        if interview_id:
            payload["interview_id"] = interview_id

        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()

            if isinstance(data, list):
                return data
            else:
                return data.get("suggestions", [])
        except requests.exceptions.RequestException as e:
            print(f"✗ Risk factors failed: {e}")
            return []

    def suggest_related_symptoms(
        self,
        evidence: List[Dict],
        age: int,
        sex: str,
        interview_id: Optional[str] = None,
    ) -> List[Dict]:
        """Get related symptoms to ask about"""
        url = f"{self.base_url}/suggest"

        payload = {
            "sex": sex,
            "age": {"value": age},
            "evidence": evidence,
            "suggest_method": "symptoms",
        }

        if interview_id:
            payload["interview_id"] = interview_id

        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()

            if isinstance(data, list):
                return data
            else:
                return data.get("suggestions", [])
        except requests.exceptions.RequestException as e:
            print(f"✗ Related symptoms failed: {e}")
            return []

    def suggest_red_flags(
        self,
        evidence: List[Dict],
        age: int,
        sex: str,
        interview_id: Optional[str] = None,
    ) -> List[Dict]:
        """Check for red flag symptoms"""
        url = f"{self.base_url}/suggest"

        payload = {
            "sex": sex,
            "age": {"value": age},
            "evidence": evidence,
            "suggest_method": "red_flags",
        }

        if interview_id:
            payload["interview_id"] = interview_id

        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()

            if isinstance(data, list):
                return data
            else:
                return data.get("suggestions", [])
        except requests.exceptions.RequestException as e:
            print(f"✗ Red flags failed: {e}")
            return []

    def diagnosis(
        self,
        evidence: List[Dict],
        age: int,
        sex: str,
        interview_id: Optional[str] = None,
        extras: Optional[Dict] = None,
    ) -> DiagnosisResult:
        """Get next question in diagnostic interview"""
        url = f"{self.base_url}/diagnosis"

        payload = {"sex": sex, "age": {"value": age}, "evidence": evidence}

        if interview_id:
            payload["interview_id"] = interview_id

        if extras:
            payload["extras"] = extras

        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()

            should_stop = data.get("should_stop", False)
            conditions = data.get("conditions", [])
            extras_response = data.get("extras", {})

            question = None
            if not should_stop and "question" in data:
                q = data["question"]
                question = DiagnosisQuestion(
                    question_type=q.get("type"),
                    question_text=q.get("text"),
                    items=q.get("items", []),
                    question_id=q.get("id"),
                )

            return DiagnosisResult(
                question=question,
                should_stop=should_stop,
                conditions=conditions,
                extras=extras_response,
            )
        except requests.exceptions.RequestException as e:
            print(f"✗ Diagnosis failed: {e}")
            return DiagnosisResult(
                question=None, should_stop=True, conditions=[], extras={}
            )


def test_infermedica():
    """Test the client"""
    print("Testing Infermedica Client")
    print("=" * 60)

    client = InfermedicaClient()

    # Parse
    print("\n1. Parse symptoms")
    symptoms = client.parse_symptoms("chest pain", 45, "male")
    print(f"✓ Parsed: {[s.common_name for s in symptoms]}")

    # Triage
    print("\n2. Run triage")
    triage = client.run_triage(symptoms, 45, "male")
    print(f"✓ Urgency: {triage.triage_level.value}")

    # Specialist
    print("\n3. Recommend specialist")
    specialist = client.recommend_specialist(symptoms, 45, "male")
    print(f"✓ Specialist: {specialist.specialist_name}")

    print("\n" + "=" * 60)
    print("✓ All tests passed!")


if __name__ == "__main__":
    test_infermedica()
