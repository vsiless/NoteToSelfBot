"""
Reminder system for deadline tracking and notifications.
"""

import asyncio
import schedule
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Callable
from threading import Thread
from .models import LinkItem, TaskStatus
from .storage import FileStorage
import logging

logger = logging.getLogger(__name__)

class ReminderType:
    """Types of reminders."""
    OVERDUE = "overdue"
    DUE_TODAY = "due_today"
    DUE_TOMORROW = "due_tomorrow"
    DUE_IN_3_DAYS = "due_in_3_days"
    DUE_IN_1_WEEK = "due_in_1_week"
    DAILY_SUMMARY = "daily_summary"
    WEEKLY_SUMMARY = "weekly_summary"

class Reminder:
    """Reminder data structure."""
    
    def __init__(self, user_id: str, link: LinkItem, reminder_type: str, message: str):
        self.user_id = user_id
        self.link = link
        self.reminder_type = reminder_type
        self.message = message
        self.created_at = datetime.now()

class ReminderSystem:
    """Manages deadline reminders and notifications."""
    
    def __init__(self, storage: FileStorage, send_message_callback: Callable[[str, str], None]):
        self.storage = storage
        self.send_message = send_message_callback
        self.running = False
        self.scheduler_thread = None
        
    def start(self):
        """Start the reminder system."""
        if self.running:
            return
            
        self.running = True
        
        # Schedule different types of checks
        schedule.every().day.at("09:00").do(self._send_daily_summary)
        schedule.every().monday.at("09:00").do(self._send_weekly_summary)
        schedule.every(4).hours.do(self._check_urgent_deadlines)
        schedule.every().day.at("18:00").do(self._check_upcoming_deadlines)
        schedule.every().day.at("12:00").do(self._check_weekly_reminders)  # Check for 1-4 week reminders
        schedule.every(1).minutes.do(self._check_immediate_reminders)  # Check for 5-minute reminders
        
        # Start scheduler in background thread
        self.scheduler_thread = Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("Reminder system started")
        
        # Trigger an immediate check for any pending reminders
        self.trigger_immediate_reminder_check()
    
    def stop(self):
        """Stop the reminder system."""
        self.running = False
        schedule.clear()
        logger.info("Reminder system stopped")
    
    def _run_scheduler(self):
        """Run the scheduler in background."""
        logger.info("Reminder scheduler thread started")
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(10)  # Check every 10 seconds for more responsive reminders
            except Exception as e:
                logger.error(f"Error in scheduler: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _get_all_users(self) -> List[str]:
        """Get all user IDs from storage directory."""
        import os
        users = []
        if os.path.exists(self.storage.data_dir):
            for filename in os.listdir(self.storage.data_dir):
                if filename.startswith("user_") and filename.endswith(".json"):
                    user_id = filename[5:-5]  # Remove "user_" prefix and ".json" suffix
                    users.append(user_id)
        return users
    
    def _check_urgent_deadlines(self):
        """Check for overdue and today's deadlines."""
        users = self._get_all_users()
        
        for user_id in users:
            try:
                # Check overdue items
                overdue_links = self.storage.get_overdue_links(user_id)
                if overdue_links:
                    self._send_overdue_reminder(user_id, overdue_links)
                
                # Check items due today
                today_links = self._get_due_today(user_id)
                if today_links:
                    self._send_due_today_reminder(user_id, today_links)
                    
            except Exception as e:
                logger.error(f"Error checking urgent deadlines for user {user_id}: {e}")
    
    def _check_upcoming_deadlines(self):
        """Check for upcoming deadlines (tomorrow, 3 days)."""
        users = self._get_all_users()
        
        for user_id in users:
            try:
                # Check items due tomorrow
                tomorrow_links = self._get_due_in_days(user_id, 1)
                if tomorrow_links:
                    self._send_due_tomorrow_reminder(user_id, tomorrow_links)
                
                # Check items due in 3 days
                three_day_links = self._get_due_in_days(user_id, 3)
                if three_day_links:
                    self._send_due_in_3_days_reminder(user_id, three_day_links)
                    
            except Exception as e:
                logger.error(f"Error checking upcoming deadlines for user {user_id}: {e}")
    
    def _check_weekly_reminders(self):
        """Check for weekly reminders (1, 2, 3, 4 weeks before deadline)."""
        users = self._get_all_users()
        
        for user_id in users:
            try:
                # Check items due in 1 week
                week_1_links = self._get_due_in_days(user_id, 7)
                if week_1_links:
                    self._send_weekly_reminder(user_id, week_1_links, 1)
                
                # Check items due in 2 weeks
                week_2_links = self._get_due_in_days(user_id, 14)
                if week_2_links:
                    self._send_weekly_reminder(user_id, week_2_links, 2)
                
                # Check items due in 3 weeks
                week_3_links = self._get_due_in_days(user_id, 21)
                if week_3_links:
                    self._send_weekly_reminder(user_id, week_3_links, 3)
                
                # Check items due in 4 weeks
                week_4_links = self._get_due_in_days(user_id, 28)
                if week_4_links:
                    self._send_weekly_reminder(user_id, week_4_links, 4)
                    
            except Exception as e:
                logger.error(f"Error checking weekly reminders for user {user_id}: {e}")
    
    def _check_immediate_reminders(self):
        """Check for immediate reminders (5 minutes after adding)."""
        users = self._get_all_users()
        logger.debug(f"Checking immediate reminders for {len(users)} users")
        
        for user_id in users:
            try:
                user_links = self.storage.get_user_links(user_id)
                now = datetime.now()
                logger.debug(f"User {user_id} has {len(user_links)} links")
                
                for link in user_links:
                    # Check if link was created 5 minutes ago and has a deadline
                    if (link.deadline and 
                        link.created_at and
                        not link.reminder_sent and
                        link.status not in [TaskStatus.DONE, TaskStatus.EXPIRED]):
                        
                        time_since_created = now - link.created_at
                        logger.debug(f"Link {link.id[:8]}: created {time_since_created} ago, deadline {link.deadline}")
                        
                        # Send reminder if it's been 5+ minutes since creation
                        if time_since_created >= timedelta(minutes=5):
                            logger.info(f"Sending immediate reminder for link {link.id[:8]} created {time_since_created} ago")
                            self._send_immediate_reminder(user_id, link)
                            
                            # Mark reminder as sent and update storage
                            link.reminder_sent = now
                            self.storage.update_link(user_id, link.id, link)
                        else:
                            logger.debug(f"Link {link.id[:8]} not ready for reminder yet (only {time_since_created} since creation)")
                            
            except Exception as e:
                logger.error(f"Error checking immediate reminders for user {user_id}: {e}")
                import traceback
                logger.error(traceback.format_exc())
    
    def _get_due_today(self, user_id: str) -> List[LinkItem]:
        """Get items due today."""
        user_links = self.storage.get_user_links(user_id)
        today = datetime.now().date()
        
        due_today = []
        for link in user_links:
            if (link.deadline and 
                link.deadline.date() == today and 
                link.status not in [TaskStatus.DONE, TaskStatus.EXPIRED]):
                due_today.append(link)
        
        return due_today
    
    def _get_due_in_days(self, user_id: str, days: int) -> List[LinkItem]:
        """Get items due in exactly N days."""
        user_links = self.storage.get_user_links(user_id)
        target_date = (datetime.now() + timedelta(days=days)).date()
        
        due_links = []
        for link in user_links:
            if (link.deadline and 
                link.deadline.date() == target_date and 
                link.status not in [TaskStatus.DONE, TaskStatus.EXPIRED]):
                due_links.append(link)
        
        return due_links
    
    def _send_overdue_reminder(self, user_id: str, overdue_links: List[LinkItem]):
        """Send overdue reminder."""
        if not overdue_links:
            return
            
        message_parts = ["🚨 **OVERDUE ITEMS ALERT!** 🚨\n"]
        message_parts.append("The following items are past their deadlines:\n")
        
        for link in overdue_links:
            days_overdue = abs(link.days_until_deadline()) if link.days_until_deadline() else 0
            category_emoji = self._get_category_emoji(link.category)
            
            message_parts.append(
                f"{category_emoji} **{link.title}**\n"
                f"⚠️ Overdue by {days_overdue} days\n"
                f"🔗 {link.url}\n"
                f"🆔 ID: `{link.id[:8]}`\n"
            )
        
        message_parts.append("\n💡 Use `done <id>` to mark as completed or `mark <id> as expired` if no longer relevant.")
        
        self.send_message(user_id, "\n".join(message_parts))
    
    def _send_due_today_reminder(self, user_id: str, today_links: List[LinkItem]):
        """Send due today reminder."""
        if not today_links:
            return
            
        message_parts = ["⏰ **DUE TODAY!** ⏰\n"]
        message_parts.append("These items are due today:\n")
        
        for link in today_links:
            category_emoji = self._get_category_emoji(link.category)
            message_parts.append(
                f"{category_emoji} **{link.title}**\n"
                f"🔗 {link.url}\n"
                f"🆔 ID: `{link.id[:8]}`\n"
            )
        
        message_parts.append("\n🎯 Don't forget to complete these today!")
        
        self.send_message(user_id, "\n".join(message_parts))
    
    def _send_due_tomorrow_reminder(self, user_id: str, tomorrow_links: List[LinkItem]):
        """Send due tomorrow reminder."""
        if not tomorrow_links:
            return
            
        message_parts = ["📅 **Due Tomorrow** 📅\n"]
        
        for link in tomorrow_links:
            category_emoji = self._get_category_emoji(link.category)
            message_parts.append(
                f"{category_emoji} **{link.title}**\n"
                f"🔗 {link.url}\n"
                f"🆔 ID: `{link.id[:8]}`\n"
            )
        
        self.send_message(user_id, "\n".join(message_parts))
    
    def _send_due_in_3_days_reminder(self, user_id: str, three_day_links: List[LinkItem]):
        """Send due in 3 days reminder."""
        if not three_day_links:
            return
            
        message_parts = ["⚡ **Due in 3 Days** ⚡\n"]
        
        for link in three_day_links:
            category_emoji = self._get_category_emoji(link.category)
            message_parts.append(
                f"{category_emoji} **{link.title}**\n"
                f"🔗 {link.url}\n"
                f"🆔 ID: `{link.id[:8]}`\n"
            )
        
        self.send_message(user_id, "\n".join(message_parts))
    
    def _send_weekly_reminder(self, user_id: str, week_links: List[LinkItem], weeks: int):
        """Send weekly reminder for items due in N weeks."""
        if not week_links:
            return
            
        week_text = f"{weeks} week{'s' if weeks > 1 else ''}"
        message_parts = [f"📅 **Due in {week_text}** 📅\n"]
        
        for link in week_links:
            category_emoji = self._get_category_emoji(link.category)
            message_parts.append(
                f"{category_emoji} **{link.title}**\n"
                f"🔗 {link.url}\n"
                f"🆔 ID: `{link.id[:8]}`\n"
            )
        
        self.send_message(user_id, "\n".join(message_parts))
    
    def _send_immediate_reminder(self, user_id: str, link: LinkItem):
        """Send immediate reminder for newly added link with deadline."""
        days_until = link.days_until_deadline()
        category_emoji = self._get_category_emoji(link.category)
        
        if days_until is None:
            deadline_text = "No deadline set"
        elif days_until < 0:
            deadline_text = f"⚠️ **OVERDUE** ({abs(days_until)} days ago)"
        elif days_until == 0:
            deadline_text = "⏰ **Due today!**"
        else:
            deadline_text = f"📅 Due in {days_until} days"
        
        message = (
            f"✅ **Link Added with Deadline!** ✅\n\n"
            f"{category_emoji} **{link.title}**\n"
            f"🔗 {link.url}\n"
            f"📂 Category: {link.category.value.replace('_', ' ').title()}\n"
            f"⏰ {deadline_text}\n"
            f"🆔 ID: `{link.id[:8]}`\n\n"
            f"📋 You'll receive reminders at 4, 3, 2, and 1 week(s) before the deadline.\n"
            f"💡 Use `add milestone {link.id[:8]} <title>` to break this into smaller steps!"
        )
        
        self.send_message(user_id, message)
    
    def _send_daily_summary(self):
        """Send daily summary to all users."""
        users = self._get_all_users()
        
        for user_id in users:
            try:
                summary = self._generate_daily_summary(user_id)
                if summary:
                    self.send_message(user_id, summary)
            except Exception as e:
                logger.error(f"Error sending daily summary to user {user_id}: {e}")
    
    def _send_weekly_summary(self):
        """Send weekly summary to all users."""
        users = self._get_all_users()
        
        for user_id in users:
            try:
                summary = self._generate_weekly_summary(user_id)
                if summary:
                    self.send_message(user_id, summary)
            except Exception as e:
                logger.error(f"Error sending weekly summary to user {user_id}: {e}")
    
    def _generate_daily_summary(self, user_id: str) -> Optional[str]:
        """Generate daily summary for a user."""
        user_links = self.storage.get_user_links(user_id)
        
        if not user_links:
            return None
        
        # Count items by status
        todo_count = len([l for l in user_links if l.status == TaskStatus.TODO])
        in_progress_count = len([l for l in user_links if l.status == TaskStatus.IN_PROGRESS])
        overdue_count = len(self.storage.get_overdue_links(user_id))
        upcoming_count = len(self.storage.get_upcoming_deadlines(user_id, 7))
        
        if todo_count == 0 and in_progress_count == 0 and overdue_count == 0 and upcoming_count == 0:
            return None
        
        summary_parts = ["🌅 **Daily Summary**\n"]
        
        if overdue_count > 0:
            summary_parts.append(f"🚨 {overdue_count} overdue items")
        
        if upcoming_count > 0:
            summary_parts.append(f"📅 {upcoming_count} items due in the next 7 days")
        
        if todo_count > 0:
            summary_parts.append(f"📋 {todo_count} items to start")
        
        if in_progress_count > 0:
            summary_parts.append(f"🔄 {in_progress_count} items in progress")
        
        summary_parts.append("\nUse `list overdue` or `list deadlines` to see details.")
        
        return "\n".join(summary_parts)
    
    def _generate_weekly_summary(self, user_id: str) -> Optional[str]:
        """Generate weekly summary for a user."""
        user_links = self.storage.get_user_links(user_id)
        
        if not user_links:
            return None
        
        # Count completed items this week
        week_ago = datetime.now() - timedelta(days=7)
        completed_this_week = len([
            l for l in user_links 
            if l.status == TaskStatus.DONE and l.updated_at >= week_ago
        ])
        
        # Count items by category
        job_count = len([l for l in user_links if l.category.value == "job_application" and l.status != TaskStatus.DONE])
        grant_count = len([l for l in user_links if l.category.value == "grant_application" and l.status != TaskStatus.DONE])
        
        summary_parts = ["📊 **Weekly Summary**\n"]
        
        if completed_this_week > 0:
            summary_parts.append(f"✅ {completed_this_week} items completed this week")
        
        if job_count > 0:
            summary_parts.append(f"💼 {job_count} active job applications")
        
        if grant_count > 0:
            summary_parts.append(f"💰 {grant_count} active grant applications")
        
        # Upcoming deadlines
        next_week_count = len(self.storage.get_upcoming_deadlines(user_id, 14))
        if next_week_count > 0:
            summary_parts.append(f"📅 {next_week_count} deadlines in the next 2 weeks")
        
        if len(summary_parts) == 1:  # Only header
            return None
        
        summary_parts.append("\nKeep up the great work! 🎉")
        
        return "\n".join(summary_parts)
    
    def schedule_reminders_for_link(self, user_id: str, link: LinkItem):
        """Schedule all reminders for a new link with deadline."""
        if not link.deadline:
            return
        
        # The reminder system will automatically handle:
        # - Immediate reminder (5 minutes after creation)
        # - Weekly reminders (4, 3, 2, 1 weeks before deadline)
        # - Daily/urgent reminders (overdue, due today, tomorrow, 3 days)
        
        logger.info(f"Scheduled reminders for link {link.id[:8]} with deadline {link.deadline}")
    
    def add_link_with_reminders(self, user_id: str, link: LinkItem) -> bool:
        """Add a link and schedule its reminders."""
        success = self.storage.add_link(user_id, link)
        if success and link.deadline:
            self.schedule_reminders_for_link(user_id, link)
            logger.info(f"Added link {link.id[:8]} with deadline {link.deadline} for user {user_id}")
        return success
    
    def trigger_immediate_reminder_check(self):
        """Manually trigger immediate reminder check for testing."""
        logger.info("Manually triggering immediate reminder check")
        self._check_immediate_reminders()
    
    def _get_category_emoji(self, category) -> str:
        """Get emoji for category."""
        from .models import LinkCategory
        
        emoji_map = {
            LinkCategory.JOB_APPLICATION: "💼",
            LinkCategory.GRANT_APPLICATION: "💰",
            LinkCategory.NOTES_TO_READ: "📖",
            LinkCategory.RESEARCH: "🔬",
            LinkCategory.LEARNING: "🎓",
            LinkCategory.PERSONAL: "👤",
            LinkCategory.OTHER: "🔗"
        }
        return emoji_map.get(category, "🔗")
    
    def send_immediate_reminder(self, user_id: str, link_id: str) -> bool:
        """Send an immediate reminder for a specific link."""
        try:
            user_links = self.storage.get_user_links(user_id)
            target_link = None
            
            for link in user_links:
                if link.id.startswith(link_id):
                    target_link = link
                    break
            
            if not target_link:
                return False
            
            days_until = target_link.days_until_deadline()
            category_emoji = self._get_category_emoji(target_link.category)
            
            if days_until is None:
                deadline_text = "No deadline set"
            elif days_until < 0:
                deadline_text = f"⚠️ **OVERDUE** ({abs(days_until)} days ago)"
            elif days_until == 0:
                deadline_text = "⏰ **Due today!**"
            else:
                deadline_text = f"📅 Due in {days_until} days"
            
            message = (
                f"🔔 **Reminder** 🔔\n\n"
                f"{category_emoji} **{target_link.title}**\n"
                f"🔗 {target_link.url}\n"
                f"📂 Category: {target_link.category.value.replace('_', ' ').title()}\n"
                f"📊 Status: {target_link.status.value.replace('_', ' ').title()}\n"
                f"⏰ {deadline_text}\n"
                f"🆔 ID: `{target_link.id[:8]}`\n\n"
                f"💡 Use `done {target_link.id[:8]}` to mark as completed"
            )
            
            self.send_message(user_id, message)
            return True
            
        except Exception as e:
            logger.error(f"Error sending immediate reminder: {e}")
            return False
