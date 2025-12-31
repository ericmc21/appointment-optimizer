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
        self, text: str, age: str, sex: str, include_tokens: bool = False
    ) -> List[ParsedSymptom]:
        """
        Parse free text into structured symptoms using Infermedica NLP

        Args:
            text: Patient's symptom descrpiption (e.g., "I have a cold and fever")
            age: Patient age
            sex: "male" or "female"
            include_tokens: Whether to include token-level analysis

        Returns:
            List of parse symptoms with IDs

        Example:
            >>> parse_symptoms("I have a cold and fever", 30, "male")
            [
                ParsedSymptom(id="s_99", name="Fever", common_name="Fever"),
                ParsedSymptom(id="s_1962", name="Nasal congestion", ...)Parse
            ]
        """
        url = f"{self.base_url}/parse"

        payload = {
            "text": text,
            "age": {"value": age},  # need to add unit
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
