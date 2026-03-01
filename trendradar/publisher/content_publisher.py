#!/usr/bin/env python3
"""
内容发布器
将格式化后的内容发布到多个平台
"""

import json
import logging
import os
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import requests

logger = logging.getLogger(__name__)


class ContentPublisher:
    """多平台内容发布器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化发布器
        
        Args:
            config_path: 配置文件路径（可选）
        """
        self.config_path = config_path
        self.platform_clients = {}
        self.publish_history = []
        
        # 平台配置模板
        self.platform_configs = {
            "wechat": {
                "name": "微信公众号",
                "api_base": "https://api.weixin.qq.com",
                "required_params": ["access_token", "article_data"],
                "publish_method": "api",
                "rate_limit": 10,  # 每天发布限制
                "enabled": False  # 默认未启用
            },
            "zhihu": {
                "name": "知乎",
                "api_base": "https://www.zhihu.com/api",
                "required_params": ["title", "content", "topics"],
                "publish_method": "api",
                "rate_limit": 5,
                "enabled": False
            },
            "xiaohongshu": {
                "name": "小红书",
                "api_base": "https://edith.xiaohongshu.com/api",
                "required_params": ["title", "content", "images"],
                "publish_method": "webhook",
                "rate_limit": 3,
                "enabled": False
            },
            "toutiao": {
                "name": "头条号",
                "api_base": "https://mp.toutiao.com/api",
                "required_params": ["title", "content", "category"],
                "publish_method": "api",
                "rate_limit": 10,
                "enabled": False
            },
            "feishu": {
                "name": "飞书",
                "api_base": "https://open.feishu.cn/open-apis",
                "required_params": ["title", "content", "receive_id"],
                "publish_method": "webhook",
                "rate_limit": 100,
                "enabled": True  # 飞书已配置
            },
            "file": {
                "name": "本地文件",
                "api_base": None,
                "required_params": ["filepath"],
                "publish_method": "local",
                "rate_limit": None,
                "enabled": True  # 文件保存始终启用
            }
        }
        
        # 加载配置
        self._load_config()
        
        # 初始化发布历史
        self.history_file = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "output",
            "publish_history.json"
        )
        self._load_history()
    
    def _load_config(self):
        """加载配置文件"""
        if self.config_path and os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 更新平台配置（兼容两种结构：root.platforms 或 modules.publisher.platforms）
                source_platforms = config.get("platforms", {})
                if not source_platforms:
                    source_platforms = config.get("modules", {}).get("publisher", {}).get("platforms", {})

                for platform, platform_config in source_platforms.items():
                    if platform in self.platform_configs:
                        self.platform_configs[platform].update(platform_config)
                
                logger.info(f"配置已加载: {self.config_path}")
            except Exception as e:
                logger.error(f"配置加载失败: {e}")
        else:
            logger.info("使用默认配置")
    
    def _load_history(self):
        """加载发布历史"""
        try:
            history_dir = os.path.dirname(self.history_file)
            if not os.path.exists(history_dir):
                os.makedirs(history_dir)
            
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.publish_history = json.load(f)
                logger.info(f"发布历史已加载: {len(self.publish_history)} 条记录")
            else:
                self.publish_history = []
        except Exception as e:
            logger.error(f"发布历史加载失败: {e}")
            self.publish_history = []
    
    def _save_history(self):
        """保存发布历史"""
        try:
            # 只保留最近100条记录
            if len(self.publish_history) > 100:
                self.publish_history = self.publish_history[-100:]
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.publish_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"发布历史保存失败: {e}")
    
    def publish_to_platforms(self, formatted_contents: List[Dict[str, Any]], 
                           platforms: List[str] = None) -> Dict[str, Any]:
        """
        发布内容到多个平台
        
        Args:
            formatted_contents: 格式化后的内容列表
            platforms: 目标平台列表（默认发布所有启用的平台）
            
        Returns:
            发布结果汇总
        """
        try:
            logger.info(f"开始发布流程，内容数: {len(formatted_contents)}")
            
            # 确定目标平台
            if platforms is None:
                platforms = [p for p, config in self.platform_configs.items() 
                           if config.get("enabled", False)]
            
            logger.info(f"目标平台: {', '.join(platforms)}")
            
            # 发布结果
            results = {
                "total_contents": len(formatted_contents),
                "total_platforms": len(platforms),
                "success_count": 0,
                "failure_count": 0,
                "start_time": datetime.now().isoformat(),
                "platform_results": {},
                "details": []
            }
            
            # 遍历每个内容
            for content_idx, formatted_content in enumerate(formatted_contents):
                content_result = {
                    "content_index": content_idx,
                    "content_title": formatted_content.get("content", {}).get("formatted_title", ""),
                    "platform_results": {}
                }
                
                # 遍历每个平台
                for platform in platforms:
                    platform_result = self._publish_single(content_idx, formatted_content, platform)
                    content_result["platform_results"][platform] = platform_result
                    
                    # 汇总统计
                    if platform_result["success"]:
                        results["success_count"] += 1
                    else:
                        results["failure_count"] += 1
                    
                    # 记录平台结果
                    if platform not in results["platform_results"]:
                        results["platform_results"][platform] = {
                            "success": 0,
                            "failure": 0
                        }
                    
                    if platform_result["success"]:
                        results["platform_results"][platform]["success"] += 1
                    else:
                        results["platform_results"][platform]["failure"] += 1
                
                results["details"].append(content_result)
            
            # 完成时间
            results["end_time"] = datetime.now().isoformat()
            results["duration_seconds"] = (
                datetime.fromisoformat(results["end_time"]) - 
                datetime.fromisoformat(results["start_time"])
            ).total_seconds()
            
            # 保存发布历史
            self._add_to_history(results)
            
            logger.info(f"发布完成，成功: {results['success_count']}, 失败: {results['failure_count']}")
            return results
            
        except Exception as e:
            logger.error(f"发布流程失败: {e}")
            raise
    
    def _publish_single(self, content_idx: int, formatted_content: Dict[str, Any], 
                       platform: str) -> Dict[str, Any]:
        """发布单个内容到单个平台"""
        try:
            logger.info(f"发布内容 #{content_idx} 到 {platform}")
            
            platform_config = self.platform_configs.get(platform, {})
            
            # 检查平台是否启用
            if not platform_config.get("enabled", False):
                return {
                    "success": False,
                    "platform": platform,
                    "error": f"平台未启用",
                    "timestamp": datetime.now().isoformat()
                }
            
            # 检查频率限制
            if not self._check_rate_limit(platform):
                return {
                    "success": False,
                    "platform": platform,
                    "error": f"达到频率限制",
                    "timestamp": datetime.now().isoformat()
                }
            
            # 根据平台类型选择发布方法
            publish_method = platform_config.get("publish_method", "file")
            
            if publish_method == "file":
                result = self._publish_to_file(formatted_content, platform)
            elif publish_method == "webhook":
                result = self._publish_via_webhook(formatted_content, platform)
            elif publish_method == "api":
                result = self._publish_via_api(formatted_content, platform)
            else:
                result = {
                    "success": False,
                    "platform": platform,
                    "error": f"不支持的发布方法: {publish_method}",
                    "timestamp": datetime.now().isoformat()
                }
            
            return result
            
        except Exception as e:
            logger.error(f"发布到 {platform} 失败: {e}")
            return {
                "success": False,
                "platform": platform,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _publish_to_file(self, formatted_content: Dict[str, Any], platform: str) -> Dict[str, Any]:
        """发布到本地文件"""
        try:
            # 创建输出目录
            output_dir = os.path.join(
                os.path.dirname(__file__),
                "..", "..", "output",
                "published",
                platform,
                datetime.now().strftime("%Y%m%d")
            )
            
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # 生成文件名
            title = formatted_content.get("content", {}).get("formatted_title", "untitled")
            safe_title = "".join(c for c in title if c.isalnum() or c in " _-")[:50]
            timestamp = datetime.now().strftime("%H%M%S")
            
            # 保存JSON格式
            json_file = os.path.join(output_dir, f"{safe_title}_{timestamp}.json")
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(formatted_content, f, ensure_ascii=False, indent=2)
            
            # 保存文本格式
            txt_file = os.path.join(output_dir, f"{safe_title}_{timestamp}.txt")
            self._save_as_text(formatted_content, txt_file)
            
            return {
                "success": True,
                "platform": platform,
                "method": "file",
                "files": [json_file, txt_file],
                "timestamp": datetime.now().isoformat(),
                "message": f"内容已保存到文件: {json_file}"
            }
            
        except Exception as e:
            logger.error(f"文件保存失败: {e}")
            return {
                "success": False,
                "platform": platform,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _save_as_text(self, formatted_content: Dict[str, Any], filepath: str):
        """保存为纯文本"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"标题: {formatted_content['content']['formatted_title']}\n")
                f.write(f"平台: {formatted_content['platform_name']}\n")
                f.write(f"时间: {formatted_content.get('formatted_at', '')}\n")
                f.write("=" * 60 + "\n\n")
                f.write(formatted_content['content']['formatted_content'])
                f.write("\n\n" + "=" * 60 + "\n")
                f.write(f"标签: {', '.join(formatted_content['content']['tags'])}\n")
                f.write(f"字数: {formatted_content['content']['word_count']}\n")
        except Exception as e:
            logger.error(f"文本保存失败: {e}")
    
    def _publish_via_webhook(self, formatted_content: Dict[str, Any], platform: str) -> Dict[str, Any]:
        """通过Webhook发布"""
        try:
            # 这里实现具体的Webhook发布逻辑
            # 目前作为占位符，返回模拟成功
            
            if platform == "feishu":
                # 飞书Webhook发布（简化版）
                webhook_url = "https://open.feishu.cn/open-apis/bot/v2/hook/xxx"  # 需要实际配置
                
                message = {
                    "msg_type": "text",
                    "content": {
                        "text": f"新内容发布: {formatted_content['content']['formatted_title']}\n{formatted_content['content']['summary']}"
                    }
                }
                
                # 实际发送请求（需要配置正确的webhook URL）
                # response = requests.post(webhook_url, json=message, timeout=10)
                # response.raise_for_status()
                
                return {
                    "success": True,
                    "platform": platform,
                    "method": "webhook",
                    "timestamp": datetime.now().isoformat(),
                    "message": "飞书Webhook发布成功（模拟）"
                }
            
            else:
                return {
                    "success": False,
                    "platform": platform,
                    "error": f"Webhook配置未实现: {platform}",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Webhook发布失败: {e}")
            return {
                "success": False,
                "platform": platform,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _publish_via_api(self, formatted_content: Dict[str, Any], platform: str) -> Dict[str, Any]:
        """通过API发布"""
        try:
            if platform == "wechat":
                return self._publish_wechat_draft(formatted_content)

            return {
                "success": True,
                "platform": platform,
                "method": "api",
                "timestamp": datetime.now().isoformat(),
                "message": f"{platform} API发布成功（模拟）"
            }

        except Exception as e:
            logger.error(f"API发布失败: {e}")
            return {
                "success": False,
                "platform": platform,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _publish_wechat_draft(self, formatted_content: Dict[str, Any]) -> Dict[str, Any]:
        """发布到微信公众号草稿箱"""
        cfg = self.platform_configs.get("wechat", {})
        app_id = cfg.get("app_id", "")
        app_secret = cfg.get("app_secret", "")

        if not app_id or not app_secret:
            return {
                "success": False,
                "platform": "wechat",
                "error": "缺少 wechat app_id 或 app_secret",
                "timestamp": datetime.now().isoformat()
            }

        token_resp = requests.get(
            "https://api.weixin.qq.com/cgi-bin/token",
            params={
                "grant_type": "client_credential",
                "appid": app_id,
                "secret": app_secret,
            },
            timeout=20,
        )
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            return {
                "success": False,
                "platform": "wechat",
                "error": f"获取access_token失败: {token_data}",
                "timestamp": datetime.now().isoformat()
            }

        thumb_media_id = cfg.get("thumb_media_id", "")
        if not thumb_media_id:
            return {
                "success": False,
                "platform": "wechat",
                "error": "缺少thumb_media_id，请在配置中补充 wechat.thumb_media_id",
                "timestamp": datetime.now().isoformat()
            }

        title = formatted_content.get("content", {}).get("formatted_title", "自动草稿")
        summary = formatted_content.get("content", {}).get("summary", "")
        body = formatted_content.get("content", {}).get("formatted_content", "")
        html_body = "".join([f"<p>{line}</p>" for line in body.splitlines() if line.strip()])

        payload = {
            "articles": [
                {
                    "title": title,
                    "author": "Sun",
                    "digest": summary[:120],
                    "content": html_body,
                    "thumb_media_id": thumb_media_id,
                    "need_open_comment": 0,
                    "only_fans_can_comment": 0,
                }
            ]
        }

        draft_resp = requests.post(
            "https://api.weixin.qq.com/cgi-bin/draft/add",
            params={"access_token": access_token},
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
            timeout=20,
        )
        draft_data = draft_resp.json()

        if draft_data.get("media_id"):
            return {
                "success": True,
                "platform": "wechat",
                "method": "api",
                "timestamp": datetime.now().isoformat(),
                "media_id": draft_data.get("media_id"),
                "message": "微信公众号草稿创建成功"
            }

        return {
            "success": False,
            "platform": "wechat",
            "error": f"draft/add失败: {draft_data}",
            "timestamp": datetime.now().isoformat()
        }
    
    def _check_rate_limit(self, platform: str) -> bool:
        """检查频率限制"""
        try:
            platform_config = self.platform_configs.get(platform, {})
            rate_limit = platform_config.get("rate_limit")
            
            if rate_limit is None:
                return True
            
            # 检查今天的发布次数
            today = datetime.now().strftime("%Y-%m-%d")
            today_publishes = [
                h for h in self.publish_history
                if h.get("platform") == platform and 
                h.get("timestamp", "").startswith(today) and
                h.get("success", False)
            ]
            
            return len(today_publishes) < rate_limit
            
        except Exception as e:
            logger.error(f"频率检查失败: {e}")
            return False
    
    def _add_to_history(self, publish_result: Dict[str, Any]):
        """添加到发布历史"""
        try:
            history_entry = {
                "timestamp": datetime.now().isoformat(),
                "total_contents": publish_result.get("total_contents", 0),
                "success_count": publish_result.get("success_count", 0),
                "failure_count": publish_result.get("failure_count", 0),
                "platform_results": publish_result.get("platform_results", {}),
                "duration_seconds": publish_result.get("duration_seconds", 0)
            }
            
            self.publish_history.append(history_entry)
            self._save_history()
            
        except Exception as e:
            logger.error(f"历史记录添加失败: {e}")
    
    def get_publish_stats(self) -> Dict[str, Any]:
        """获取发布统计"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            today_publishes = [h for h in self.publish_history if h.get("timestamp", "").startswith(today)]
            
            stats = {
                "total_publishes": len(self.publish_history),
                "today_publishes": len(today_publishes),
                "success_rate": 0,
                "platform_stats": {},
                "recent_publishes": self.publish_history[-10:] if self.publish_history else []
            }
            
            # 计算成功率
            if self.publish_history:
                total_success = sum(1 for h in self.publish_history if h.get("success_count", 0) > 0)
                stats["success_rate"] = total_success / len(self.publish_history) * 100
            
            # 按平台统计
            for platform in self.platform_configs:
                platform_publishes = [h for h in self.publish_history 
                                    if h.get("platform_results", {}).get(platform)]
                stats["platform_stats"][platform] = {
                    "total": len(platform_publishes),
                    "today": len([h for h in platform_publishes 
                                if h.get("timestamp", "").startswith(today)])
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"统计获取失败: {e}")
            return {}
    
    def enable_platform(self, platform: str, enable: bool = True):
        """启用/禁用平台"""
        if platform in self.platform_configs:
            self.platform_configs[platform]["enabled"] = enable
            logger.info(f"平台 {platform} {'启用' if enable else '禁用'}")
            return True
        else:
            logger.error(f"未知平台: {platform}")
            return False
    
    def update_platform_config(self, platform: str, config_updates: Dict[str, Any]) -> bool:
        """更新平台配置"""
        if platform in self.platform_configs:
            self.platform_configs[platform].update(config_updates)
            logger.info(f"平台 {platform} 配置已更新")
            return True
        else:
            logger.error(f"未知平台: {platform}")
            return False


# 使用示例
if __name__ == "__main__":
    # 测试数据
    test_formatted_content = {
        "platform": "wechat",
        "platform_name": "微信公众号",
        "formatted_at": "2026-02-28T22:55:00",
        "content": {
            "formatted_title": "AI大模型技术突破分析与未来展望",
            "formatted_content": "随着AI技术的快速发展...",
            "summary": "深度分析AI大模型技术趋势",
            "tags": ["AI", "大模型", "技术分析"],
            "word_count": 1200
        }
    }
    
    # 创建发布器
    publisher = ContentPublisher()
    
    # 启用测试平台
    publisher.enable_platform("file", True)
    publisher.enable_platform("feishu", True)
    
    # 发布测试内容
    results = publisher.publish_to_platforms(
        [test_formatted_content],
        platforms=["file", "feishu"]
    )
    
    print("发布结果:")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    
    # 获取统计信息
    stats = publisher.get_publish_stats()
    print("\n发布统计:")
    print(f"总发布次数: {stats.get('total_publishes', 0)}")
    print(f"今日发布: {stats.get('today_publishes', 0)}")
    print(f"成功率: {stats.get('success_rate', 0):.1f}%")