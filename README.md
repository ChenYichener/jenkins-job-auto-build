# Jenkins 自动化构建工具 🚀

一个强大而灵活的Jenkins自动化构建工具，支持多任务顺序执行、智能中断处理、完整日志记录等功能。

## ✨ 主要特性

- 🔄 **多任务支持** - 支持任意数量的Jenkins任务按顺序执行
- 🔒 **安全认证** - 自动处理CSRF Token，支持用户名密码和API Token
- 📝 **完整日志** - 所有操作记录到文件，带时间戳，支持控制台同步输出
- ⚡ **精确跟踪** - 准确跟踪每次触发的构建，避免混淆历史构建
- 🛑 **智能中断** - Ctrl+C时可选择是否停止正在运行的Jenkins任务
- ⏰ **灵活等待** - 任务间可配置等待时间
- 🔧 **向后兼容** - 完全兼容旧版本配置
- 🎯 **参数化构建** - 支持为每个任务传递独立的构建参数

## 📦 安装

### 环境要求
- Python 3.6+
- 网络连接到Jenkins服务器

### 快速安装
```bash
# 克隆项目
git clone https://github.com/your-username/jenkins-auto-build.git
cd jenkins-auto-build

# 安装依赖
pip install -r requirements.txt

# 复制配置模板
cp jenkins_config.json.template jenkins_config.json

# 编辑配置文件
vi jenkins_config.json
```

## 🚀 快速开始

### 1. 配置Jenkins信息
编辑 `jenkins_config.json` 文件：

```json
{
  "jenkins_url": "http://your-jenkins-server:8080/",
  "username": "your-username",
  "password_or_token": "your-api-token",
  "branch": "master",
  "jobs": [
    {
      "name": "build-app",
      "description": "构建应用",
      "parameters": {}
    },
    {
      "name": "deploy-app", 
      "description": "部署应用",
      "parameters": {
        "ENV": "production"
      }
    }
  ],
  "wait_between_builds": 30
}
```

### 2. 测试连接
```bash
python3 jenkins_auto_build_enhanced.py --test
```

### 3. 查看配置
```bash
python3 jenkins_auto_build_enhanced.py --dry-run
```

### 4. 执行构建
```bash
python3 jenkins_auto_build_enhanced.py
```

## 📋 配置说明

### 基本配置

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `jenkins_url` | string | ✅ | Jenkins服务器地址 |
| `username` | string | ✅ | Jenkins用户名 |
| `password_or_token` | string | ✅ | 密码或API Token（推荐） |
| `branch` | string | ❌ | 构建分支，默认master |
| `wait_between_builds` | number | ❌ | 任务间等待秒数，默认30 |

### 任务配置

#### 新格式（推荐）
```json
{
  "jobs": [
    {
      "name": "job-name",
      "description": "任务描述",
      "parameters": {
        "PARAM1": "value1",
        "PARAM2": "value2"
      }
    }
  ]
}
```

#### 简化格式
```json
{
  "jobs": ["job1", "job2", "job3"]
}
```

#### 向后兼容格式
```json
{
  "first_job": "job1",
  "second_job": "job2"
}
```

### 高级配置

```json
{
  "enable_polling": false,
  "polling_url": "http://api-endpoint/status",
  "polling_config": {
    "max_attempts": 60,
    "interval_seconds": 30,
    "expected_status_code": 200
  },
  "build_config": {
    "timeout_seconds": 1800,
    "check_interval_seconds": 30
  }
}
```

## 🎯 使用示例

### 示例1：简单的2任务流程
```json
{
  "jenkins_url": "http://jenkins.company.com:8080/",
  "username": "developer",
  "password_or_token": "abc123def456",
  "jobs": [
    {
      "name": "build-frontend",
      "description": "构建前端应用"
    },
    {
      "name": "deploy-frontend",
      "description": "部署前端应用"
    }
  ]
}
```

