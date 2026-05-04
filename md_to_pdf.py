import markdown
from fpdf import FPDF, HTMLMixin

class MyFPDF(FPDF, HTMLMixin):
    pass

def convert_md_to_pdf(md_file, pdf_file):
    with open(md_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    import re
    text = re.sub(r'!\[.*?\]\(.*?\)', r'> *[Image Placeholder]*', text)
        
    html = markdown.markdown(text, extensions=['tables'])
    
    html = f"""
    <font face="DejaVu">
    {html}
    </font>
    """
    
    pdf = MyFPDF()
    pdf.add_page()
    
    # Use standard DejaVu (packaged with matplotlib or just Windows standard unicode font)
    import os
    font_path = r"C:\Windows\Fonts\arial.ttf"
    font_b_path = r"C:\Windows\Fonts\arialbd.ttf"
    font_i_path = r"C:\Windows\Fonts\ariali.ttf"
    
    if os.path.exists(font_path):
        pdf.add_font("DejaVu", style="", fname=font_path, uni=True)
    if os.path.exists(font_b_path):
        pdf.add_font("DejaVu", style="B", fname=font_b_path, uni=True)
    if os.path.exists(font_i_path):
        pdf.add_font("DejaVu", style="I", fname=font_i_path, uni=True)
        
    pdf.set_font("DejaVu", size=10)
    pdf.write_html(html)
    pdf.output(pdf_file)

if __name__ == '__main__':
    convert_md_to_pdf('LAPI_IEEE_Report.md', 'LAPI_IEEE_Report.pdf')
    print("PDF converted successfully!")
