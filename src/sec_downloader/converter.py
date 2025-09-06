"""
PDF Converter for SEC documents
"""

import logging
from pathlib import Path
from typing import List, Optional
import subprocess
import tempfile
import os

from .config import Config


class PDFConverter:
    """Converts SEC text documents to PDF format"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def convert_to_pdf(self, input_file: Path, output_file: Path = None) -> bool:
        """Convert a text file to PDF"""
        if output_file is None:
            output_file = input_file.with_suffix('.pdf')
        
        try:
            # Read the input file
            with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Create a temporary HTML file for better formatting
            html_content = self._create_html_from_text(content, input_file.name)
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as temp_file:
                temp_file.write(html_content)
                temp_html = temp_file.name
            
            try:
                # Use wkhtmltopdf if available, otherwise use a simple text-to-PDF approach
                if self._is_wkhtmltopdf_available():
                    return self._convert_with_wkhtmltopdf(temp_html, output_file)
                else:
                    return self._convert_with_weasyprint(temp_html, output_file)
            
            finally:
                # Clean up temporary file
                if os.path.exists(temp_html):
                    os.unlink(temp_html)
                
        except Exception as e:
            self.logger.error(f"Failed to convert {input_file} to PDF: {e}")
            return False
    
    def _create_html_from_text(self, content: str, filename: str) -> str:
        """Create HTML content from text with proper formatting"""
        # Basic HTML template
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Courier New', monospace;
            font-size: 12px;
            line-height: 1.4;
            margin: 40px;
            color: #333;
            background: white;
        }}
        .header {{
            text-align: center;
            border-bottom: 2px solid #333;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .content {{
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        .page-break {{
            page-break-before: always;
        }}
        @media print {{
            body {{
                margin: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>SEC Filing Document</h1>
        <p>{filename}</p>
        <p>Generated on {date}</p>
    </div>
    <div class="content">{content}</div>
</body>
</html>
        """
        
        from datetime import datetime
        return html_template.format(
            title=filename,
            filename=filename,
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            content=content
        )
    
    def _is_wkhtmltopdf_available(self) -> bool:
        """Check if wkhtmltopdf is available"""
        try:
            subprocess.run(['wkhtmltopdf', '--version'], 
                         capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _convert_with_wkhtmltopdf(self, html_file: str, output_file: Path) -> bool:
        """Convert HTML to PDF using wkhtmltopdf"""
        try:
            cmd = [
                'wkhtmltopdf',
                '--page-size', 'A4',
                '--margin-top', '20mm',
                '--margin-right', '20mm',
                '--margin-bottom', '20mm',
                '--margin-left', '20mm',
                '--encoding', 'UTF-8',
                '--print-media-type',
                html_file,
                str(output_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info(f"Successfully converted to PDF using wkhtmltopdf: {output_file}")
                return True
            else:
                self.logger.error(f"wkhtmltopdf failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error running wkhtmltopdf: {e}")
            return False
    
    def _convert_with_weasyprint(self, html_file: str, output_file: Path) -> bool:
        """Convert HTML to PDF using WeasyPrint (fallback)"""
        try:
            import weasyprint
            
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Convert to PDF
            weasyprint.HTML(string=html_content).write_pdf(str(output_file))
            
            self.logger.info(f"Successfully converted to PDF using WeasyPrint: {output_file}")
            return True
            
        except ImportError:
            self.logger.warning("WeasyPrint not available. Install with: pip install weasyprint")
            return self._convert_with_basic_pdf(html_file, output_file)
        except Exception as e:
            self.logger.warning(f"WeasyPrint failed: {e}. Falling back to ReportLab.")
            return self._convert_with_basic_pdf(html_file, output_file)
    
    def _convert_with_basic_pdf(self, html_file: str, output_file: Path) -> bool:
        """Basic PDF conversion using reportlab as last resort"""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import inch
            
            # Read the original text file
            text_file = html_file.replace('.html', '.txt')
            if not os.path.exists(text_file):
                # Extract text from HTML
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Simple HTML tag removal
                    import re
                    content = re.sub(r'<[^>]+>', '', content)
            else:
                with open(text_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            
            # Create output directory if it doesn't exist
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Create PDF
            doc = SimpleDocTemplate(str(output_file), pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Split content into paragraphs
            paragraphs = content.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    # Clean up the paragraph text
                    clean_para = para.strip().replace('\n', ' ')
                    if clean_para:
                        p = Paragraph(clean_para, styles['Normal'])
                        story.append(p)
                        story.append(Spacer(1, 12))
            
            doc.build(story)
            
            self.logger.info(f"Successfully converted to PDF using ReportLab: {output_file}")
            return True
            
        except ImportError:
            self.logger.error("ReportLab not available. Install with: pip install reportlab")
            return False
        except Exception as e:
            self.logger.error(f"Error with ReportLab: {e}")
            return False
    
    def batch_convert(self, input_files: List[Path], output_dir: Path = None) -> List[Path]:
        """Convert multiple files to PDF"""
        if output_dir is None:
            output_dir = Path(self.config.get('download.output_dir')) / 'pdf'
        
        output_dir.mkdir(parents=True, exist_ok=True)
        converted_files = []
        
        for input_file in input_files:
            output_file = output_dir / f"{input_file.stem}.pdf"
            
            if self.convert_to_pdf(input_file, output_file):
                converted_files.append(output_file)
            else:
                self.logger.warning(f"Failed to convert {input_file}")
        
        return converted_files
