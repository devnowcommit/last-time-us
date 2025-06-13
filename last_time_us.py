"""
last_time_us.py
A command-line application to track tasks, their last completion times, daily streaks,
and total completions. Features a configurable streak grace period.
Tasks are stored in a JSON file named 'tasks.json'.
The JSON file contains a dictionary where keys are task names.
Each task object has the following structure:
{
    "task_name_key": {
        "creation_timestamp": "ISO_DATETIME_STRING_OR_NULL", # <-- New field
        "last_completed_timestamp": "ISO_DATETIME_STRING_OR_NULL",
        "current_streak": INTEGER,
        "streak_last_updated_date": "ISO_DATE_STRING_OR_NULL",
        "total_completions": INTEGER
    },
    ...
}
Example:
{
    "Grocery Shopping": {
        "creation_timestamp": "2023-10-26T10:00:00.000000",
        "last_completed_timestamp": "2023-10-27T14:30:00.123456",
        "current_streak": 5,
        "streak_last_updated_date": "2023-10-27",
        "total_completions": 10
    },
    "Workout": {
        "creation_timestamp": "2023-10-27T12:00:00.000000",
        "last_completed_timestamp": null,
        "current_streak": 0,
        "streak_last_updated_date": null,
        "total_completions": 0
    }
}
"""
import os
import datetime
import json # <--- Add this import

# ANSI Color Codes for Terminal Output
COLOR_GREEN = "\033[92m"    # Bright Green
COLOR_YELLOW = "\033[93m"   # Bright Yellow
COLOR_BLUE = "\033[94m"     # Bright Blue
COLOR_MAGENTA = "\033[95m"  # Bright Magenta
COLOR_CYAN = "\033[96m"     # Bright Cyan
# COLOR_RED = "\033[91m"      # Bright Red (example, not used for menu yet)
# COLOR_BOLD = "\033[1m"      # Bold
COLOR_RESET = "\033[0m"     # Reset all attributes

# ... (DATA_FILE constant is already updated)

DATA_FILE = "tasks.json"
GRACE_DAYS = 1 # Number of days a task can be missed before a streak breaks

def load_tasks():
    """Loads tasks from the JSON data file (tasks.json).

    Tasks are deserialized from JSON. For each task, it ensures:
    - "creation_timestamp" (ISO string) is converted to a datetime.datetime object (or None if missing/invalid).
    - "last_completed_timestamp" (ISO string) is converted to a datetime.datetime object (or None if missing/invalid).
    - "streak_last_updated_date" (ISO string) is converted to a datetime.date object (or None if missing/invalid).
    - "current_streak" is an integer (defaulting to 0 if missing/invalid).
    - "total_completions" is an integer (defaulting to 0 if missing/invalid).
    Handles potential JSON decoding errors or file not found by returning an empty dictionary.

    Returns:
        dict: A dictionary where keys are task names (str) and values are task data objects (dict)
              containing processed timestamps, dates, streak, and total completions information.
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
        # Convert creation_timestamp string to datetime object
        if data.get("creation_timestamp"):
            try:
                data["creation_timestamp"] = datetime.datetime.fromisoformat(data["creation_timestamp"])
            except (ValueError, TypeError):
                print(f"Warning: Malformed creation_timestamp for task '{task_name}'. Setting to None.")
                data["creation_timestamp"] = None
        else:
            data["creation_timestamp"] = None # Ensure it's None if missing or null in JSON

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

        # Ensure total_completions is an int, default to 0 if missing/invalid
        try:
            data["total_completions"] = int(data.get("total_completions", 0))
        except (ValueError, TypeError):
            print(f"Warning: Invalid total_completions value for task '{task_name}'. Resetting to 0.")
            data["total_completions"] = 0

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

        # Convert creation_timestamp datetime object to ISO string (NEW BLOCK)
        if isinstance(task_data_copy.get("creation_timestamp"), datetime.datetime):
            task_data_copy["creation_timestamp"] = task_data_copy["creation_timestamp"].isoformat()
        elif task_data_copy.get("creation_timestamp") is not None:
            # This handles cases where it might be something other than None or datetime,
            # which would also cause JSON serialization issues.
            print(f"Warning: Invalid type for creation_timestamp for task '{task_name}' during save. Setting to null.")
            task_data_copy["creation_timestamp"] = None

        # Convert last_completed_timestamp datetime object to ISO string (Existing block)
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
    New tasks are initialized with a 'creation_timestamp' set to the current time,
    and default values for 'last_completed_timestamp' (None), 'current_streak' (0),
    'streak_last_updated_date' (None), and 'total_completions' (0).
    Saves changes to the JSON file.

    Args:
        task_name (str): The name of the task to add.
    """
    tasks = load_tasks()
    if task_name in tasks:
        print(f"La tarea '{task_name}' ya existe.")
    else:
        current_time = datetime.datetime.now() # Get current time
        tasks[task_name] = {
            "creation_timestamp": current_time, # <--- Store datetime object directly for now
            "last_completed_timestamp": None,
            "current_streak": 0,
            "streak_last_updated_date": None,
            "total_completions": 0
        }
        save_tasks(tasks) # save_tasks will handle converting datetime to string
        print(f"Tarea '{task_name}' añadida con una racha inicial de 0.")

