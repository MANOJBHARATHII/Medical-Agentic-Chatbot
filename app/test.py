import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import agent
from app.config import settings


def groq_response(content):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )


class AgentWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.groq_client = SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=Mock()))
        )
        self.client_patch = patch(
            "app.agent.client",
            return_value=(None, self.groq_client),
        )
        self.search_patch = patch("app.agent.search_kb", return_value=[])
        self.client_patch.start()
        self.search_kb = self.search_patch.start()
        self.addCleanup(self.client_patch.stop)
        self.addCleanup(self.search_patch.stop)

    def test_retrieves_reference_before_answering_when_planner_requests_it(self):
        self.groq_client.chat.completions.create.side_effect = [
            groq_response(json.dumps({
                "needs_retrieval": True,
                "search_query": "headache causes",
            })),
            groq_response("Common causes are listed in the reference (page 4)."),
        ]
        self.search_kb.return_value = [
            {"page": 4, "text": "Reference about headaches.", "source": "test"}
        ]

        answer = agent.respond(
            [{"role": "user", "content": "What causes headaches?"}],
            use_knowledge=True,
        )

        self.assertIn("page 4", answer)
        self.search_kb.assert_called_once_with("headache causes")
        self.assertEqual(self.groq_client.chat.completions.create.call_count, 2)
        final_messages = self.groq_client.chat.completions.create.call_args_list[1].kwargs["messages"]
        self.assertIn("Reference about headaches.", final_messages[0]["content"])

    def test_skips_planner_and_retrieval_when_knowledge_is_disabled(self):
        self.groq_client.chat.completions.create.return_value = groq_response("Hello.")

        answer = agent.respond(
            [{"role": "user", "content": "Hello"}],
            use_knowledge=False,
        )

        self.assertEqual(answer, "Hello.")
        self.search_kb.assert_not_called()
        self.groq_client.chat.completions.create.assert_called_once()

    def test_skips_retrieval_when_planner_says_it_is_not_needed(self):
        self.groq_client.chat.completions.create.side_effect = [
            groq_response(json.dumps({
                "needs_retrieval": False,
                "search_query": "",
            })),
            groq_response("Hello."),
        ]

        answer = agent.respond([{"role": "user", "content": "Hello"}])

        self.assertEqual(answer, "Hello.")
        self.search_kb.assert_not_called()
        self.assertEqual(self.groq_client.chat.completions.create.call_count, 2)

    def test_image_request_uses_vision_model_and_image_content(self):
        self.groq_client.chat.completions.create.return_value = groq_response(
            "I cannot diagnose an image."
        )

        agent.respond(
            [{"role": "user", "content": "What is shown here?"}],
            image_url="data:image/png;base64,AAAA",
            use_knowledge=False,
        )

        request = self.groq_client.chat.completions.create.call_args.kwargs
        self.assertEqual(request["model"], settings.vision_model)
        user_content = request["messages"][-1]["content"]
        self.assertEqual(user_content[0]["type"], "text")
        self.assertEqual(user_content[1]["type"], "image_url")

    def test_requires_a_user_message(self):
        with self.assertRaisesRegex(ValueError, "At least one user message"):
            agent.respond([{"role": "assistant", "content": "How can I help?"}])

    def test_rejects_malformed_retrieval_plan(self):
        self.groq_client.chat.completions.create.return_value = groq_response(
            '{"needs_retrieval": "yes", "search_query": "test"}'
        )

        with self.assertRaisesRegex(RuntimeError, "invalid shape"):
            agent.respond([{"role": "user", "content": "A health question"}])


if __name__ == "__main__":
    unittest.main(verbosity=2)
