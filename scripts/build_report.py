"""Render REPORT.md to REPORT.pdf (print layout) and report the page count.
Uses markdown-it-py for HTML and headless Chrome for PDF.
Usage: python scripts/build_report.py [chrome_path]"""
import os
import subprocess
import sys

from markdown_it import MarkdownIt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = sys.argv[1] if len(sys.argv) > 1 else "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CSS = """
@page { size: Letter; margin: 2cm 2cm; }
body { font-family: 'Times New Roman', Times, serif; font-size: 11pt; line-height: 1.25; }
h1 { font-size: 15pt; margin: 0 0 4pt; } h2 { font-size: 12.5pt; margin: 10pt 0 3pt; }
h3 { font-size: 11pt; margin: 8pt 0 2pt; } p, li { margin: 2pt 0; text-align: justify; }
ul, ol { margin: 2pt 0; padding-left: 16pt; }
table { border-collapse: collapse; width: 100%; font-size: 8.5pt; margin: 4pt 0; page-break-inside: auto; }
th, td { border: 0.5pt solid #777; padding: 1.5pt 3pt; vertical-align: top; text-align: left; }
th { background: #eee; } code { font-family: Menlo, Consolas, monospace; font-size: 8pt; }
pre { font-size: 8pt; margin: 3pt 0; } blockquote { margin: 3pt 0; padding-left: 8pt; border-left: 2pt solid #999; }
"""
md = MarkdownIt("commonmark").enable("table")
body = md.render(open(os.path.join(ROOT, "REPORT.md")).read())
html_path = os.path.join(ROOT, "results", "REPORT.html")
with open(html_path, "w") as f:
    f.write(f"<!doctype html><meta charset='utf-8'><title>ECE 322 Report</title><style>{CSS}</style>{body}")
pdf = os.path.join(ROOT, "REPORT.pdf")
if os.path.exists(pdf):
    os.remove(pdf)
import pathlib
import tempfile

r = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    f"--user-data-dir={tempfile.mkdtemp()}", f"--print-to-pdf={pdf}",
                    pathlib.Path(html_path).as_uri()], capture_output=True, text=True)
if not os.path.exists(pdf):
    sys.exit(r.stderr[-2000:])
try:
    import pypdf
    print("pages:", len(pypdf.PdfReader(pdf).pages))
except ImportError:
    print("written", pdf, "(install pypdf to count pages)")
