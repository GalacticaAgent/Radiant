"""
论文处理服务
"""

import os
import uuid
from typing import Optional, List, Dict
from datetime import datetime
from sqlalchemy.orm import Session
import PyPDF2
from io import BytesIO
from zipfile import ZipFile
import xml.etree.ElementTree as ET
import re

from app.models.paper import Paper, PaperReview
from app.models.user import User
from app.core.config import settings


class PaperService:
    """论文处理服务类"""

    @staticmethod
    def extract_text_from_pdf(file_content: bytes) -> str:
        """
        从PDF文件中提取文本

        Args:
            file_content: PDF文件的字节内容

        Returns:
            str: 提取的文本内容
        """
        try:
            pdf_reader = PyPDF2.PdfReader(BytesIO(file_content))
            text_content = []

            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    text_content.append(text)

            return "\n\n".join(text_content)
        except Exception as e:
            raise ValueError(f"PDF解析失败: {str(e)}")

    @staticmethod
    def extract_text_from_docx(file_content: bytes) -> str:
        """
        从DOCX文件中提取文本（不依赖第三方库，解析 word/document.xml）
        """
        try:
            with ZipFile(BytesIO(file_content)) as z:
                xml_bytes = z.read("word/document.xml")
            root = ET.fromstring(xml_bytes)
            parts: List[str] = []
            for el in root.iter():
                tag = el.tag
                if tag.endswith("}t") and el.text:
                    parts.append(el.text)
                elif tag.endswith("}tab"):
                    parts.append("\t")
                elif tag.endswith("}br") or tag.endswith("}cr"):
                    parts.append("\n")
                elif tag.endswith("}p"):
                    parts.append("\n")
            text = "".join(parts)
            text = text.replace("\r\n", "\n").replace("\r", "\n")
            text = re.sub(r"\n{3,}", "\n\n", text).strip()
            return text
        except Exception as e:
            raise ValueError(f"DOCX解析失败: {str(e)}")

    @staticmethod
    def extract_docx_style_snapshot(file_content: bytes) -> Dict:
        try:
            from app.utils.docx_inspect import extract_docx_style_snapshot

            return extract_docx_style_snapshot(file_content)
        except Exception as e:
            raise ValueError(f"DOCX样式解析失败: {str(e)}")

    @staticmethod
    def extract_text_from_doc(file_content: bytes) -> str:
        try:
            from app.utils.doc_convert import convert_doc_bytes_to_docx_bytes

            docx_bytes = convert_doc_bytes_to_docx_bytes(file_content)
            return PaperService.extract_text_from_docx(docx_bytes)
        except Exception as e:
            raise ValueError(f"DOC解析失败: {str(e)}")

    @staticmethod
    def extract_doc_style_snapshot(file_content: bytes) -> Dict:
        try:
            from app.utils.doc_convert import convert_doc_bytes_to_docx_bytes

            docx_bytes = convert_doc_bytes_to_docx_bytes(file_content)
            return PaperService.extract_docx_style_snapshot(docx_bytes)
        except Exception as e:
            raise ValueError(f"DOC样式解析失败: {str(e)}")

    @staticmethod
    def extract_metadata(content: str) -> Dict:
        """
        从论文内容中提取元数据

        Args:
            content: 论文文本内容

        Returns:
            Dict: 提取的元数据
        """
        # 简单的元数据提取（可以使用更复杂的NLP方法）
        metadata = {
            "word_count": len(content.split()),
            "char_count": len(content),
            "extracted_at": datetime.utcnow().isoformat()
        }

        lines = [ln.strip() for ln in content.split("\n")]

        for ln in lines[:40]:
            if not ln:
                continue
            low = ln.lower()
            if "abstract" in low or "introduction" in low or "keywords" in low:
                continue
            if len(ln) < 12 or len(ln) > 180:
                continue
            if sum(ch.isalpha() for ch in ln) < 8:
                continue
            metadata["auto_extracted_title"] = ln[:200]
            break

        # 尝试提取摘要（通常在开头）
        abstract_start = -1
        abstract_end = -1

        for i, line in enumerate(lines):
            if 'abstract' in line.lower():
                abstract_start = i
            if abstract_start > 0 and abstract_end < 0:
                if 'introduction' in line.lower() or 'keywords' in line.lower():
                    abstract_end = i
                    break

        if abstract_start > 0 and abstract_end > abstract_start:
            abstract = '\n'.join(lines[abstract_start+1:abstract_end]).strip()
            if abstract:
                metadata["auto_extracted_abstract"] = abstract[:1000]  # 限制长度

        return metadata

    @staticmethod
    def save_paper(
        db: Session,
        user_id: str,
        filename: str,
        file_content: bytes,
        title: Optional[str] = None
    ) -> Paper:
        """
        保存上传的论文

        Args:
            db: 数据库会话
            user_id: 用户ID
            filename: 文件名
            file_content: 文件内容
            title: 论文标题（可选）

        Returns:
            Paper: 保存的论文对象
        """
        # 创建上传目录
        upload_dir = settings.UPLOAD_DIR
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)

        # 生成唯一文件名
        file_id = str(uuid.uuid4())
        file_ext = os.path.splitext(filename)[1]
        unique_filename = f"{file_id}{file_ext}"
        file_path = os.path.join(upload_dir, unique_filename)

        # 保存文件
        with open(file_path, 'wb') as f:
            f.write(file_content)

        # 提取文本内容
        content = ""
        abstract = None
        paper_metadata = {}

        if file_ext.lower() == '.pdf':
            try:
                content = PaperService.extract_text_from_pdf(file_content)
                paper_metadata = PaperService.extract_metadata(content)

                # 如果元数据中有摘要，提取出来
                if "auto_extracted_abstract" in paper_metadata:
                    abstract = paper_metadata["auto_extracted_abstract"]

            except Exception as e:
                print(f"PDF解析失败: {e}")
                paper_metadata["parse_error"] = str(e)
        elif file_ext.lower() == '.docx':
            try:
                content = PaperService.extract_text_from_docx(file_content)
                paper_metadata = PaperService.extract_metadata(content)
                if "auto_extracted_abstract" in paper_metadata:
                    abstract = paper_metadata["auto_extracted_abstract"]
            except Exception as e:
                print(f"DOCX解析失败: {e}")
                paper_metadata["parse_error"] = str(e)
        elif file_ext.lower() == '.doc':
            try:
                content = PaperService.extract_text_from_doc(file_content)
                paper_metadata = PaperService.extract_metadata(content)
                if "auto_extracted_abstract" in paper_metadata:
                    abstract = paper_metadata["auto_extracted_abstract"]
            except Exception as e:
                print(f"DOC解析失败: {e}")
                paper_metadata["parse_error"] = str(e)

        final_title = title
        if not final_title:
            extracted_title = paper_metadata.get("auto_extracted_title") if isinstance(paper_metadata, dict) else None
            if extracted_title:
                final_title = extracted_title
            else:
                final_title = filename

        # 创建数据库记录
        paper = Paper(
            user_id=uuid.UUID(user_id),
            title=final_title,
            filename=filename,
            file_path=file_path,
            file_size=len(file_content),
            content=content,
            abstract=abstract,
            paper_metadata=paper_metadata,
            version=1
        )

        db.add(paper)
        db.commit()
        db.refresh(paper)

        return paper

    @staticmethod
    def get_paper(db: Session, paper_id: str, user_id: str) -> Optional[Paper]:
        """
        获取论文（验证所有权）

        Args:
            db: 数据库会话
            paper_id: 论文ID
            user_id: 用户ID

        Returns:
            Optional[Paper]: 论文对象
        """
        return db.query(Paper).filter(
            Paper.id == uuid.UUID(paper_id),
            Paper.user_id == uuid.UUID(user_id)
        ).first()

    @staticmethod
    def get_user_papers(
        db: Session,
        user_id: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[Paper]:
        """
        获取用户的所有论文

        Args:
            db: 数据库会话
            user_id: 用户ID
            skip: 跳过数量
            limit: 限制数量

        Returns:
            List[Paper]: 论文列表
        """
        return db.query(Paper).filter(
            Paper.user_id == uuid.UUID(user_id)
        ).order_by(Paper.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def create_new_version(
        db: Session,
        parent_paper_id: str,
        user_id: str,
        filename: str,
        file_content: bytes,
        title: Optional[str] = None
    ) -> Paper:
        """
        创建论文新版本

        Args:
            db: 数据库会话
            parent_paper_id: 父版本ID
            user_id: 用户ID
            filename: 文件名
            file_content: 文件内容
            title: 标题

        Returns:
            Paper: 新版本论文对象
        """
        # 获取父版本
        parent = PaperService.get_paper(db, parent_paper_id, user_id)
        if not parent:
            raise ValueError("父版本论文不存在")

        # 保存新版本（与保存论文类似）
        paper = PaperService.save_paper(db, user_id, filename, file_content, title)

        # 设置版本信息
        paper.version = parent.version + 1
        paper.parent_id = uuid.UUID(parent_paper_id)

        db.commit()
        db.refresh(paper)

        return paper

    @staticmethod
    def get_paper_versions(
        db: Session,
        paper_id: str,
        user_id: str
    ) -> List[Paper]:
        """
        获取论文的所有版本

        Args:
            db: 数据库会话
            paper_id: 论文ID
            user_id: 用户ID

        Returns:
            List[Paper]: 版本列表
        """
        # 先找到根论文
        current = PaperService.get_paper(db, paper_id, user_id)
        if not current:
            return []

        # 如果有父版本，一直往上找
        while current.parent_id:
            current = db.query(Paper).filter(Paper.id == current.parent_id).first()
            if not current:
                break

        root_id = current.id if current else uuid.UUID(paper_id)

        # 获取所有版本（包括根和所有子版本）
        versions = db.query(Paper).filter(
            (Paper.id == root_id) | (Paper.parent_id == root_id),
            Paper.user_id == uuid.UUID(user_id)
        ).order_by(Paper.version.asc()).all()

        return versions

    @staticmethod
    def save_review(
        db: Session,
        paper_id: str,
        user_id: str,
        reviewer_id: Optional[str],
        reviewer_name: str,
        reviewer_profile: str,
        review_content: str,
        rating: Optional[int] = None,
        review_metadata: Optional[Dict] = None,
        strengths: Optional[List[str]] = None,
        weaknesses: Optional[List[str]] = None,
        suggestions: Optional[List[str]] = None
    ) -> PaperReview:
        """
        保存审稿意见

        Args:
            db: 数据库会话
            paper_id: 论文ID
            user_id: 用户ID
            reviewer_id: 审稿人ID
            reviewer_name: 审稿人姓名
            reviewer_profile: 审稿人画像
            review_content: 审稿内容
            rating: 评分
            strengths: 优点列表
            weaknesses: 缺点列表
            suggestions: 建议列表

        Returns:
            PaperReview: 审稿意见对象
        """
        review = PaperReview(
            paper_id=uuid.UUID(paper_id),
            user_id=uuid.UUID(user_id),
            reviewer_id=reviewer_id,
            reviewer_name=reviewer_name,
            reviewer_profile=reviewer_profile,
            review_content=review_content,
            rating=rating,
            review_metadata=review_metadata,
            strengths=strengths,
            weaknesses=weaknesses,
            suggestions=suggestions
        )

        db.add(review)
        db.commit()
        db.refresh(review)

        return review

    @staticmethod
    def get_paper_reviews(
        db: Session,
        paper_id: str,
        user_id: str
    ) -> List[PaperReview]:
        """
        获取论文的所有审稿意见

        Args:
            db: 数据库会话
            paper_id: 论文ID
            user_id: 用户ID

        Returns:
            List[PaperReview]: 审稿意见列表
        """
        return db.query(PaperReview).filter(
            PaperReview.paper_id == uuid.UUID(paper_id),
            PaperReview.user_id == uuid.UUID(user_id)
        ).order_by(PaperReview.created_at.desc()).all()
