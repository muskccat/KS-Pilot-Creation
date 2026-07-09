import json


_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR"
    b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
    b"\x00\x00\x00\x0cIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfeA\xad\xa2\x9b"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


def generate_base_image(plan, run_dir):
    request_path = run_dir / "comfy_request.json"
    image_path = run_dir / "base_image.png"
    request_path.write_text(
        json.dumps(
            {
                "mode": "mock",
                "prompt": plan.image_prompt,
                "negative_prompt": plan.negative_prompt,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    image_path.write_bytes(_PNG_BYTES)
    return image_path
