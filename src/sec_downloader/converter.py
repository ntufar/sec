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
        """Convert a SEC iXBRL document to PDF"""
        if output_file is None:
            output_file = input_file.with_suffix('.pdf')
        
        try:
            # Read the input file
            with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Detect file format and convert accordingly
            if self._is_ixbrl_document(content):
                self.logger.info("Detected iXBRL document format - using specialized converter")
                return self._convert_ixbrl_to_pdf(input_file, output_file)
            elif self._is_sec_sgml_document(content):
                self.logger.info("Detected SEC SGML/XML document format")
                return self._convert_sec_document_to_pdf(content, input_file.name, output_file)
            else:
                # Fallback to text conversion
                self.logger.info("Converting as plain text document")
                return self._convert_text_to_pdf(content, input_file.name, output_file)
                
        except Exception as e:
            self.logger.error(f"PDF conversion failed: {e}")
            return False
    
    def convert_to_html(self, input_file: Path, output_file: Path = None) -> bool:
        """Convert a SEC iXBRL document to HTML (much faster than PDF)"""
        if output_file is None:
            output_file = input_file.with_suffix('.html')
        
        try:
            import time
            
            self.logger.info(f"🔄 Starting iXBRL to HTML conversion: {input_file}")
            start_time = time.time()
            
            # Read the input file
            with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Create output directory if it doesn't exist
            self.logger.info("📁 Creating output directory...")
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Detect file format and convert accordingly
            if self._is_ixbrl_document(content):
                self.logger.info("Detected iXBRL document format - converting to HTML")
                html_content = self._convert_ixbrl_to_html_simple(content, input_file.name)
            elif self._is_sec_sgml_document(content):
                self.logger.info("Detected SEC SGML/XML document format - converting to HTML")
                parsed_content = self._parse_sec_document(content)
                html_content = self._create_sec_html(parsed_content, input_file.name)
            else:
                # Fallback to text conversion
                self.logger.info("Converting as plain text document to HTML")
                html_content = self._create_html_from_text(content, input_file.name)
            
            # Write HTML file
            self.logger.info("💾 Writing HTML file...")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            elapsed_time = time.time() - start_time
            file_size = output_file.stat().st_size
            self.logger.info(f"✅ Successfully converted to HTML in {elapsed_time:.1f} seconds: {output_file}")
            self.logger.info(f"📊 HTML file size: {file_size:,} bytes ({file_size / 1024 / 1024:.1f} MB)")
            return True
                
        except Exception as e:
            self.logger.error(f"❌ HTML conversion failed: {e}")
            return False
    
    def _is_ixbrl_document(self, content: str) -> bool:
        """Check if the content is an iXBRL document"""
        return ('ix:nonNumeric' in content or 
                'ix:numeric' in content or
                'ix:hidden' in content or
                'xmlns:ix=' in content or
                'ix:format' in content or
                'ix:contextRef' in content)
    
    def _is_sec_sgml_document(self, content: str) -> bool:
        """Check if the content is a SEC SGML/XML document"""
        return ('<SEC-DOCUMENT>' in content or 
                '<SEC-HEADER>' in content or
                '<ACCEPTANCE-DATETIME>' in content or
                'ACCESSION NUMBER:' in content)
    
    def _convert_sec_document_to_pdf(self, content: str, filename: str, output_file: Path) -> bool:
        """Convert SEC SGML/XML document to PDF"""
        try:
            # Parse SEC document structure
            parsed_content = self._parse_sec_document(content)
            
            # Create HTML with proper SEC document formatting
            html_content = self._create_sec_html(parsed_content, filename)
            
            # Create temporary HTML file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(html_content)
                temp_html = temp_file.name
            
            try:
                # Try WeasyPrint first (good quality, but skip for very large files)
                if self._convert_with_weasyprint(temp_html, output_file):
                    return True
                
                # Try wkhtmltopdf if available (best for large files)
                if self._is_wkhtmltopdf_available():
                    if self._convert_with_wkhtmltopdf(temp_html, output_file):
                        return True
                
                # Fall back to basic PDF conversion (always works)
                if self._convert_with_basic_pdf(temp_html, output_file):
                    return True
                
                self.logger.error("All PDF conversion methods failed")
                return False
            
            finally:
                # Clean up temporary file
                if os.path.exists(temp_html):
                    os.unlink(temp_html)
                    
        except Exception as e:
            self.logger.error(f"SEC document conversion failed: {e}")
            return False
    
    def _convert_text_to_pdf(self, content: str, filename: str, output_file: Path) -> bool:
        """Convert plain text to PDF (fallback method)"""
        try:
            # Create a temporary HTML file for better formatting
            html_content = self._create_html_from_text(content, filename)
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as temp_file:
                temp_file.write(html_content)
                temp_html = temp_file.name
            
            try:
                # Try WeasyPrint first (good quality, but skip for very large files)
                if self._convert_with_weasyprint(temp_html, output_file):
                    return True
                
                # Try wkhtmltopdf if available (best for large files)
                if self._is_wkhtmltopdf_available():
                    if self._convert_with_wkhtmltopdf(temp_html, output_file):
                        return True
                
                # Fall back to basic PDF conversion (always works)
                if self._convert_with_basic_pdf(temp_html, output_file):
                    return True
                
                self.logger.error("All PDF conversion methods failed")
                return False
            
            finally:
                # Clean up temporary file
                if os.path.exists(temp_html):
                    os.unlink(temp_html)
                    
        except Exception as e:
            self.logger.error(f"Text conversion failed: {e}")
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
        """Convert HTML to PDF using wkhtmltopdf (optimized for large files)"""
        try:
            # Create output directory if it doesn't exist
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            cmd = [
                'wkhtmltopdf',
                '--page-size', 'A4',
                '--margin-top', '20mm',
                '--margin-right', '20mm',
                '--margin-bottom', '20mm',
                '--margin-left', '20mm',
                '--encoding', 'UTF-8',
                '--print-media-type',
                '--disable-smart-shrinking',  # Prevent text from being too small
                '--enable-local-file-access',  # Allow local file access
                '--load-error-handling', 'ignore',  # Ignore load errors
                '--load-media-error-handling', 'ignore',  # Ignore media errors
                '--no-stop-slow-scripts',  # Don't stop slow scripts
                '--javascript-delay', '1000',  # Wait for JS to load
                '--timeout', '300',  # 5 minute timeout
                '--lowquality',  # Reduce quality for large files
                html_file,
                str(output_file)
            ]
            
            self.logger.info(f"Converting large file with wkhtmltopdf: {html_file}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)  # 10 minute timeout
            
            if result.returncode == 0:
                self.logger.info(f"Successfully converted to PDF using wkhtmltopdf: {output_file}")
                return True
            else:
                self.logger.warning(f"wkhtmltopdf failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.warning("wkhtmltopdf timed out - file may be too large")
            return False
        except Exception as e:
            self.logger.warning(f"Error running wkhtmltopdf: {e}")
            return False
    
    def _convert_with_weasyprint(self, html_file: str, output_file: Path) -> bool:
        """Convert HTML to PDF using WeasyPrint (fallback for smaller files)"""
        try:
            import weasyprint
            import sys
            
            # Check file size - WeasyPrint struggles with very large files
            file_size = os.path.getsize(html_file)
            if file_size > 10 * 1024 * 1024:  # 10MB limit
                self.logger.warning(f"File too large for WeasyPrint ({file_size / 1024 / 1024:.1f}MB), skipping")
                return False
            
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Create output directory if it doesn't exist
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert to PDF with memory optimization
            html_doc = weasyprint.HTML(string=html_content)
            html_doc.write_pdf(str(output_file))
            
            self.logger.info(f"Successfully converted to PDF using WeasyPrint: {output_file}")
            return True
            
        except ImportError:
            self.logger.warning("WeasyPrint not available. Install with: pip install weasyprint")
            return False
        except RecursionError:
            self.logger.warning("WeasyPrint failed: maximum recursion depth exceeded. File too complex.")
            return False
        except Exception as e:
            self.logger.warning(f"WeasyPrint failed: {e}. Falling back to ReportLab.")
            return False
    
    def _convert_with_basic_pdf(self, html_file: str, output_file: Path) -> bool:
        """Basic PDF conversion using reportlab (optimized for large files)"""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            import re
            
            # Read the original text file
            text_file = html_file.replace('.html', '.txt')
            if not os.path.exists(text_file):
                # Extract text from HTML
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Better HTML tag removal
                    content = self._clean_html_content(content)
            else:
                with open(text_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    # Clean the content even if it's from text file
                    content = self._clean_html_content(content)
            
            # Create output directory if it doesn't exist
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Create PDF with optimized settings for large files
            doc = SimpleDocTemplate(
                str(output_file), 
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            styles = getSampleStyleSheet()
            
            # Create custom styles optimized for large documents
            normal_style = styles['Normal']
            normal_style.fontSize = 9  # Smaller font for large documents
            normal_style.leading = 11
            normal_style.spaceAfter = 6
            
            title_style = styles['Heading1']
            title_style.fontSize = 12
            title_style.spaceAfter = 8
            
            story = []
            
            # Process content in chunks to handle large files
            lines = content.split('\n')
            current_paragraph = []
            processed_lines = 0
            max_lines_per_chunk = 1000  # Process in chunks

            self.logger.info(f"📊 Processing large document with {len(lines):,} lines using ReportLab")
            self.logger.info(f"📈 Processing in chunks of {max_lines_per_chunk:,} lines")
            
            for line in lines:
                line = line.strip()
                processed_lines += 1
                
                # Process in chunks to handle large files
                if processed_lines % max_lines_per_chunk == 0:
                    progress = (processed_lines / len(lines)) * 100
                    self.logger.info(f"📈 Progress: {processed_lines:,}/{len(lines):,} lines ({progress:.1f}%)")
                    # Build PDF in chunks to avoid memory issues
                    if story:
                        try:
                            self.logger.info(f"🔨 Building PDF chunk {processed_lines // max_lines_per_chunk}...")
                            doc.build(story)
                            story = []  # Clear story to free memory
                            self.logger.info(f"✅ Chunk {processed_lines // max_lines_per_chunk} completed")
                        except Exception as e:
                            self.logger.warning(f"⚠️ Chunk processing failed: {e}")
                
                if not line:
                    if current_paragraph:
                        # Process accumulated paragraph
                        para_text = ' '.join(current_paragraph)
                        if para_text.strip():
                            try:
                                p = Paragraph(para_text, normal_style)
                                story.append(p)
                                story.append(Spacer(1, 6))
                            except Exception as e:
                                # If paragraph fails, add as plain text
                                self.logger.warning(f"Paragraph parsing failed, adding as plain text: {e}")
                                story.append(Paragraph(para_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'), normal_style))
                                story.append(Spacer(1, 6))
                        current_paragraph = []
                else:
                    # Check if this looks like a header
                    if (line.isupper() and len(line) > 10) or line.startswith('Item '):
                        if current_paragraph:
                            # Process current paragraph first
                            para_text = ' '.join(current_paragraph)
                            if para_text.strip():
                                try:
                                    p = Paragraph(para_text, normal_style)
                                    story.append(p)
                                    story.append(Spacer(1, 6))
                                except Exception:
                                    story.append(Paragraph(para_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'), normal_style))
                                    story.append(Spacer(1, 6))
                            current_paragraph = []
                        
                        # Add header
                        try:
                            p = Paragraph(line, title_style)
                            story.append(p)
                            story.append(Spacer(1, 12))
                        except Exception:
                            story.append(Paragraph(line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'), title_style))
                            story.append(Spacer(1, 12))
                    else:
                        current_paragraph.append(line)
            
            # Process any remaining paragraph
            if current_paragraph:
                para_text = ' '.join(current_paragraph)
                if para_text.strip():
                    try:
                        p = Paragraph(para_text, normal_style)
                        story.append(p)
                    except Exception:
                        story.append(Paragraph(para_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'), normal_style))
            
            self.logger.info("🔨 Building final PDF...")
            doc.build(story)

            self.logger.info(f"✅ Successfully converted to PDF using ReportLab: {output_file}")
            return True
            
        except ImportError:
            self.logger.error("ReportLab not available. Install with: pip install reportlab")
            return False
        except Exception as e:
            self.logger.error(f"Error with ReportLab: {e}")
            return False
    
    def _clean_html_content(self, content: str) -> str:
        """Clean HTML content and extract readable text"""
        import re
        from bs4 import BeautifulSoup
        
        try:
            # Use BeautifulSoup to parse and clean HTML
            soup = BeautifulSoup(content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text
            
        except Exception as e:
            self.logger.warning(f"BeautifulSoup parsing failed: {e}, using regex fallback")
            # Fallback to regex-based cleaning
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', '', content)
            # Remove multiple whitespace
            text = re.sub(r'\s+', ' ', text)
            # Remove special characters that might cause issues
            text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)\[\]\{\}\"\'\/\\]', '', text)
            return text
    
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
    
    def _parse_sec_document(self, content: str) -> dict:
        """Parse SEC SGML/XML document structure"""
        import re
        
        parsed = {
            'header': {},
            'content': '',
            'exhibits': []
        }
        
        # Extract header information
        header_match = re.search(r'<SEC-HEADER>(.*?)</SEC-HEADER>', content, re.DOTALL)
        if header_match:
            header_content = header_match.group(1)
            # Parse key-value pairs
            for line in header_content.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    parsed['header'][key.strip()] = value.strip()
        
        # Extract main document content (between <DOCUMENT> tags)
        doc_match = re.search(r'<DOCUMENT>(.*?)</DOCUMENT>', content, re.DOTALL)
        if doc_match:
            doc_content = doc_match.group(1)
            # Clean up the content
            parsed['content'] = self._clean_sec_content(doc_content)
        else:
            # Fallback: extract content after header
            header_end = content.find('</SEC-HEADER>')
            if header_end != -1:
                parsed['content'] = self._clean_sec_content(content[header_end + len('</SEC-HEADER>'):])
            else:
                parsed['content'] = self._clean_sec_content(content)
        
        return parsed
    
    def _clean_sec_content(self, content: str) -> str:
        """Clean SEC document content for better readability"""
        import re
        
        # Remove SGML/XML tags but keep structure
        content = re.sub(r'<[^>]+>', '', content)
        
        # Clean up whitespace
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)  # Multiple newlines to double
        content = re.sub(r'[ \t]+', ' ', content)  # Multiple spaces to single
        
        # Clean up common SEC formatting issues
        content = re.sub(r'^\s*[^\w\s]*\s*$', '', content, flags=re.MULTILINE)  # Remove lines with only symbols
        content = re.sub(r'\n\s*\n', '\n\n', content)  # Clean up spacing
        
        return content.strip()
    
    def _create_sec_html(self, parsed_content: dict, filename: str) -> str:
        """Create properly formatted HTML for SEC documents"""
        from datetime import datetime
        
        # Extract key information
        company_name = parsed_content['header'].get('COMPANY CONFORMED NAME', 'Unknown Company')
        accession_number = parsed_content['header'].get('ACCESSION NUMBER', 'Unknown')
        filing_date = parsed_content['header'].get('FILED AS OF DATE', 'Unknown')
        document_type = parsed_content['header'].get('CONFORMED SUBMISSION TYPE', 'Unknown')
        
        # Format filing date
        if filing_date != 'Unknown' and len(filing_date) == 8:
            try:
                formatted_date = f"{filing_date[:4]}-{filing_date[4:6]}-{filing_date[6:8]}"
            except:
                formatted_date = filing_date
        else:
            formatted_date = filing_date
        
        html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{company_name} - {document_type}</title>
    <style>
        body {{
            font-family: 'Times New Roman', serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            color: #333;
            background: white;
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #2c3e50;
            padding-bottom: 20px;
            margin-bottom: 30px;
            background: #f8f9fa;
            padding: 20px;
        }}
        .company-name {{
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        .document-type {{
            font-size: 18px;
            color: #7f8c8d;
            margin-bottom: 10px;
        }}
        .filing-info {{
            font-size: 14px;
            color: #7f8c8d;
        }}
        .content {{
            white-space: pre-wrap;
            word-wrap: break-word;
            font-size: 12px;
            line-height: 1.5;
        }}
        .content strong {{
            font-weight: bold;
            color: #2c3e50;
            font-size: 13px;
            display: block;
            margin: 8px 0 4px 0;
        }}
        .section-header {{
            font-weight: bold;
            font-size: 14px;
            margin-top: 20px;
            margin-bottom: 10px;
            color: #2c3e50;
            border-bottom: 1px solid #bdc3c7;
            padding-bottom: 5px;
        }}
        .page-break {{
            page-break-before: always;
        }}
        @media print {{
            body {{
                margin: 15px;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="company-name">{company_name}</div>
        <div class="document-type">{document_type}</div>
        <div class="filing-info">
            <div>Accession Number: {accession_number}</div>
            <div>Filing Date: {formatted_date}</div>
            <div>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>
        </div>
    </div>
    
    <div class="content">{parsed_content['content']}</div>
</body>
</html>
        """
        
        return html_template

    def _convert_ixbrl_to_pdf(self, input_file: Path, output_file: Path) -> bool:
        """Convert iXBRL document to PDF using simplified parser"""
        try:
            import tempfile
            import os
            import time
            
            self.logger.info(f"🔄 Starting iXBRL conversion: {input_file}")
            start_time = time.time()
            
            # Create output directory if it doesn't exist
            self.logger.info("📁 Creating output directory...")
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Read the iXBRL file
            self.logger.info("📖 Reading iXBRL file...")
            file_size = input_file.stat().st_size
            self.logger.info(f"📊 File size: {file_size:,} bytes ({file_size / 1024 / 1024:.1f} MB)")
            
            with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Convert iXBRL to HTML with proper formatting
            self.logger.info("🔧 Parsing iXBRL content and generating HTML...")
            html_content = self._convert_ixbrl_to_html_simple(content, input_file.name)
            
            # Create temporary HTML file
            self.logger.info("💾 Creating temporary HTML file...")
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(html_content)
                temp_html = temp_file.name
            
            try:
                # Convert HTML to PDF using ReportLab (most reliable for large documents)
                self.logger.info("📄 Converting HTML to PDF using ReportLab...")
                if self._convert_with_basic_pdf(temp_html, output_file):
                    elapsed_time = time.time() - start_time
                    self.logger.info(f"✅ Successfully converted iXBRL to PDF in {elapsed_time:.1f} seconds: {output_file}")
                    return True
                else:
                    self.logger.error("❌ Failed to convert HTML to PDF")
                    return False
            
            finally:
                # Clean up temporary file
                if os.path.exists(temp_html):
                    os.unlink(temp_html)
                
        except Exception as e:
            self.logger.error(f"❌ iXBRL conversion failed: {e}")
            return False
    
    def _convert_ixbrl_to_html(self, model_document, filename: str) -> str:
        """Convert iXBRL model document to formatted HTML"""
        from datetime import datetime
        import re
        
        # Extract basic document information
        company_name = "Unknown Company"
        accession_number = "Unknown"
        filing_date = "Unknown"
        document_type = "10-K"
        
        # Try to extract information from the document
        try:
            # Look for company name in various places
            if hasattr(model_document, 'modelXbrl') and model_document.modelXbrl:
                # Extract from XBRL context
                contexts = model_document.modelXbrl.contexts
                if contexts:
                    for context in contexts.values():
                        if hasattr(context, 'entityIdentifier') and context.entityIdentifier:
                            company_name = context.entityIdentifier[1]  # Entity name
                            break
            
            # Extract from document URI or filename
            if 'JXN' in filename:
                company_name = "Jackson Financial Inc."
            
            # Extract accession number from filename
            accession_match = re.search(r'(\d{10}-\d{2}-\d{6})', filename)
            if accession_match:
                accession_number = accession_match.group(1)
            
            # Extract filing date from filename
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
            if date_match:
                filing_date = date_match.group(1)
                
        except Exception as e:
            self.logger.warning(f"Could not extract document metadata: {e}")
        
        # Convert iXBRL content to readable HTML
        html_content = self._extract_readable_content_from_ixbrl(model_document)
        
        # Create formatted HTML
        html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{company_name} - {document_type}</title>
    <style>
        body {{
            font-family: 'Times New Roman', serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            color: #333;
            background: white;
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #2c3e50;
            padding-bottom: 20px;
            margin-bottom: 30px;
            background: #f8f9fa;
            padding: 20px;
        }}
        .company-name {{
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        .document-type {{
            font-size: 18px;
            color: #7f8c8d;
            margin-bottom: 10px;
        }}
        .filing-info {{
            font-size: 14px;
            color: #7f8c8d;
        }}
        .content {{
            white-space: pre-wrap;
            word-wrap: break-word;
            font-size: 12px;
            line-height: 1.5;
        }}
        .content strong {{
            font-weight: bold;
            color: #2c3e50;
            font-size: 13px;
            display: block;
            margin: 8px 0 4px 0;
        }}
        .section-header {{
            font-weight: bold;
            font-size: 14px;
            margin-top: 20px;
            margin-bottom: 10px;
            color: #2c3e50;
            border-bottom: 1px solid #bdc3c7;
            padding-bottom: 5px;
        }}
        .financial-data {{
            background: #f8f9fa;
            padding: 10px;
            margin: 10px 0;
            border-left: 4px solid #2c3e50;
        }}
        .page-break {{
            page-break-before: always;
        }}
        @media print {{
            body {{
                margin: 15px;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="company-name">{company_name}</div>
        <div class="document-type">{document_type}</div>
        <div class="filing-info">
            <div>Accession Number: {accession_number}</div>
            <div>Filing Date: {filing_date}</div>
            <div>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>
        </div>
    </div>
    
    <div class="content">{html_content}</div>
</body>
</html>
        """
        
        return html_template
    
    def _extract_readable_content_from_ixbrl(self, model_document) -> str:
        """Extract readable content from iXBRL model document"""
        try:
            content_parts = []
            
            # Extract facts (financial data)
            if hasattr(model_document, 'modelXbrl') and model_document.modelXbrl:
                facts = model_document.modelXbrl.facts
                if facts:
                    content_parts.append("FINANCIAL DATA:")
                    content_parts.append("=" * 50)
                    
                    for fact in facts:
                        if hasattr(fact, 'concept') and hasattr(fact, 'xValue'):
                            concept_name = fact.concept.qname.localName if fact.concept else "Unknown"
                            value = str(fact.xValue) if fact.xValue else "N/A"
                            content_parts.append(f"{concept_name}: {value}")
                    
                    content_parts.append("")
            
            # Extract document content from the original file
            if hasattr(model_document, 'uri'):
                try:
                    with open(model_document.uri, 'r', encoding='utf-8', errors='ignore') as f:
                        raw_content = f.read()
                    
                    # Clean up iXBRL tags and extract readable content
                    cleaned_content = self._clean_ixbrl_content(raw_content)
                    content_parts.append(cleaned_content)
                    
                except Exception as e:
                    self.logger.warning(f"Could not read document content: {e}")
                    content_parts.append("Document content could not be extracted.")
            
            return "\n".join(content_parts)
            
        except Exception as e:
            self.logger.warning(f"Could not extract content from iXBRL: {e}")
            return "iXBRL content could not be processed."
    
    def _clean_ixbrl_content(self, content: str) -> str:
        """Clean iXBRL content for better readability"""
        import re
        
        # Remove iXBRL tags but keep the text content
        content = re.sub(r'<ix:[^>]*>', '', content)
        content = re.sub(r'</ix:[^>]*>', '', content)
        
        # Remove style attributes and other formatting tags but keep structure
        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL)
        content = re.sub(r'style="[^"]*"', '', content)
        
        # Convert some HTML tags to plain text equivalents
        content = re.sub(r'<br\s*/?>', '\n', content)
        content = re.sub(r'<p[^>]*>', '\n\n', content)
        content = re.sub(r'</p>', '', content)
        content = re.sub(r'<div[^>]*>', '\n', content)
        content = re.sub(r'</div>', '', content)
        
        # Remove remaining HTML tags but preserve text
        content = re.sub(r'<[^>]+>', '', content)
        
        # Clean up whitespace
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        content = re.sub(r'[ \t]+', ' ', content)
        
        # Remove lines with only symbols or whitespace
        content = re.sub(r'^\s*[^\w\s]*\s*$', '', content, flags=re.MULTILINE)
        
        return content.strip()
    
    def _format_table_of_contents(self, content: str) -> str:
        """Format table of contents with bold chapter titles"""
        import re
        
        lines = content.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                formatted_lines.append('')
                continue
                
            # Check if this looks like a chapter/section title
            # Look for patterns like "Item 1. Business", "Part I", "Item 1A. Risk Factors", etc.
            if (re.match(r'^(Part [IVX]+|Item \d+[A-Z]?\.)', line, re.IGNORECASE) or
                re.match(r'^Item \d+[A-Z]?\.[^0-9]', line, re.IGNORECASE) or
                re.match(r'^[A-Z][a-z]+ [A-Z][a-z]+', line) or
                line in ['Overview', 'Competition', 'Risk Management', 'Regulation', 
                        'Corporate Responsibility', 'Human Capital Resources', 
                        'Intellectual Property', 'Available Information', 
                        'Information about our Executive Officers', 'Executive Summary',
                        'Key Operating Measures', 'Macroeconomic, Industry and Regulatory Trends',
                        'Non-GAAP Financial Measures', 'Consolidated Results of Operations',
                        'Segment Results of Operations', 'Investments', 'Policy and Contract Liabilities',
                        'Liquidity and Capital Resources', 'Impact of Recent Accounting Pronouncements',
                        'Critical Accounting Estimates', 'Reference to Financial Statements and Schedules',
                        'Changes in and Disagreements with Accountants on Accounting and Financial Disclosure',
                        'Controls and Procedures', 'Other Information', 'Disclosure Regarding Foreign Jurisdictions that Prevent Inspections',
                        'Directors, Executive Officers and Corporate Governance', 'Executive Compensation',
                        'Security Ownership of Certain Beneficial Owners and Management and Related Shareholder Matters',
                        'Certain Relationships and Related Transactions, and Director Independence',
                        'Principal Accountant Fees and Services']):
                # Format as bold chapter title
                formatted_lines.append(f'<strong>{line}</strong>')
            else:
                # Regular content
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)

    def _extract_complete_report_content(self, content: str) -> str:
        """Extract clean, readable report content from SEC document, focusing on main 10-K content"""
        import re
        
        try:
            self.logger.info("🔍 Extracting clean report content from SEC document...")
            
            # Find all document sections
            document_sections = re.findall(r'<DOCUMENT>.*?</DOCUMENT>', content, re.DOTALL | re.IGNORECASE)
            self.logger.info(f"📄 Found {len(document_sections)} document sections")
            
            # Priority order for document types (most important first)
            priority_types = ['10-K', '10-Q', '8-K', 'EX-21.1', 'EX-23.1', 'EX-31.1', 'EX-31.2', 'EX-32.1', 'EX-32.2']
            
            # Types to exclude (technical/binary content)
            exclude_types = ['XML', 'GRAPHIC', 'EXCEL', 'JSON', 'ZIP', 'EX-101.SCH', 'EX-101.CAL', 'EX-101.DEF', 'EX-101.LAB', 'EX-101.PRE']
            
            main_content = []
            exhibit_content = []
            
            for i, section in enumerate(document_sections):
                # Extract document type
                doc_type_match = re.search(r'<TYPE>([^<\n]+)', section, re.IGNORECASE)
                doc_type = doc_type_match.group(1).strip() if doc_type_match else "Unknown"
                
                # Skip excluded types
                if doc_type.upper() in [t.upper() for t in exclude_types]:
                    self.logger.info(f"⏭️ Skipping technical section: {doc_type}")
                    continue
                
                self.logger.info(f"📋 Processing document section {i+1}: {doc_type}")
                
                # Extract text content from this section
                text_match = re.search(r'<TEXT>(.*?)</TEXT>', section, re.DOTALL | re.IGNORECASE)
                if text_match:
                    text_content = text_match.group(1)
                    
                    # Clean and process content
                    cleaned_content = self._clean_document_content(text_content, doc_type)
                    
                    if cleaned_content and len(cleaned_content) > 200:  # Only include substantial content
                        if doc_type.upper() in [t.upper() for t in priority_types]:
                            main_content.append(f"=== {doc_type} ===\n{cleaned_content}\n")
                            self.logger.info(f"✅ Added {len(cleaned_content):,} characters from main section {doc_type}")
                        else:
                            # Add exhibits but with less priority
                            exhibit_content.append(f"=== {doc_type} ===\n{cleaned_content}\n")
                            self.logger.info(f"📄 Added {len(cleaned_content):,} characters from exhibit {doc_type}")
            
            # Combine main content first, then exhibits
            all_content = main_content + exhibit_content
            
            if all_content:
                complete_content = '\n\n'.join(all_content)
                self.logger.info(f"📝 Total clean content: {len(complete_content):,} characters")
                return complete_content
            else:
                self.logger.warning("⚠️ No substantial content found in any document section")
                return content[:50000]  # Return first 50KB as fallback
                
        except Exception as e:
            self.logger.error(f"Error extracting complete report content: {e}")
            return content[:50000]  # Return first 50KB as fallback

    def _clean_document_content(self, text_content: str, doc_type: str) -> str:
        """Clean and format document content for better readability"""
        import re
        
        # Remove style attributes and complex formatting
        text_content = re.sub(r'style="[^"]*"', '', text_content)
        text_content = re.sub(r'class="[^"]*"', '', text_content)
        text_content = re.sub(r'id="[^"]*"', '', text_content)
        
        # Convert common HTML tags to newlines
        text_content = re.sub(r'<br\s*/?>', '\n', text_content, flags=re.IGNORECASE)
        text_content = re.sub(r'</?p[^>]*>', '\n', text_content, flags=re.IGNORECASE)
        text_content = re.sub(r'</?div[^>]*>', '\n', text_content, flags=re.IGNORECASE)
        text_content = re.sub(r'</?span[^>]*>', '', text_content, flags=re.IGNORECASE)
        
        # Remove script tags and their content
        text_content = re.sub(r'<script[^>]*>.*?</script>', '', text_content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove JavaScript code patterns
        text_content = re.sub(r'var\s+\w+\s*=.*?;', '', text_content, flags=re.DOTALL)
        text_content = re.sub(r'function\s+\w+.*?}', '', text_content, flags=re.DOTALL)
        
        # Remove XML/HTML comments
        text_content = re.sub(r'<!--.*?-->', '', text_content, flags=re.DOTALL)
        
        # Remove remaining HTML tags but keep text
        text_content = re.sub(r'<[^>]+>', '', text_content)
        
        # Clean up whitespace and formatting
        text_content = re.sub(r'\n\s*\n\s*\n', '\n\n', text_content)  # Max 2 consecutive newlines
        text_content = re.sub(r'[ \t]+', ' ', text_content)  # Multiple spaces to single space
        text_content = re.sub(r'\n ', '\n', text_content)  # Remove leading spaces on new lines
        
        # Remove lines that are just numbers or technical identifiers
        lines = text_content.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if not line:
                cleaned_lines.append('')
                continue
            
            # Skip lines that are just numbers, IDs, or technical data
            if (re.match(r'^\d+$', line) or  # Just numbers
                re.match(r'^[A-Z0-9\-_]{20,}$', line) or  # Long technical IDs
                re.match(r'^[a-f0-9]{32,}$', line) or  # Hex strings
                line.startswith('// Edgar') or  # SEC technical comments
                line.startswith('var ') or  # JavaScript
                line.startswith('function ') or  # JavaScript
                line.startswith('/*') or  # Comments
                line.startswith('*/') or  # Comments
                len(line) > 500 and not re.search(r'[.!?]', line)):  # Very long lines without punctuation
                continue
            
            cleaned_lines.append(line)
        
        text_content = '\n'.join(cleaned_lines)
        text_content = text_content.strip()
        
        return text_content

    def _convert_ixbrl_to_html_simple(self, content: str, filename: str) -> str:
        """Convert iXBRL content to formatted HTML using simple parsing"""
        from datetime import datetime
        import re
        
        # Extract basic document information
        company_name = "Unknown Company"
        accession_number = "Unknown"
        filing_date = "Unknown"
        document_type = "10-K"
        
        # Extract from filename or content
        if 'JXN' in filename:
            company_name = "Jackson Financial Inc."
        
        # Extract accession number from filename
        accession_match = re.search(r'(\d{10}-\d{2}-\d{6})', filename)
        if accession_match:
            accession_number = accession_match.group(1)
        
        # Extract filing date from filename
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        if date_match:
            filing_date = date_match.group(1)
        
        # Extract company name from content
        company_match = re.search(r'COMPANY CONFORMED NAME:\s*(.+)', content)
        if company_match:
            company_name = company_match.group(1).strip()
        
        # Extract accession number from content
        accession_match = re.search(r'ACCESSION NUMBER:\s*(\d{10}-\d{2}-\d{6})', content)
        if accession_match:
            accession_number = accession_match.group(1)
        
        # Extract filing date from content
        filing_match = re.search(r'FILED AS OF DATE:\s*(\d{8})', content)
        if filing_match:
            filing_date = filing_match.group(1)
            if len(filing_date) == 8:
                filing_date = f"{filing_date[:4]}-{filing_date[4:6]}-{filing_date[6:8]}"
        
        # Extract document type from content
        doc_type_match = re.search(r'CONFORMED SUBMISSION TYPE:\s*(.+)', content)
        if doc_type_match:
            document_type = doc_type_match.group(1).strip()
        
        # Extract main report content using the new improved method
        self.logger.info("🔍 Extracting complete report content...")
        main_content = self._extract_complete_report_content(content)
        self.logger.info(f"📄 Main content length: {len(main_content):,} characters")
        
        # Check if this appears to be a truncated report (exhibits/regulatory content only)
        import re
        has_exhibits = bool(re.search(r'Part IV|Item 15|Exhibit|SIGNATURES', main_content, re.IGNORECASE))
        has_main_content = bool(re.search(r'Item 1\.\s*Business|Item 1A\.\s*Risk|Item 2\.\s*Properties', main_content, re.IGNORECASE))
        is_truncated = has_exhibits and not has_main_content and len(main_content) < 100000
        
        # Clean iXBRL content for better readability
        self.logger.info("🧹 Cleaning iXBRL content...")
        cleaned_content = self._clean_ixbrl_content(main_content)
        self.logger.info(f"📝 Cleaned content length: {len(cleaned_content):,} characters")
        
        # Format table of contents with bold chapter titles
        self.logger.info("🎨 Formatting table of contents...")
        formatted_content = self._format_table_of_contents(cleaned_content)
        
        # Create formatted HTML
        html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{company_name} - {document_type}</title>
    <style>
        body {{
            font-family: 'Times New Roman', serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            color: #333;
            background: white;
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #2c3e50;
            padding-bottom: 20px;
            margin-bottom: 30px;
            background: #f8f9fa;
            padding: 20px;
        }}
        .company-name {{
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        .document-type {{
            font-size: 18px;
            color: #7f8c8d;
            margin-bottom: 10px;
        }}
        .filing-info {{
            font-size: 14px;
            color: #7f8c8d;
        }}
        .content {{
            white-space: pre-wrap;
            word-wrap: break-word;
            font-size: 12px;
            line-height: 1.5;
        }}
        .content strong {{
            font-weight: bold;
            color: #2c3e50;
            font-size: 13px;
            display: block;
            margin: 8px 0 4px 0;
        }}
        .section-header {{
            font-weight: bold;
            font-size: 14px;
            margin-top: 20px;
            margin-bottom: 10px;
            color: #2c3e50;
            border-bottom: 1px solid #bdc3c7;
            padding-bottom: 5px;
        }}
        .financial-data {{
            background: #f8f9fa;
            padding: 10px;
            margin: 10px 0;
            border-left: 4px solid #2c3e50;
        }}
        .page-break {{
            page-break-before: always;
        }}
        @media print {{
            body {{
                margin: 15px;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="company-name">{company_name}</div>
        <div class="document-type">{document_type}</div>
        <div class="filing-info">
            <div>Accession Number: {accession_number}</div>
            <div>Filing Date: {filing_date}</div>
            <div>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>
        </div>
    </div>
    
    {f'<div style="background-color: #fff3cd; border: 1px solid #ffeaa7; color: #856404; padding: 15px; border-radius: 5px; margin-bottom: 20px;"><strong>⚠️ Notice:</strong> This appears to be a truncated iXBRL filing containing only exhibits, signatures, and regulatory content. The main narrative sections (Item 1 - Business, Item 1A - Risk Factors, Item 2 - Properties, etc.) are not available in this file. This is common with some SEC iXBRL filings that separate narrative content from exhibits and regulatory information.</div>' if is_truncated else ''}
    
    <div class="content">{formatted_content}</div>
</body>
</html>
        """
        
        return html_template

    def _extract_main_report_content(self, content: str) -> str:
        """Extract the main 10-K report content, skipping exhibits table"""
        import re
        
        try:
            self.logger.info("🔍 Searching for main 10-K report content...")
            
            # First, try to find the main 10-K document section (not exhibits)
            # Look for document sections that contain the actual 10-K content
            document_sections = re.findall(r'<DOCUMENT>.*?</DOCUMENT>', content, re.DOTALL | re.IGNORECASE)
            
            main_document_content = None
            for i, section in enumerate(document_sections):
                # Check if this section contains the main 10-K content
                # Look for typical 10-K sections like "Item 1. Business" or "Part I"
                # But exclude sections that are clearly exhibits or certifications
                if (re.search(r'Item 1\.\s*Business', section, re.IGNORECASE) or \
                   re.search(r'\bPart I\b(?!\s*[,V])', section, re.IGNORECASE)) and \
                   not re.search(r'<TYPE>EX-', section, re.IGNORECASE) and \
                   not re.search(r'Exhibit\s+\d+', section, re.IGNORECASE):
                    self.logger.info(f"✅ Found main 10-K content in document section {i+1}")
                    main_document_content = section
                    break
            
            # If we found a main document section, use that; otherwise use the full content
            search_content = main_document_content if main_document_content else content
            
            # Look for Part I or Item 1 to find the main report content
            # Be more specific to avoid matching "Part I" in table of contents or exhibits
            # Look for "Part I" that is NOT followed by a comma (table of contents) or "V" (Part IV)
            part1_match = re.search(r'\bPart I\b(?!\s*[,V])[^<]*', search_content, re.IGNORECASE | re.DOTALL)
            item1_match = re.search(r'\bItem 1\.[^<]*', search_content, re.IGNORECASE | re.DOTALL)
            
            if part1_match:
                self.logger.info("✅ Found Part I section - extracting main report content")
                # Extract from Part I to the end, but stop before Part IV (exhibits)
                part4_match = re.search(r'\bPart IV\b[^<]*', search_content, re.IGNORECASE | re.DOTALL)
                if part4_match:
                    main_content = search_content[part1_match.start():part4_match.start()]
                else:
                    main_content = search_content[part1_match.start():]
                
                # If the content is too short, try to get more content
                if len(main_content) < 10000:  # Less than 10KB
                    self.logger.info("📄 Content too short, trying to extract more...")
                    # Look for the actual business content after the table of contents
                    business_match = re.search(r'Item 1\.\s*Business[^<]*', main_content, re.IGNORECASE | re.DOTALL)
                    if business_match:
                        # Extract from Item 1 Business to the end of Part III
                        part3_match = re.search(r'\bPart III\b[^<]*', main_content, re.IGNORECASE | re.DOTALL)
                        if part3_match:
                            main_content = main_content[business_match.start():part3_match.start()]
                        else:
                            main_content = main_content[business_match.start():]
                        self.logger.info(f"📄 Extended content length: {len(main_content):,} characters")
                
                return main_content
            elif item1_match:
                self.logger.info("✅ Found Item 1 section - extracting main report content")
                # Extract from Item 1 to the end, but stop before Part IV (exhibits)
                part4_match = re.search(r'\bPart IV\b[^<]*', search_content, re.IGNORECASE | re.DOTALL)
                if part4_match:
                    main_content = search_content[item1_match.start():part4_match.start()]
                else:
                    main_content = search_content[item1_match.start():]
                return main_content
            else:
                # Check if this is a truncated report (only exhibits and signatures)
                # This is common with some SEC iXBRL files that contain only regulatory content
                has_exhibits = bool(re.search(r'Part IV|Item 15|Exhibit|SIGNATURES', search_content, re.IGNORECASE))
                has_main_content = bool(re.search(r'Item 1\.\s*Business|Item 1A\.\s*Risk|Item 2\.\s*Properties', search_content, re.IGNORECASE))
                
                if has_exhibits and not has_main_content and len(search_content) < 100000:
                    self.logger.warning("⚠️ This appears to be a truncated iXBRL file containing only exhibits, signatures, and regulatory content")
                    self.logger.warning("⚠️ The main narrative sections (Item 1 Business, Item 1A Risk Factors, etc.) are not available in this file")
                    self.logger.info("ℹ️ This is common with some SEC iXBRL filings that separate narrative content from exhibits")
                    return search_content
                else:
                    self.logger.warning("⚠️ Could not find Part I or Item 1 - using full content")
                    return search_content
                
        except Exception as e:
            self.logger.error(f"Error extracting main report content: {e}")
            return content

    def extract_pure_html_from_sec_document(self, input_file: Path, output_file: Path = None) -> bool:
        """Extract pure HTML content from SEC 10-K document, focusing on the main report"""
        if output_file is None:
            output_file = input_file.with_suffix('.html')
        
        try:
            self.logger.info(f"🔄 Extracting pure HTML from SEC document: {input_file}")
            
            # Read the SEC document
            with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Create output directory if it doesn't exist
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Extract the main 10-K HTML content
            html_content = self._extract_main_10k_html(content, input_file.name)
            
            if not html_content:
                self.logger.error("❌ No HTML content found in SEC document")
                return False
            
            # Write the HTML file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            file_size = output_file.stat().st_size
            self.logger.info(f"✅ Successfully extracted HTML: {output_file}")
            self.logger.info(f"📊 HTML file size: {file_size:,} bytes ({file_size / 1024 / 1024:.1f} MB)")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ HTML extraction failed: {e}")
            return False
    
    def _extract_main_10k_html(self, content: str, filename: str) -> str:
        """Extract the main 10-K HTML content from SEC document"""
        import re
        from datetime import datetime
        
        # Extract metadata from SEC header
        company_name = "Unknown Company"
        accession_number = "Unknown"
        filing_date = "Unknown"
        document_type = "10-K"
        
        # Extract company name
        company_match = re.search(r'COMPANY CONFORMED NAME:\s*(.+)', content)
        if company_match:
            company_name = company_match.group(1).strip()
        
        # Extract accession number
        accession_match = re.search(r'ACCESSION NUMBER:\s*(\d{10}-\d{2}-\d{6})', content)
        if accession_match:
            accession_number = accession_match.group(1)
        
        # Extract filing date
        filing_match = re.search(r'FILED AS OF DATE:\s*(\d{8})', content)
        if filing_match:
            filing_date = filing_match.group(1)
            if len(filing_date) == 8:
                filing_date = f"{filing_date[:4]}-{filing_date[4:6]}-{filing_date[6:8]}"
        
        # Extract document type
        doc_type_match = re.search(r'CONFORMED SUBMISSION TYPE:\s*(.+)', content)
        if doc_type_match:
            document_type = doc_type_match.group(1).strip()
        
        # Find the main 10-K document (first document with TYPE=10-K)
        main_doc_match = re.search(r'<DOCUMENT>\s*<TYPE>10-K.*?<TEXT>(.*?)</TEXT>', content, re.DOTALL | re.IGNORECASE)
        
        if not main_doc_match:
            self.logger.warning("⚠️ No main 10-K document found, looking for any HTML content...")
            # Fallback: look for any HTML content in the document
            html_match = re.search(r'<TEXT>(.*?<html.*?</html>.*?)</TEXT>', content, re.DOTALL | re.IGNORECASE)
            if html_match:
                main_doc_match = html_match
            else:
                self.logger.error("❌ No HTML content found in any document section")
                return None
        
        # Extract the HTML content
        html_content = main_doc_match.group(1)
        
        # Clean up the HTML content
        cleaned_html = self._clean_sec_html_content(html_content)
        
        # Create a complete HTML document
        complete_html = self._create_complete_html_document(cleaned_html, company_name, document_type, accession_number, filing_date, filename)
        
        return complete_html
    
    def _clean_sec_html_content(self, html_content: str) -> str:
        """Clean and format SEC HTML content for better readability"""
        import re
        from bs4 import BeautifulSoup
        
        try:
            # Use BeautifulSoup to parse the HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove all XBRL-related elements
            for element in soup.find_all(['ix:header', 'ix:hidden', 'ix:nonNumeric', 'ix:numeric', 'ix:format']):
                element.decompose()
            
            # Remove script and style elements
            for element in soup.find_all(['script', 'style']):
                element.decompose()
            
            # Remove elements with display:none or visibility:hidden
            for element in soup.find_all(attrs={'style': re.compile(r'display\s*:\s*none|visibility\s*:\s*hidden', re.I)}):
                element.decompose()
            
            # Remove empty divs and spans
            for element in soup.find_all(['div', 'span']):
                if not element.get_text(strip=True) and not element.find_all():
                    element.decompose()
            
            # Clean up attributes
            for element in soup.find_all():
                # Remove XBRL and technical attributes
                attrs_to_remove = []
                for attr in element.attrs:
                    if (attr.startswith('xmlns:') or 
                        attr.startswith('ix:') or 
                        attr in ['contextRef', 'name', 'id', 'formatRef'] or
                        attr.startswith('xbrl')):
                        attrs_to_remove.append(attr)
                
                for attr in attrs_to_remove:
                    del element.attrs[attr]
                
                # Clean up style attributes
                if 'style' in element.attrs:
                    style = element.attrs['style']
                    # Remove display:none and visibility:hidden
                    style = re.sub(r'display\s*:\s*none[^;]*;?', '', style)
                    style = re.sub(r'visibility\s*:\s*hidden[^;]*;?', '', style)
                    style = re.sub(r'[;]+', ';', style).strip(';')
                    if style:
                        element.attrs['style'] = style
                    else:
                        del element.attrs['style']
            
            # Get the cleaned HTML
            cleaned_html = str(soup)
            
            # Additional cleanup with regex
            # Remove remaining XBRL tags
            cleaned_html = re.sub(r'<ix:[^>]*>', '', cleaned_html)
            cleaned_html = re.sub(r'</ix:[^>]*>', '', cleaned_html)
            
            # Remove excessive whitespace
            cleaned_html = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned_html)
            cleaned_html = re.sub(r'[ \t]+', ' ', cleaned_html)
            
            # Remove empty paragraphs and divs
            cleaned_html = re.sub(r'<p[^>]*>\s*</p>', '', cleaned_html)
            cleaned_html = re.sub(r'<div[^>]*>\s*</div>', '', cleaned_html)
            
            return cleaned_html.strip()
            
        except Exception as e:
            self.logger.warning(f"BeautifulSoup parsing failed: {e}, using regex fallback")
            # Fallback to regex-based cleaning
            # Remove XBRL tags and namespaces that clutter the HTML
            html_content = re.sub(r'<ix:[^>]*>', '', html_content)
            html_content = re.sub(r'</ix:[^>]*>', '', html_content)
            html_content = re.sub(r'xmlns:[^=]*="[^"]*"', '', html_content)
            
            # Remove style attributes that make the HTML messy
            html_content = re.sub(r'style="[^"]*"', '', html_content)
            html_content = re.sub(r'class="[^"]*"', '', html_content)
            html_content = re.sub(r'id="[^"]*"', '', html_content)
            
            # Remove script tags and their content
            html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            
            # Remove XML comments
            html_content = re.sub(r'<!--.*?-->', '', html_content, flags=re.DOTALL)
            
            # Clean up excessive whitespace
            html_content = re.sub(r'\n\s*\n\s*\n', '\n\n', html_content)
            html_content = re.sub(r'[ \t]+', ' ', html_content)
            
            return html_content.strip()
    
    def _create_complete_html_document(self, body_content: str, company_name: str, document_type: str, accession_number: str, filing_date: str, filename: str) -> str:
        """Create a complete HTML document with proper structure and styling"""
        from datetime import datetime
        
        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{company_name} - {document_type}</title>
    <style>
        body {{
            font-family: 'Times New Roman', serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            color: #333;
            background: white;
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #2c3e50;
            padding: 20px;
            margin-bottom: 30px;
            background: #f8f9fa;
        }}
        .company-name {{
            font-size: 28px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        .document-type {{
            font-size: 20px;
            color: #7f8c8d;
            margin-bottom: 15px;
        }}
        .filing-info {{
            font-size: 14px;
            color: #7f8c8d;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
        }}
        .content {{
            font-size: 12px;
            line-height: 1.5;
        }}
        .content h1, .content h2, .content h3 {{
            color: #2c3e50;
            margin-top: 20px;
            margin-bottom: 10px;
        }}
        .content h1 {{
            font-size: 18px;
            border-bottom: 2px solid #bdc3c7;
            padding-bottom: 5px;
        }}
        .content h2 {{
            font-size: 16px;
            border-bottom: 1px solid #bdc3c7;
            padding-bottom: 3px;
        }}
        .content h3 {{
            font-size: 14px;
        }}
        .content p {{
            margin-bottom: 10px;
        }}
        .content table {{
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
        }}
        .content table th, .content table td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        .content table th {{
            background-color: #f2f2f2;
            font-weight: bold;
        }}
        .content strong {{
            font-weight: bold;
            color: #2c3e50;
        }}
        .toc {{
            background: #f8f9fa;
            padding: 15px;
            margin: 20px 0;
            border-left: 4px solid #2c3e50;
        }}
        .toc h3 {{
            margin-top: 0;
            color: #2c3e50;
        }}
        .toc ul {{
            margin: 0;
            padding-left: 20px;
        }}
        .toc li {{
            margin-bottom: 5px;
        }}
        .toc a {{
            color: #2c3e50;
            text-decoration: none;
        }}
        .toc a:hover {{
            text-decoration: underline;
        }}
        @media print {{
            body {{
                margin: 15px;
            }}
            .header {{
                page-break-after: avoid;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="company-name">{company_name}</div>
        <div class="document-type">{document_type}</div>
        <div class="filing-info">
            <div><strong>Accession Number:</strong> {accession_number}</div>
            <div><strong>Filing Date:</strong> {filing_date}</div>
            <div><strong>Generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>
            <div><strong>Source:</strong> {filename}</div>
        </div>
    </div>
    
    <div class="content">
        {body_content}
    </div>
</body>
</html>"""
        
        return html_template

    def batch_convert_to_html(self, input_files: List[Path]) -> List[Path]:
        """Convert multiple files to HTML"""
        converted_files = []
        
        for input_file in input_files:
            if input_file.suffix.lower() in ['.txt', '.html']:
                # Create output file path
                output_file = input_file.parent / 'html' / f"{input_file.stem}.html"
                
                # Convert to HTML
                if self.convert_to_html(input_file, output_file):
                    converted_files.append(output_file)
                else:
                    self.logger.warning(f"Failed to convert {input_file} to HTML")
            else:
                self.logger.warning(f"Skipping unsupported file type: {input_file}")
        
        return converted_files
