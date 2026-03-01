#!/usr/bin/env python3
"""
简单的内容生产流水线演示
绕过原有依赖，直接运行我们新建的模块
"""

import os
import sys
import json
import logging
from datetime import datetime

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

print("=" * 60)
print("简单内容生产流水线演示")
print("=" * 60)
print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 添加模块目录到路径
module_dir = os.path.join(os.path.dirname(__file__), "trendradar")
sys.path.insert(0, module_dir)

# 1. 创建测试灵感数据
print("📝 步骤1: 创建测试灵感数据")
inspirations = [
    {
        "title": "AI大模型技术最新突破与未来趋势",
        "keywords": ["AI", "大模型", "深度学习", "GPT", "transformer"],
        "summary": "最新研究表明，AI大模型在多个领域取得突破性进展，包括自然语言理解、代码生成和推理能力",
        "source": "科技热点监测",
        "timestamp": datetime.now().isoformat()
    }
]
print(f"✅ 创建了 {len(inspirations)} 条灵感数据")
print(f"   标题: {inspirations[0]['title']}")
print()

# 2. 动态导入大纲生成器
print("📋 步骤2: 大纲生成")
try:
    # 动态导入，避免原有依赖
    outline_path = os.path.join(module_dir, "outline", "outline_generator.py")
    
    import importlib.util
    spec = importlib.util.spec_from_file_location("outline_generator", outline_path)
    outline_module = importlib.util.module_from_spec(spec)
    
    # 创建一个简单的日志对象来满足模块需求
    import logging
    outline_module.logger = logging.getLogger("outline")
    
    # 执行导入
    spec.loader.exec_module(outline_module)
    
    # 创建大纲生成器实例
    OutlineGenerator = outline_module.OutlineGenerator
    generator = OutlineGenerator()
    
    # 生成大纲
    outline = generator.generate_outline(inspirations[0], style="tech_analysis")
    
    print(f"✅ 大纲生成成功")
    print(f"   大纲标题: {outline['title']}")
    print(f"   章节数量: {len(outline['sections'])}")
    
    # 保存大纲
    output_dir = os.path.join(os.path.dirname(__file__), "output", "demo")
    os.makedirs(output_dir, exist_ok=True)
    
    outline_file = os.path.join(output_dir, "demo_outline.json")
    with open(outline_file, 'w', encoding='utf-8') as f:
        json.dump(outline, f, ensure_ascii=False, indent=2)
    
    print(f"💾 大纲已保存: {outline_file}")
    print()
    
except Exception as e:
    print(f"❌ 大纲生成失败: {e}")
    import traceback
    traceback.print_exc()
    print("\n⚠️  继续演示其他步骤...")
    outline = None

# 3. 动态导入内容创作器
if outline:
    print("✍️ 步骤3: 内容创作")
    try:
        writer_path = os.path.join(module_dir, "writer", "content_writer.py")
        
        spec = importlib.util.spec_from_file_location("content_writer", writer_path)
        writer_module = importlib.util.module_from_spec(spec)
        writer_module.logger = logging.getLogger("writer")
        spec.loader.exec_module(writer_module)
        
        ContentWriter = writer_module.ContentWriter
        writer = ContentWriter()
        
        # 创作内容
        article = writer.write_content(outline, style="professional")
        
        print(f"✅ 内容创作成功")
        print(f"   文章标题: {article['metadata']['title']}")
        print(f"   文章字数: {article['metadata']['word_count']}字")
        
        # 保存文章
        article_file = os.path.join(output_dir, "demo_article.json")
        with open(article_file, 'w', encoding='utf-8') as f:
            json.dump(article, f, ensure_ascii=False, indent=2)
        
        # 同时保存为Markdown
        md_content = f"""# {article['metadata']['title']}

> 生成时间: {article['metadata']['generated_at']}
> 字数: {article['metadata']['word_count']}字
> 风格: {article['metadata']['writing_tone']}

{article['content']['introduction']}

"""
        
        for section in article['content']['sections']:
            md_content += f"{section['content']}\n\n"
        
        md_content += f"{article['content']['conclusion']}\n"
        
        md_file = os.path.join(output_dir, "demo_article.md")
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        print(f"💾 文章已保存:")
        print(f"   JSON格式: {article_file}")
        print(f"   Markdown格式: {md_file}")
        print()
        
    except Exception as e:
        print(f"❌ 内容创作失败: {e}")
        import traceback
        traceback.print_exc()
        article = None

