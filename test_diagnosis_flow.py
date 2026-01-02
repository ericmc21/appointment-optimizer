"""
Test script for full Infermedica diagnosis flow
Tests all new methods: risk factors, related symptoms, red flags, diagnosis loop
"""

import sys

sys.path.append("/home/claude")

from infermedica_client import InfermedicaClient
import uuid


def test_full_diagnosis_flow():
    """Test the complete diagnosis flow"""

    print("=" * 60)
    print("Testing Full Infermedica Diagnosis Flow")
    print("=" * 60)

    # Initialize client
    client = InfermedicaClient()

    # Generate interview ID for tracking
    interview_id = f"test_{uuid.uuid4().hex[:12]}"
    print(f"\n📋 Interview ID: {interview_id}")

    # Patient info
    age = 35
    sex = "male"
    symptom_text = "I have chest pain and shortness of breath"

    print(f"\n👤 Patient: {age} year old {sex}")
    print(f'💬 Chief complaint: "{symptom_text}"')

    # Step 1: Parse initial symptoms
    print("\n" + "=" * 60)
    print("STEP 1: Parse Initial Symptoms (/parse)")
    print("=" * 60)

    parsed_symptoms = client.parse_symptoms(symptom_text, age, sex)
    print(f"✓ Parsed {len(parsed_symptoms)} symptoms:")
    for symptom in parsed_symptoms:
        print(f"  - {symptom.name} (ID: {symptom.id})")

    # Build evidence list
    evidence = [
        {"id": symptom.id, "choice_id": symptom.choice_id, "source": "initial"}
        for symptom in parsed_symptoms
    ]

    # Step 2: Get demographic risk factors
    print("\n" + "=" * 60)
    print("STEP 2: Check Demographic Risk Factors (/suggest risk_factors)")
    print("=" * 60)

    risk_factors = client.suggest_risk_factors(age, sex, interview_id)
    print(f"✓ Found {len(risk_factors)} risk factors to check:")
    for i, rf in enumerate(risk_factors[:5], 1):  # Show first 5
        print(f"  {i}. {rf.get('name')} (ID: {rf.get('id')})")

    # For demo, assume user answers "no" to all risk factors
    # In real app, you'd ask user

    # Step 3: Get related symptoms
    print("\n" + "=" * 60)
    print("STEP 3: Suggest Related Symptoms (/suggest symptoms)")
    print("=" * 60)

    related = client.suggest_related_symptoms(evidence, age, sex, interview_id)
    print(f"✓ Found {len(related)} related symptoms:")
    for i, sym in enumerate(related[:5], 1):  # Show first 5
        print(f"  {i}. {sym.get('name')} (ID: {sym.get('id')})")

    # Step 4: Check red flags
    print("\n" + "=" * 60)
    print("STEP 4: Check Red Flags (/suggest red_flags)")
    print("=" * 60)

    red_flags = client.suggest_red_flags(evidence, age, sex, interview_id)
    print(f"✓ Found {len(red_flags)} red flags to check:")
    for i, rf in enumerate(red_flags, 1):
        print(f"  {i}. {rf.get('name')} (ID: {rf.get('id')}) ⚠️")

    # Step 5: Diagnosis interview loop
    print("\n" + "=" * 60)
    print("STEP 5: Diagnosis Interview Loop (/diagnosis)")
    print("=" * 60)

    max_questions = 5  # Limit for demo
    question_count = 0

    while question_count < max_questions:
        result = client.diagnosis(evidence, age, sex, interview_id)

        if result.should_stop:
            print(f"\n✓ Interview complete (should_stop=True)")
            print(f"\n📊 Final Conditions ({len(result.conditions)}):")
            for i, condition in enumerate(result.conditions[:5], 1):
                prob = result.conditions[i - 1].get("probability", 0) * 100
                print(f"  {i}. {condition.get('common_name')} ({prob:.1f}%)")
            break

        if result.question:
            question_count += 1
            q = result.question

            print(f"\n❓ Question {question_count}:")
            print(f"   Type: {q.question_type}")
            print(f"   Text: {q.question_text}")
            print(f"   Options: {len(q.items)}")

            # For demo, simulate user answering "no" to first item
            if q.items:
                first_item = q.items[0]
                print(f"   → Simulating 'no' to: {first_item.get('name')}")

                # Add response to evidence
                evidence.append(
                    {
                        "id": first_item.get("id"),
                        "choice_id": "absent",
                        "source": "predefined",
                    }
                )
        else:
            print("⚠️ No question returned but should_stop is False")
            break

    if question_count >= max_questions:
        print(f"\n⚠️ Stopped after {max_questions} questions (demo limit)")

    # Step 6: Final triage
    print("\n" + "=" * 60)
    print("STEP 6: Final Triage (/triage)")
    print("=" * 60)

    triage = client.run_triage(parsed_symptoms, age, sex)
    print(f"✓ Triage Level: {triage.triage_level.value}")
    print(f"✓ Recommended Specialist: {triage.recommended_specialist_name}")
    print(f"✓ Channel: {triage.recommended_channel}")
    print(f"✓ Root Cause: {triage.root_cause}")

    print("\n" + "=" * 60)
    print("✅ Full Flow Test Complete!")
    print("=" * 60)


def test_individual_methods():
    """Test each new method individually"""

    print("\n" + "=" * 60)
    print("Testing Individual Methods")
    print("=" * 60)

    client = InfermedicaClient()
    age = 30
    sex = "female"

    # Test risk factors
    print("\n1. Testing suggest_risk_factors()...")
    risk_factors = client.suggest_risk_factors(age, sex)
    print(f"   ✓ Returned {len(risk_factors)} risk factors")

    # Test related symptoms (need some evidence first)
    print("\n2. Testing suggest_related_symptoms()...")
    evidence = [{"id": "s_99", "choice_id": "present"}]  # Fever
    related = client.suggest_related_symptoms(evidence, age, sex)
    print(f"   ✓ Returned {len(related)} related symptoms")

    # Test red flags
    print("\n3. Testing suggest_red_flags()...")
    red_flags = client.suggest_red_flags(evidence, age, sex)
    print(f"   ✓ Returned {len(red_flags)} red flags")

    # Test diagnosis
    print("\n4. Testing diagnosis()...")
    result = client.diagnosis(evidence, age, sex)
    print(f"   ✓ should_stop: {result.should_stop}")
    if result.question:
        print(f"   ✓ Question type: {result.question.question_type}")
        print(f"   ✓ Question text: {result.question.question_text[:50]}...")
    print(f"   ✓ Conditions: {len(result.conditions)}")

    print("\n✅ All individual methods working!")


if __name__ == "__main__":
    print("\n🧪 Running Infermedica V2 Tests\n")

    try:
        # Test individual methods first
        test_individual_methods()

        # Then test full flow
        test_full_diagnosis_flow()

        print("\n🎉 All tests passed!\n")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
