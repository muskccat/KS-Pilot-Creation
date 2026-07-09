import shutil


def generate_poster_image(plan, base_image, run_dir):
    poster_path = run_dir / "poster_image.png"
    shutil.copyfile(base_image, poster_path)
    (run_dir / "poster_copy.txt").write_text(
        f"{plan.poster_copy.headline}\n{plan.poster_copy.subtitle}\n",
        encoding="utf-8",
    )
    return poster_path
