import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from pymongo import MongoClient
from bson.objectid import ObjectId
import datetime

# MongoDB setup
client = MongoClient("mongodb://localhost:27017")
db = client["todolist"]
tasks_collection = db["tasks"]

# Telegram Bot setup
API_KEY = "7673819576:AAGIr1jFLJZLc9f-k2ABcQpUuR_EInBOrxE"
application = Application.builder().token(API_KEY).build()

# Logging setup
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Command Handlers
async def start(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    await update.message.reply_text(
        f"Hello {user.first_name}! I am your To-Do bot. Here are the commands you can use:\n"
        "/add <task_description> - Add a task\n"
        "/list - List all tasks\n"
        "/complete <task_id> - Mark a task as completed\n"
        "/remove <task_id> - Remove a task\n"
        "/edit <task_id> <new_description> - Edit a task\n"
        "/help - Show this message"
    )

async def add_task(update: Update, context: CallbackContext) -> None:
    user_input = ' '.join(context.args)
    if not user_input:
        await update.message.reply_text("Please provide a task description. Example: /add Buy groceries")
        return

    task = {
        "description": user_input,
        "completed": False,
        "created_at": datetime.datetime.now()
    }
    tasks_collection.insert_one(task)
    await update.message.reply_text(f"Task '{user_input}' added successfully!")

async def list_tasks(update: Update, context: CallbackContext) -> None:
    tasks = tasks_collection.find({"completed": False})
    task_list = list(tasks)

    if not task_list:
        await update.message.reply_text("You have no pending tasks.")
        return

    task_display = "\n".join([f"{task['_id']} - {task['description']}" for task in task_list])
    await update.message.reply_text(f"Your pending tasks:\n{task_display}")

# Complete a task by name
async def complete_task(update: Update, context: CallbackContext) -> None:
    task_name = ' '.join(context.args)
    if not task_name:
        await update.message.reply_text("Please provide the task name to mark it as completed. Example: /complete Buy groceries")
        return
    
    task = tasks_collection.find_one({"description": task_name, "completed": False})
    if not task:
        await update.message.reply_text(f"Task '{task_name}' not found or already completed.")
        return
    
    tasks_collection.update_one({"description": task_name}, {"$set": {"completed": True}})
    await update.message.reply_text(f"Task '{task_name}' marked as completed!")

# Remove a task by name
async def remove_task(update: Update, context: CallbackContext) -> None:
    task_name = ' '.join(context.args)
    if not task_name:
        await update.message.reply_text("Please provide the task name to remove it. Example: /remove Buy groceries")
        return
    
    task = tasks_collection.find_one({"description": task_name})
    if not task:
        await update.message.reply_text(f"Task '{task_name}' not found.")
        return
    
    tasks_collection.delete_one({"description": task_name})
    await update.message.reply_text(f"Task '{task_name}' removed successfully!")

# Edit a task by name
async def edit_task(update: Update, context: CallbackContext) -> None:
    if len(context.args) < 2:
        await update.message.reply_text("Please provide the task name and the new description. Example: /edit 'Buy groceries' 'Buy vegetables'")
        return

    old_task_name = context.args[0]  # The old task description to find
    new_task_description = ' '.join(context.args[1:])  # The new description

    # Search for the task by its description (not _id)
    task = tasks_collection.find_one({"description": old_task_name})

    if not task:
        await update.message.reply_text(f"Task '{old_task_name}' not found.")
        return

    # Update the task with the new description
    tasks_collection.update_one(
        {"description": old_task_name},
        {"$set": {"description": new_task_description}}
    )

    await update.message.reply_text(f"Task '{old_task_name}' has been updated to '{new_task_description}'")
    if len(context.args) < 2:
        await update.message.reply_text("Please provide the task name and the new description. Example: /edit Buy groceries Buy vegetables")
        return

    old_task_name = context.args[0]  # The old task description to find
    new_task_description = ' '.join(context.args[1:])  # The new description

    # Search for the task by its name
    task = tasks_collection.find_one({"description": old_task_name})

    if not task:
        await update.message.reply_text(f"Task '{old_task_name}' not found.")
        return

    # Update the task with the new description
    tasks_collection.update_one(
        {"description": old_task_name},
        {"$set": {"description": new_task_description}}
    )

    await update.message.reply_text(f"Task '{old_task_name}' has been updated to '{new_task_description}'")

    if len(context.args) < 2:
        await update.message.reply_text("Please provide the task ID and the new description. Example: /edit <task_id> <new_description>")
        return

    task_id = context.args[0]
    new_description = ' '.join(context.args[1:])

    try:
        result = tasks_collection.update_one(
            {"_id": ObjectId(task_id)},
            {"$set": {"description": new_description}}
        )
        if result.matched_count == 0:
            await update.message.reply_text("Task not found.")
        else:
            await update.message.reply_text(f"Task {task_id} updated to: {new_description}")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

# Register handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("add", add_task))
application.add_handler(CommandHandler("list", list_tasks))
application.add_handler(CommandHandler("complete", complete_task))
application.add_handler(CommandHandler("remove", remove_task))
application.add_handler(CommandHandler("edit", edit_task))

# Run the bot
if __name__ == "__main__":
    application.run_polling()
