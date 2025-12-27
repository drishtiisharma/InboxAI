#============================IMAGE DESCRIPTION============================
import subprocess

def describe_image(image_path):
    prompt = (
        "Describe the image clearly in one or two sentences. "
        "Mention visible objects and what seems to be happening. "
        "If it looks like an illustration or artwork, say so."
    )

    try:
        with open(image_path, "rb") as img:
            result = subprocess.run(
                ["ollama", "run", "moondream", prompt],
                input=img.read(),
                capture_output=True
            )

        return result.stdout.decode("utf-8", errors="ignore").strip()

    except Exception as e:
        return f"Could not describe image: {e}"

def is_meaningful_text(text):
    text = text.strip()
    if len(text) < 30:
        return False
    if text.count("\n") > len(text) * 0.3:
        return False
    return True