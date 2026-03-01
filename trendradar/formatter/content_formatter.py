#!/usr/bin/env python3
"""
内容格式化器
将文章内容转换为各平台适配的格式
"""

import json
import logging
import re
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ContentFormatter:
    """内容格式化器"""
    
    def __init__(self):
        """初始化格式化器"""
        self.platform_formats = {
            "wechat": {
                "name": "微信公众号",
                "features": ["富文本", "图片居中", "段落间距", "小标题加粗"],
                "max_length": 20000,
                "allowed_tags": ["h1", "h2", "h3", "p", "strong", "em", "ul", "li", "blockquote"],
                "style_rules": {
                    "heading_prefix": "# ",
                    "subheading_prefix": "## ",
                    "paragraph_spacing": "\n\n",
                    "image_wrap": "![图片描述](图片URL)"
                }
            },
            "zhihu": {
                "name": "知乎",
                "features": ["Markdown", "代码块", "引用块", "表格支持"],
                "max_length": 40000,
                "allowed_tags": ["h1", "h2", "h3", "p", "code", "blockquote", "table", "img"],
                "style_rules": {
                    "heading_prefix": "# ",
                    "subheading_prefix": "## ",
                    "code_block": "```\n代码内容\n```",
                    "quote_prefix": "> "
                }
            },
            "xiaohongshu": {
                "name": "小红书",
                "features": ["简短精炼", "emoji表情", "话题标签", "图片为主"],
                "max_length": 1000,
                "allowed_tags": ["p", "strong", "emoji", "hashtag"],
                "style_rules": {
                    "emoji_frequency": 0.1,  # 10%的句子带emoji
                    "hashtag_count": 3,
                    "paragraph_max_lines": 4
                }
            },
            "toutiao": {
                "name": "头条号",
                "features": ["吸引眼球", "段落简短", "重点加粗", "互动引导"],
                "max_length": 5000,
                "allowed_tags": ["h1", "h2", "p", "strong", "question"],
                "style_rules": {
                    "opening_hook": True,
                    "interactive_questions": 2,
                    "bold_keywords": True
                }
            },
            "blog": {
                "name": "个人博客",
                "features": ["完整Markdown", "TOC目录", "代码高亮", "标签分类"],
                "max_length": None,  # 无限制
                "allowed_tags": "all",
                "style_rules": {
                    "toc": True,
                    "code_highlight": True,
                    "tags": True,
                    "categories": True
                }
            }
        }
    
    def format_for_platform(self, article: Dict[str, Any], platform: str = "wechat") -> Dict[str, Any]:
        """
        为特定平台格式化文章
        
        Args:
            article: 文章内容
            platform: 目标平台
            
        Returns:
            格式化后的内容
        """
        try:
            logger.info(f"开始格式化，平台: {platform}")
            
            # 检查平台支持
            if platform not in self.platform_formats:
                logger.warning(f"平台 {platform} 不支持，使用默认格式")
                platform = "wechat"
            
            platform_config = self.platform_formats[platform]
            
            # 格式化内容
            formatted = {
                "platform": platform,
                "platform_name": platform_config["name"],
                "formatted_at": datetime.now().isoformat(),
                "metadata": article.get("metadata", {}).copy(),
                "content": {
                    "original_title": article["metadata"].get("title", ""),
                    "formatted_title": "",
                    "formatted_content": "",
                    "summary": "",
                    "tags": [],
                    "images": [],
                    "word_count": 0,
                    "format_validation": {
                        "max_length_ok": True,
                        "tag_compliance": True,
                        "style_requirements_met": True
                    }
                }
            }
            
            # 格式化标题
            formatted["content"]["formatted_title"] = self._format_title(
                article["metadata"].get("title", ""),
                platform
            )
            
            # 格式化正文内容
            formatted["content"]["formatted_content"] = self._format_content(
                article, platform
            )
            
            # 生成摘要
            formatted["content"]["summary"] = self._generate_summary(
                article, platform
            )
            
            # 生成标签
            formatted["content"]["tags"] = self._generate_tags(
                article, platform
            )
            
            # 验证格式
            self._validate_format(formatted, platform_config)
            
            # 统计字数
            formatted["content"]["word_count"] = self._count_formatted_words(
                formatted["content"]["formatted_content"]
            )
            
            logger.info(f"格式化完成，平台: {platform}")
            return formatted
            
        except Exception as e:
            logger.error(f"格式化失败: {e}")
            raise
    
    def _format_title(self, title: str, platform: str) -> str:
        """格式化标题"""
        if platform == "xiaohongshu":
            # 小红书标题需要吸引眼球
            if len(title) > 20:
                title = title[:20] + "..."
            return f"🔥 {title}"
        
        elif platform == "toutiao":
            # 头条号标题需要吸引点击
            if not title.endswith("？") and not title.endswith("！"):
                title = title + "？"
            return title
        
        else:
            # 其他平台保持原样
            return title
    
    def _format_content(self, article: Dict[str, Any], platform: str) -> str:
        """格式化正文内容"""
        content_parts = []
        
        # 添加引言
        intro = article["content"].get("introduction", "")
        if intro:
            content_parts.append(self._format_paragraph(intro, platform))
        
        # 添加各章节
        sections = article["content"].get("sections", [])
        for section in sections:
            if isinstance(section, dict):
                section_content = section.get("content", "")
                if section_content:
                    content_parts.append(self._format_section(section_content, platform, section.get("title", "")))
        
        # 添加结论
        conclusion = article["content"].get("conclusion", "")
        if conclusion:
            content_parts.append(self._format_paragraph(conclusion, platform))
        
        # 平台特定处理
        formatted = "\n\n".join(content_parts)
        
        if platform == "xiaohongshu":
            formatted = self._format_for_xiaohongshu(formatted)
        elif platform == "toutiao":
            formatted = self._format_for_toutiao(formatted)
        elif platform == "zhihu":
            formatted = self._format_for_zhihu(formatted)
        
        return formatted
    
    def _format_paragraph(self, text: str, platform: str) -> str:
        """格式化段落"""
        # 基本清理
        text = re.sub(r'\n{3,}', '\n\n', text.strip())
        
        if platform == "xiaohongshu":
            # 小红书：短段落，加emoji
            paragraphs = text.split('\n\n')
            formatted_paragraphs = []
            for i, para in enumerate(paragraphs):
                if i % 3 == 0 and len(para) < 100:
                    # 每3段加一个emoji
                    emoji = self._get_random_emoji()
                    para = f"{emoji} {para}"
                formatted_paragraphs.append(para)
            return '\n\n'.join(formatted_paragraphs)
        
        elif platform == "toutiao":
            # 头条：加粗关键词，添加互动
            lines = text.split('\n')
            formatted_lines = []
            for line in lines:
                # 简单加粗处理
                if len(line) > 50:
                    words = line.split()
                    if len(words) > 10:
                        # 加粗中间的关键词
                        mid_idx = len(words) // 2
                        words[mid_idx] = f"**{words[mid_idx]}**"
                        line = ' '.join(words)
                formatted_lines.append(line)
            
            # 添加互动问题
            if len(formatted_lines) >= 3:
                questions = [
                    "你怎么看？",
                    "对此你有什么想法？",
                    "欢迎在评论区讨论！"
                ]
                import random
                formatted_lines.append(f"\n{random.choice(questions)}")
            
            return '\n'.join(formatted_lines)
        
        else:
            # 其他平台保持原样
            return text
    
    def _format_section(self, section_content: str, platform: str, section_title: str = "") -> str:
        """格式化章节"""
        if platform in ["wechat", "zhihu", "blog"]:
            # 这些平台支持完整的Markdown标题
            if section_title and section_content.startswith('#'):
                # 已经是Markdown标题格式
                return section_content
            elif section_title:
                return f"## {section_title}\n\n{section_content}"
            else:
                return section_content
        else:
            # 其他平台可能不需要标题
            return section_content
    
    def _format_for_xiaohongshu(self, content: str) -> str:
        """为小红书格式化"""
        # 添加话题标签
        tags = ["#AI技术", "#科技生活", "#知识分享"]
        tag_line = " ".join(tags[:3])
        
        # 限制长度
        if len(content) > 800:
            content = content[:800] + "..."
        
        return f"{content}\n\n{tag_line}"
    
    def _format_for_toutiao(self, content: str) -> str:
        """为头条号格式化"""
        # 添加吸引人的开头
        hooks = [
            "最近这个话题很火，一起来看看！",
            "深度分析，建议收藏！",
            "一文读懂，不再困惑！"
        ]
        import random
        hook = random.choice(hooks)
        
        return f"{hook}\n\n{content}"
    
    def _format_for_zhihu(self, content: str) -> str:
        """为知乎格式化"""
        # 知乎喜欢详细的、有深度的内容
        # 添加适当的代码块和引用格式
        content = re.sub(r'```(.*?)```', self._format_code_block, content, flags=re.DOTALL)
        content = re.sub(r'>(.*?)$', r'> \1', content, flags=re.MULTILINE)
        
        return content
    
    def _format_code_block(self, match) -> str:
        """格式化代码块"""
        code = match.group(1).strip()
        return f"```\n{code}\n```"
    
    def _get_random_emoji(self) -> str:
        """获取随机emoji"""
        emojis = ["✨", "🔥", "💡", "🚀", "📚", "👀", "💪", "🌟"]
        import random
        return random.choice(emojis)
    
    def _generate_summary(self, article: Dict[str, Any], platform: str) -> str:
        """生成摘要"""
        intro = article["content"].get("introduction", "")
        topic = article["metadata"].get("topic", "")
        
        if platform == "xiaohongshu":
            # 小红书：简短吸引人
            if len(intro) > 100:
                summary = intro[:100] + "..."
            else:
                summary = intro
            return summary
        
        elif platform == "toutiao":
            # 头条：问题引导式
            return f"关于{topic}，这些要点你需要了解："
        
        else:
            # 其他平台：使用引言前几句
            sentences = intro.split('。')
            if len(sentences) > 1:
                return sentences[0] + "。"
            else:
                return intro[:150] + "..."
    
    def _generate_tags(self, article: Dict[str, Any], platform: str) -> List[str]:
        """生成标签"""
        keywords = article["metadata"].get("keywords", [])
        topic = article["metadata"].get("topic", "")
        
        tags = []
        
        # 基础标签
        if topic:
            tags.append(topic)
        
        # 关键词标签
        tags.extend(keywords[:3])
        
        # 平台特定标签
        if platform == "xiaohongshu":
            tags.extend(["种草", "干货分享", "学习笔记"])
        elif platform == "zhihu":
            tags.extend(["深度分析", "知识分享", "行业观察"])
        elif platform == "toutiao":
            tags.extend(["热点解读", "趋势分析", "实用指南"])
        
        # 去重并限制数量
        tags = list(dict.fromkeys(tags))[:5]
        
        return tags
    
    def _validate_format(self, formatted: Dict[str, Any], platform_config: Dict[str, Any]):
        """验证格式要求"""
        content = formatted["content"]["formatted_content"]
        max_length = platform_config.get("max_length")
        
        if max_length and len(content) > max_length:
            formatted["content"]["format_validation"]["max_length_ok"] = False
            logger.warning(f"内容超过平台最大长度限制: {len(content)} > {max_length}")
    
    def _count_formatted_words(self, content: str) -> int:
        """统计格式化后的字数"""
        # 去除Markdown标记
        clean_content = re.sub(r'[#*`\-\[\]\(\)]', '', content)
        # 统计中文字数
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', clean_content)
        return len(chinese_chars)
    
    def save_formatted_content(self, formatted: Dict[str, Any], filepath: str) -> bool:
        """保存格式化后的内容"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(formatted, f, ensure_ascii=False, indent=2)
            
            # 同时保存为平台适配的文本格式
            text_filepath = filepath.replace('.json', '.txt')
            self._save_as_platform_text(formatted, text_filepath)
            
            logger.info(f"格式化内容已保存: {filepath}")
            return True
        except Exception as e:
            logger.error(f"格式化内容保存失败: {e}")
            return False
    
    def _save_as_platform_text(self, formatted: Dict[str, Any], filepath: str):
        """保存为平台适配的文本格式"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                platform = formatted.get("platform", "unknown")
                platform_name = formatted.get("platform_name", "")
                
                f.write(f"平台: {platform_name}\n")
                f.write(f"生成时间: {formatted.get('formatted_at', '')}\n")
                f.write("=" * 50 + "\n\n")
                
                f.write(f"标题: {formatted['content']['formatted_title']}\n\n")
                f.write(f"摘要: {formatted['content']['summary']}\n\n")
                f.write("正文:\n")
                f.write(formatted['content']['formatted_content'])
                f.write("\n\n")
                
                if formatted['content']['tags']:
                    f.write(f"标签: {', '.join(formatted['content']['tags'])}\n")
                
                f.write(f"\n字数: {formatted['content']['word_count']}\n")
            
            logger.info(f"平台文本已保存: {filepath}")
        except Exception as e:
            logger.error(f"平台文本保存失败: {e}")


