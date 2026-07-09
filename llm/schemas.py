from dataclasses import dataclass


@dataclass(frozen=True)
class PosterCopy:
    headline: str
    subtitle: str

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            raise ValueError("poster_copy must be an object")
        headline = data.get("headline")
        subtitle = data.get("subtitle")
        if not isinstance(headline, str) or not headline.strip():
            raise ValueError("poster_copy.headline is required")
        if not isinstance(subtitle, str) or not subtitle.strip():
            raise ValueError("poster_copy.subtitle is required")
        return cls(headline=headline, subtitle=subtitle)

    def to_dict(self):
        return {
            "headline": self.headline,
            "subtitle": self.subtitle,
        }


@dataclass(frozen=True)
class PdfSection:
    title: str
    body: str

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            raise ValueError("pdf_outline entries must be objects")
        title = data.get("title")
        body = data.get("body")
        if not isinstance(title, str) or not title.strip():
            raise ValueError("pdf_outline.title is required")
        if not isinstance(body, str) or not body.strip():
            raise ValueError("pdf_outline.body is required")
        return cls(title=title, body=body)

    def to_dict(self):
        return {
            "title": self.title,
            "body": self.body,
        }


@dataclass(frozen=True)
class ProductionPlan:
    project_title: str
    concept: str
    image_prompt: str
    negative_prompt: str
    poster_copy: PosterCopy
    pdf_outline: tuple[PdfSection, ...]

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            raise ValueError("LLM response must be an object")

        required_strings = [
            "project_title",
            "concept",
            "image_prompt",
            "negative_prompt",
        ]
        values = {}
        for key in required_strings:
            value = data.get(key)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{key} is required")
            values[key] = value

        outline = data.get("pdf_outline")
        if not isinstance(outline, list) or not outline:
            raise ValueError("pdf_outline must be a non-empty array")

        return cls(
            project_title=values["project_title"],
            concept=values["concept"],
            image_prompt=values["image_prompt"],
            negative_prompt=values["negative_prompt"],
            poster_copy=PosterCopy.from_dict(data.get("poster_copy")),
            pdf_outline=tuple(PdfSection.from_dict(item) for item in outline),
        )

    def to_dict(self):
        return {
            "project_title": self.project_title,
            "concept": self.concept,
            "image_prompt": self.image_prompt,
            "negative_prompt": self.negative_prompt,
            "poster_copy": self.poster_copy.to_dict(),
            "pdf_outline": [section.to_dict() for section in self.pdf_outline],
        }
