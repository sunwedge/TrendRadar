#!/usr/bin/env python3
"""
内容生产流水线 - 主控制器
整合：灵感收集 → 大纲生成 → 内容创作 → 排版优化 → 多平台发布
"""

import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional

# 导入各模块
try:
    from outline.outline_generator import OutlineGenerator
    from writer.content_writer import ContentWriter
    from formatter.content_formatter import ContentFormatter
    from publisher.content_publisher import ContentPublisher
except ImportError:
    # 如果相对导入失败，使用绝对导入
    sys.path.append(os.path.dirname(__file__))
    from outline.outline_generator import OutlineGenerator
    from writer.content_writer import ContentWriter
    from formatter.content_formatter import ContentFormatter
    from publisher.content_publisher import ContentPublisher

logger = logging.getLogger(__name__)


class ContentPipeline:
    """内容生产流水线"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化流水线
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = self._load_config()
        
        # 初始化各模块
        self.outline_generator = OutlineGenerator()
        self.content_writer = ContentWriter()
        self.content_formatter = ContentFormatter()
        self.content_publisher = ContentPublisher(config_path)
        
        # 流水线状态
        self.pipeline_status = {
            "initialized": True,
            "last_run": None,
            "total_runs": 0,
            "success_count": 0,
            "failure_count": 0
        }
        
        # 输出目录
        self.output_base = os.path.join(
            os.path.dirname(__file__),
            "..", "output", "pipeline"
        )
        if not os.path.exists(self.output_base):
            os.makedirs(self.output_base)
        
        logger.info("内容生产流水线初始化完成")
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        default_config = {
            "pipeline": {
                "enabled": True,
                "max_articles_per_run": 3,
                "default_writing_style": "professional",
                "default_format_platforms": ["wechat", "zhihu", "xiaohongshu", "toutiao"],
                "auto_publish": True,
                "publish_platforms": ["file"]  # 默认只保存到文件
            },
            "modules": {
                "outline": {
                    "enabled": True,
                    "default_style": "tech_analysis"
                },
                "writer": {
                    "enabled": True
                },
                "formatter": {
                    "enabled": True
                },
                "publisher": {
                    "enabled": True
                }
            }
        }
        
        if self.config_path and os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                
                # 深度合并配置
                def merge_dict(d1, d2):
                    for k, v in d2.items():
                        if k in d1 and isinstance(d1[k], dict) and isinstance(v, dict):
                            merge_dict(d1[k], v)
                        else:
                            d1[k] = v
                    return d1
                
                default_config = merge_dict(default_config, user_config)
                logger.info(f"配置已加载: {self.config_path}")
            except Exception as e:
                logger.error(f"配置加载失败，使用默认配置: {e}")
        
        return default_config
    
    def run_pipeline(self, inspiration_data: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        运行完整的内容生产流水线
        
        Args:
            inspiration_data: 灵感数据列表（如果为None，则从TrendRadar获取）
            
        Returns:
            流水线执行结果
        """
        try:
            logger.info("开始运行内容生产流水线")
            start_time = datetime.now()
            
            # 更新状态
            self.pipeline_status["last_run"] = start_time.isoformat()
            self.pipeline_status["total_runs"] += 1
            
            # 结果容器
            results = {
                "pipeline_run_id": start_time.strftime("%Y%m%d_%H%M%S"),
                "start_time": start_time.isoformat(),
                "end_time": None,
                "duration_seconds": 0,
                "total_inspirations": 0,
                "total_articles": 0,
                "total_published": 0,
                "module_results": {
                    "outline": {"processed": 0, "success": 0, "failed": 0},
                    "writer": {"processed": 0, "success": 0, "failed": 0},
                    "formatter": {"processed": 0, "success": 0, "failed": 0},
                    "publisher": {"processed": 0, "success": 0, "failed": 0}
                },
                "output_files": [],
                "errors": [],
                "summary": {}
            }
            
            # 步骤1: 获取灵感数据
            inspirations = self._get_inspirations(inspiration_data)
            if not inspirations:
                logger.warning("未获取到灵感数据，流水线终止")
                results["errors"].append("未获取到灵感数据")
                return results
            
            results["total_inspirations"] = len(inspirations)
            logger.info(f"获取到 {len(inspirations)} 条灵感数据")
            
            # 限制处理数量
            max_articles = self.config["pipeline"]["max_articles_per_run"]
            if len(inspirations) > max_articles:
                logger.info(f"限制处理数量: {max_articles}/{len(inspirations)}")
                inspirations = inspirations[:max_articles]
            
            # 步骤2: 生成大纲
            outlines = self._generate_outlines(inspirations, results)
            if not outlines:
                logger.error("大纲生成失败，流水线终止")
                results["errors"].append("大纲生成失败")
                return results
            
            # 步骤3: 内容创作
            articles = self._write_contents(outlines, results)
            if not articles:
                logger.error("内容创作失败，流水线终止")
                results["errors"].append("内容创作失败")
                return results
            
            results["total_articles"] = len(articles)
            
            # 步骤4: 排版优化
            formatted_contents = self._format_contents(articles, results)
            if not formatted_contents:
                logger.error("排版优化失败，流水线终止")
                results["errors"].append("排版优化失败")
                return results
            
            # 步骤5: 发布分发
            if self.config["pipeline"]["auto_publish"]:
                publish_results = self._publish_contents(formatted_contents, results)
                results["total_published"] = publish_results.get("success_count", 0)
            
            # 保存结果
            end_time = datetime.now()
            results["end_time"] = end_time.isoformat()
            results["duration_seconds"] = (end_time - start_time).total_seconds()
            
            # 生成摘要
            results["summary"] = self._generate_summary(results)
            
            # 保存执行记录
            self._save_results(results)
            
            # 更新成功计数
            if not results["errors"]:
                self.pipeline_status["success_count"] += 1
                logger.info("流水线执行成功")
            else:
                self.pipeline_status["failure_count"] += 1
                logger.warning(f"流水线执行完成，但有错误: {len(results['errors'])}")
            
            return results
            
        except Exception as e:
            logger.error(f"流水线执行失败: {e}")
            self.pipeline_status["failure_count"] += 1
            raise
    
    def _get_inspirations(self, inspiration_data: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """获取灵感数据"""
        if inspiration_data is not None:
            return inspiration_data
        
        # 如果没有提供数据，先使用生产模板兜底（非测试文案）
        logger.info("未提供外部灵感数据，使用生产模板兜底")

        return [
            {
                "title": "今日AI行业关键动态与机会窗口",
                "keywords": ["AI", "大模型", "行业应用", "产品化"],
                "summary": "围绕模型能力、商业化落地和组织提效，提炼今天最值得关注的机会点与执行建议。",
                "source": "TrendRadar内容生产流水线",
                "url": "",
                "timestamp": datetime.now().isoformat()
            },
            {
                "title": "企业级AI落地路径：从试点到规模化",
                "keywords": ["企业AI", "工作流自动化", "ROI", "规模化"],
                "summary": "结合案例复盘企业在AI导入过程中的关键阻碍、成功策略与可复制方法。",
                "source": "TrendRadar内容生产流水线",
                "url": "",
                "timestamp": datetime.now().isoformat()
            }
        ]
    
    def _generate_outlines(self, inspirations: List[Dict[str, Any]], 
                          results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成大纲"""
        if not self.config["modules"]["outline"]["enabled"]:
            logger.info("大纲生成模块已禁用，跳过")
            return []
        
        logger.info("开始生成大纲...")
        outlines = []
        
        for i, inspiration in enumerate(inspirations):
            try:
                # 确定大纲风格
                style = self.config["modules"]["outline"]["default_style"]
                
                # 生成大纲
                outline = self.outline_generator.generate_outline(inspiration, style)
                
                # 保存大纲文件
                outline_file = os.path.join(
                    self.output_base,
                    "outlines",
                    f"outline_{results['pipeline_run_id']}_{i:02d}.json"
                )
                os.makedirs(os.path.dirname(outline_file), exist_ok=True)
                
                if self.outline_generator.save_outline(outline, outline_file):
                    outline["file_path"] = outline_file
                    outlines.append(outline)
                    
                    # 更新结果
                    results["module_results"]["outline"]["processed"] += 1
                    results["module_results"]["outline"]["success"] += 1
                    results["output_files"].append(outline_file)
                    
                    logger.info(f"大纲生成成功: {outline['title']}")
                else:
                    results["module_results"]["outline"]["processed"] += 1
                    results["module_results"]["outline"]["failed"] += 1
                    results["errors"].append(f"大纲保存失败: {inspiration.get('title', '未知')}")
                    
            except Exception as e:
                logger.error(f"大纲生成失败: {e}")
                results["module_results"]["outline"]["processed"] += 1
                results["module_results"]["outline"]["failed"] += 1
                results["errors"].append(f"大纲生成异常: {str(e)}")
        
        logger.info(f"大纲生成完成: {len(outlines)}/{len(inspirations)}")
        return outlines
    
    def _write_contents(self, outlines: List[Dict[str, Any]], 
                       results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """创作内容"""
        if not self.config["modules"]["writer"]["enabled"]:
            logger.info("内容创作模块已禁用，跳过")
            return []
        
        logger.info("开始内容创作...")
        articles = []
        
        for i, outline in enumerate(outlines):
            try:
                # 确定写作风格
                style = self.config["pipeline"]["default_writing_style"]
                
                # 创作内容
                article = self.content_writer.write_content(outline, style)
                
                # 保存文章文件
                article_file = os.path.join(
                    self.output_base,
                    "articles",
                    f"article_{results['pipeline_run_id']}_{i:02d}.json"
                )
                os.makedirs(os.path.dirname(article_file), exist_ok=True)
                
                if self.content_writer.save_article(article, article_file):
                    article["file_path"] = article_file
                    articles.append(article)
                    
                    # 更新结果
                    results["module_results"]["writer"]["processed"] += 1
                    results["module_results"]["writer"]["success"] += 1
                    results["output_files"].append(article_file)
                    
                    logger.info(f"内容创作成功: {article['metadata']['title']}")
                else:
                    results["module_results"]["writer"]["processed"] += 1
                    results["module_results"]["writer"]["failed"] += 1
                    results["errors"].append(f"文章保存失败: {outline.get('title', '未知')}")
                    
            except Exception as e:
                logger.error(f"内容创作失败: {e}")
                results["module_results"]["writer"]["processed"] += 1
                results["module_results"]["writer"]["failed"] += 1
                results["errors"].append(f"内容创作异常: {str(e)}")
        
        logger.info(f"内容创作完成: {len(articles)}/{len(outlines)}")
        return articles
    
    def _format_contents(self, articles: List[Dict[str, Any]], 
                        results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """排版优化"""
        if not self.config["modules"]["formatter"]["enabled"]:
            logger.info("排版优化模块已禁用，跳过")
            return []
        
        logger.info("开始排版优化...")
        formatted_contents = []
        platforms = self.config["pipeline"]["default_format_platforms"]
        
        for article_idx, article in enumerate(articles):
            for platform in platforms:
                try:
                    # 格式化内容
                    formatted = self.content_formatter.format_for_platform(article, platform)
                    
                    # 保存格式化文件
                    formatted_file = os.path.join(
                        self.output_base,
                        "formatted",
                        platform,
                        f"formatted_{results['pipeline_run_id']}_{article_idx:02d}.json"
                    )
                    os.makedirs(os.path.dirname(formatted_file), exist_ok=True)
                    
                    if self.content_formatter.save_formatted_content(formatted, formatted_file):
                        formatted["file_path"] = formatted_file
                        formatted_contents.append(formatted)
                        
                        # 更新结果
                        results["module_results"]["formatter"]["processed"] += 1
                        results["module_results"]["formatter"]["success"] += 1
                        results["output_files"].append(formatted_file)
                        
                        logger.info(f"排版优化成功: {platform}/{article['metadata']['title']}")
                    else:
                        results["module_results"]["formatter"]["processed"] += 1
                        results["module_results"]["formatter"]["failed"] += 1
                        results["errors"].append(f"格式化保存失败: {platform}")
                        
                except Exception as e:
                    logger.error(f"排版优化失败: {e}")
                    results["module_results"]["formatter"]["processed"] += 1
                    results["module_results"]["formatter"]["failed"] += 1
                    results["errors"].append(f"排版优化异常: {str(e)}")
        
        logger.info(f"排版优化完成: {len(formatted_contents)}个格式化内容")
        return formatted_contents
    
    def _publish_contents(self, formatted_contents: List[Dict[str, Any]], 
                         results: Dict[str, Any]) -> Dict[str, Any]:
        """发布分发"""
        if not self.config["modules"]["publisher"]["enabled"]:
            logger.info("发布分发模块已禁用，跳过")
            return {}

        logger.info("开始发布分发...")
        publish_platforms = self.config["pipeline"]["publish_platforms"]

        try:
            aggregate = {
                "total_contents": 0,
                "total_platforms": len(publish_platforms),
                "success_count": 0,
                "failure_count": 0,
                "platform_results": {},
                "details": []
            }

            # 只发布与平台匹配的格式化内容，避免笛卡尔积重复发布
            for platform in publish_platforms:
                platform_contents = [c for c in formatted_contents if c.get("platform") == platform]
                if not platform_contents:
                    logger.info(f"平台 {platform} 无匹配内容，跳过")
                    continue

                publish_results = self.content_publisher.publish_to_platforms(
                    platform_contents,
                    platforms=[platform]
                )

                aggregate["total_contents"] += publish_results.get("total_contents", 0)
                aggregate["success_count"] += publish_results.get("success_count", 0)
                aggregate["failure_count"] += publish_results.get("failure_count", 0)
                aggregate["details"].extend(publish_results.get("details", []))

                for p_name, p_stats in publish_results.get("platform_results", {}).items():
                    if p_name not in aggregate["platform_results"]:
                        aggregate["platform_results"][p_name] = {"success": 0, "failure": 0}
                    aggregate["platform_results"][p_name]["success"] += p_stats.get("success", 0)
                    aggregate["platform_results"][p_name]["failure"] += p_stats.get("failure", 0)

            # 更新结果
            results["module_results"]["publisher"]["processed"] = aggregate.get("total_contents", 0)
            results["module_results"]["publisher"]["success"] = aggregate.get("success_count", 0)
            results["module_results"]["publisher"]["failed"] = aggregate.get("failure_count", 0)

            logger.info(f"发布分发完成: 成功{aggregate['success_count']}, 失败{aggregate['failure_count']}")
            return aggregate

        except Exception as e:
            logger.error(f"发布分发失败: {e}")
            results["module_results"]["publisher"]["failed"] = len(formatted_contents)
            results["errors"].append(f"发布分发异常: {str(e)}")
            return {}
    
    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """生成执行摘要"""
        summary = {
            "overall_success": len(results["errors"]) == 0,
            "total_errors": len(results["errors"]),
            "processing_rate": 0,
            "time_efficiency": 0,
            "module_performance": {}
        }
        
        # 计算处理率
        total_processed = sum(m["processed"] for m in results["module_results"].values())
        total_success = sum(m["success"] for m in results["module_results"].values())
        
        if total_processed > 0:
            summary["processing_rate"] = total_success / total_processed * 100
        
        # 计算时间效率（每篇文章平均处理时间）
        if results["total_articles"] > 0 and results["duration_seconds"] > 0:
            summary["time_efficiency"] = results["duration_seconds"] / results["total_articles"]
        
        # 模块性能
        for module_name, module_results in results["module_results"].items():
            if module_results["processed"] > 0:
                success_rate = module_results["success"] / module_results["processed"] * 100
            else:
                success_rate = 0
            
            summary["module_performance"][module_name] = {
                "success_rate": success_rate,
                "processed": module_results["processed"],
                "success": module_results["success"],
                "failed": module_results["failed"]
            }
        
        return summary
    
    def _save_results(self, results: Dict[str, Any]):
        """保存执行结果"""
        try:
            results_file = os.path.join(
                self.output_base,
                "runs",
                f"pipeline_run_{results['pipeline_run_id']}.json"
            )
            os.makedirs(os.path.dirname(results_file), exist_ok=True)
            
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"流水线结果已保存: {results_file}")
            results["output_files"].append(results_file)
            
        except Exception as e:
            logger.error(f"结果保存失败: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取流水线状态"""
        return {
            **self.pipeline_status,
            "config_summary": {
                "pipeline_enabled": self.config["pipeline"]["enabled"],
                "auto_publish": self.config["pipeline"]["auto_publish"],
                "max_articles_per_run": self.config["pipeline"]["max_articles_per_run"]
            },
            "output_directory": self.output_base
        }
    
    def update_config(self, config_updates: Dict[str, Any]) -> bool:
        """更新配置"""
        try:
            def merge_dict(d1, d2):
                for k, v in d2.items():
                    if k in d1 and isinstance(d1[k], dict) and isinstance(v, dict):
                        merge_dict(d1[k], v)
                    else:
                        d1[k] = v
                return d1
            
            merge_dict(self.config, config_updates)
            
            # 保存配置
            if self.config_path:
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, ensure_ascii=False, indent=2)
            
            logger.info("配置已更新")
            return True
            
        except Exception as e:
            logger.error(f"配置更新失败: {e}")
            return False


# 主函数
def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="内容生产流水线")
    parser.add_argument("--config", type=str, help="配置文件路径")
    parser.add_argument("--test", action="store_true", help="测试模式")
    parser.add_argument("--status", action="store_true", help="查看状态")
    parser.add_argument("--inspirations", type=str, help="灵感数据JSON文件路径")
    
    args = parser.parse_args()
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # 创建流水线
    pipeline = ContentPipeline(args.config)
    
    if args.status:
        # 查看状态
        status = pipeline.get_status()
        print("流水线状态:")
        print(json.dumps(status, ensure_ascii=False, indent=2))
        return
    
    if args.test:
        # 测试模式
        print("开始测试内容生产流水线...")
        test_inspirations = [
            {
                "title": "测试文章：AI技术发展趋势",
                "keywords": ["测试", "AI", "技术趋势"],
                "summary": "这是一篇测试文章，用于验证内容生产流水线功能",
                "source": "测试数据",
                "timestamp": datetime.now().isoformat()
            }
        ]
        
        results = pipeline.run_pipeline(test_inspirations)
        print("\n测试结果:")
        print(f"处理灵感: {results['total_inspirations']}")
        print(f"生成文章: {results['total_articles']}")
        print(f"发布内容: {results['total_published']}")
        print(f"执行时间: {results['duration_seconds']:.1f}秒")
        
        if results['errors']:
            print(f"\n错误 ({len(results['errors'])}个):")
            for error in results['errors']:
                print(f"  - {error}")
        else:
            print("\n测试成功！")
        
        print(f"\n输出文件保存在: {pipeline.output_base}")
        return
    
    # 正常执行
    inspirations = None
    if args.inspirations and os.path.exists(args.inspirations):
        try:
            with open(args.inspirations, 'r', encoding='utf-8') as f:
                inspirations = json.load(f)
            print(f"已加载灵感数据: {len(inspirations)} 条")
        except Exception as e:
            print(f"灵感数据加载失败: {e}")
            return
    
    print("开始运行内容生产流水线...")
    results = pipeline.run_pipeline(inspirations)
    
    # 输出摘要
    summary = results.get("summary", {})
    print("\n" + "="*50)
    print("内容生产流水线执行完成")
    print("="*50)
    print(f"执行ID: {results['pipeline_run_id']}")
    print(f"总耗时: {results['duration_seconds']:.1f}秒")
    print(f"处理灵感: {results['total_inspirations']}")
    print(f"生成文章: {results['total_articles']}")
    print(f"发布内容: {results['total_published']}")
    print(f"总体成功率: {summary.get('processing_rate', 0):.1f}%")
    
    if results['errors']:
        print(f"\n错误 ({len(results['errors'])}个):")
        for error in results['errors'][:5]:  # 只显示前5个错误
            print(f"  - {error}")
        if len(results['errors']) > 5:
            print(f"  ... 还有 {len(results['errors']) - 5} 个错误")
    
    print(f"\n输出目录: {pipeline.output_base}")
    print("详细结果已保存到JSON文件")


if __name__ == "__main__":
    main()