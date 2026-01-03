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

    def collect_related_symptoms(self) -> List[Dict]:
        """
        Get related symptoms to ask about

        Returns:
            List of related symptoms (empty if already collected)
        """
        if self.state.stage != InterviewStage.RISK_FACTORS:
            return []

        # Call Infermedica API
        related = self.client.suggest_related_symptoms(
            evidence=self.state.evidence,
            age=self.state.patient_age,
            sex=self.state.patient_sex,
            interview_id=self.state.interview_id,
        )

        # Store for later processing
        self.pending_related_symptoms = related
        self.state.stage = InterviewStage.RELATED_SYMPTOMS

        return related

    def add_related_symptom_response(self, symptom_id: str, response: str):
        """
        Add user's response to a related symptom question

        Args:
            symptom_id: Symptom ID
            response: "present", "absent", or "unknown"
        """
        # Add to evidence
        self.state.evidence.append(
            {"id": symptom_id, "choice_id": response, "source": "suggest"}
        )

        # Find the symptom name
        sym_name = "Symptom"
        for sym in self.pending_related_symptoms:
            if sym.get("id") == symptom_id:
                sym_name = sym.get("name", "Symptom")
                break

        # Add to history
        self.state.history.append(
            InterviewHistory(
                stage=InterviewStage.RELATED_SYMPTOMS,
                question_text=f"Do you have {sym_name}?",
                question_type="related_symptom",
                item_id=symptom_id,
                item_name=sym_name,
                response=response,
                timestamp=datetime.now().isoformat(),
            )
        )

    def check_red_flags(self) -> List[Dict]:
        """
        Check for safety-critical red flag symptoms

        Returns:
            List of red flags to check (empty if already checked)
        """
        if self.state.stage != InterviewStage.RELATED_SYMPTOMS:
            return []

        # Call Infermedica API
        red_flags = self.client.suggest_red_flags(
            evidence=self.state.evidence,
            age=self.state.patient_age,
            sex=self.state.patient_sex,
            interview_id=self.state.interview_id,
        )

        # Store for later processing
        self.pending_red_flags = red_flags
        self.state.stage = InterviewStage.RED_FLAGS

        return red_flags

    def add_red_flag_response(self, red_flag_id: str, response: str):
        """
        Add user's response to a red flag question

        Args:
            red_flag_id: Red flag symptom ID
            response: "present", "absent", or "unknown"
        """
        # Add to evidence
        self.state.evidence.append(
            {"id": red_flag_id, "choice_id": response, "source": "suggest"}
        )

        # Find the red flag name
        rf_name = "Red flag symptom"
        for rf in self.pending_red_flags:
            if rf.get("id") == red_flag_id:
                rf_name = rf.get("name", "Red flag symptom")
                break

        # Add to history
        self.state.history.append(
            InterviewHistory(
                stage=InterviewStage.RED_FLAGS,
                question_text=f"Do you have {rf_name}?",
                question_type="red_flag",
                item_id=red_flag_id,
                item_name=rf_name,
                response=response,
                timestamp=datetime.now().isoformat(),
            )
        )

    def get_next_question(self) -> Optional[DiagnosisQuestion]:
        """
        Get next question from /diagnosis interview loop

        Returns:
            DiagnosisQuestion or None if interview complete
        """
        # Can only be called after red flags stage (not really)
        if self.state.stage == InterviewStage.RED_FLAGS:
            self.state.stage = InterviewStage.INTERVIEW_LOOP

        if self.state.stage != InterviewStage.INTERVIEW_LOOP:
            return None
        # Call /diagnosis endpoint
        result = self.client.diagnosis(
            evidence=self.state.evidence,
            age=self.state.patient_age,
            sex=self.state.patient_sex,
            interview_id=self.state.interview_id,
        )

        # Store current conditions
        self.state.conditions = result.conditions

        # Check if interview should stop
        if result.should_stop:
            self.state.is_complete = True
            self.state.stage = InterviewStage.COMPLETE
            self.state.current_question = None
            return None

        # Store current question
        self.state.current_question = result.question
        self.state.questions_asked += 1

        return result.question

    def answer_question(self, item_id: str, response: str):
        """
        Record answer to current diagnosis question

        Args:
            item_id: ID of the symptom/condition being answered
            response: "present", "absent", or "unknown"
        """
        if not self.state.current_question:
            return

        # Add to evidence
        self.state.evidence.append(
            {"id": item_id, "choice_id": response, "source": "predefined"}  # what?
        )

        # Find item name from current question
        item_name = "Symptom"
        for item in self.state.current_question.items:
            if item.get("id") == item_id:
                item_name = item.get("name", "Symptom")
                break

        # Add to history
        self.state.history.append(
            InterviewHistory(
                stage=InterviewStage.INTERVIEW_LOOP,
                question_text=self.state.current_question.question_text,
                question_type=self.state.current_question.question_type,
                item_id=item_id,
                item_name=item_name,
                response=response,
                timestamp=datetime.now().isoformat(),
            )
        )

    def is_interview_complete(self) -> bool:
        """Check if interview is complete"""
        return self.state.is_complete

    def get_progress(self) -> Dict:
        """
        Get interview progress information

        Returns:
            Dict with progress metrics
        """
        return {
            "stage": self.state.stage.value,
            "questions_asked": self.state.questions_asked,
            "evidence_count": len(self.state.evidence),
            "is_complete": self.state.is_complete,
            "conditions_count": len(self.state.conditions),
        }

    def get_final_results(self) -> Dict:
        """
        Get final results after interview completion

        Returns:
            Dict with conditions, triage, and history
        """
        if not self.state.is_complete:
            return {"error": "Interview not complete", "stage": self.state.stage.value}

        # Get final triage (need to convert evidence back to symptoms for compatibility)
        # For now, use the conditions we already have

        return {
            "interview_id": self.state.interview_id,
            "conditions": self.state.conditions,
            "evidence": self.state.evidence,
            "questions_asked": self.state.questions_asked,
            "history": [
                {
                    "stage": h.stage.value,
                    "question": h.question_text,
                    "item": h.item_name,
                    "response": h.response,
                    "timestamp": h.timestamp,
                }
                for h in self.state.history
            ],
        }

    def get_state_summary(self) -> str:
        """Get human-readable summary of interview state"""
        lines = [
            f"Interview ID: {self.state.interview_id}",
            f"Patient: {self.state.patient_age}yo {self.state.patient_sex}",
            f"Stage: {self.state.stage.value}",
            f"Questions asked: {self.state.questions_asked}",
            f"Evidence collected: {len(self.state.evidence)} items",
            f"Complete: {self.state.is_complete}",
        ]

        if self.state.conditions:
            lines.append(f"Top conditions: {len(self.state.conditions)}")
            for i, cond in enumerate(self.state.conditions[:3], 1):
                prob = cond.get("probability", 0) * 100
                lines.append(f"  {i}. {cond.get('common_name')} ({prob:.1f}%)")

        return "\n".join(lines)


