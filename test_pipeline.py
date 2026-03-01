#!/usr/bin/env python3
"""
独立测试内容生产流水线
"""

import sys
import os
import json
import logging
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

print("=" * 60)
print("内容生产流水线 - 独立测试")
print("=" * 60)

# 测试导入流水线模块
print("\n🔧 测试导入流水线模块...")
try:
    # 直接导入我们创建的新模块
    from trendradar.outline.outline_generator import OutlineGenerator
    from trendradar.writer.content_writer import ContentWriter
    from trendradar.formatter.content_formatter import ContentFormatter
    from trendradar.publisher.content_publisher import ContentPublisher
    from trendradar.content_pipeline import ContentPipeline
    
    print("✅ 所有模块导入成功")
except ImportError as e:
    print(f"❌ 模块导入失败: {e}")
    print("\n尝试修复导入路径...")
    
    # 尝试直接导入模块文件
    import importlib.util
    
    # 测试大纲生成器
    outline_path = os.path.join(os.path.dirname(__file__), "trendradar", "outline", "outline_generator.py")
    if os.path.exists(outline_path):
        print(f"✅ 大纲生成器模块文件存在: {outline_path}")
    else:
        print(f"❌ 大纲生成器模块文件不存在: {outline_path}")
    
    sys.exit(1)

# 创建测试灵感数据
print("\n📝 创建测试灵感数据...")
test_inspirations = [
    {
        "title": "AI大模型最新技术突破分析",
        "keywords": ["AI", "大模型", "深度学习", "GPT-5", "transformer"],
        "summary": "最新研究显示，AI大模型在推理能力和代码生成方面取得显著进展，多项基准测试刷新记录",
        "source": "TrendRadar热点监测",
        "url": "https://example.com/ai-breakthrough",
        "timestamp": datetime.now().isoformat()
    },
    {
        "title": "量子计算商业化进程加速趋势分析",
        "keywords": ["量子计算", "商业化", "云计算", "量子优势", "量子算法"],
        "summary": "多家科技公司宣布量子计算云服务，量子计算商业化进入新阶段，预计未来三年市场规模将翻倍",
        "source": "TrendRadar热点监测", 
        "url": "https://example.com/quantum-computing",
        "timestamp": datetime.now().isoformat()
    }
]

print(f"✅ 创建了 {len(test_inspirations)} 条测试灵感数据")

# 测试大纲生成器
print("\n📋 测试大纲生成器...")
try:
    outline_gen = OutlineGenerator()
    
    for i, inspiration in enumerate(test_inspirations):
        print(f"\n  处理灵感 #{i+1}: {inspiration['title']}")
        
        outline = outline_gen.generate_outline(inspiration, style="tech_analysis")
        
        print(f"    生成大纲: {outline['title']}")
        print(f"    章节数量: {len(outline['sections'])}")
        
        # 保存大纲
        outline_dir = os.path.join(os.path.dirname(__file__), "output", "pipeline", "outlines")
        os.makedirs(outline_dir, exist_ok=True)
        outline_file = os.path.join(outline_dir, f"test_outline_{i+1}.json")
        
        if outline_gen.save_outline(outline, outline_file):
            print(f"    ✅ 大纲已保存: {outline_file}")
        else:
            print(f"    ❌ 大纲保存失败")
    
    print("✅ 大纲生成器测试完成")
    
except Exception as e:
    print(f"❌ 大纲生成器测试失败: {e}")
    import traceback
    traceback.print_exc()

# 测试内容创作器
print("\n✍️ 测试内容创作器...")
try:
    # 加载刚才生成的大纲
    outline_dir = os.path.join(os.path.dirname(__file__), "output", "pipeline", "outlines")
    outline_files = [f for f in os.listdir(outline_dir) if f.endswith('.json')][:1]  # 只测试一个
    
    if outline_files:
        outline_file = os.path.join(outline_dir, outline_files[0])
        
        # 加载大纲
        with open(outline_file, 'r', encoding='utf-8') as f:
            outline = json.load(f)
        
        print(f"  加载大纲: {outline['title']}")
        
        # 创建内容
        content_writer = ContentWriter()
        article = content_writer.write_content(outline, style="professional")
        
        print(f"  创作文章: {article['metadata']['title']}")
        print(f"  文章字数: {article['metadata']['word_count']}字")
        
        # 保存文章
        article_dir = os.path.join(os.path.dirname(__file__), "output", "pipeline", "articles")
        os.makedirs(article_dir, exist_ok=True)
        article_file = os.path.join(article_dir, f"test_article_{datetime.now().strftime('%H%M%S')}.json")
        
        if content_writer.save_article(article, article_file):
            print(f"  ✅ 文章已保存: {article_file}")
            
            # 同时保存Markdown版本
            md_file = article_file.replace('.json', '.md')
            if os.path.exists(md_file):
                print(f"  📝 Markdown版本: {md_file}")
        else:
            print(f"  ❌ 文章保存失败")
    
    print("✅ 内容创作器测试完成")
    
