#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
英文单词学习系统 - 启动脚本

这个脚本自动处理依赖安装和应用启动
"""

import subprocess
import sys
import os

def print_banner():
    """打印欢迎横幅"""
    print("\n" + "="*60)
    print("  英文单词学习系统 - Spaced Repetition Learner")
    print("  基于艾宾浩斯遗忘曲线的科学记忆系统")
    print("="*60 + "\n")

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python版本过低！需要Python 3.8或更高版本")
        print(f"   当前版本: {version.major}.{version.minor}")
        sys.exit(1)
    print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro}")

def install_dependencies():
    """安装依赖包"""
    print("\n📦 正在检查依赖包...")

    requirements_file = "backend/requirements.txt"
    if not os.path.exists(requirements_file):
        print(f"❌ 找不到 {requirements_file}")
        sys.exit(1)

    try:
        # 尝试导入主要包
        required_packages = ['flask', 'flask_cors', 'apscheduler', 'requests']
        missing_packages = []

        for package in required_packages:
            try:
                __import__(package.replace('_', '-'))
            except ImportError:
                missing_packages.append(package)

        if missing_packages:
            print(f"⚠️  发现缺失的包: {', '.join(missing_packages)}")
            print("📥 正在安装依赖包...")

            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", requirements_file],
                cwd=os.path.dirname(os.path.abspath(__file__))
            )

            if result.returncode != 0:
                print("❌ 依赖安装失败！")
                sys.exit(1)
            print("✅ 依赖安装完成")
        else:
            print("✅ 所有依赖包已就绪")

    except Exception as e:
        print(f"❌ 检查依赖时出错: {e}")
        sys.exit(1)

def create_data_directories():
    """创建数据目录"""
    print("\n📁 正在检查数据目录...")

    data_dir = "backend/data"
    os.makedirs(data_dir, exist_ok=True)
    print(f"✅ 数据目录就绪: {data_dir}")

def start_server():
    """启动应用服务器"""
    print("\n🚀 正在启动应用服务器...")
    print("""
    ╔════════════════════════════════════════════════════════╗
    ║                                                        ║
    ║  📌 应用已启动！                                      ║
    ║                                                        ║
    ║  🌐 访问地址: http://localhost:5000                  ║
    ║                                                        ║
    ║  功能导航:                                            ║
    ║    📊 主页: http://localhost:5000                    ║
    ║    📚 学习: http://localhost:5000/study              ║
    ║    ✏️  复习: http://localhost:5000/review            ║
    ║    ⚙️  设置: http://localhost:5000/settings          ║
    ║                                                        ║
    ║  💡 提示:                                            ║
    ║    • 按 Ctrl+C 停止服务器                           ║
    ║    • 首次使用请先在设置页面配置邮件提醒             ║
    ║    • 查看 README.md 了解详细使用说明                ║
    ║                                                        ║
    ╚════════════════════════════════════════════════════════╝
    """)

    try:
        # 启动Flask应用
        project_root = os.path.dirname(os.path.abspath(__file__))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        from backend.app import create_app

        app = create_app()
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=True
        )

    except KeyboardInterrupt:
        print("\n\n⛔ 应用已停止")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        sys.exit(1)

def main():
    """主函数"""
    print_banner()

    # 执行启动步骤
    check_python_version()
    install_dependencies()
    create_data_directories()
    start_server()

if __name__ == "__main__":
    main()
