"""
Test Interview Manager
Tests the complete interview flow with state management
"""

from interview_manager import InterviewManager, InterviewStage
from infermedica_client import InfermedicaClient


def test_interview_manager_flow():
    """Test complete interview flow with manager"""

    print("=" * 70)
    print("Testing Interview Manager - Complete Flow")
    print("=" * 70)

    # Initialize
    client = InfermedicaClient()
    manager = InterviewManager(client, age=35, sex="male")

    print(f"\n✓ Initialized Interview Manager")
    print(f"  Interview ID: {manager.state.interview_id}")
    print(f"  Patient: {manager.state.patient_age}yo {manager.state.patient_sex}")

    # Step 1: Parse and start with initial symptoms
    print("\n" + "=" * 70)
    print("STEP 1: Initial Symptoms")
    print("=" * 70)

    symptom_text = "I have chest pain and shortness of breath"
    print(f'Parsing: "{symptom_text}"')

    symptoms = client.parse_symptoms(symptom_text, 35, "male")
    print(f"✓ Parsed {len(symptoms)} symptoms:")
    for s in symptoms:
        print(f"  - {s.name}")

    manager.start_interview(symptoms)
    print(f"\n✓ Interview started")
    print(f"  Stage: {manager.state.stage.value}")
    print(f"  Evidence: {len(manager.state.evidence)} items")

    # Step 2: Risk Factors
    print("\n" + "=" * 70)
    print("STEP 2: Risk Factors")
    print("=" * 70)

    risk_factors = manager.collect_risk_factors()
    print(f"✓ Collected {len(risk_factors)} risk factors:")
    for i, rf in enumerate(risk_factors[:5], 1):
        print(f"  {i}. {rf.get('name')}")

    # Simulate answering (say "no" to all for demo)
    for rf in risk_factors[:3]:  # Answer first 3
        manager.add_risk_factor_response(rf.get("id"), "absent")

    print(f"\n✓ Answered {min(3, len(risk_factors))} risk factor questions")
    print(f"  Evidence: {len(manager.state.evidence)} items")

    # Step 3: Related Symptoms
    print("\n" + "=" * 70)
    print("STEP 3: Related Symptoms")
    print("=" * 70)

    related = manager.collect_related_symptoms()
    print(f"✓ Collected {len(related)} related symptoms:")
    for i, sym in enumerate(related[:5], 1):
        print(f"  {i}. {sym.get('name')}")

    # Simulate answering
    for sym in related[:3]:  # Answer first 3
        manager.add_related_symptom_response(sym.get("id"), "absent")

    print(f"\n✓ Answered {min(3, len(related))} related symptom questions")
    print(f"  Evidence: {len(manager.state.evidence)} items")

    # Step 4: Red Flags
    print("\n" + "=" * 70)
    print("STEP 4: Red Flags (Safety Critical)")
    print("=" * 70)

    red_flags = manager.check_red_flags()
    print(f"✓ Collected {len(red_flags)} red flags:")
    for i, rf in enumerate(red_flags, 1):
        print(f"  {i}. ⚠️  {rf.get('name')}")

    # Simulate answering
    for rf in red_flags:  # Answer all red flags
        manager.add_red_flag_response(rf.get("id"), "absent")

    print(f"\n✓ Answered {len(red_flags)} red flag questions")
    print(f"  Evidence: {len(manager.state.evidence)} items")

    # Step 5: Diagnosis Interview Loop
    print("\n" + "=" * 70)
    print("STEP 5: Diagnosis Interview Loop")
    print("=" * 70)

    max_questions = 5  # Limit for demo
    question_count = 0

    while not manager.is_interview_complete() and question_count < max_questions:
        question = manager.get_next_question()

        if not question:
            print(f"\n✓ Interview complete!")
            break

        question_count += 1
        print(f"\n❓ Question {question_count}:")
        print(f"   Type: {question.question_type}")
        print(f"   Text: {question.question_text}")
        print(f"   Items: {len(question.items)}")

        if question.items:
            item = question.items[0]
            print(f"   → Item: {item.get('name')}")

            # Simulate answering "no"
            manager.answer_question(item.get("id"), "absent")
            print(f"   → Response: absent")

    if question_count >= max_questions:
        print(f"\n⚠️  Stopped after {max_questions} questions (demo limit)")

    # Show progress
    print("\n" + "=" * 70)
    print("PROGRESS SUMMARY")
    print("=" * 70)

    progress = manager.get_progress()
    print(f"Stage: {progress['stage']}")
    print(f"Questions asked: {progress['questions_asked']}")
    print(f"Evidence collected: {progress['evidence_count']}")
    print(f"Conditions found: {progress['conditions_count']}")
    print(f"Complete: {progress['is_complete']}")

    # Show state summary
    print("\n" + "=" * 70)
    print("STATE SUMMARY")
    print("=" * 70)
    print(manager.get_state_summary())

    # Get final results (if complete)
    if manager.is_interview_complete():
        print("\n" + "=" * 70)
        print("FINAL RESULTS")
        print("=" * 70)

        results = manager.get_final_results()
        print(f"✓ Interview ID: {results['interview_id']}")
        print(f"✓ Questions asked: {results['questions_asked']}")
        print(f"✓ Top conditions:")
        for i, cond in enumerate(results["conditions"][:5], 1):
            prob = cond.get("probability", 0) * 100
            print(f"  {i}. {cond.get('common_name')} ({prob:.1f}%)")

    print("\n" + "=" * 70)
    print("✅ Interview Manager Test Complete!")
    print("=" * 70)


def test_manager_state():
    """Test state management features"""

    print("\n" + "=" * 70)
    print("Testing State Management")
    print("=" * 70)

    client = InfermedicaClient()
    manager = InterviewManager(client, age=30, sex="female")

    # Test initial state
    print("\n1. Initial State")
    print(f"   Stage: {manager.state.stage.value}")
    print(f"   Complete: {manager.state.is_complete}")
    print(f"   Evidence: {len(manager.state.evidence)} items")

    # Start interview
    symptoms = client.parse_symptoms("headache", 30, "female")
    manager.start_interview(symptoms)

    print("\n2. After Starting")
    print(f"   Stage: {manager.state.stage.value}")
    print(f"   Evidence: {len(manager.state.evidence)} items")

    # Progress
    progress = manager.get_progress()
    print("\n3. Progress Info")
    for key, value in progress.items():
        print(f"   {key}: {value}")

    print("\n✅ State management working!")


if __name__ == "__main__":
    print("\n🧪 Running Interview Manager Tests\n")

    try:
        # Test state management
        test_manager_state()

        # Test complete flow
        test_interview_manager_flow()

        print("\n🎉 All tests passed!\n")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