def mark_task_completed(task_name):
    """Marks a task as completed with the current timestamp and updates its daily streak.

    Streak logic incorporates a grace period defined by `GRACE_DAYS` global constant:
    - If the task was last completed for streak purposes on the previous day,
      the streak continues normally.
    - If the task was last completed for streak purposes within `GRACE_DAYS + 1` days
      (e.g., if GRACE_DAYS = 1, this means completed the day before yesterday),
      the streak also continues, utilizing the grace period.
    - If the task was already marked completed for streak purposes today, the streak
      count does not change further, but the 'last_completed_timestamp' is updated.
    - Otherwise (e.g., gap is too large, or it's the first completion), the streak
      resets to 1. A distinction is made in messaging between a "started" and "restarted" streak.

    Increments the task's 'total_completions' counter.
    Updates 'last_completed_timestamp' to the current datetime, and 'streak_last_updated_date'
    to the current date if the streak was affected. Saves changes to the JSON file.

    Args:
        task_name (str): The name of the task to mark as completed.
    """
    tasks = load_tasks()
    if task_name not in tasks:
        print(f"Tarea '{task_name}' no encontrada. Puedes añadirla primero.")
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

    if last_streak_update_date == today:
        # Task already completed today for streak purposes, streak doesn't change further.
        print(f"Tarea '{task_name}' ya marcada para la racha de hoy. Hora de completada actualizada.")
    else:
        # Calculate the difference in days from the last streak update
        days_difference = (today - last_streak_update_date).days if last_streak_update_date else float('inf')

        if days_difference == 1: # Completed yesterday, normal continuation
            task_data["current_streak"] += 1
            print(f"¡Buen trabajo! Racha continuada para '{task_name}'. Racha actual: {task_data['current_streak']}.")
        elif 1 < days_difference <= (GRACE_DAYS + 1): # Completed within grace period
            task_data["current_streak"] += 1
            # It might be nice to let the user know they used a grace day, but for simplicity,
            # the message can be the same as normal continuation or slightly adjusted.
            # Let's make it distinct for now.
            print(f"¡Racha continuada para '{task_name}' (día(s) de gracia usados)! Racha actual: {task_data['current_streak']}.")
        else: # Streak broken (gap too large) or first completion
            task_data["current_streak"] = 1
            if last_streak_update_date: # It's a reset
                 print(f"¡Racha reiniciada para '{task_name}'! Racha actual: 1.")
            else: # It's the very first time
                 print(f"¡Racha iniciada para '{task_name}'! Racha actual: 1.")

        task_data["streak_last_updated_date"] = today

    # Increment total completions (existing logic - should be here)
    task_data["total_completions"] = task_data.get("total_completions", 0) + 1

    task_data["last_completed_timestamp"] = now
    save_tasks(tasks)

    formatted_time = task_data["last_completed_timestamp"].strftime('%Y-%m-%d %H:%M:%S')
    print(f"Tarea '{task_name}' marcada como completada a las {formatted_time}.")

