import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
from datetime import datetime


class EmailManager:
    """管理邮件发送功能"""

    @staticmethod
    def send_email(
        smtp_server: str,
        smtp_port: int,
        sender_email: str,
        sender_password: str,
        recipient_email: str,
        subject: str,
        body: str,
        is_html: bool = True
    ) -> Dict[str, bool]:
        """
        发送邮件

        参数:
            smtp_server: SMTP服务器地址
            smtp_port: SMTP端口
            sender_email: 发件人邮箱
            sender_password: 发件人密码（通常是应用密码）
            recipient_email: 收件人邮箱
            subject: 邮件主题
            body: 邮件内容
            is_html: 是否为HTML格式

        返回:
            {"success": True/False, "error": "错误信息"}
        """
        try:
            # 创建邮件对象
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = sender_email
            message["To"] = recipient_email

            # 添加邮件内容
            mime_type = "html" if is_html else "plain"
            message.attach(MIMEText(body, mime_type, "utf-8"))

            # 连接SMTP服务器发送邮件
            with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, recipient_email, message.as_string())

            return {"success": True}

        except smtplib.SMTPAuthenticationError:
            return {
                "success": False,
                "error": "认证失败：邮箱或密码错误"
            }
        except smtplib.SMTPException as e:
            return {
                "success": False,
                "error": f"SMTP错误：{str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"邮件发送失败：{str(e)}"
            }

    @staticmethod
    def test_email_configuration(
        smtp_server: str,
        smtp_port: int,
        sender_email: str,
        sender_password: str
    ) -> Dict[str, bool]:
        """
        测试邮件配置是否正确

        参数:
            smtp_server: SMTP服务器地址
            smtp_port: SMTP端口
            sender_email: 发件人邮箱
            sender_password: 发件人密码

        返回:
            {"success": True/False, "error": "错误信息"}
        """
        try:
            with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
                server.starttls()
                server.login(sender_email, sender_password)

            return {"success": True}

        except smtplib.SMTPAuthenticationError:
            return {
                "success": False,
                "error": "认证失败：邮箱或密码错误"
            }
        except smtplib.SMTPException as e:
            return {
                "success": False,
                "error": f"SMTP错误：{str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"连接失败：{str(e)}"
            }

    @staticmethod
    def generate_daily_review_email(
        user_name: str,
        review_words: List[Dict],
        app_url: str = "http://localhost:5000"
    ) -> str:
        """
        生成每日复习提醒邮件的HTML内容

        参数:
            user_name: 用户名
            review_words: 需要复习的单词列表
            app_url: 应用URL

        返回:
            HTML格式的邮件内容
        """
        today = datetime.now().strftime("%Y年%m月%d日")

        # 构建单词表格
        word_rows = ""
        for word in review_words[:20]:  # 最多显示20个单词
            phonetic = word.get("phonetic", "")
            word_name = word.get("word", "")
            review_count = word.get("review_count", 0)
            scheduled_date = word.get("next_review_date", "")

            word_rows += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{word_name}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{phonetic}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: center;">{review_count}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{scheduled_date}</td>
            </tr>
            """

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f5f5f5;
                    margin: 0;
                    padding: 20px;
                }}
                .container {{
                    background-color: white;
                    border-radius: 8px;
                    padding: 30px;
                    max-width: 800px;
                    margin: 0 auto;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .header {{
                    color: #333;
                    border-bottom: 3px solid #4CAF50;
                    padding-bottom: 15px;
                    margin-bottom: 20px;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                    color: #4CAF50;
                }}
                .header p {{
                    margin: 5px 0 0 0;
                    color: #666;
                    font-size: 14px;
                }}
                .content {{
                    margin: 20px 0;
                    color: #333;
                }}
                .stats {{
                    display: flex;
                    gap: 20px;
                    margin: 20px 0;
                    background-color: #f9f9f9;
                    padding: 15px;
                    border-radius: 5px;
                }}
                .stat-item {{
                    flex: 1;
                    text-align: center;
                }}
                .stat-number {{
                    font-size: 32px;
                    font-weight: bold;
                    color: #4CAF50;
                }}
                .stat-label {{
                    font-size: 14px;
                    color: #666;
                    margin-top: 5px;
                }}
                .words-table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                    background-color: #fff;
                }}
                .words-table th {{
                    background-color: #4CAF50;
                    color: white;
                    padding: 12px;
                    text-align: left;
                    font-weight: bold;
                }}
                .words-table td {{
                    padding: 10px;
                    border-bottom: 1px solid #ddd;
                }}
                .button {{
                    display: inline-block;
                    background-color: #4CAF50;
                    color: white;
                    padding: 12px 30px;
                    text-decoration: none;
                    border-radius: 5px;
                    font-weight: bold;
                    margin-top: 20px;
                    margin-bottom: 10px;
                }}
                .button:hover {{
                    background-color: #45a049;
                }}
                .footer {{
                    border-top: 1px solid #ddd;
                    padding-top: 15px;
                    margin-top: 30px;
                    font-size: 12px;
                    color: #999;
                    text-align: center;
                }}
                .motivate {{
                    color: #4CAF50;
                    font-weight: bold;
                    font-size: 16px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📚 英文单词复习提醒</h1>
                    <p>今日：{today}</p>
                </div>

                <div class="content">
                    <p>亲爱的 <strong>{user_name}</strong>，</p>
                    <p>今天有 <span class="motivate">{len(review_words)} 个单词</span> 需要你复习！</p>

                    <div class="stats">
                        <div class="stat-item">
                            <div class="stat-number">{len(review_words)}</div>
                            <div class="stat-label">今日复习</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number">12:00</div>
                            <div class="stat-label">建议时间</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number">30分钟</div>
                            <div class="stat-label">预计时长</div>
                        </div>
                    </div>

                    <p>坚持是成功的秘诀。每天复习一点点，最终你将掌握所有单词！💪</p>

                    <table class="words-table">
                        <thead>
                            <tr>
                                <th>单词</th>
                                <th>音标</th>
                                <th>复习次数</th>
                                <th>下次复习</th>
                            </tr>
                        </thead>
                        <tbody>
                            {word_rows}
                        </tbody>
                    </table>

                    <a href="{app_url}/review.html" class="button">🚀 开始复习</a>
                </div>

                <div class="footer">
                    <p>这是来自 "英文单词学习系统" 的自动提醒邮件</p>
                    <p>如需停止接收提醒，请在设置页面禁用邮件提醒功能</p>
                </div>
            </div>
        </body>
        </html>
        """

        return html_content

    @staticmethod
    def generate_test_email(app_name: str = "英文单词学习系统") -> str:
        """
        生成邮件配置测试邮件

        参数:
            app_name: 应用名称

        返回:
            HTML格式的邮件内容
        """
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f5f5f5;
                    margin: 0;
                    padding: 20px;
                }}
                .container {{
                    background-color: white;
                    border-radius: 8px;
                    padding: 30px;
                    max-width: 600px;
                    margin: 0 auto;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .header {{
                    color: #333;
                    border-bottom: 3px solid #4CAF50;
                    padding-bottom: 15px;
                    margin-bottom: 20px;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 24px;
                    color: #4CAF50;
                }}
                .content {{
                    margin: 20px 0;
                    color: #333;
                }}
                .success {{
                    background-color: #d4edda;
                    border: 1px solid #c3e6cb;
                    color: #155724;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 15px 0;
                }}
                .footer {{
                    border-top: 1px solid #ddd;
                    padding-top: 15px;
                    margin-top: 30px;
                    font-size: 12px;
                    color: #999;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✅ 邮件配置测试成功</h1>
                </div>

                <div class="content">
                    <p>恭喜！你的邮件配置已正确设置。</p>

                    <div class="success">
                        <strong>邮件系统正常工作！</strong>
                        <p>你将能够收到以下邮件：</p>
                        <ul>
                            <li>每日单词复习提醒</li>
                            <li>学习进度统计</li>
                            <li>重要通知</li>
                        </ul>
                    </div>

                    <p>现在你可以在应用的设置页面配置每日提醒时间和频率。</p>
                </div>

                <div class="footer">
                    <p>来自 {app_name} 的测试邮件</p>
                    <p>发送时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                </div>
            </div>
        </body>
        </html>
        """

        return html_content