### 示例2：复杂的CI/CD流程
```json
{
  "jobs": [
    {
      "name": "unit-tests",
      "description": "单元测试",
      "parameters": {
        "TEST_SUITE": "unit",
        "COVERAGE": "true"
      }
    },
    {
      "name": "integration-tests", 
      "description": "集成测试",
      "parameters": {
        "TEST_ENV": "staging",
        "PARALLEL": "4"
      }
    },
    {
      "name": "build-docker",
      "description": "构建Docker镜像",
      "parameters": {
        "IMAGE_TAG": "latest",
        "PUSH_REGISTRY": "true"
      }
    },
    {
      "name": "deploy-production",
      "description": "生产部署",
      "parameters": {
        "REPLICAS": "3",
        "STRATEGY": "rolling"
      }
    }
  ],
  "wait_between_builds": 60
}
```

## 🔧 命令行选项

```bash
# 基本使用
python3 jenkins_auto_build_enhanced.py

# 指定配置文件
python3 jenkins_auto_build_enhanced.py --config my-config.json

# 测试连接
python3 jenkins_auto_build_enhanced.py --test

# 干运行（查看配置）
python3 jenkins_auto_build_enhanced.py --dry-run

# 使用Shell脚本
./run_jenkins_build.sh
```

## 📝 日志记录

- **控制台输出** - 实时显示执行进度
- **文件日志** - 所有操作记录到 `run.log`
- **时间戳** - 每行日志都有精确时间
- **结构化** - 清晰的步骤分隔和状态标识

**日志示例：**
```
2025-07-18 12:00:00 - 🚀 开始自动化构建流程...
2025-07-18 12:00:01 - ✅ 成功获取 Jenkins crumb: Jenkins-Crumb
2025-07-18 12:00:02 - 📋 步骤1: 构建任务 [build-app] - 构建应用
2025-07-18 12:00:03 - 🔢 获取到构建号: #123
2025-07-18 12:05:30 - ✅ 构建成功: build-app #123
2025-07-18 12:05:30 - ⏰ 等待 30 秒后开始下一个任务...
```

## 🛑 中断处理

按 `Ctrl+C` 中断程序时：

```
🛑 检测到中断信号...
当前正在运行: build-app #123

是否要停止当前正在运行的Jenkins任务? (y/n): y
正在停止任务: build-app #123
✅ 任务已成功停止
程序退出
```

## 📚 获取Jenkins API Token

1. 登录Jenkins
2. 点击右上角用户名 → **Configure**
3. 找到 **API Token** 部分
4. 点击 **Add new Token**
5. 输入Token名称，点击 **Generate**
6. 复制生成的Token

## ❗ 故障排除

### 常见问题

**1. 403 Forbidden错误**
```
❌ 触发构建失败，状态码: 403
```
- 检查用户名和密码/Token是否正确
- 确保用户有构建权限

**2. 400 Bad Request错误**
```
❌ 触发构建失败，状态码: 400
```
- 检查任务名称是否存在
- 确认任务参数是否正确

**3. 连接超时**
```
❌ Jenkins 连接异常: Connection timeout
```
- 检查Jenkins URL是否正确
- 确认网络连接正常

**4. 构建参数错误**
```
❌ 参数 'ENV' 不存在
```
- 确保Jenkins任务已配置相应参数
- 检查参数名称大小写

### 调试技巧

1. **使用测试模式**
   ```bash
   python3 jenkins_auto_build_enhanced.py --test
   ```

2. **查看详细日志**
   ```bash
   tail -f run.log
   ```

3. **干运行检查配置**
   ```bash
   python3 jenkins_auto_build_enhanced.py --dry-run
   ```

## 🤝 贡献

欢迎提交Issue和Pull Request！

### 开发环境设置
```bash
# 克隆仓库
git clone https://github.com/your-username/jenkins-auto-build.git
cd jenkins-auto-build

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

感谢所有使用和贡献这个项目的开发者！

---

**⭐ 如果这个项目对你有帮助，请给它一个星星！**