# Example usage
if __name__ == "__main__":
    print("Interview Manager - Example Usage")
    print("=" * 60)

    # This would normally be run with real API credentials
    print(
        """
    from interview_manager import InterviewManager
    from infermedica_client import InfermedicaClient
    
    # Initialize
    client = InfermedicaClient()
    manager = InterviewManager(client, age=35, sex="male")
    
    # Parse initial symptoms
    symptoms = client.parse_symptoms("chest pain", 35, "male")
    
    # Start interview
    manager.start_interview(symptoms)
    
    # Collect risk factors
    risk_factors = manager.collect_risk_factors()
    for rf in risk_factors:
        # Ask user, then:
        manager.add_risk_factor_response(rf["id"], "absent")
    
    # Collect related symptoms
    related = manager.collect_related_symptoms()
    for sym in related:
        manager.add_related_symptom_response(sym["id"], "absent")
    
    # Check red flags
    red_flags = manager.check_red_flags()
    for rf in red_flags:
        manager.add_red_flag_response(rf["id"], "absent")
    
    # Interview loop
    while not manager.is_interview_complete():
        question = manager.get_next_question()
        if question:
            print(f"Q: {question.question_text}")
            # Get user response, then:
            manager.answer_question(question.items[0]["id"], "absent")
        else:
            break
    
    # Get results
    results = manager.get_final_results()
    print(f"Conditions: {results['conditions']}")
    """
    )
