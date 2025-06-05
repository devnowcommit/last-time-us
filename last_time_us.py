"""
last_time_us.py
A command-line application to track tasks, their last completion times, and daily streaks.
Tasks are stored in a JSON file named 'tasks.json'.
The JSON file contains a dictionary where keys are task names.
Each task object has the following structure:
{
    "task_name_key": {
        "last_completed_timestamp": "ISO_DATETIME_STRING_OR_NULL",
        "current_streak": INTEGER,
        "streak_last_updated_date": "ISO_DATE_STRING_OR_NULL"
    },
    ...
}
Example:
{
    "Grocery Shopping": {
        "last_completed_timestamp": "2023-10-27T14:30:00.123456",
        "current_streak": 5,
        "streak_last_updated_date": "2023-10-27"
    },
    "Workout": {
        "last_completed_timestamp": null,
        "current_streak": 0,
        "streak_last_updated_date": null
    }
}
"""
import os
import datetime
import json # <--- Add this import

# ... (DATA_FILE constant is already updated)

DATA_FILE = "tasks.json"

def load_tasks():
    """Loads tasks from the JSON data file (tasks.json).

    Tasks are deserialized from JSON. For each task, it ensures:
    - "last_completed_timestamp" is a datetime.datetime object (or None if missing/invalid).
    - "streak_last_updated_date" is a datetime.date object (or None if missing/invalid).
    - "current_streak" is an integer (defaulting to 0 if missing/invalid).
    Handles potential JSON decoding errors or file not found by returning an empty dictionary.

    Returns:
        dict: A dictionary where keys are task names (str) and values are task data objects (dict)
              containing processed timestamps, dates, and streak information.
    """
    if not os.path.exists(DATA_FILE):
        return {}

    try:
        with open(DATA_FILE, "r") as f:
            if os.fstat(f.fileno()).st_size == 0: # Check if file is empty
                return {}
            tasks_raw = json.load(f)
    except json.JSONDecodeError:
        print(f"Warning: Error decoding JSON from {DATA_FILE}. Starting with empty tasks.")
        return {} # Or handle more gracefully, e.g., backup old file and start fresh
    except FileNotFoundError: # Should be caught by os.path.exists, but good practice
        return {}

    processed_tasks = {}
    for task_name, data in tasks_raw.items():
        # Convert timestamp string to datetime object
        if data.get("last_completed_timestamp"):
            try:
                data["last_completed_timestamp"] = datetime.datetime.fromisoformat(data["last_completed_timestamp"])
            except (ValueError, TypeError):
                print(f"Warning: Malformed timestamp for task '{task_name}'. Setting to None.")
                data["last_completed_timestamp"] = None
        else:
            data["last_completed_timestamp"] = None # Ensure it's None if missing or null

        # Convert streak_last_updated_date string to date object
        if data.get("streak_last_updated_date"):
            try:
                data["streak_last_updated_date"] = datetime.date.fromisoformat(data["streak_last_updated_date"])
            except (ValueError, TypeError):
                print(f"Warning: Malformed streak_last_updated_date for task '{task_name}'. Setting to None.")
                data["streak_last_updated_date"] = None
        else:
            data["streak_last_updated_date"] = None # Ensure it's None if missing or null

        # Ensure current_streak is an int, default to 0 if missing/invalid
        try:
            data["current_streak"] = int(data.get("current_streak", 0))
        except (ValueError, TypeError):
            print(f"Warning: Invalid streak value for task '{task_name}'. Resetting to 0.")
            data["current_streak"] = 0

        processed_tasks[task_name] = data

    return processed_tasks

