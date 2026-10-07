"""
Simple Command-Line To-Do List Application
"""

def show_menu():
    print("\n" + "=" * 30)
    print("        TO-DO LIST")
    print("=" * 30)
    print("1. View tasks")
    print("2. Add task")
    print("3. Mark task as completed")
    print("4. Delete task")
    print("5. Exit")
    print("=" * 30)


def view_tasks(tasks):
    if not tasks:
        print("\nYour to-do list is empty!")
        return

    print("\nYour tasks:")
    for i, task in enumerate(tasks, start=1):
        status = "✔" if task["completed"] else " "
        print(f"  {i}. [{status}] {task['title']}")


def add_task(tasks):
    title = input("\nEnter task description: ").strip()
    if title:
        tasks.append({"title": title, "completed": False})
        print(f"Task '{title}' added successfully!")
    else:
        print("Task cannot be empty.")


def complete_task(tasks):
    view_tasks(tasks)
    if not tasks:
        return

    try:
        task_num = int(input("\nEnter task number to mark completed: "))
        if 1 <= task_num <= len(tasks):
            tasks[task_num - 1]["completed"] = True
            print(f"Task {task_num} marked as completed!")
        else:
            print("Invalid task number.")
    except ValueError:
        print("Please enter a valid number.")


def delete_task(tasks):
    view_tasks(tasks)
    if not tasks:
        return

    try:
        task_num = int(input("\nEnter task number to delete: "))
        if 1 <= task_num <= len(tasks):
            removed = tasks.pop(task_num - 1)
            print(f"Task '{removed['title']}' deleted!")
        else:
            print("Invalid task number.")
    except ValueError:
        print("Please enter a valid number.")


def main():
    tasks = []

    while True:
        show_menu()
        choice = input("Choose an option (1-5): ").strip()

        if choice == "1":
            view_tasks(tasks)
        elif choice == "2":
            add_task(tasks)
        elif choice == "3":
            complete_task(tasks)
        elif choice == "4":
            delete_task(tasks)
        elif choice == "5":
            print("\nGoodbye! Have a productive day.")
            break
        else:
            print("Invalid choice, please select between 1 and 5.")


if __name__ == "__main__":
    main()