from ingest_saya import parse_sections

sections, aliases = parse_sections()
print("jumlah section:", len(sections))
for s in sections:
    if s.entry == "Abdominal wall defects":
        teks = " ".join(s.lines)
        print(f"- {s.section:<20} hlm PDF {s.pdf_page:<3} | ...{teks[-70:]}")

#output langkah 9
# jumlah section: 2007
# - Definition           hlm PDF 19  | ...(congenital) defects that allow the stomach or intestines to protrude.
# - Description          hlm PDF 20  | ...ls or stomach to remain outside or squeeze through the abdominal wall.
# - Causes and symptoms  hlm PDF 20  | ...to indicate that the defects are present in the fetus are nondescript.
# - Diagnosis            hlm PDF 20  | ...defect to look for others, because birth defects are usually multiple.
# - Treatment            hlm PDF 20  | ...y be difficult to fit all the viscera into the small abdominal cavity.
# - Prognosis            hlm PDF 20  | ...he stretched abdomen can compromise the function of the organs inside.
# - Prevention           hlm PDF 20  | ...o— and other elements of a healthy lifestyle. J. Ricker Polsdorfer, MD

#output langkah 10
# jumlah section: 2272
# - Definition           hlm PDF 19  | ...(congenital) defects that allow the stomach or intestines to protrude.
# - Key terms            hlm PDF 20  | ...ter. Viscera—Any of the body’s organs located in the chest or abdomen.
# - Description          hlm PDF 20  | ...ls or stomach to remain outside or squeeze through the abdominal wall.
# - Causes and symptoms  hlm PDF 20  | ...to indicate that the defects are present in the fetus are nondescript.
# - Diagnosis            hlm PDF 20  | ...defect to look for others, because birth defects are usually multiple.
# - Treatment            hlm PDF 20  | ...y be difficult to fit all the viscera into the small abdominal cavity.
# - Prognosis            hlm PDF 20  | ...he stretched abdomen can compromise the function of the organs inside.
# - Prevention           hlm PDF 20  | ...emicals—especially tobacco— and other elements of a healthy lifestyle.