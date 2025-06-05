"""
last_time_us.py
A simple command-line application to track when tasks were last completed.
Tasks are stored in a text file named 'tasks.txt'.
Each line in 'tasks.txt' represents one task in the format:
task_name,timestamp_iso_format_or_Never
Example:
Grocery Shopping,2023-10-27T14:30:00.123456
Workout,Never
"""
import os
import datetime

DATA_FILE = "tasks.txt"

def load_tasks():
    """Loads tasks from the data file.

    Tasks are read from DATA_FILE. Each line is expected to be in the format:
    'task_name,timestamp' or 'task_name'.
    If the timestamp is missing, invalid, or 'None'/'Never', the task's timestamp will be None.

    Returns:
        dict: A dictionary where keys are task names (str) and values are their
              last completion timestamps (datetime.datetime objects or None if never completed
              or if the timestamp was malformed).
    """
    tasks = {}
    if not os.path.exists(DATA_FILE):
        return tasks

    with open(DATA_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(",", 1)  # Split only on the first comma to separate task name from timestamp
            task_name = parts[0]
            timestamp_str = parts[1] if len(parts) > 1 else None

            if timestamp_str and timestamp_str != "None" and timestamp_str != "Never": # Check for valid timestamp string
                try:
                    tasks[task_name] = datetime.datetime.fromisoformat(timestamp_str)
                except ValueError:
                    # Handle potential malformed timestamps gracefully, e.g., log an error or skip
                    print(f"Warning: Malformed timestamp for task '{task_name}': {timestamp_str}")
                    tasks[task_name] = None
            else:
                tasks[task_name] = None
    return tasks

def save_tasks(tasks):
    """Saves tasks to the data file.

    Tasks are written to DATA_FILE. Timestamps are stored in ISO format.
    If a task's timestamp is None, it's saved as "Never".

    Args:
        tasks (dict): A dictionary of tasks to save, where keys are task names (str)
                      and values are datetime.datetime objects or None.
    """
    with open(DATA_FILE, "w") as f:
        for task_name, timestamp in tasks.items():
            timestamp_str = timestamp.isoformat() if timestamp else "Never" # Convert datetime to ISO string or use "Never"
            f.write(f"{task_name},{timestamp_str}\n")

def add_task(task_name):
    """Adds a new task to the task list.

    If the task already exists, a message is printed and no action is taken.
    New tasks are initialized with no completion timestamp (None).

    Args:
        task_name (str): The name of the task to add.
    """
    tasks = load_tasks()
    if task_name in tasks:
        print(f"Task '{task_name}' already exists.")
    else:
        tasks[task_name] = None  # None indicates never completed
        save_tasks(tasks)
        print(f"Task '{task_name}' added.")

def mark_task_completed(task_name):
    """Marks a task as completed with the current timestamp.

    If the task does not exist, a message is printed. Otherwise, the task's
    timestamp is updated to the current time.

    Args:
        task_name (str): The name of the task to mark as completed.
    """
    tasks = load_tasks()
    if task_name not in tasks:
        print(f"Task '{task_name}' not found. You can add it first.")
    else:
        tasks[task_name] = datetime.datetime.now()
        save_tasks(tasks)
        print(f"Task '{task_name}' marked as completed at {tasks[task_name].strftime('%Y-%m-%d %H:%M:%S')}.")

def list_tasks():
    """Lists all tasks with their last completion times.

    If no tasks are found, a message is printed. Otherwise, tasks are listed
    with their completion timestamp or "Never completed".
    """
    tasks = load_tasks()
    if not tasks:
        print("No tasks found. Add some tasks first!")
        return

    print("\n--- Your Tasks ---")
    for task_name, timestamp in tasks.items():
        if timestamp:
            time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        else:
            time_str = "Never completed"
        print(f"- {task_name}: {time_str}")
    print("------------------\n")

def main_cli():
    """Runs the main command-line interface for the application.

    Presents a menu to the user to add tasks, mark tasks as completed,
    list tasks, or exit the application.
    Ensures `tasks.txt` exists before starting the loop.
    """
    # Create tasks.txt if it doesn't exist, to avoid error on first load_tasks by list_tasks or other operations.
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
