#!/bin/bash
# 内容生产流水线启动脚本

set -e

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "========================================"
echo "  内容生产流水线启动脚本 v1.0"
echo "========================================"
echo "项目根目录: $PROJECT_ROOT"
echo "当前时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 检查Python环境
echo "🔍 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "✅ Python $PYTHON_VERSION 已安装"

# 检查依赖
echo ""
echo "🔍 检查Python依赖..."
cd "$PROJECT_ROOT"

if [ -f "requirements.txt" ]; then
    echo "安装依赖..."
    pip3 install -r requirements.txt
else
    echo "⚠️  未找到 requirements.txt，跳过依赖安装"
fi

# 创建必要目录
echo ""
echo "📁 创建目录结构..."
mkdir -p output/pipeline/{outlines,articles,formatted,published,runs}
mkdir -p logs
mkdir -p backup

echo "✅ 目录结构创建完成"

# 测试流水线
echo ""
echo "🧪 测试内容生产流水线..."
cd "$PROJECT_ROOT"

TEST_RESULT=$(python3 -c "
import sys
sys.path.append('.')
try:
    from trendradar.content_pipeline import ContentPipeline
    pipeline = ContentPipeline('config/content_pipeline.json')
    status = pipeline.get_status()
    print('✅ 流水线导入成功')
    print(f'   名称: {status[\"config_summary\"].get(\"pipeline_enabled\", \"N/A\")}')
    print(f'   最大文章数: {status[\"config_summary\"].get(\"max_articles_per_run\", \"N/A\")}')
except Exception as e:
    print(f'❌ 流水线导入失败: {e}')
    sys.exit(1)
")

echo "$TEST_RESULT"

if [[ $? -ne 0 ]]; then
    echo "❌ 流水线测试失败"
    exit 1
fi

# 显示配置
echo ""
echo "⚙️  当前配置:"
echo "----------------------------------------"
cat "$PROJECT_ROOT/config/content_pipeline.json" | python3 -c "
import json, sys
data = json.load(sys.stdin)
pipeline = data.get('pipeline', {})
print(f'流水线状态: {\"启用\" if pipeline.get(\"enabled\") else \"禁用\"}')
print(f'最大文章数: {pipeline.get(\"max_articles_per_run\", \"N/A\")}')
print(f'默认写作风格: {pipeline.get(\"default_writing_style\", \"N/A\")}')
print(f'自动发布: {\"是\" if pipeline.get(\"auto_publish\") else \"否\"}')
print(f'发布平台: {\", \".join(pipeline.get(\"publish_platforms\", []))}')
"

# 运行模式选择
echo ""
echo "🚀 选择运行模式:"
echo "  1) 完整流水线运行（使用测试数据）"
echo "  2) 仅查看状态"
echo "  3) 退出"
echo ""

read -p "请输入选择 (1-3): " choice

case $choice in
    1)
        echo ""
        echo "▶️  开始完整流水线运行..."
        cd "$PROJECT_ROOT"
        
        # 运行流水线
        python3 -m trendradar.content_pipeline --config config/content_pipeline.json --test
        
        echo ""
        echo "📊 运行完成，输出文件保存在: $PROJECT_ROOT/output/pipeline"
        ;;
    2)
        echo ""
        echo "📊 查看流水线状态..."
        cd "$PROJECT_ROOT"
        
        python3 -m trendradar.content_pipeline --config config/content_pipeline.json --status
        ;;
    3)
        echo "👋 退出"
        exit 0
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

echo ""
echo "========================================"
echo "  脚本执行完成"
echo "========================================"
echo ""
echo "📋 后续操作建议:"
echo "  1. 编辑 config/content_pipeline.json 调整配置"
echo "  2. 配置 AI_API_KEY 以启用AI增强功能"
echo "  3. 配置各平台API密钥以启用自动发布"
echo "  4. 设置定时任务（cron）自动运行"
echo ""
echo "📁 项目结构:"
echo "  trendradar/outline/     - 大纲生成模块"
echo "  trendradar/writer/      - 内容创作模块"
echo "  trendradar/formatter/   - 排版优化模块"
echo "  trendradar/publisher/   - 发布分发模块"
echo "  config/                 - 配置文件"
echo "  output/pipeline/        - 输出文件"
echo "  scripts/                - 工具脚本"
echo ""
echo "🔄 定时任务示例（每天9点和18点运行）:"
echo "  0 9,18 * * * cd $PROJECT_ROOT && python3 -m trendradar.content_pipeline --config config/content_pipeline.json"
echo ""