def save_tasks(tasks):
    """Saves tasks to the JSON data file (tasks.json).

    Datetime.datetime objects (for "last_completed_timestamp") and datetime.date objects
    (for "streak_last_updated_date") within the task data are converted to ISO format strings
    before serialization. The JSON file is pretty-printed with an indent of 4.

    Args:
        tasks (dict): A dictionary of tasks to save, where keys are task names (str)
                      and values are task data objects (dict).
    """
    serializable_tasks = {}
    for task_name, data in tasks.items():
        # Create a copy of data to avoid modifying the original dict in memory during serialization
        task_data_copy = data.copy()

        # Convert datetime object to ISO string
        if isinstance(task_data_copy.get("last_completed_timestamp"), datetime.datetime):
            task_data_copy["last_completed_timestamp"] = task_data_copy["last_completed_timestamp"].isoformat()
        elif task_data_copy.get("last_completed_timestamp") is not None: # If it's some other non-None, non-datetime type, ensure it's nullified for JSON
            print(f"Warning: Invalid type for last_completed_timestamp for task '{task_name}' during save. Setting to null.")
            task_data_copy["last_completed_timestamp"] = None

        # Convert date object to ISO string
        if isinstance(task_data_copy.get("streak_last_updated_date"), datetime.date):
            task_data_copy["streak_last_updated_date"] = task_data_copy["streak_last_updated_date"].isoformat()
        elif task_data_copy.get("streak_last_updated_date") is not None: # If it's some other non-None, non-date type, ensure it's nullified
            print(f"Warning: Invalid type for streak_last_updated_date for task '{task_name}' during save. Setting to null.")
            task_data_copy["streak_last_updated_date"] = None

        serializable_tasks[task_name] = task_data_copy

    with open(DATA_FILE, "w") as f:
        json.dump(serializable_tasks, f, indent=4)

def add_task(task_name):
    """Adds a new task to the task list and saves to the JSON file.

    If the task already exists, a message is printed, and no changes are made.
    New tasks are initialized with:
    - "last_completed_timestamp": None
    - "current_streak": 0
    - "streak_last_updated_date": None

    Args:
        task_name (str): The name of the task to add.
    """
    tasks = load_tasks()
    if task_name in tasks:
        print(f"Task '{task_name}' already exists.")
    else:
        tasks[task_name] = {
            "last_completed_timestamp": None,
            "current_streak": 0,
            "streak_last_updated_date": None
        }
        save_tasks(tasks)
        print(f"Task '{task_name}' added with an initial streak of 0.")

def mark_task_completed(task_name):
    """Marks a task as completed with the current timestamp and updates its daily streak.

    The function implements a daily streak logic:
    - If the task is completed on a new calendar day (compared to 'streak_last_updated_date'):
        - If 'streak_last_updated_date' was yesterday, 'current_streak' is incremented.
        - Otherwise (e.g., first completion ever, or a day was missed), 'current_streak' is reset to 1.
    - If the task has already been marked completed earlier today (i.e., 'streak_last_updated_date' is today),
      the 'current_streak' and 'streak_last_updated_date' do not change further.

    In all cases where the task is found, 'last_completed_timestamp' is updated to the current datetime.
    The 'streak_last_updated_date' is updated to the current date if the streak was affected (i.e., it's a new day for the streak).
    Saves changes to the JSON file.

    Args:
        task_name (str): The name of the task to mark as completed.
    """
    tasks = load_tasks()
    if task_name not in tasks:
        print(f"Task '{task_name}' not found. You can add it first.")
        return

    task_data = tasks[task_name]
    now = datetime.datetime.now()
    today = now.date()

    # Initialize streak and last_updated_date if they don't exist (e.g. for tasks from old format)
    if "current_streak" not in task_data or not isinstance(task_data["current_streak"], int):
        task_data["current_streak"] = 0
    if "streak_last_updated_date" not in task_data or not isinstance(task_data["streak_last_updated_date"], datetime.date):
        # If it's a string, try to parse it (e.g. from an older version of JSON before type conversion in load_tasks was perfect)
        if isinstance(task_data.get("streak_last_updated_date"), str):
            try:
                task_data["streak_last_updated_date"] = datetime.date.fromisoformat(task_data["streak_last_updated_date"])
            except ValueError:
                task_data["streak_last_updated_date"] = None # Set to None if parsing fails
        else:
             task_data["streak_last_updated_date"] = None


    last_streak_update_date = task_data.get("streak_last_updated_date")

    if last_streak_update_date != today: # Only update streak if it's a new day or first time
        if last_streak_update_date == today - datetime.timedelta(days=1):
            task_data["current_streak"] += 1
            print(f"Good job! Streak continued for '{task_name}'. Current streak: {task_data['current_streak']}.")
        else:
            # This covers:
            # 1. First time completing the task (last_streak_update_date is None).
            # 2. Missed one or more days (last_streak_update_date is not yesterday).
            task_data["current_streak"] = 1
            print(f"Streak started/restarted for '{task_name}'! Current streak: 1.")
        task_data["streak_last_updated_date"] = today
    else:
        # Task already completed today, streak doesn't change further.
        # last_completed_timestamp will still be updated.
        print(f"Task '{task_name}' already marked for today's streak. Completion time updated.")


    task_data["last_completed_timestamp"] = now
    save_tasks(tasks)
    # Use task_data here as 'tasks' dict in memory is updated by save_tasks preparing for serialization.
    # For display, better to use the value from task_data which is definitively a datetime object.
    formatted_time = task_data["last_completed_timestamp"].strftime('%Y-%m-%d %H:%M:%S')
    print(f"Task '{task_name}' marked as completed at {formatted_time}.")

