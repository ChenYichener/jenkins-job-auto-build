 #!/usr/bin/env python3
"""
Jenkins 自动化构建脚本 - 增强版
支持从配置文件读取参数，更灵活的配置选项
"""

import requests
import time
import json
import sys
import argparse
import os
from urllib.parse import urljoin
import base64
import logging
from datetime import datetime
import signal

class JenkinsAutoBuildEnhanced:
    def __init__(self, config_file='jenkins_config.json'):
        """
        初始化 Jenkins 自动构建类
        
        Args:
            config_file: 配置文件路径
        """
        self.config = self.load_config(config_file)
        self.session = requests.Session()
        
        # 设置认证
        auth_string = f"{self.config['username']}:{self.config['password_or_token']}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        self.session.headers.update({
            'Authorization': f'Basic {encoded_auth}'
        })
        
        # 设置日志记录器
        self.setup_logger()
        
        # 跟踪当前运行的任务
        self.current_job = None
        self.current_build_number = None
        
        # 设置信号处理器
        self.setup_signal_handlers()
        
        # 获取 CSRF token (crumb)
        self.crumb = self.get_crumb()
        
    def setup_logger(self):
        """
        设置日志记录器，同时输出到控制台和文件
        """
        # 创建日志记录器
        self.logger = logging.getLogger('jenkins_auto_build')
        self.logger.setLevel(logging.INFO)
        
        # 清除已有的处理器
        self.logger.handlers.clear()
        
        # 创建格式化器
        formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # 文件处理器
        file_handler = logging.FileHandler('run.log', mode='a', encoding='utf-8')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # 防止日志重复
        self.logger.propagate = False
        
    def log(self, message):
        """
        统一的日志输出方法
        
        Args:
            message: 要输出的消息
        """
        self.logger.info(message)
        
    def setup_signal_handlers(self):
        """
        设置信号处理器
        """
        def signal_handler(signum, frame):
            self.handle_interrupt()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
    def handle_interrupt(self):
        """
        处理中断信号
        """
        self.log("\n🛑 检测到中断信号...")
        
        if self.current_job and self.current_build_number:
            self.log(f"当前正在运行: {self.current_job} #{self.current_build_number}")
            
            try:
                # 询问用户是否要停止当前构建
                while True:
                    choice = input("\n是否要停止当前正在运行的Jenkins任务? (y/n): ").strip().lower()
                    if choice in ['y', 'yes', '是']:
                        self.log(f"正在停止任务: {self.current_job} #{self.current_build_number}")
                        if self.stop_build(self.current_job, self.current_build_number):
                            self.log("✅ 任务已成功停止")
                        else:
                            self.log("❌ 停止任务失败")
                        break
                    elif choice in ['n', 'no', '否']:
                        self.log("保留Jenkins任务继续运行")
                        break
                    else:
                        print("请输入 y 或 n")
            except:
                self.log("无法获取用户输入，保留Jenkins任务继续运行")
        
        self.log("程序退出")
        sys.exit(1)
        
    def stop_build(self, job_name, build_number):
        """
        停止指定的构建
        
        Args:
            job_name: 任务名称
            build_number: 构建号
            
        Returns:
            bool: 是否成功停止
        """
        try:
            jenkins_url = self.config['jenkins_url'].rstrip('/')
            url = f"{jenkins_url}/job/{job_name}/{build_number}/stop"
            
            # 准备请求头
            headers = {}
            if self.crumb:
                headers[self.crumb['crumbRequestField']] = self.crumb['crumb']
            
            response = self.session.post(url, headers=headers)
            
            if response.status_code in [200, 201, 302]:  # 302也是成功的重定向
                return True
            else:
                self.log(f"停止构建失败，状态码: {response.status_code}")
                self.log(f"响应内容: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"停止构建异常: {str(e)}")
            return False
        
    def get_crumb(self):
        """
        获取 Jenkins CSRF token (crumb)
        
        Returns:
            dict: 包含crumb信息的字典，如果获取失败则返回None
        """
        try:
            jenkins_url = self.config['jenkins_url'].rstrip('/')
            crumb_url = f"{jenkins_url}/crumbIssuer/api/json"
            
            response = self.session.get(crumb_url)
            
            if response.status_code == 200:
                crumb_data = response.json()
                self.log(f"✅ 成功获取 Jenkins crumb: {crumb_data.get('crumbRequestField')}")
                return crumb_data
            else:
                self.log(f"⚠️  获取 crumb 失败，状态码: {response.status_code}")
                self.log("Jenkins可能未启用CSRF保护，或者版本较老")
                return None
                
        except Exception as e:
            self.log(f"⚠️  获取 crumb 异常: {str(e)}")
            self.log("将尝试不使用crumb继续执行")
            return None
        
    def load_config(self, config_file):
        """
        加载配置文件
        
        Args:
            config_file: 配置文件路径
            
        Returns:
            dict: 配置信息
        """
        if not os.path.exists(config_file):
            print(f"❌ 配置文件不存在: {config_file}")
            print("请先创建配置文件，可以从 jenkins_config.json.template 复制")
            sys.exit(1)
            
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # 验证必要的配置项
            required_fields = ['jenkins_url', 'username', 'password_or_token']
            for field in required_fields:
                if field not in config:
                    print(f"❌ 配置文件缺少必要字段: {field}")
                    sys.exit(1)
            
            # 如果启用了轮询，验证轮询URL
            if config.get('enable_polling', False):
                if 'polling_url' not in config:
                    print(f"❌ 启用轮询时必须配置 polling_url 字段")
                    sys.exit(1)
                    
            return config
            
        except json.JSONDecodeError as e:
            print(f"❌ 配置文件格式错误: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ 读取配置文件失败: {e}")
            sys.exit(1)
    
    def trigger_build(self, job_name, branch=None, parameters=None):
        """
        触发 Jenkins 构建
        
        Args:
            job_name: 任务名称
            branch: 分支名称
            parameters: 构建参数字典
            
        Returns:
            int: 构建号，如果失败则返回None
        """
        try:
            branch = branch or self.config.get('branch', 'master')
            
            # 构建 URL
            jenkins_url = self.config['jenkins_url'].rstrip('/')
            
            # 准备请求头
            headers = {}
            if self.crumb:
                headers[self.crumb['crumbRequestField']] = self.crumb['crumb']
                self.log(f"🔒 使用 CSRF token: {self.crumb['crumbRequestField']}")
            
            # 总是使用带参数的构建，因为Jenkins任务需要BRANCH参数
            url = f"{jenkins_url}/job/{job_name}/buildWithParameters"
            build_params = {"BRANCH": branch}
            
            # 如果有额外参数，添加到构建参数中
            if parameters:
                build_params.update(parameters)
                self.log(f"正在触发带参数构建: {job_name} (分支: {branch})")
                self.log(f"构建参数: {build_params}")
            else:
                self.log(f"正在触发构建: {job_name} (分支: {branch})")
                self.log(f"构建参数: {build_params}")
                
            response = self.session.post(url, data=build_params, headers=headers)
            
            self.log(f"构建 URL: {url}")
            
            if response.status_code in [200, 201]:
                self.log(f"✅ 成功触发构建: {job_name}")
                
                # 获取构建号
                build_number = self.get_build_number_from_queue(response, job_name)
                if build_number:
                    self.log(f"🔢 获取到构建号: #{build_number}")
                    return build_number
                else:
                    self.log(f"⚠️  无法获取构建号，将使用最新构建")
                    return -1  # -1表示使用lastBuild
            else:
                self.log(f"❌ 触发构建失败: {job_name}")
                self.log(f"状态码: {response.status_code}")
                self.log(f"响应内容: {response.text}")
                return None
                
        except Exception as e:
            self.log(f"❌ 触发构建异常: {job_name}, 错误: {str(e)}")
            return None
            
    def get_build_number_from_queue(self, response, job_name):
        """
        从队列响应中获取构建号
        
        Args:
            response: HTTP响应对象
            job_name: 任务名称
            
        Returns:
            int: 构建号，如果获取失败则返回None
        """
        try:
            # 从Location头获取队列item ID
            location = response.headers.get('Location')
            if not location:
                self.log(f"⚠️  响应中没有Location头")
                return None
            
            self.log(f"📍 队列位置: {location}")
            
            # 轮询队列直到获取构建号
            jenkins_url = self.config['jenkins_url'].rstrip('/')
            queue_url = location
            if not queue_url.startswith('http'):
                queue_url = f"{jenkins_url}{location}" if location.startswith('/') else f"{jenkins_url}/{location}"
            
            queue_api_url = f"{queue_url}api/json"
            
            for attempt in range(30):  # 最多等待30次，每次2秒
                try:
                    queue_response = self.session.get(queue_api_url)
                    if queue_response.status_code == 200:
                        queue_data = queue_response.json()
                        
                        # 检查是否已经开始构建
                        executable = queue_data.get('executable')
                        if executable:
                            build_number = executable.get('number')
                            if build_number:
                                return build_number
                        
                        # 检查是否被取消或失败
                        if queue_data.get('cancelled'):
                            self.log(f"❌ 构建被取消")
                            return None
                        
                        self.log(f"⏳ 等待队列分配构建号... (尝试 {attempt + 1}/30)")
                        time.sleep(2)
                    else:
                        self.log(f"⚠️  队列API调用失败，状态码: {queue_response.status_code}")
                        break
                        
                except Exception as e:
                    self.log(f"⚠️  队列查询异常: {str(e)}")
                    break
            
            self.log(f"⚠️  无法从队列获取构建号，将使用最新构建")
            return None
            
        except Exception as e:
            self.log(f"⚠️  解析队列响应异常: {str(e)}")
            return None
    
    def get_job_status(self, job_name, build_number=None):
        """
        获取任务状态
        
        Args:
            job_name: 任务名称
            build_number: 构建号，如果为None或-1则获取最新构建
            
        Returns:
            dict: 任务状态信息
        """
        try:
            jenkins_url = self.config['jenkins_url'].rstrip('/')
            
            if build_number and build_number != -1:
                url = f"{jenkins_url}/job/{job_name}/{build_number}/api/json"
            else:
                url = f"{jenkins_url}/job/{job_name}/lastBuild/api/json"
            
            response = self.session.get(url)
            
            if response.status_code == 200:
                return response.json()
            else:
                self.log(f"⚠️ 获取任务状态失败: {job_name}, 状态码: {response.status_code}")
                return None
                
        except Exception as e:
            self.log(f"❌ 获取任务状态异常: {job_name}, 错误: {str(e)}")
            return None
    
    def wait_for_build_completion(self, job_name, build_number=None):
        """
        等待构建完成
        
        Args:
            job_name: 任务名称
            build_number: 构建号，如果为None或-1则等待最新构建
            
        Returns:
            bool: 构建是否成功
        """
        build_config = self.config.get('build_config', {})
        timeout = build_config.get('timeout_seconds', 1800)
        check_interval = build_config.get('check_interval_seconds', 30)
        
        build_desc = f"{job_name} #{build_number}" if build_number and build_number != -1 else f"{job_name} (最新)"
        self.log(f"等待构建完成: {build_desc} (超时: {timeout}秒)")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_job_status(job_name, build_number)
            
            if status:
                result = status.get('result')
                building = status.get('building', False)
                actual_build_number = status.get('number', 'N/A')
                
                # 如果我们指定了构建号，验证返回的是正确的构建
                if build_number and build_number != -1 and actual_build_number != build_number:
                    self.log(f"⚠️  期望构建号 #{build_number}，但获取到 #{actual_build_number}")
                
                if not building and result:
                    if result == 'SUCCESS':
                        self.log(f"✅ 构建成功: {job_name} #{actual_build_number}")
                        return True
                    else:
                        self.log(f"❌ 构建失败: {job_name} #{actual_build_number}, 结果: {result}")
                        build_url = status.get('url', '')
                        if build_url:
                            self.log(f"构建详情: {build_url}")
                        return False
                else:
                    elapsed = int(time.time() - start_time)
                    self.log(f"⏳ 构建进行中: {job_name} #{actual_build_number} (已用时: {elapsed}秒)")
            
            time.sleep(check_interval)
        
        self.log(f"❌ 构建超时: {build_desc}")
        return False
    
    def poll_interface(self, interface_url=None):
        """
        轮询接口直到成功
        
        Args:
            interface_url: 接口地址，如果为 None 则使用配置文件中的地址
            
        Returns:
            bool: 接口是否调用成功
        """
        interface_url = interface_url or self.config['polling_url']
        polling_config = self.config.get('polling_config', {})
        
        max_attempts = polling_config.get('max_attempts', 60)
        interval = polling_config.get('interval_seconds', 30)
        expected_status = polling_config.get('expected_status_code', 200)
        
        self.log(f"开始轮询接口: {interface_url}")
        self.log(f"配置: 最大尝试 {max_attempts} 次，间隔 {interval} 秒，期望状态码 {expected_status}")
        
        for attempt in range(1, max_attempts + 1):
            try:
                self.log(f"第 {attempt}/{max_attempts} 次尝试...")
                
                response = requests.get(interface_url, timeout=10)
                
                self.log(f"响应状态码: {response.status_code}")
                
                if response.status_code == expected_status:
                    self.log(f"✅ 接口调用成功!")
                    try:
                        # 尝试解析 JSON 响应
                        json_response = response.json()
                        self.log(f"响应内容: {json.dumps(json_response, indent=2, ensure_ascii=False)}")
                    except:
                        self.log(f"响应内容: {response.text[:200]}...")
                    return True
                else:
                    self.log(f"⏳ 接口调用失败, 状态码: {response.status_code}")
                    if response.text:
                        self.log(f"响应内容: {response.text[:200]}...")
                    
            except Exception as e:
                self.log(f"⏳ 接口调用异常: {str(e)}")
            
            if attempt < max_attempts:
                self.log(f"等待 {interval} 秒后重试...")
                time.sleep(interval)
        
        self.log(f"❌ 接口轮询失败，已达到最大尝试次数: {max_attempts}")
        return False
    
    def get_jobs_list(self):
        """
        获取任务列表，支持新格式和向后兼容
        
        Returns:
            list: 任务列表，每个任务包含 name, description, parameters
        """
        jobs = []
        
        # 优先使用新的 jobs 配置
        if 'jobs' in self.config and self.config['jobs']:
            for job in self.config['jobs']:
                if isinstance(job, dict) and 'name' in job:
                    jobs.append({
                        'name': job['name'],
                        'description': job.get('description', job['name']),
                        'parameters': job.get('parameters', {})
                    })
                elif isinstance(job, str):
                    jobs.append({
                        'name': job,
                        'description': job,
                        'parameters': {}
                    })
        else:
            # 向后兼容：使用 first_job 和 second_job
            first_job = self.config.get('first_job', 'tdms-stock-boot')
            second_job = self.config.get('second_job', 'tdms-stock-boot-slave-rights-collection')
            
            jobs.append({
                'name': first_job,
                'description': '第一个任务',
                'parameters': {}
            })
            
            if second_job and second_job != first_job:
                jobs.append({
                    'name': second_job,
                    'description': '第二个任务',
                    'parameters': {}
                })
        
        return jobs

    def run_build_workflow(self):
        """
        运行完整的构建工作流
        """
        branch = self.config.get('branch', 'master')
        
        # 检查是否需要接口轮询（向后兼容）
        enable_polling = self.config.get('enable_polling', False)
        
        # 获取等待时间配置
        wait_time = self.config.get('wait_between_builds', 30)
        
        # 获取任务列表
        jobs = self.get_jobs_list()
        
        if not jobs:
            self.log("❌ 没有配置任何任务")
            return False
        
        self.log("🚀 开始自动化构建流程...")
        self.log("=" * 60)
        self.log(f"配置信息:")
        self.log(f"  Jenkins: {self.config['jenkins_url']}")
        self.log(f"  用户: {self.config['username']}")
        self.log(f"  分支: {branch}")
        self.log(f"  任务数量: {len(jobs)} 个")
        for i, job in enumerate(jobs, 1):
            self.log(f"    {i}. {job['name']} - {job['description']}")
        self.log(f"  任务间等待时间: {wait_time} 秒")
        if enable_polling:
            self.log(f"  轮询接口: {self.config.get('polling_url', 'N/A')}")
        else:
            self.log(f"  模式: 直接构建模式（无需轮询外部接口）")
        self.log("=" * 60)
        
        # 循环执行所有任务
        for i, job in enumerate(jobs):
            job_name = job['name']
            job_desc = job['description']
            job_params = job['parameters']
            
            self.log(f"\n📋 步骤{i+1}: 构建任务 [{job_name}] - {job_desc}")
            self.log("-" * 50)
            
            # 触发构建
            build_number = self.trigger_build(job_name, branch, job_params if job_params else None)
            if build_number is None:
                self.log(f"❌ 任务 {job_name} 触发失败，终止流程")
                return False
            
            # 更新当前运行任务跟踪
            self.current_job = job_name
            self.current_build_number = build_number
            
            # 等待任务完成
            if not self.wait_for_build_completion(job_name, build_number):
                self.log(f"❌ 任务 {job_name} 构建失败，终止流程")
                return False
            
            # 任务完成，清除跟踪
            self.current_job = None
            self.current_build_number = None
            
            self.log(f"✅ 任务 {job_name} 构建成功！")
            
            # 如果不是最后一个任务，进行等待和可选的接口轮询
            if i < len(jobs) - 1:  # 不是最后一个任务
                next_job = jobs[i + 1]
                
                # 可选的接口轮询（仅在第一个任务后）
                if i == 0 and enable_polling:
                    self.log(f"\n📡 接口轮询检查")
                    self.log("-" * 40)
                    if not self.poll_interface():
                        self.log("❌ 接口轮询失败，终止流程")
                        return False
                
                # 等待指定时间后执行下一个任务
                if wait_time > 0:
                    self.log(f"\n⏰ 等待 {wait_time} 秒后开始下一个任务 [{next_job['name']}]...")
                    self.log("-" * 40)
                    for remaining in range(wait_time, 0, -1):
                        print(f"⏳ 倒计时: {remaining} 秒", end='\r')
                        time.sleep(1)
                    self.log(f"✅ 等待完成，开始下一个任务!")
                else:
                    self.log(f"\n🚀 立即开始下一个任务 [{next_job['name']}]...")
        
        self.log("\n" + "=" * 60)
        self.log("🎉 所有任务完成!")
        self.log("=" * 60)
        return True
    
    def test_connection(self):
        """
        测试 Jenkins 连接
        """
        try:
            jenkins_url = self.config['jenkins_url'].rstrip('/')
            url = f"{jenkins_url}/api/json"
            
            self.log(f"测试 Jenkins 连接: {jenkins_url}")
            response = self.session.get(url)
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Jenkins 连接成功")
                self.log(f"版本: {data.get('version', 'Unknown')}")
                return True
            else:
                self.log(f"❌ Jenkins 连接失败，状态码: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Jenkins 连接异常: {str(e)}")
            return False


def main():
    parser = argparse.ArgumentParser(description='Jenkins 自动化构建脚本 - 增强版')
    parser.add_argument('--config', default='jenkins_config.json', help='配置文件路径')
    parser.add_argument('--test', action='store_true', help='测试 Jenkins 连接')
    parser.add_argument('--dry-run', action='store_true', help='干运行模式，不执行实际构建')
    
    args = parser.parse_args()
    
    try:
        # 创建自动构建实例
        jenkins_builder = JenkinsAutoBuildEnhanced(args.config)
        
        if args.test:
            # 测试连接
            if jenkins_builder.test_connection():
                print("✅ 连接测试通过")
                sys.exit(0)
            else:
                print("❌ 连接测试失败")
                sys.exit(1)
        
        if args.dry_run:
            print("🔍 干运行模式 - 仅显示配置信息，不执行实际操作")
            print(f"配置文件: {args.config}")
            print(f"Jenkins URL: {jenkins_builder.config['jenkins_url']}")
            print(f"用户名: {jenkins_builder.config['username']}")
            
            # 显示任务列表
            jobs = jenkins_builder.get_jobs_list()
            print(f"任务数量: {len(jobs)} 个")
            for i, job in enumerate(jobs, 1):
                print(f"  {i}. {job['name']} - {job['description']}")
                if job['parameters']:
                    print(f"     参数: {job['parameters']}")
            
            # 向后兼容信息
            if 'first_job' in jenkins_builder.config or 'second_job' in jenkins_builder.config:
                print("\n向后兼容配置:")
                print(f"  第一个任务: {jenkins_builder.config.get('first_job', 'N/A')}")
                print(f"  第二个任务: {jenkins_builder.config.get('second_job', 'N/A')}")
            
            polling_url = jenkins_builder.config.get('polling_url', 'N/A')
            print(f"轮询接口: {polling_url}")
            print(f"启用轮询: {jenkins_builder.config.get('enable_polling', False)}")
            print(f"任务间等待时间: {jenkins_builder.config.get('wait_between_builds', 30)} 秒")
            sys.exit(0)
        
        # 运行构建工作流
        success = jenkins_builder.run_build_workflow()
        
        if success:
            print("✅ 构建流程完成")
            sys.exit(0)
        else:
            print("❌ 构建流程失败")
            sys.exit(1)
            
    except KeyboardInterrupt:
        # 信号处理器已经处理了中断逻辑
        pass
    except Exception as e:
        print(f"❌ 程序异常: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()