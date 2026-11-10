import pymupdf
from ingest_saya import PDF_PATH, _block_kind

page = pymupdf.open(PDF_PATH)[19]
for block in page.get_text("dict")["blocks"]:
    if "lines" not in block:
        continue
    spans = [s for l in block["lines"] for s in l["spans"] if s["text"].strip()]
    if spans:
        print(f"{_block_kind(spans):<16} | {spans[0]['text'][:45]}")


#output langkah 6:
# section          | Description
# body             | Many unexpected and fascinating events occur 
# section          | Causes and symptoms
# body             | There are many causes for 
# section          | Diagnosis
# body             | At birth, the problem is obvious, because the
# section          | Treatment
# body             | Abdominal wall defects are effectively treate
# section          | Prognosis
# body             | If there are no other defects, the prognosis 
# keyterms_header  | KEY TERMS
# keyterm          | Hernia
# keyterm          | Umbilical
# keyterm          | Viscera
# body             | 10% of those with more severe or additional a
# section          | Prevention
# body             | Some, but by no means all, birth defects are 
# resources        | Resources
# small            | PERIODICALS
# body             | J. Ricker Polsdorfer, MD
# crossref         | Abnormal heart rhythms 
# entry            | Abortion, partial birth
# section          | Definition
# body             | Partial birth abortion is a method of late-te
# section          | Purpose
# body             | Partial birth abortion, or D&X, is performed 
# small            | GALE ENCYCLOPEDIA OF MEDICINE 2
# keyterm          | Abortion, partial birth