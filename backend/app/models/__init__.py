"""
Models 包初始化
导入所有数据库模型
"""

from app.models.user import User
from app.models.conversation import Conversation, ChatSession
from app.models.paper import Paper, PaperReview
from app.models.reviewer import VirtualReviewer, PaperReviewerCandidate
from app.models.kb import Author, PaperAuthor, Topic, PaperTopic, ExternalPaper, Embedding, CrawlJob, CrawlEvent
from app.models.format_review import FormatReviewSession, FormatReviewTask, FormatReviewHistory, FormatReviewUpload, FormatReviewFixTask, DownloadToken
from app.models.format_rule import FormatRule, FormatRuleVersion, FormatRuleFile

__all__ = [
    "User",
    "Conversation",
    "ChatSession",
    "Paper",
    "PaperReview",
    "VirtualReviewer",
    "PaperReviewerCandidate",
    "Author",
    "PaperAuthor",
    "Topic",
    "PaperTopic",
    "ExternalPaper",
    "Embedding",
    "CrawlJob",
    "CrawlEvent",
    "FormatReviewSession",
    "FormatReviewTask",
    "FormatReviewHistory",
    "FormatReviewUpload",
    "FormatReviewFixTask",
    "DownloadToken",
    "FormatRule",
    "FormatRuleVersion",
    "FormatRuleFile",
]
