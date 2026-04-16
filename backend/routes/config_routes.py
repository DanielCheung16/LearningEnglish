from flask import Blueprint, request, jsonify
import json
import os
from datetime import datetime
from backend.modules.email_manager import EmailManager

config_bp = Blueprint('config', __name__, url_prefix='/api/config')


def get_config_file(data_dir: str = "backend/data") -> str:
    """获取配置文件路径"""
    return os.path.join(data_dir, "user_config.json")


def read_config() -> dict:
    """读取配置文件"""
    config_file = get_config_file()
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return _get_default_config()


def _get_default_config() -> dict:
    """获取默认配置"""
    return {
        "user_info": {
            "email": "",
            "name": ""
        },
        "email_settings": {
            "enable_reminders": False,
            "reminder_frequency": "daily",
            "reminder_time": "09:00",
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "sender_email": "",
            "app_password": "",
            "last_sent_date": ""
        },
        "review_settings": {
            "intervals": [1, 3, 7, 15, 30, 60]
        }
    }


def write_config(config: dict):
    """写入配置文件"""
    config_file = get_config_file()
    os.makedirs(os.path.dirname(config_file), exist_ok=True)
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


@config_bp.route('', methods=['GET'])
def get_config():
    """获取用户配置"""
    try:
        config = read_config()
        return jsonify({
            "success": True,
            "data": config
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@config_bp.route('', methods=['PUT'])
def update_config():
    """更新用户配置"""
    try:
        data = request.get_json()

        current_config = read_config()

        # 更新用户信息
        if "user_info" in data:
            current_config["user_info"].update(data["user_info"])

        # 更新邮件设置
        if "email_settings" in data:
            current_config["email_settings"].update(data["email_settings"])

        # 更新复习设置
        if "review_settings" in data:
            current_config["review_settings"].update(data["review_settings"])

        write_config(current_config)

        return jsonify({
            "success": True,
            "message": "配置已更新",
            "data": current_config
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@config_bp.route('/email-test', methods=['POST'])
def test_email_config():
    """
    测试邮件配置是否正确

    请求体:
    {
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "sender_email": "your-email@gmail.com",
        "app_password": "your-app-password"
    }
    """
    try:
        data = request.get_json()

        smtp_server = data.get("smtp_server", "smtp.gmail.com")
        smtp_port = data.get("smtp_port", 587)
        sender_email = data.get("sender_email")
        app_password = data.get("app_password")

        if not sender_email or not app_password:
            return jsonify({
                "success": False,
                "error": "请提供邮箱和密码"
            }), 400

        # 测试连接
        test_result = EmailManager.test_email_configuration(
            smtp_server=smtp_server,
            smtp_port=smtp_port,
            sender_email=sender_email,
            sender_password=app_password
        )

        if test_result.get("success"):
            # 尝试发送测试邮件
            test_email_html = EmailManager.generate_test_email()
            send_result = EmailManager.send_email(
                smtp_server=smtp_server,
                smtp_port=smtp_port,
                sender_email=sender_email,
                sender_password=app_password,
                recipient_email=sender_email,
                subject="✅ 邮件配置测试 - 英文单词学习系统",
                body=test_email_html,
                is_html=True
            )

            return jsonify({
                "success": send_result.get("success"),
                "message": "测试邮件已发送，请检查邮箱" if send_result.get("success") else send_result.get("error"),
                "email": sender_email
            })
        else:
            return jsonify({
                "success": False,
                "error": test_result.get("error", "连接失败")
            }), 400

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@config_bp.route('/reminder-time', methods=['PUT'])
def update_reminder_time():
    """
    更新邮件提醒时间

    请求体:
    {
        "reminder_time": "09:00"
    }
    """
    try:
        data = request.get_json()
        reminder_time = data.get("reminder_time", "09:00")

        # 验证时间格式
        parts = reminder_time.split(":")
        if len(parts) != 2:
            return jsonify({
                "success": False,
                "error": "时间格式错误，应为 HH:MM"
            }), 400

        hour, minute = int(parts[0]), int(parts[1])
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            return jsonify({
                "success": False,
                "error": "小时应在 0-23，分钟应在 0-59"
            }), 400

        config = read_config()
        config["email_settings"]["reminder_time"] = reminder_time
        write_config(config)

        # 如果调度器在运行，更新任务
        try:
            from backend.modules.scheduler import get_scheduler
            scheduler = get_scheduler()
            if scheduler.is_running:
                scheduler.update_reminder_settings(reminder_time)
        except:
            pass

        return jsonify({
            "success": True,
            "message": f"提醒时间已设置为 {reminder_time}",
            "reminder_time": reminder_time
        })

    except (ValueError, AttributeError):
        return jsonify({
            "success": False,
            "error": "时间格式错误，应为 HH:MM"
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@config_bp.route('/reminder-toggle', methods=['PUT'])
def toggle_reminder():
    """
    切换邮件提醒开关

    请求体:
    {
        "enable": true/false
    }
    """
    try:
        data = request.get_json()
        enable = data.get("enable", False)

        config = read_config()
        config["email_settings"]["enable_reminders"] = enable
        write_config(config)

        # 如果调度器在运行，更新任务
        try:
            from backend.modules.scheduler import get_scheduler
            scheduler = get_scheduler()
            if scheduler.is_running:
                scheduler._schedule_daily_reminder()
        except:
            pass

        status = "已启用" if enable else "已禁用"
        return jsonify({
            "success": True,
            "message": f"邮件提醒{status}",
            "enabled": enable
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