# Helper function for list_tasks
def time_since(dt_object):
    """Calculates time elapsed since a datetime object in a human-readable Spanish string.

    Args:
        dt_object (datetime.datetime): The past datetime object.

    Returns:
        str: Human-readable string of time elapsed in Spanish (e.g., "hace 1 día, 2 horas").
             Returns "Nunca" if dt_object is None.
             Returns "Justo ahora" if the difference is minimal.
    """
    if dt_object is None:
        return "Nunca"  # Translated

    now = datetime.datetime.now()
    delta = now - dt_object

    # Ensure delta is not negative (i.e. dt_object is not in the future)
    if delta.total_seconds() < 0:
        # Or handle as an error, or return a specific string for future dates
        return "En el futuro" # "In the future" - or adapt as needed

    days = delta.days
    seconds_in_day_remainder = delta.seconds # Renamed for clarity

    hours, remainder_after_hours = divmod(seconds_in_day_remainder, 3600)
    minutes, seconds = divmod(remainder_after_hours, 60)

    parts = []
    if days > 0:
        parts.append(f"{days} {'días' if days != 1 else 'día'}") # Spanish pluralization
    if hours > 0:
        parts.append(f"{hours} {'horas' if hours != 1 else 'hora'}") # Spanish pluralization
    if minutes > 0:
        parts.append(f"{minutes} {'minutos' if minutes != 1 else 'minuto'}") # Spanish pluralization

    # Show seconds if it's the only unit, or if other units are present and seconds > 0.
    # Or always show seconds if delta is less than a minute.
    if not parts and seconds >= 0: # If no days, hours, minutes, show seconds (even if 0 for "Justo ahora" case)
         parts.append(f"{seconds} {'segundos' if seconds != 1 else 'segundo'}") # Spanish pluralization
    elif parts and seconds > 0 : # If there are other parts, only add seconds if non-zero
         parts.append(f"{seconds} {'segundos' if seconds != 1 else 'segundo'}")


    if not parts:
        # This case should ideally be caught if seconds are always added when no other parts exist.
        # If parts is empty, it means days, hours, minutes, AND seconds were all zero (or seconds logic was skipped).
        return "Justo ahora" # Translated

    # Construct the string with "hace" at the beginning
    time_str = ", ".join(parts)
    return f"hace {time_str}"

def list_tasks():
    """Lists all tasks, displaying their name, last completion time, time elapsed, and current streak.

    If no tasks are found, a message is printed.
    For each task, it displays:
    - Task Name.
    - Time elapsed since creation (if available).
    - Last completion time (absolute and relative time via `time_since`).
    - Current streak count.
    - Total number of completions for the task.
    """
    tasks = load_tasks()
    if not tasks:
        print("No se encontraron tareas. ¡Añade algunas tareas primero!")
        return

    print("\n--- Tus Tareas ---")
    for task_name, data in tasks.items():
        print(f"Tarea: {task_name}")

        # Display Creation Timestamp (New Block)
        creation_ts = data.get("creation_timestamp")
        if creation_ts:
            # Ensure it's a datetime object (load_tasks should handle this)
            if isinstance(creation_ts, datetime.datetime):
                created_ago_str = time_since(creation_ts) # Reuse existing helper
                # Optional: also print the absolute creation time
                # created_time_str = creation_ts.strftime("%Y-%m-%d %H:%M:%S")
                # print(f"  Creada: {created_time_str} ({created_ago_str})")
                print(f"  Creada: {created_ago_str}")
            else: # Should ideally not happen if load_tasks is correct
                print(f"  Creada: Error procesando timestamp de creación.")
        else:
            # This case handles tasks created before this feature was implemented,
            # or if creation_timestamp was explicitly null or malformed during load.
            print(f"  Creada: Información no disponible")

        last_completed_timestamp = data.get("last_completed_timestamp")

        if last_completed_timestamp:
            # Ensure it's a datetime object if loaded correctly
            if isinstance(last_completed_timestamp, datetime.datetime):
                time_ago_str = time_since(last_completed_timestamp)
                last_time_str = last_completed_timestamp.strftime("%Y-%m-%d %H:%M:%S")
                print(f"  Última vez completada: {last_time_str} ({time_ago_str})")
            else: # Should not happen if load_tasks works correctly
                print(f"  Última vez completada: Error procesando timestamp ({last_completed_timestamp})")
        else:
            print("  Última vez completada: Nunca")

        current_streak = data.get("current_streak", 0) # Default to 0 if not found
        print(f"  Racha Actual: {current_streak} día{'s' if current_streak != 1 else ''}")

        total_completions = data.get("total_completions", 0)
        print(f"  Veces completada: {total_completions}")
        print("-" * 20) # Separator for tasks
    print("------------------\n")