# 4. 动态导入格式化器
if article:
    print("🎨 步骤4: 排版优化")
    try:
        formatter_path = os.path.join(module_dir, "formatter", "content_formatter.py")
        
        spec = importlib.util.spec_from_file_location("content_formatter", formatter_path)
        formatter_module = importlib.util.module_from_spec(spec)
        formatter_module.logger = logging.getLogger("formatter")
        spec.loader.exec_module(formatter_module)
        
        ContentFormatter = formatter_module.ContentFormatter
        formatter = ContentFormatter()
        
        # 测试不同平台格式化
        platforms = ["wechat", "xiaohongshu"]
        
        for platform in platforms:
            formatted = formatter.format_for_platform(article, platform)
            
            print(f"✅ {platform} 格式化完成")
            print(f"   平台标题: {formatted['content']['formatted_title'][:40]}...")
            print(f"   生成标签: {', '.join(formatted['content']['tags'][:3])}")
            
            # 保存格式化内容
            platform_dir = os.path.join(output_dir, "formatted", platform)
            os.makedirs(platform_dir, exist_ok=True)
            
            formatted_file = os.path.join(platform_dir, f"demo_{platform}.json")
            with open(formatted_file, 'w', encoding='utf-8') as f:
                json.dump(formatted, f, ensure_ascii=False, indent=2)
            
            # 保存为文本
            text_file = formatted_file.replace('.json', '.txt')
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(f"平台: {formatted['platform_name']}\n")
                f.write(f"标题: {formatted['content']['formatted_title']}\n")
                f.write("="*50 + "\n\n")
                f.write(formatted['content']['formatted_content'])
                f.write("\n\n" + "="*50 + "\n")
                f.write(f"标签: {', '.join(formatted['content']['tags'])}\n")
                f.write(f"字数: {formatted['content']['word_count']}\n")
            
            print(f"💾 保存到: {formatted_file}")
            print()
        
    except Exception as e:
        print(f"❌ 格式化失败: {e}")
        import traceback
        traceback.print_exc()

# 5. 动态导入发布器
print("🚀 步骤5: 发布演示")
try:
    publisher_path = os.path.join(module_dir, "publisher", "content_publisher.py")
    
    spec = importlib.util.spec_from_file_location("content_publisher", publisher_path)
    publisher_module = importlib.util.module_from_spec(spec)
    publisher_module.logger = logging.getLogger("publisher")
    
    # 需要requests模块，如果没有就跳过
    try:
        import requests
        publisher_module.requests = requests
    except ImportError:
        print("⚠️  requests模块未安装，跳过Webhook发布演示")
        publisher_module.requests = None
    
    spec.loader.exec_module(publisher_module)
    
    ContentPublisher = publisher_module.ContentPublisher
    publisher = ContentPublisher()
    
    # 启用文件发布
    publisher.enable_platform("file", True)
    
    print(f"✅ 发布器初始化完成")
    print(f"   已启用平台: file (本地文件保存)")
    print()
    
    # 演示文件发布
    print("📁 演示文件发布...")
    
    # 创建一个简单的格式化内容用于发布
    demo_content = {
        "platform": "wechat",
        "platform_name": "微信公众号",
        "formatted_at": datetime.now().isoformat(),
        "content": {
            "formatted_title": "AI大模型技术最新突破与未来趋势",
            "formatted_content": "随着AI技术的快速发展，大模型已成为当前行业关注的重点...\n\n本文将从多个维度深入分析AI大模型的技术原理、应用场景及未来趋势...",
            "summary": "深度分析AI大模型技术趋势与发展前景",
            "tags": ["AI", "大模型", "技术分析", "未来趋势"],
            "word_count": 1500
        }
    }
    
    # 发布到文件
    result = publisher._publish_to_file(demo_content, "file")
    
    if result.get("success"):
        print(f"✅ 文件发布成功")
        print(f"   保存文件: {result.get('files', ['未知'])[0]}")
    else:
        print(f"❌ 文件发布失败: {result.get('error', '未知错误')}")
    
    print()
    
except Exception as e:
    print(f"❌ 发布器演示失败: {e}")
    import traceback
    traceback.print_exc()

# 6. 显示生成的文件
print("📁 生成文件检查")
output_dir = os.path.join(os.path.dirname(__file__), "output", "demo")

if os.path.exists(output_dir):
    print(f"输出目录: {output_dir}")
    print()
    
    file_count = 0
    for root, dirs, files in os.walk(output_dir):
        level = root.replace(output_dir, '').count(os.sep)
        indent = ' ' * 2 * level
        
        dir_name = os.path.basename(root)
        if dir_name:
            print(f"{indent}📂 {dir_name}/")
        
        for file in files:
            if file.endswith(('.json', '.md', '.txt')):
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, output_dir)
                file_size = os.path.getsize(filepath)
                
                print(f"{indent}  📄 {rel_path} ({file_size} bytes)")
                file_count += 1
    
    print(f"\n✅ 共生成 {file_count} 个文件")
else:
    print(f"⚠️  输出目录不存在: {output_dir}")

print()
print("=" * 60)
print("🎉 内容生产流水线演示完成!")
print("=" * 60)
print()
print("📊 演示总结:")
print(f"  执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"  输出目录: {output_dir}")
print(f"  完整流水线: 灵感 → 大纲 → 内容 → 排版 → 发布")
print()
print("💡 实际运行建议:")
print("  1. 安装必要的Python依赖: pip install --user requests")
print("  2. 配置 config/content_pipeline.json 文件")
print("  3. 启用AI增强功能（需要API密钥）")
print("  4. 配置各平台API实现自动发布")
print()
print("🔧 模块位置:")
print("  trendradar/outline/     - 大纲生成模块")
print("  trendradar/writer/      - 内容创作模块")
print("  trendradar/formatter/   - 排版优化模块")
print("  trendradar/publisher/   - 发布分发模块")
print()