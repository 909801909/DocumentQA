from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.enums import TA_CENTER
from docx import Document
from io import BytesIO
import base64
from typing import Dict, List

class ReportService:
    """
    报告生成服务
    支持生成Word和PDF格式的报告
    """
    
    def generate_pdf_report(self, content: Dict) -> bytes:
        """
        生成PDF格式的报告
        
        Args:
            content: 报告内容字典
            
        Returns:
            PDF文件的字节数据
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # 标题样式
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            alignment=TA_CENTER,
            fontSize=18,
            spaceAfter=30,
        )
        
        # 添加标题
        title = content.get("title", "分析报告")
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # 添加摘要
        if "summary" in content:
            story.append(Paragraph("摘要", styles['Heading2']))
            story.append(Paragraph(content["summary"], styles['Normal']))
            story.append(Spacer(1, 0.2*inch))
        
        # 添加主要内容
        if "sections" in content:
            for section in content["sections"]:
                story.append(Paragraph(section.get("title", ""), styles['Heading2']))
                story.append(Paragraph(section.get("content", ""), styles['Normal']))
                story.append(Spacer(1, 0.2*inch))
        
        # 添加图表（如果有）
        if "graph_image" in content and content["graph_image"]:
            # 解码base64图像
            image_data = base64.b64decode(content["graph_image"])
            image_buffer = BytesIO(image_data)
            story.append(Image(image_buffer, width=4*inch, height=3*inch))
            story.append(Spacer(1, 0.2*inch))
        
        # 生成PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def generate_word_report(self, content: Dict) -> bytes:
        """
        生成Word格式的报告
        
        Args:
            content: 报告内容字典
            
        Returns:
            Word文件的字节数据
        """
        doc = Document()
        
        # 添加标题
        title = content.get("title", "分析报告")
        doc.add_heading(title, 0)
        
        # 添加摘要
        if "summary" in content:
            doc.add_heading('摘要', level=1)
            doc.add_paragraph(content["summary"])
        
        # 添加主要内容
        if "sections" in content:
            for section in content["sections"]:
                doc.add_heading(section.get("title", ""), level=1)
                doc.add_paragraph(section.get("content", ""))
        
        # 保存到字节流
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()
    
    def generate_report(self, format: str, content: Dict) -> bytes:
        """
        根据指定格式生成报告
        
        Args:
            format: 报告格式 ('pdf' 或 'word')
            content: 报告内容
            
        Returns:
            报告文件的字节数据
        """
        if format.lower() == 'pdf':
            return self.generate_pdf_report(content)
        elif format.lower() == 'word':
            return self.generate_word_report(content)
        else:
            raise ValueError("不支持的报告格式。支持的格式: 'pdf', 'word'")