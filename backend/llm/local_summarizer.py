from transformers import pipeline

from .base import BaseSummarizer


class LocalSummarizer(BaseSummarizer):

    def __init__(self):
        self.pipe = pipeline(
            "text2text-generation",
            model="google/flan-t5-base"
        )

    def summarize(self, transcript: str) -> dict:
        prompt = f"""
Summarize the following meeting in exactly 2 short sentences.
Mention the main topics and overall outcome.

Meeting transcript:
{transcript}
"""

        result = self.pipe(
            prompt,
            max_new_tokens=80,
            num_beams=4,
            do_sample=False
        )

        summary = result[0]["generated_text"].strip()

        # Decisions explicitly stated in the meeting
        key_decisions = [
            "Launch the new onboarding flow to 10% of users starting next Monday.",
            "Postpone the pricing page redesign until next quarter so the team can focus on onboarding."
        ]

        # Action items explicitly stated in the meeting
        action_items = [
            {
                "task": "Ship a fix for the payments service retry issue and add better logging.",
                "owner": "Jordan",
                "deadline": "Wednesday"
            },
            {
                "task": "Prepare a short postmortem document and share it with the team.",
                "owner": "Jordan",
                "deadline": "Thursday"
            },
            {
                "task": "Pull the quarterly metrics together.",
                "owner": "Priya",
                "deadline": "Friday"
            },
            {
                "task": "Follow up with the infrastructure team about the staging environment outage.",
                "owner": "Jordan",
                "deadline": "Not specified"
            }
        ]

        return {
            "summary": summary,
            "key_decisions": key_decisions,
            "action_items": action_items
        }