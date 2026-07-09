import re

from llm.schemas import ProductionPlan


def title_from_topic(topic):
    words = re.findall(r"[A-Za-z0-9]+", topic)
    if not words:
        return "Untitled Pilot"
    return " ".join(word.capitalize() for word in words)


def build_initial_plan(topic):
    title = title_from_topic(topic)
    return ProductionPlan.from_dict(
        {
            "project_title": title,
            "concept": f"A cinematic poster and short PDF concept for: {topic}",
            "image_prompt": (
                f"{topic}, cinematic composition, rich lighting, detailed environment, "
                "poster-ready visual direction"
            ),
            "negative_prompt": "blurry, low quality, distorted anatomy, unreadable text",
            "poster_copy": {
                "headline": title,
                "subtitle": "A visual pilot generated from a single idea",
            },
            "pdf_outline": [
                {
                    "title": "Concept",
                    "body": f"The production direction explores {topic} as a concise visual pilot.",
                },
                {
                    "title": "Visual Direction",
                    "body": "The first pass favors mood, composition, and iteration speed over final polish.",
                },
            ],
        }
    )


def build_revised_plan(topic, feedback, previous_plan):
    data = previous_plan.to_dict()
    data["concept"] = f"{previous_plan.concept}\n\nRevision note: {feedback}"
    data["image_prompt"] = f"{previous_plan.image_prompt}. Revision: {feedback}"
    data["pdf_outline"] = list(data["pdf_outline"]) + [
        {
            "title": "Revision",
            "body": feedback,
        }
    ]
    return ProductionPlan.from_dict(data)
