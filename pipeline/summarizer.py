import re
from transformers import pipeline


def clean_text(text):
    text = str(text)
    text = re.sub(r"\s+", " ", text)
    text = text.strip()
    return text


def regulation_to_text(regulation):
    text = ""

    if "title" in regulation:
        text += regulation["title"] + " "

    if "agency" in regulation:
        text += regulation["agency"] + " "

    if "permit" in regulation:
        text += regulation["permit"] + " "

    if "requirements" in regulation:
        if type(regulation["requirements"]) == list:
            text += " ".join(regulation["requirements"]) + " "
        else:
            text += regulation["requirements"] + " "

    if "text" in regulation:
        text += regulation["text"] + " "

    if "content" in regulation:
        text += regulation["content"] + " "

    return clean_text(text)


def split_long_text(text, max_words=450):
    words = text.split()
    chunks = []

    for i in range(0, len(words), max_words):
        chunk = words[i:i + max_words]
        chunks.append(" ".join(chunk))

    return chunks


def summarize_text(text):
    text = clean_text(text)

    if len(text.split()) < 40:
        return text

    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

    chunks = split_long_text(text)
    summaries = []

    for chunk in chunks:
        if len(chunk.split()) < 40:
            summaries.append(chunk)
        else:
            summary = summarizer(
                chunk,
                max_length=130,
                min_length=40,
                do_sample=False
            )
            summaries.append(summary[0]["summary_text"])

    final_summary = " ".join(summaries)

    return final_summary


def summarize_regulations(regulations):
    full_text = ""

    for regulation in regulations:
        full_text += regulation_to_text(regulation) + " "

    summary = summarize_text(full_text)

    return summary


def create_checklist(regulations):
    checklist = []

    keywords = [
        "must",
        "required",
        "require",
        "permit",
        "license",
        "application",
        "inspection",
        "fee",
        "renew",
        "approval",
        "certificate",
        "department"
    ]

    for regulation in regulations:
        text = regulation_to_text(regulation)
        sentences = re.split(r"(?<=[.!?])\s+", text)

        for sentence in sentences:
            sentence = clean_text(sentence)
            sentence_lower = sentence.lower()

            for keyword in keywords:
                if keyword in sentence_lower and len(sentence.split()) > 4:
                    item = "Review requirement: " + sentence

                    if item not in checklist:
                        checklist.append(item)

                    break

    return checklist[:8]


def generate_output(regulations):
    summary = summarize_regulations(regulations)
    checklist = create_checklist(regulations)

    sources = []

    for regulation in regulations:
        source = {
            "title": regulation.get("title", "Untitled regulation"),
            "agency": regulation.get("agency", "Not specified"),
            "score": regulation.get("score", None)
        }

        sources.append(source)

    output = {
        "summary": summary,
        "checklist": checklist,
        "sources": sources
    }

    return output


if __name__ == "__main__":
    sample_regulations = [
        {
            "title": "Restaurant Health Permit",
            "agency": "Los Angeles County Department of Public Health",
            "text": """
            A restaurant must obtain a public health permit before operating.
            The owner is required to submit an application, pay the required fee,
            and schedule an inspection before opening to the public.
            The permit must be renewed annually.
            """
        }
    ]

    output = generate_output(sample_regulations)

    print("SUMMARY:")
    print(output["summary"])

    print("\nCHECKLIST:")
    for item in output["checklist"]:
        print("-", item)

    print("\nSOURCES:")
    for source in output["sources"]:
        print(source)