def display_statistics():
    """Calculates and displays statistics about the tasks.

    Statistics displayed:
    - Total number of tasks.
    - Number of tasks with an active streak (current_streak > 0).
    - Task(s) with the highest current streak and that streak count.
    - Total number of completions across all tasks.
    - Task(s) with the highest number of total completions and that count.
    Handles the case where no tasks exist by printing an informative message.
    """
    tasks = load_tasks()

    if not tasks:
        print("No hay tareas disponibles para calcular estadísticas.")
        return

    total_tasks = len(tasks)
    active_streak_tasks_count = 0
    highest_streak_value = 0 # Renamed from highest_streak to avoid confusion
    tasks_with_highest_streak = []

    total_completions_all_tasks = 0
    max_completions_count = 0
    tasks_with_max_completions = []

    for task_name, data in tasks.items():
        # Streak calculations (existing logic)
        current_streak = data.get("current_streak", 0)
        if current_streak > 0:
            active_streak_tasks_count += 1

        if current_streak > highest_streak_value:
            highest_streak_value = current_streak
            tasks_with_highest_streak = [task_name]
        elif current_streak == highest_streak_value and current_streak > 0:
            tasks_with_highest_streak.append(task_name)

        # Total completions calculations (new logic)
        task_total_completions = data.get("total_completions", 0)
        total_completions_all_tasks += task_total_completions

        if task_total_completions > max_completions_count:
            max_completions_count = task_total_completions
            tasks_with_max_completions = [task_name]
        elif task_total_completions == max_completions_count and task_total_completions > 0: # task_total_completions > 0 ensures we don't list all 0-completion tasks if max_completions_count is 0
            tasks_with_max_completions.append(task_name)


    print("\n--- Estadísticas de Tareas ---")
    print(f"Número total de tareas: {total_tasks}")
    print(f"Tareas con racha activa: {active_streak_tasks_count}")

    if highest_streak_value > 0:
        print(f"Racha actual más larga: {highest_streak_value} día{'s' if highest_streak_value != 1 else ''}")
        if tasks_with_highest_streak:
            print(f"  Lograda por (racha): {', '.join(tasks_with_highest_streak)}")
    else:
        print("Actualmente ninguna tarea tiene una racha activa.")

    print(f"Total de veces completadas (todas las tareas): {total_completions_all_tasks}")

    if max_completions_count > 0: # New block for displaying most frequent
        print(f"Mayor número de veces completada (tarea individual): {max_completions_count}")
        if tasks_with_max_completions:
            print(f"  Tarea(s) completada(s) más frecuentemente: {', '.join(tasks_with_max_completions)}")
    else:
        print("Ninguna tarea ha sido completada aún.")

    print("-----------------------\n")

