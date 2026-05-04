import os
from pdflatex import PDFLaTeX

def compile_tex(filename):
    print(f"Compiling {filename}...")
    try:
        pdfl = PDFLaTeX.from_texfile(filename)
        pdf, log, completed_process = pdfl.create_pdf(keep_pdf_file=True, keep_log_file=True)
        print(f"Successfully compiled {filename}")
    except Exception as e:
        print(f"Error compiling {filename}: {e}")

if __name__ == '__main__':
    compile_tex('LAPI_IEEE_Report.tex')
    compile_tex('LAPI_Cahier_Des_Charges.tex')
