from ingest_saya import _join_lines

contoh = [
    "dilation and evacuation (D & E), suction dilation, vacu-",
    "um curettage, or suction curettage.",
    "The Epstein-",
    "Barr virus causes mononucleosis.",
]

print(_join_lines(contoh))

#output langkah 8:
# dilation and evacuation (D & E), suction dilation, vacuum curettage, or suction curettage. The Epstein- Barr virus causes mononucleosis.