def list_tasks():
    """Lists all tasks, displaying their name, last completion time, time elapsed, and current streak.

    If no tasks are found, a message is printed.
    For each task, it displays:
    - Task Name
    - Last Completed: Timestamp (YYYY-MM-DD HH:MM:SS) and human-readable time since (e.g., "X days ago").
                      Shows "Never" if never completed.
    - Current Streak: Number of consecutive days the task has been completed.
    """
    tasks = load_tasks()
    if not tasks:
        print("No tasks found. Add some tasks first!")
        return

    print("\n--- Your Tasks ---")
    for task_name, data in tasks.items():
        print(f"Task: {task_name}")

        last_completed_timestamp = data.get("last_completed_timestamp")

        if last_completed_timestamp:
            # Ensure it's a datetime object if loaded correctly
            if isinstance(last_completed_timestamp, datetime.datetime):
                time_ago_str = time_since(last_completed_timestamp)
                last_time_str = last_completed_timestamp.strftime("%Y-%m-%d %H:%M:%S")
                print(f"  Last completed: {last_time_str} ({time_ago_str})")
            else: # Should not happen if load_tasks works correctly
                print(f"  Last completed: Error processing timestamp ({last_completed_timestamp})")
        else:
            print("  Last completed: Never")

        current_streak = data.get("current_streak", 0) # Default to 0 if not found
        print(f"  Current Streak: {current_streak} day{'s' if current_streak != 1 else ''}")
        print("-" * 20) # Separator for tasks
    print("------------------\n")

def main_cli():
    """Runs the main command-line interface for the task and streak management application.

    Presents a menu to the user to:
    1. Add a new task.
    2. Mark a task as completed (which also updates its streak).
    3. List all tasks with their details.
    4. Exit the application.
    Ensures `tasks.json` (the data file) exists before starting; creates an empty one if not.
    """
    # Create tasks.json if it doesn't exist, to avoid error on first load_tasks by list_tasks or other operations.
    if not os.path.exists(DATA_FILE):
        save_tasks({}) # Create an empty tasks file

    while True:
        print("\nWhat would you like to do?")
        print("1. Add a new task")
        print("2. Mark a task as completed")
        print("3. List all tasks")
        print("4. Exit")

        choice = input("Enter your choice (1-4): ")

        if choice == '1':
            task_name = input("Enter the name of the new task: ")
            if task_name.strip(): # Ensure task name is not empty after removing leading/trailing whitespace
                 add_task(task_name.strip())
            else:
                print("Task name cannot be empty.")
        elif choice == '2':
            task_name = input("Enter the name of the task to mark as completed: ")
            if task_name.strip(): # Ensure task name is not empty
                mark_task_completed(task_name.strip())
            else:
                print("Task name cannot be empty.")
        elif choice == '3':
            list_tasks()
        elif choice == '4':
            print("Exiting application. Goodbye!")
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 4.")

if __name__ == '__main__':
    main_cli()

# Helper Functions
# ----------------

def time_since(dt_object):
    """Calculates time elapsed since a datetime object into a human-readable string.

    Args:
        dt_object (datetime.datetime or None): The past datetime object from which to calculate
                                             the time elapsed. If None, indicates the event
                                             has not occurred.

    Returns:
        str: A human-readable string representing the time elapsed (e.g., "2 days, 3 hours ago").
             Returns "Never" if dt_object is None.
             Returns "Just now" if the time difference is negligible or in the future (though future is unexpected).
    """
    if dt_object is None:
        return "Never"

    now = datetime.datetime.now()
    delta = now - dt_object

    days = delta.days
    seconds_in_day = delta.seconds

    hours, remainder = divmod(seconds_in_day, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if days > 0:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if seconds > 0 or not parts: # show seconds if it's the only unit or if it's non-zero
        parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")

    if not parts: # Should ideally not happen if dt_object is in the past.
        return "Just now"

    return ", ".join(parts) + " ago"
