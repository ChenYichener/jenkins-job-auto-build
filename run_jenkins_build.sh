 #!/bin/bash

# Jenkins 自动化构建脚本
# 使用方法: ./run_jenkins_build.sh

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Jenkins 自动化构建脚本${NC}"
echo "================================="

# 检查配置文件是否存在
if [ ! -f "jenkins_config.json" ]; then
    echo -e "${YELLOW}⚠️  配置文件不存在，正在创建模板...${NC}"
    cp jenkins_config.json.template jenkins_config.json
    echo -e "${RED}❌ 请先编辑 jenkins_config.json 文件，填入正确的配置信息${NC}"
    echo "配置项说明:"
    echo "- jenkins_url: Jenkins 服务器地址"
    echo "- username: Jenkins 用户名"
    echo "- password_or_token: Jenkins 密码或 API Token"
    echo "- polling_url: 需要轮询的接口地址"
    echo "- 其他配置项可根据需要调整"
    exit 1
fi

# 读取配置文件
CONFIG_FILE="jenkins_config.json"

# 使用 Python 解析 JSON 配置
JENKINS_URL=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['jenkins_url'])")
USERNAME=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['username'])")
PASSWORD=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['password_or_token'])")
POLLING_URL=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['polling_url'])")
BRANCH=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['branch'])")
FIRST_JOB=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['first_job'])")
SECOND_JOB=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['second_job'])")

echo "配置信息:"
echo "- Jenkins 地址: $JENKINS_URL"
echo "- 用户名: $USERNAME"
echo "- 分支: $BRANCH"
echo "- 第一个任务: $FIRST_JOB"
echo "- 第二个任务: $SECOND_JOB"
echo "- 轮询接口: $POLLING_URL"
echo ""

# 确认执行
read -p "确认开始执行构建流程? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "取消执行"
    exit 1
fi

# 执行 Python 脚本
echo -e "${GREEN}开始执行构建流程...${NC}"
python3 jenkins_auto_build_enhanced.py \
    --jenkins-url "$JENKINS_URL" \
    --username "$USERNAME" \
    --password "$PASSWORD" \
    --polling-url "$POLLING_URL" \
    --branch "$BRANCH" \
    --first-job "$FIRST_JOB" \
    --second-job "$SECOND_JOB"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 构建流程完成!${NC}"
else
    echo -e "${RED}❌ 构建流程失败!${NC}"
    exit 1
fi