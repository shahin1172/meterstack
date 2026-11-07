import os
from fpdf import FPDF

# ---------- configuration ----------
PROJECT_ROOT = os.getcwd()
OUTPUT_PDF = os.path.join(PROJECT_ROOT, "meterstack_full_code.pdf")
EXCLUDE_DIRS = {
    '.git', '__pycache__', 'venv', 'env', '.idea', 'migrations', 'static',
    'node_modules', 'tests/__pycache__', 'billing/migrations/__pycache__',
    'usage/migrations/__pycache__', 'users/migrations/__pycache__',
    'tenants/migrations/__pycache__', 'meterstack2/__pycache__',
}
INCLUDE_EXTENSIONS = {
    '.py', '.txt', '.md', '.yml', '.yaml', '.sh', '.cfg', '.ini',
    '.env', '.env.example', '.sql', '.json', '.html', '.css', '.js',
    'Dockerfile', '01-docker-compose.yml'
}
# -----------------------------------

def safe_encode(text):
    """Replace characters that can't be encoded in latin-1 with '?'."""
    return text.encode('latin-1', errors='replace').decode('latin-1')

pdf = FPDF()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.add_page()
pdf.set_font("Courier", size=8)

for root, dirs, files in os.walk(PROJECT_ROOT):
    dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith('.')]

    for file in sorted(files):
        ext = os.path.splitext(file)[1].lower()
        name = file.lower()
        if ext not in INCLUDE_EXTENSIONS and name not in INCLUDE_EXTENSIONS:
            continue

        filepath = os.path.join(root, file)
        relpath = os.path.relpath(filepath, PROJECT_ROOT)

        pdf.set_font("Courier", 'B', 10)
        pdf.cell(0, 10, safe_encode(f"File: {relpath}"), ln=True)
        pdf.set_font("Courier", size=8)

        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    cleaned = line.rstrip('\n').expandtabs(4)
                    # replace tabs with spaces and ensure latin-1 compatibility
                    pdf.cell(0, 4, safe_encode(cleaned), ln=True)
        except Exception as e:
            pdf.cell(0, 4, safe_encode(f"Error reading file: {e}"), ln=True)

        pdf.add_page()

pdf.output(OUTPUT_PDF)
print(f"PDF generated: {OUTPUT_PDF}")