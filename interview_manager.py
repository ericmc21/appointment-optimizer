"""
Interview Manager
Managers multi-turn diagnostic interview with Infermedica
"""

import uuid
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from infermedica_client import (
    InfermedicaClient,
    ParsedSymptom,
    DiagnosisQuestion,
    DiagnosisResult,
    TriageResult,
)


class InterviewStage(Enum):
    """Stages of the diagnostic interview"""

    NOT_STARTED = "not_started"
    INITIAL_SYMPTOMS = "initial_symptoms"
    RISK_FACTORS = "risk_factors"
    RELATED_SYMPTOMS = "related_symptoms"
    RED_FLAGS = "red_flags"
    INTERVIEW_LOOP = "interview_loop"
    COMPLETE = "complete"


@dataclass
class InterviewHistory:
    """Record of a question and answer in the interview"""

    stage: InterviewStage
    question_text: str
    question_type: str
    item_id: str
    item_name: str
    response: str  # "present", "absent", "unknown"
    timestamp: str = ""


@dataclass
class InterviewState:
    """Complete state of an interview session"""

    interview_id: str
    patient_age: int
    patient_sex: str
    stage: InterviewStage = InterviewStage.NOT_STARTED
    evidence: List[Dict] = field(default_factory=list)
    history: List[InterviewHistory] = field(default_factory=list)
    conditions: List[Dict] = field(default_factory=list)
    is_complete: bool = False
    questions_asked: int = 0
    current_question: Optional[DiagnosisQuestion] = None


class InterviewManager:
    """
    Manages the com
    """

    def __init__(
        self,
        client: InfermedicaClient,
        age: int,
        sex: str,
        interview_id: Optional[str] = None,
    ):
        """
        Initialize interview manager

        Args:
            client: InfermedicaClient instance
            age: patient age
            sex: "male" or "female"
            interview_id: Optional custom interview ID
        """
        self.client = client
        self.state = InterviewState(
            interview_id=interview_id or self._generate_interview_id(),
            patient_age=age,
            patient_sex=sex,
        )

        # Pending items to ask about (populated by sugget methods)
        self.pending_risk_factors = []
        self.pending_related_symptoms = []
        self.pending_red_flags = []

    def _generate_interview_id(self) -> str:
        """Generate unique interview ID"""
        interview_id = uuid.uuid4()
        return interview_id.hex

    def start_interview(self, initial_symptoms: List[ParsedSymptom]):
        """
        Start interview with parsed symptoms

        Args:
            initial_symptoms: List of ParsedSymptom from /parse endpoint
        """
        self.state.stage = InterviewStage.INITIAL_SYMPTOMS

        # Add initial symptoms to evidence
        for symptom in initial_symptoms:
            self.state.evidence.append(
                {"id": symptom.id, "choice_id": symptom.choice_id, "source": "initial"}
            )

            # Add to history
            self.state.history.append(
                InterviewHistory(
                    stage=InterviewStage.INITIAL_SYMPTOMS,
                    question_text="Initial symptoms",
                    question_type="initial",
                    item_id=symptom.id,
                    item_name=symptom.name,
                    response=symptom.choice_id,
                    timestamp=datetime.now().isoformat(),
                )
            )

    def collect_risk_factors(self) -> List[Dict]:
        """
        Get demographic risk factors to ask about

        Returns:
            List of risk factors (empty if already collected)
        """
        if self.state.stage != InterviewStage.INITIAL_SYMPTOMS:
            return []

        # Call Infermedica API
        risk_factors = self.client.suggest_risk_factors(
            age=self.state.patient_age,
            sex=self.state.patient_sex,
            interview_id=self.state.interview_id,
        )

        # Store for later processing
        self.pending_risk_factors = risk_factors
        self.state.stage = InterviewStage.RISK_FACTORS

        return risk_factors

    def add_risk_factor_response(self, risk_factor_id: str, response: str):
        """
        Add user's response to a risk factor question

        Args:
            risk_factor_id: Risk factor ID (e.g., "p_8")
            response: "present", "absent", or "unknown"
        """
        # Add to evidence
        self.state.evidence.append(
            {"id": risk_factor_id, "choice_id": response, "source": "suggest"}
        )

        # Find the risk factor name
        rf_name = "Risk factor"
        for rf in self.pending_risk_factors:
            if rf.get("id") == risk_factor_id:
                rf_name = rf.get("name", "Risk factor")
                break

        # Add to history
        self.state.history.append(
            InterviewHistory(
                stage=InterviewStage.RISK_FACTORS,
                question_text=f"Do you have {rf_name}?",
                question_type="risk_factor",
                item_id=risk_factor_id,
                item_name=rf_name,
                response=response,
                timestamp=datetime.now().isoformat(),
            )
        )
