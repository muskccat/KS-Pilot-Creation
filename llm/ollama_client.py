from llm.prompt_engine import build_initial_plan, build_revised_plan


class MockOllamaClient:
    def create_plan(self, topic):
        return build_initial_plan(topic)

    def revise_plan(self, topic, feedback, previous_plan):
        return build_revised_plan(topic, feedback, previous_plan)
