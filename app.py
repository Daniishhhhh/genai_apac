import os, sys, asyncio
from dotenv import load_dotenv
load_dotenv()

from google.adk.agents import SequentialAgent
from google.adk.runners import InMemoryRunner
from google.genai.types import Content, Part

from agents.label_extractor    import LabelExtractorAgent
from agents.regulatory_auditor import RegulatoryAuditorAgent
from agents.sanity_agent       import SanityAgent
from agents.user_advisor       import UserAdvisorAgent
# Phase 3 agents — uncomment as you build each one:
from agents.wellness_advisor import WellnessAdvisorAgent
from agents.education_agent  import EducationAgent

NutriGuardOrchestrator = SequentialAgent(
    name="NutriGuardOrchestrator",
    description="FSSAI audit: Extract → Audit → Sanity → Advise",
    sub_agents=[
        LabelExtractorAgent,
        RegulatoryAuditorAgent,
        SanityAgent,
        UserAdvisorAgent,
        WellnessAdvisorAgent,   # uncomment after Step 4
        EducationAgent,         # uncomment after Step 5
    ]
)

APP_NAME   = "nutriguard"
USER_ID    = "local-user"
SESSION_ID = "test-session-001"

async def run_audit(image_path: str):
    runner = InMemoryRunner(
        agent=NutriGuardOrchestrator,
        app_name=APP_NAME,
    )

    await runner.session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )

    message = Content(
        role="user",
        parts=[Part(text=f"Audit this food label image: {image_path}")]
    )

    print(f"\n🔍 Auditing: {image_path}\n{'─'*45}")

    final_response = None
    for event in runner.run(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=message,
    ):
        if hasattr(event, 'author') and event.author:
            print(f"\n[{event.author}]")
        if hasattr(event, 'content') and event.content:
            for part in event.content.parts:
                if hasattr(part, 'text') and part.text:
                    print(part.text)
                    final_response = part.text

    print(f"\n{'─'*45}")
    print("✅ Audit complete.")
    return final_response


if __name__ == "__main__":
    image_path = sys.argv[1] if len(sys.argv) > 1 else "data/test_label.jpg"

    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        print("   Add a food label photo at data/test_label.jpg and retry.")
        sys.exit(1)

    asyncio.run(run_audit(image_path))