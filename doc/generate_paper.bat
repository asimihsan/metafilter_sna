pandoc paper.md -o paper.tex
pandoc -H margins.sty paper.tex -o paper.pdf
rem "c:\Program Files (x86)\SumatraPDF\SumatraPDF.exe" paper.pdf