def select_task_from_list(action_verb="select"):
    """Displays a numbered list of tasks and prompts the user to select one.

    Handles cases where no tasks are available or the user cancels the selection.
    Uses a loop to ensure valid numeric input within the range of available tasks or 0 for cancellation.

    Args:
        action_verb (str): The verb to use in the prompt, e.g., "select", "delete", "edit".
                               Defaults to "select".

    Returns:
        str|None: The name of the selected task if a valid selection is made.
                      Returns None if no tasks are available, or if the user chooses to cancel.
    """
    tasks = load_tasks()
    if not tasks:
        print("No hay tareas disponibles. Por favor, añade algunas tareas primero.")
        return None

    print(f"\n--- Tareas disponibles para {action_verb} ---")
    # Create a list of task names to ensure consistent ordering for selection
    task_names_ordered = list(tasks.keys())

    for i, task_name in enumerate(task_names_ordered):
        print(f"{i+1}. {task_name}")
    print("-----------------------------")

    while True:
        try:
            choice_str = input(f"Ingresa el número de la tarea para {action_verb} (o 0 para cancelar): ")
            choice_num = int(choice_str)

            if choice_num == 0:
                return None # Cancellation

            if 1 <= choice_num <= len(task_names_ordered):
                return task_names_ordered[choice_num - 1] # Return the actual task name
            else:
                print(f"Número inválido. Por favor, ingresa un número entre 1 y {len(task_names_ordered)}, o 0 para cancelar.")
        except ValueError:
            print("Entrada inválida. Por favor, ingresa un número.")
        except Exception as e: # Catch any other unexpected error during input
            print(f"Ocurrió un error inesperado: {e}")
            return None # Safer to cancel on unexpected error

def main_cli():
    """Runs the main command-line interface for the task and streak management application.

    Presents a menu to the user to:
    1. Add a new task (user types the name).
    2. Mark a task as completed (user selects from a list, which also updates its streak).
    3. List all tasks with their details.
    4. Show Statistics.
    5. Exit the application.
    Ensures `tasks.json` (the data file) exists before starting; creates an empty one if not.
    """
    # Create tasks.json if it doesn't exist, to avoid error on first load_tasks by list_tasks or other operations.
    if not os.path.exists(DATA_FILE):
        save_tasks({}) # Create an empty tasks file

    while True:
        print("\n¿Qué te gustaría hacer?")
        print(f"{COLOR_GREEN}1. Añadir nueva tarea{COLOR_RESET}")
        print(f"{COLOR_YELLOW}2. Marcar tarea como completada{COLOR_RESET}")
        print(f"{COLOR_BLUE}3. Listar todas las tareas{COLOR_RESET}")
        print(f"{COLOR_MAGENTA}4. Mostrar estadísticas{COLOR_RESET}")
        print(f"{COLOR_CYAN}5. Salir{COLOR_RESET}")

        choice = input("Ingresa tu opción (1-5): ")

        if choice == '1':
            task_name = input("Ingresa el nombre de la nueva tarea: ")
            if task_name.strip(): # Ensure task name is not empty after removing leading/trailing whitespace
                 add_task(task_name.strip())
            else:
                print("El nombre de la tarea no puede estar vacío.")
        elif choice == '2':
            selected_task_name = select_task_from_list(action_verb="marcar como completada") # Call the helper
            if selected_task_name: # If a task name was returned (not None)
                mark_task_completed(selected_task_name)
            # If selected_task_name is None, it means either no tasks were available or the user cancelled.
            # The select_task_from_list function already prints "No tasks available..." if needed.
            # So, no explicit 'else' is needed here unless we want to print "Cancelled."
        elif choice == '3':
            list_tasks()
        elif choice == '4': # <--- New elif block
            display_statistics()
        elif choice == '5': # <--- Exit condition updated
            print("Saliendo de la aplicación. ¡Adiós!")
            break
        else:
            print("Opción inválida. Por favor, ingresa un número entre 1 y 5.")

if __name__ == '__main__':
    main_cli()