except Exception as e:
    print(f"❌ 内容创作器测试失败: {e}")
    import traceback
    traceback.print_exc()

# 测试格式化器
print("\n🎨 测试排版格式化器...")
try:
    # 加载刚才生成的文章
    article_dir = os.path.join(os.path.dirname(__file__), "output", "pipeline", "articles")
    article_files = [f for f in os.listdir(article_dir) if f.endswith('.json')][:1]  # 只测试一个
    
    if article_files:
        article_file = os.path.join(article_dir, article_files[0])
        
        # 加载文章
        with open(article_file, 'r', encoding='utf-8') as f:
            article = json.load(f)
        
        print(f"  加载文章: {article['metadata']['title']}")
        
        # 创建格式化器
        formatter = ContentFormatter()
        
        # 测试不同平台格式化
        test_platforms = ["wechat", "xiaohongshu", "toutiao"]
        
        for platform in test_platforms:
            print(f"\n  格式化到平台: {platform}")
            
            formatted = formatter.format_for_platform(article, platform)
            
            print(f"    格式化标题: {formatted['content']['formatted_title'][:50]}...")
            print(f"    生成标签: {', '.join(formatted['content']['tags'][:3])}")
            print(f"    字数: {formatted['content']['word_count']}")
            
            # 保存格式化内容
            formatted_dir = os.path.join(os.path.dirname(__file__), "output", "pipeline", "formatted", platform)
            os.makedirs(formatted_dir, exist_ok=True)
            formatted_file = os.path.join(formatted_dir, f"test_formatted_{platform}.json")
            
            if formatter.save_formatted_content(formatted, formatted_file):
                print(f"    ✅ 格式化内容已保存: {formatted_file}")
            else:
                print(f"    ❌ 格式化内容保存失败")
    
    print("✅ 排版格式化器测试完成")
    
except Exception as e:
    print(f"❌ 排版格式化器测试失败: {e}")
    import traceback
    traceback.print_exc()

# 测试发布器
print("\n🚀 测试内容发布器...")
try:
    # 加载格式化内容
    formatted_dir = os.path.join(os.path.dirname(__file__), "output", "pipeline", "formatted")
    
    formatted_contents = []
    
    # 收集所有平台的格式化内容
    for platform in os.listdir(formatted_dir):
        platform_dir = os.path.join(formatted_dir, platform)
        if os.path.isdir(platform_dir):
            for file in os.listdir(platform_dir):
                if file.endswith('.json'):
                    filepath = os.path.join(platform_dir, file)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = json.load(f)
                        formatted_contents.append(content)
    
    if formatted_contents:
        print(f"  加载到 {len(formatted_contents)} 个格式化内容")
        
        # 创建发布器
        publisher = ContentPublisher()
        
        # 启用文件发布
        publisher.enable_platform("file", True)
        
        # 发布内容
        results = publisher.publish_to_platforms(
            formatted_contents[:2],  # 只发布前2个
            platforms=["file"]
        )
        
        print(f"  发布结果: 成功{results.get('success_count', 0)}个, 失败{results.get('failure_count', 0)}个")
        
        # 获取发布统计
        stats = publisher.get_publish_stats()
        print(f"  发布统计: 总发布{stats.get('total_publishes', 0)}次, 今日发布{stats.get('today_publishes', 0)}次")
        
        print("✅ 内容发布器测试完成")
    else:
        print("⚠️  未找到格式化内容，跳过发布测试")
    
except Exception as e:
    print(f"❌ 内容发布器测试失败: {e}")
    import traceback
    traceback.print_exc()

# 最终输出目录检查
print("\n📁 输出目录检查...")
output_base = os.path.join(os.path.dirname(__file__), "output", "pipeline")

if os.path.exists(output_base):
    print(f"输出根目录: {output_base}")
    
    for root, dirs, files in os.walk(output_base):
        level = root.replace(output_base, '').count(os.sep)
        indent = ' ' * 2 * level
        
        # 只显示前3级目录
        if level <= 2:
            print(f"{indent}📂 {os.path.basename(root)}/")
            
            subindent = ' ' * 2 * (level + 1)
            file_count = 0
            for file in files[:5]:  # 只显示前5个文件
                if file.endswith(('.json', '.md', '.txt')):
                    print(f"{subindent}📄 {file}")
                    file_count += 1
            
            if len(files) > 5:
                print(f"{subindent}... 还有 {len(files) - 5} 个文件")
            
            if file_count == 0 and files:
                print(f"{subindent}(包含 {len(files)} 个非文本文件)")
else:
    print(f"❌ 输出目录不存在: {output_base}")

print("\n" + "=" * 60)
print("🎉 内容生产流水线独立测试完成!")
print("=" * 60)
print("\n📊 测试总结:")
print(f"  灵感数据: {len(test_inspirations)} 条")
print(f"  输出目录: {output_base}")
print(f"  测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("\n💡 下一步:")
print("  1. 检查输出目录中的生成文件")
print("  2. 编辑 config/content_pipeline.json 调整配置")
print("  3. 配置AI API密钥启用智能增强")
print("  4. 配置各平台API启用自动发布")