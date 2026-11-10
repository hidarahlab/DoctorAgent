import pymupdf
from ingest_saya import PDF_PATH, _page_blocks

page = pymupdf.open(PDF_PATH)[19]
for kind, lines in _page_blocks(page):
    print(f"{kind:<16} | {lines[0][:45]}")

#output langkah 7:
# keyterms_header  | KEY TERMS
# keyterm          | Hernia—Movement of a structure into a place i
# keyterm          | Umbilical—Referring to the opening in the
# keyterm          | Viscera—Any of the body’s organs located in t
# section          | Description
# body             | Many unexpected and fascinating events occur 
# section          | Causes and symptoms
# body             | There are many causes for birth defects that 
# section          | Diagnosis
# body             | At birth, the problem is obvious, because the
# section          | Treatment
# body             | Abdominal wall defects are effectively treate
# section          | Prognosis
# body             | If there are no other defects, the prognosis 
# body             | 10% of those with more severe or additional a
# section          | Prevention
# body             | Some, but by no means all, birth defects are 
# resources        | Resources
# small            | PERIODICALS
# body             | J. Ricker Polsdorfer, MD
# crossref         | Abnormal heart rhythms see Arrhythmias
# entry            | Abortion, partial birth
# section          | Definition
# body             | Partial birth abortion is a method of late-te
# section          | Purpose
# body             | Partial birth abortion, or D&X, is performed