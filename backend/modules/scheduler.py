from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging
from typing import Optional, Callable
import os
import json
from .email_manager import EmailManager
from .review_manager import ReviewManager


class ReviewScheduler:
    """管理后台任务调度，包括定时邮件提醒"""

    def __init__(self, data_dir: str = "backend/data"):
        self.scheduler = BackgroundScheduler()
        self.data_dir = data_dir
        self.config_file = os.path.join(data_dir, "user_config.json")
        self.is_running = False

        # 配置日志
        logging.basicConfig()
        logging.getLogger('apscheduler').setLevel(logging.WARNING)

    def _read_config(self) -> dict:
        """读取用户配置"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def start(self):
        """启动调度器"""
        if self.is_running:
            print("调度器已经在running...")
            return

        self.scheduler.start()
        self.is_running = True
        print("✅ 调度器已启动")

        # 启动每日邮件提醒任务
        self._schedule_daily_reminder()

    def stop(self):
        """停止调度器"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            print("✅ 调度器已停止")

    def _schedule_daily_reminder(self):
        """
        安排每日邮件提醒任务

        根据user_config.json中的设置，每天在指定时间发送复习提醒
        """
        config = self._read_config()
        email_settings = config.get("email_settings", {})

        # 检查是否启用了提醒
        if not email_settings.get("enable_reminders", False):
            print("⚠️ 邮件提醒未启用")
            return

        # 获取提醒时间 (格式 "HH:MM")
        reminder_time = email_settings.get("reminder_time", "09:00")
        try:
            hour, minute = map(int, reminder_time.split(":"))
        except (ValueError, AttributeError):
            print("⚠️ 提醒时间格式错误，使用默认时间 09:00")
            hour, minute = 9, 0

        # 移除旧任务（如果存在）
        try:
            self.scheduler.remove_job("daily_email_reminder")
        except:
            pass

        # 添加新的定时任务
        try:
            self.scheduler.add_job(
                self._send_daily_reminder_task,
                trigger=CronTrigger(hour=hour, minute=minute),
                id="daily_email_reminder",
                name="每日邮件提醒",
                replace_existing=True
            )
            print(f"✅ 每日邮件提醒已设置为 {reminder_time}")
        except Exception as e:
            print(f"❌ 设置邮件提醒失败: {e}")

    def _send_daily_reminder_task(self):
        """
        执行每日邮件提醒任务

        这是一个后台定时任务
        """
        try:
            config = self._read_config()
            user_info = config.get("user_info", {})
            email_settings = config.get("email_settings", {})

            if not email_settings.get("enable_reminders", False):
                return

            recipient_email = user_info.get("email")
            user_name = user_info.get("name", "用户")

            if not recipient_email:
                print("❌ 未配置收件人邮箱")
                return

            # 获取今日复习列表
            review_manager = ReviewManager(self.data_dir)
            today_reviews = review_manager.get_today_review_list()

            if not today_reviews:
                print("📨 今日无复习单词，跳过发送邮件")
                return

            # 生成邮件内容
            email_body = EmailManager.generate_daily_review_email(
                user_name=user_name,
                review_words=today_reviews
            )

            # 发送邮件
            result = EmailManager.send_email(
                smtp_server=email_settings.get("smtp_server", "smtp.gmail.com"),
                smtp_port=email_settings.get("smtp_port", 587),
                sender_email=email_settings.get("sender_email"),
                sender_password=email_settings.get("app_password"),
                recipient_email=recipient_email,
                subject=f"📚 {len(today_reviews)} 个单词待复习 - {user_name}的学习提醒",
                body=email_body,
                is_html=True
            )

            if result.get("success"):
                print(f"✅ 邮件已发送到 {recipient_email}")
            else:
                print(f"❌ 邮件发送失败: {result.get('error')}")

        except Exception as e:
            print(f"❌ 执行每日提醒任务失败: {e}")

    def add_custom_job(
        self,
        func: Callable,
        trigger_type: str = "cron",
        job_id: Optional[str] = None,
        **trigger_kwargs
    ):
        """
        添加自定义定时任务

        参数:
            func: 要执行的函数
            trigger_type: 触发器类型 ("cron", "interval", "date")
            job_id: 任务ID
            **trigger_kwargs: 触发器参数

        示例：
            添加每小时执行一次的任务：
            scheduler.add_custom_job(
                func=my_function,
                trigger_type="interval",
                hours=1
            )

            添加每天9点和下午3点执行的任务：
            scheduler.add_custom_job(
                func=my_function,
                trigger_type="cron",
                hour="9,15"
            )
        """
        try:
            if trigger_type == "cron":
                trigger = CronTrigger(**trigger_kwargs)
            elif trigger_type == "interval":
                from apscheduler.triggers.interval import IntervalTrigger
                trigger = IntervalTrigger(**trigger_kwargs)
            elif trigger_type == "date":
                from apscheduler.triggers.date import DateTrigger
                trigger = DateTrigger(**trigger_kwargs)
            else:
                print(f"❌ 未知的触发器类型: {trigger_type}")
                return

            self.scheduler.add_job(
                func,
                trigger=trigger,
                id=job_id,
                replace_existing=True
            )
            print(f"✅ 任务 {job_id} 已添加")
        except Exception as e:
            print(f"❌ 添加任务失败: {e}")

    def update_reminder_settings(self, reminder_time: str):
        """
        更新邮件提醒时间

        参数:
            reminder_time: 提醒时间 (格式 "HH:MM")
        """
        config = self._read_config()
        email_settings = config.get("email_settings", {})
        email_settings["reminder_time"] = reminder_time

        config["email_settings"] = email_settings

        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        # 重新安排任务
        self._schedule_daily_reminder()

    def get_scheduled_jobs(self):
        """获取所有已安排的任务"""
        return self.scheduler.get_jobs()

    def remove_job(self, job_id: str) -> bool:
        """
        移除指定的任务

        参数:
            job_id: 任务ID

        返回:
            是否成功移除
        """
        try:
            self.scheduler.remove_job(job_id)
            print(f"✅ 任务 {job_id} 已移除")
            return True
        except Exception as e:
            print(f"❌ 移除任务失败: {e}")
            return False


# 全局调度器实例
_scheduler_instance = None


def get_scheduler(data_dir: str = "backend/data") -> ReviewScheduler:
    """获取全局调度器实例"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = ReviewScheduler(data_dir)
    return _scheduler_instance


if __name__ == "__main__":
    # 测试调度器
    scheduler = ReviewScheduler()
    scheduler.start()

    # 添加一个测试任务（每分钟执行一次）
    def test_task():
        print("测试任务执行...")

    scheduler.add_custom_job(
        func=test_task,
        trigger_type="interval",
        job_id="test_job",
        seconds=60
    )

    print("调度器运行中，按 Ctrl+C 停止...")
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.stop()
        print("调度器已停止")
