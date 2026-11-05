"""Generate a small set of sample job description + resume files (DOCX and PDF)
so the parsing + keyword-ranking pipeline can be demonstrated end-to-end
without a real dataset. Run once: python scripts/generate_sample_data.py
"""
from pathlib import Path

from docx import Document
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "sample_data"
RESUME_DIR = OUT_DIR / "resumes"

JOB_DESCRIPTION = """Backend Developer

We are hiring a Backend Developer to build and maintain our REST APIs.

Required skills:
- Strong experience with Python and FastAPI or Django
- Experience with PostgreSQL and database design
- Familiarity with REST API development and authentication
- Experience with Git and collaborative development workflows
- Bachelor's degree in Computer Science or related field
- 2+ years of professional experience
"""

RESUMES = {
    "Candidate_StrongMatch": """Ananya Rao
Backend Engineer

Summary
Backend engineer with 3 years of experience building REST APIs using Python and FastAPI.
Strong background in PostgreSQL database design and query optimization.

Skills
Python, FastAPI, Django, PostgreSQL, REST API development, Git, Docker

Experience
Backend Developer, TechWave Pvt Ltd (2022 - Present)
- Built and maintained REST APIs serving production traffic using FastAPI
- Designed PostgreSQL schemas and optimized slow queries
- Collaborated with a team of 5 engineers using Git-based workflows

Education
B.E. Computer Science, 2021
""",
    "Candidate_PartialMatch": """Rohan Mehta
Software Developer

Summary
Software developer with experience mainly in frontend development, with some backend exposure.

Skills
JavaScript, React, Node.js, MongoDB, basic Python scripting

Experience
Frontend Developer, PixelCraft Studios (2021 - Present)
- Built React-based dashboards and internal tools
- Wrote small Node.js services for internal automation
- Occasionally used Python for data cleanup scripts

Education
B.E. Information Technology, 2020
""",
    "Candidate_WeakMatch": """Simran Kaur
Marketing Analyst

Summary
Marketing analyst with a background in digital campaigns and data reporting.

Skills
Excel, Google Analytics, SQL (basic), content strategy, campaign management

Experience
Marketing Analyst, BrightAds Media (2022 - Present)
- Analyzed campaign performance using SQL and spreadsheets
- Prepared marketing reports for stakeholders

Education
BBA Marketing, 2021
""",
}


def write_docx(path: Path, text: str) -> None:
    doc = Document()
    for line in text.strip().split("\n"):
        doc.add_paragraph(line)
    doc.save(path)


def write_pdf(path: Path, text: str) -> None:
    c = canvas.Canvas(str(path), pagesize=LETTER)
    width, height = LETTER
    y = height - 50
    for line in text.strip().split("\n"):
        c.drawString(50, y, line[:100])
        y -= 16
        if y < 50:
            c.showPage()
            y = height - 50
    c.save()


def main() -> None:
    RESUME_DIR.mkdir(parents=True, exist_ok=True)

    write_docx(OUT_DIR / "job_description.docx", JOB_DESCRIPTION)

    names = list(RESUMES.items())
    # Mix formats: first as DOCX, second as PDF, third as DOCX, to exercise both parsers.
    write_docx(RESUME_DIR / f"{names[0][0]}.docx", names[0][1])
    write_pdf(RESUME_DIR / f"{names[1][0]}.pdf", names[1][1])
    write_docx(RESUME_DIR / f"{names[2][0]}.docx", names[2][1])

    print(f"Wrote job description to {OUT_DIR / 'job_description.docx'}")
    print(f"Wrote {len(names)} sample resumes to {RESUME_DIR}")


if __name__ == "__main__":
    main()
