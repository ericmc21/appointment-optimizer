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
    serious_observations: List[Dict]
    root_cause: str


@dataclass
class SpecialistRecommendation:
    """Result from /recommend_specialist endpont"""

    specialist_id: str
    specialist_name: str
    specialist_category: str


@dataclass
class DiagnosisQuestion:
    """Question from diagnosis endpoint"""

    question_type: str  # single, group_single, group_multiple
    question_text: str
    items: List[Dict]  # List of symptoms/conditions to ask about
    question_id: Optional[str] = None


@dataclass
class DiagnosisResult:
    """Result from diagnosis endpoint"""

    question: Optional[DiagnosisQuestion]
    should_stop: bool
    conditions: List[Dict]
    extras: Dict


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
                serious_observations=data.get("serious", []),
                root_cause=data.get("root_cause", ""),
            )

        except requests.exceptions.RequestException as e:
            print(f"✗ Infermedica triage failed: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"Response: {e.response.text}")
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
        """
        Get common demographic risk factors to ask about

        Args:
            age: Patient age
            sex: "male" or "female"
            interview_id: Optional interview tracking ID

        Returns:
            List of risk factors to confirm
        """
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

            # Return the suggestions
            if isinstance(data, list):
                return data
            else:
                return data.get("key", [])
        except requests.exceptions.RequestException as e:
            print(f"x Risk factors request failed: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"Response: {e.response.text}")
            return []

    def suggest_related_symptoms(
        self,
        evidence: List[Dict],
        age: int,
        sex: str,
        interview_id: Optional[str] = None,
    ) -> List[Dict]:
        """
        Get related symptoms to ask about based on current evidence

        Args:
            evidence: List of symptoms already collected
            age: Patient age
            sex: "male" or "female"
            interview_id: Optional interview tracking ID

        Returns:
            List of related symptoms to ask about
        """
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

            # Return the suggestions
            if isinstance(data, list):
                return data
            else:
                return data.get("key", [])

        except requests.exceptions.RequestException as e:
            print(f"✗ Related symptoms suggestion failed: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"Response: {e.response.text}")
            return []

    def suggest_red_flags(
        self,
        evidence: List[Dict],
        age: int,
        sex: str,
        interview_id: Optional[str] = None,
    ) -> List[Dict]:
        """
        Check for red flag symptoms (safety critical)

        Args:
            evidence: List of symptoms already collected
            age: Patient age
            sex: "male" or "female"
            interview_id: Optional interview tracking ID

        Returns:
            List of red flag symptoms to check
        """
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

            # Return the suggestions
            if isinstance(data, list):
                return data
            else:
                return data.get("key", [])

        except requests.exceptions.RequestException as e:
            print(f"✗ Red flags check failed: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"Response: {e.response.text}")
            return []

    def diagnosis(
        self,
        evidence: List[Dict],
        age: int,
        sex: str,
        interview_id: Optional[str] = None,
        extras: Optional[Dict] = None,
    ) -> DiagnosisResult:
        """
        Get next question in the diagnostic interview

        This is the core of the iterative interview loop. Call repeatedly until should_stop=True.

        Args:
            evidence: List of symptoms/conditions with responses
            age: Patient age
            sex: "male" or "female"
            interview_id: Optional interview tracking ID (recommended)
            extras: Optional additional context
        """
        url = f"{self.base_url}/diagnosis"

        payload = {"sex": sex, "age": {"value": age}, "evidence": evidence}

        if interview_id:
            payload["interview_Id"] = interview_id

        if extras:
            payload["extras"] = extras

        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()

            # Parse the response
            should_stop = data.get("should_stop", False)
            conditions = data.get("conditions", [])
            extras_response = data.get("extras", {})

            # Parse question if present
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
            print(f"✗ Diagnosis call failed: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"Response: {e.response.text}")

            # Return safe default - stop interview
            return DiagnosisResult(
                question=None, should_stop=True, conditions=[], extras={}
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