# 使用示例
if __name__ == "__main__":
    # 测试数据
    test_article = {
        "metadata": {
            "title": "AI大模型技术突破分析与未来展望",
            "topic": "AI大模型",
            "keywords": ["AI", "大模型", "深度学习"],
            "generated_at": "2026-02-28T22:55:00"
        },
        "content": {
            "introduction": "随着AI技术的快速发展，大模型已成为当前行业关注的重点。",
            "sections": [
                {
                    "title": "技术背景",
                    "content": "近年来，transformer架构的出现彻底改变了自然语言处理领域。"
                },
                {
                    "title": "应用场景",
                    "content": "大模型在多个领域展现出强大能力，包括代码生成、内容创作等。"
                }
            ],
            "conclusion": "总体来看，AI大模型技术将继续快速发展，为各行各业带来变革。"
        }
    }
    
    formatter = ContentFormatter()
    
    # 测试不同平台格式化
    platforms = ["wechat", "zhihu", "xiaohongshu", "toutiao"]
    
    for platform in platforms:
        formatted = formatter.format_for_platform(test_article, platform)
        print(f"\n=== {platform.upper()} 格式 ===")
        print(f"标题: {formatted['content']['formatted_title']}")
        print(f"字数: {formatted['content']['word_count']}")
        print(f"标签: {formatted['content']['tags']}")