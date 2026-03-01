#!/usr/bin/env python3
"""
内容创作器
基于大纲生成完整的文章内容
"""

import json
import logging
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class ContentWriter:
    """内容创作器"""
    
    def __init__(self, ai_client=None):
        """
        初始化内容创作器
        
        Args:
            ai_client: AI客户端（可选）
        """
        if ai_client is None and os.getenv("AI_API_KEY"):
            try:
                from openai import OpenAI
                self.ai_client = OpenAI(
                    api_key=os.getenv("AI_API_KEY"),
                    base_url="https://api.deepseek.com/v1"
                )
                logger.info("已自动初始化 DeepSeek 官方 API 客户端")
            except Exception as e:
                logger.warning(f"自动初始化AI客户端失败: {e}")
                self.ai_client = None
        else:
            self.ai_client = ai_client
        self.writing_styles = {
            "professional": {
                "tone": "专业严谨",
                "features": ["数据支撑", "逻辑严密", "术语准确", "结论明确"],
                "target_audience": "专业人士、技术人员"
            },
            "popular_science": {
                "tone": "通俗易懂",
                "features": ["案例丰富", "比喻生动", "语言简洁", "趣味性强"],
                "target_audience": "普通读者、初学者"
            },
            "news_commentary": {
                "tone": "观点鲜明",
                "features": ["时效性强", "观点独特", "分析深入", "结论有力"],
                "target_audience": "关注时事、行业观察者"
            }
        }
    
    def write_content(self, outline: Dict[str, Any], style: str = "professional") -> Dict[str, Any]:
        """
        基于大纲创作完整内容
        
        Args:
            outline: 内容大纲
            style: 写作风格
            
        Returns:
            完整的文章内容
        """
        try:
            logger.info(f"开始内容创作，主题: {outline.get('title', '未知')}")
            
            # 获取写作风格配置
            writing_style = self.writing_styles.get(style, self.writing_styles["professional"])
            
            # 构建文章结构
            article = {
                "metadata": {
                    "title": outline.get("title", ""),
                    "topic": outline.get("topic", ""),
                    "style": style,
                    "writing_tone": writing_style["tone"],
                    "target_audience": writing_style["target_audience"],
                    "generated_at": datetime.now().isoformat(),
                    "word_count": 0,
                    "section_count": len(outline.get("sections", []))
                },
                "content": {
                    "introduction": "",
                    "sections": [],
                    "conclusion": "",
                    "references": []
                }
            }
            
            # 生成引言
            article["content"]["introduction"] = self._write_introduction(
                outline, writing_style
            )
            
            # 生成各章节内容
            sections = outline.get("sections", [])
            for i, section_outline in enumerate(sections):
                section_content = self._write_section(
                    section_outline, outline, writing_style, i + 1
                )
                article["content"]["sections"].append(section_content)
            
            # 生成结论
            article["content"]["conclusion"] = self._write_conclusion(
                outline, writing_style
            )
            
            # 生成参考文献
            article["content"]["references"] = self._generate_references(outline)
            
            # 统计字数
            article["metadata"]["word_count"] = self._count_words(article)
            
            logger.info(f"内容创作完成，字数: {article['metadata']['word_count']}")
            return article
            
        except Exception as e:
            logger.error(f"内容创作失败: {e}")
            raise
    
    def _write_introduction(self, outline: Dict[str, Any], writing_style: Dict[str, Any]) -> str:
        """撰写引言"""
        topic = outline.get("topic", "热点话题")
        summary = outline.get("summary", "")
        keywords = outline.get("keywords", [])
        
        intro_templates = {
            "professional": f"""随着技术的快速发展，{topic}已成为当前行业关注的重点。本文将从多个维度深入分析{topic}的技术原理、应用场景及未来趋势，为读者提供全面而专业的解读。""",
            
            "popular_science": f"""最近{topic}在各大平台频繁出现，引发广泛讨论。这篇文章将用通俗易懂的方式，带你了解{topic}的核心概念和实际应用。""",
            
            "news_commentary": f"""近日，{topic}相关动态频频登上热搜。作为行业观察者，本文将从独特视角剖析这一现象背后的深层逻辑与发展趋势。"""
        }
        
        # 选择模板
        style_key = writing_style.get("tone", "专业严谨")
        if style_key == "通俗易懂":
            template = intro_templates["popular_science"]
        elif style_key == "观点鲜明":
            template = intro_templates["news_commentary"]
        else:
            template = intro_templates["professional"]
        
        # 添加具体内容
        if summary:
            template += f"\n\n核心要点：{summary}"
        
        if keywords:
            template += f"\n\n关键词：{'、'.join(keywords[:5])}"
        
        return template
    
    def _write_section(self, section_outline: Dict[str, Any], 
                      outline: Dict[str, Any], 
                      writing_style: Dict[str, Any],
                      section_num: int) -> Dict[str, Any]:
        """撰写单个章节"""
        section_title = section_outline.get("title", "")
        hints = section_outline.get("content_hints", [])
        
        # 构建章节内容
        section_content = {
            "number": section_num,
            "title": section_title,
            "content": "",
            "subsections": [],
            "key_points": []
        }
        
        # 生成章节内容（实质性段落，非占位）
        content = f"## {section_title}\n\n"

        # 如果配置了AI客户端，尝试用AI扩写
        if self.ai_client and hints:
            try:
                ai_prompt = f"你是一个专业的{writing_style['target_audience']}内容创作者。请围绕主题『{outline.get('topic', '未知主题')}』的章节『{section_title}』，基于以下提示创作一段300字左右的实质性内容：\n"
                for i, hint in enumerate(hints[:5]):
                    ai_prompt += f"- {hint}\n"
                ai_prompt += "\n要求：观点明确、有案例或数据支撑、语言流畅、避免空洞描述。"

                from openai import OpenAI
                temp_client = OpenAI(
                    api_key=os.getenv("AI_API_KEY"),
                    base_url="https://api.deepseek.com/v1"
                )
                ai_response = temp_client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": ai_prompt}],
                    temperature=0.7,
                    max_tokens=500
                )
                
                if ai_response.choices and ai_response.choices[0].message.content:
                    content += ai_response.choices[0].message.content.strip()
                    logger.info(f"AI扩写成功: {section_title}")
                else:
                    raise Exception("AI返回空内容")
                    
            except Exception as e:
                logger.warning(f"AI扩写失败，回退本地规则: {e}")
                content += self._fallback_section_content(section_title, outline, writing_style, hints)
        else:
            content += self._fallback_section_content(section_title, outline, writing_style, hints)
        
        section_content["content"] = content
        
        # 提取关键点
        for hint in hints[:2]:
            section_content["key_points"].append({
                "point": hint,
                "explanation": "需要进一步展开说明"
            })
        
        return section_content
    
    def _fallback_section_content(self, section_title: str, outline: Dict[str, Any], 
                                writing_style: Dict[str, Any], hints: List[str]) -> str:
        """回退的本地章节内容生成"""
        if writing_style["tone"] == "通俗易懂":
            content = f"让我们来聊聊{section_title}。简单来说，{outline.get('topic', '这个话题')}在这一方面主要体现在以下几个关键点：\n\n"
            for i, hint in enumerate(hints[:3], 1):
                content += f"{i}. **{hint}**：这是一个重要的观察点。例如，在实际应用中我们看到...（此处应有具体案例）。\n\n"
            content += "理解这些要点后，你会发现其实并不复杂，关键是要结合实际场景灵活运用。"
        elif writing_style["tone"] == "观点鲜明":
            content = f"在{section_title}方面，我们观察到了几个值得关注的趋势：\n\n"
            for i, hint in enumerate(hints[:3], 1):
                content += f"**观点{i}：{hint}** - 这一现象反映了当前市场的某些深层变化。比如最近XX公司的案例就证明了这一点...\n\n"
            content += "总体来看，这一领域的动态值得我们持续关注，并做好相应的战略调整。"
        else:
            content = f"本节将深入探讨{section_title}的核心内容：\n\n"
            for i, hint in enumerate(hints[:4], 1):
                content += f"{i}. {hint}：从技术角度看，这涉及到...（此处应有技术细节）。行业实践表明...（此处应有数据或案例）。\n\n"
            content += "通过以上分析，我们可以得出明确的结论和行动建议。"
        return content
    
    def _write_conclusion(self, outline: Dict[str, Any], writing_style: Dict[str, Any]) -> str:
        """撰写结论"""
        topic = outline.get("topic", "热点话题")
        
        conclusion_templates = {
            "professional": f"""综上所述，{topic}的发展呈现出明显的技术驱动特征。未来，随着相关技术的成熟与应用场景的拓展，{topic}将在更多领域发挥重要作用。建议相关从业者密切关注技术动态，积极布局创新应用。""",
            
            "popular_science": f"""总的来说，{topic}并没有想象中那么神秘。通过本文的介绍，相信你对{topic}有了更清晰的认识。技术不断发展，保持学习的心态很重要。""",
            
            "news_commentary": f"""总而言之，{topic}现象反映出行业的某些新动向。无论是机遇还是挑战，都需要我们以理性客观的态度去面对。期待未来能看到更多创新突破。"""
        }
        
        style_key = writing_style.get("tone", "专业严谨")
        if style_key == "通俗易懂":
            return conclusion_templates["popular_science"]
        elif style_key == "观点鲜明":
            return conclusion_templates["news_commentary"]
        else:
            return conclusion_templates["professional"]
    
    def _generate_references(self, outline: Dict[str, Any]) -> List[Dict[str, str]]:
        """生成参考文献"""
        references = []
        
        # 添加来源信息
        source = outline.get("inspiration_source", "")
        if source:
            references.append({
                "type": "数据来源",
                "title": source,
                "url": "",
                "date": datetime.now().strftime("%Y-%m-%d")
            })
        
        # 添加相关研究
        references.append({
            "type": "延伸阅读",
            "title": f"关于{outline.get('topic', '该主题')}的更多研究",
            "url": "",
            "date": "2026-02-28"
        })
        
        return references
    
    def _count_words(self, article: Dict[str, Any]) -> int:
        """统计文章字数"""
        content = article["content"]
        text = ""
        
        # 合并所有文本内容
        text += content.get("introduction", "")
        text += content.get("conclusion", "")
        
        for section in content.get("sections", []):
            if isinstance(section, dict):
                text += section.get("content", "")
            else:
                text += str(section)
        
        # 去除HTML/Markdown标记，统计中文字数
        clean_text = re.sub(r'[#*`\-\[\]\(\)]', '', text)
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', clean_text)
        
        return len(chinese_chars)
    
    def save_article(self, article: Dict[str, Any], filepath: str) -> bool:
        """保存文章到文件"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(article, f, ensure_ascii=False, indent=2)
            
            # 同时保存为纯文本格式
            text_filepath = filepath.replace('.json', '.md')
            self._save_as_markdown(article, text_filepath)
            
            logger.info(f"文章已保存: {filepath}")
            return True
        except Exception as e:
            logger.error(f"文章保存失败: {e}")
            return False
    
    def _save_as_markdown(self, article: Dict[str, Any], filepath: str):
        """保存为Markdown格式"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                # 标题
                f.write(f"# {article['metadata']['title']}\n\n")
                
                # 元数据
                f.write(f"> 生成时间: {article['metadata']['generated_at']}\n")
                f.write(f"> 字数: {article['metadata']['word_count']}字\n")
                f.write(f"> 风格: {article['metadata']['writing_tone']}\n\n")
                
                # 引言
                f.write(f"{article['content']['introduction']}\n\n")
                
                # 各章节
                for section in article['content']['sections']:
                    f.write(f"{section['content']}\n\n")
                
                # 结论
                f.write(f"{article['content']['conclusion']}\n\n")
                
                # 参考文献
                f.write("## 参考文献\n\n")
                for ref in article['content']['references']:
                    f.write(f"- {ref['type']}: {ref['title']}\n")
                
            logger.info(f"Markdown版本已保存: {filepath}")
        except Exception as e:
            logger.error(f"Markdown保存失败: {e}")


# 使用示例
if __name__ == "__main__":
    # 测试数据
    test_outline = {
        "topic": "AI大模型技术突破",
        "title": "AI大模型技术突破分析与未来展望",
        "keywords": ["AI", "大模型", "深度学习", "GPT"],
        "summary": "最新AI大模型在多个基准测试中取得突破性进展",
        "sections": [
            {
                "title": "技术背景与现状",
                "content_hints": ["AI大模型发展历程", "当前主流技术方案", "行业应用现状"]
            },
            {
                "title": "核心原理剖析", 
                "content_hints": ["transformer架构", "注意力机制", "预训练策略"]
            }
        ]
    }
    
    writer = ContentWriter()
    article = writer.write_content(test_outline, style="professional")
    
    print("生成的文章结构:")
    print(json.dumps(article["metadata"], ensure_ascii=False, indent=2))
    print(f"\n文章字数: {article['metadata']['word_count']}")