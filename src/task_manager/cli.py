"""
Command-line interface for the Task Manager application.

This module provides a user-friendly CLI for managing tasks using argparse.
"""

import argparse
import sys
from typing import List
from src.task_manager import operations
from src.task_manager.models import Task, Status, ValidationError
from src.task_manager.storage import TaskNotFoundError, StorageError


def create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser for the CLI.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        description='Task Manager CLI - Manage your daily tasks',
        prog='task_cli'
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Add command
    add_parser = subparsers.add_parser('add', help='Add a new task')
    add_parser.add_argument('--title', required=True, help='Task title')
    add_parser.add_argument('--description', help='Task description')
    add_parser.add_argument('--priority', default='medium',
                           choices=['high', 'medium', 'low'],
                           help='Task priority (default: medium)')
    add_parser.add_argument('--due-date', dest='due_date',
                           help='Due date (YYYY-MM-DD format)')

    # List command
    list_parser = subparsers.add_parser('list', help='List tasks')
    list_parser.add_argument('--status',
                            choices=['active', 'completed'],
                            help='Filter by status')
    list_parser.add_argument('--priority',
                            choices=['high', 'medium', 'low'],
                            help='Filter by priority')
    list_parser.add_argument('--sort-by', dest='sort_by',
                            default='created_at',
                            choices=['created_at', 'due_date', 'priority'],
                            help='Sort by field (default: created_at)')

    # Complete command
    complete_parser = subparsers.add_parser('complete', help='Mark task as completed')
    complete_parser.add_argument('task_id', help='Task ID')

    # Incomplete command
    incomplete_parser = subparsers.add_parser('incomplete', help='Mark task as active')
    incomplete_parser.add_argument('task_id', help='Task ID')

    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a task')
    delete_parser.add_argument('task_id', help='Task ID')

    # Clear command
    subparsers.add_parser('clear', help='Clear all completed tasks')

    return parser


def format_task(task: Task) -> str:
    """
    Format a single task for display.

    Args:
        task: Task to format.

    Returns:
        Formatted task string.
    """
    lines = []
    lines.append(f"ID: {task.id}")
    lines.append(f"Title: {task.title}")
    if task.description:
        lines.append(f"Description: {task.description}")
    lines.append(f"Priority: {task.priority.value}")
    lines.append(f"Status: {task.status.value}")
    if task.due_date:
        lines.append(f"Due Date: {task.due_date}")
    lines.append(f"Created: {task.created_at}")
    if task.completed_at:
        lines.append(f"Completed: {task.completed_at}")

    return '\n'.join(lines)


def format_task_list(tasks: List[Task]) -> str:
    """
    Format a list of tasks as a table.

    Args:
        tasks: List of tasks to format.

    Returns:
        Formatted table string.
    """
    if not tasks:
        return "No tasks found."

    # Header
    header = f"{'ID':<36} | {'Title':<30} | {'Priority':<8} | {'Status':<10} | {'Due Date':<12}"
    separator = '-' * len(header)

    lines = [header, separator]

    # Task rows
    for task in tasks:
        task_id = str(task.id)[:8] + '...'  # Truncate ID for display
        title = task.title[:27] + '...' if len(task.title) > 30 else task.title
        priority = task.priority.value
        status = task.status.value
        due_date = task.due_date or 'N/A'

        row = f"{task_id:<36} | {title:<30} | {priority:<8} | {status:<10} | {due_date:<12}"
        lines.append(row)

    return '\n'.join(lines)


def cmd_add(args) -> None:
    """
    Handle the 'add' command.

    Args:
        args: Parsed command-line arguments.
    """
    try:
        task = operations.create_task(
            args.title,
            args.description,
            args.priority,
            args.due_date
        )
        print("Task created successfully!")
        print(format_task(task))
    except ValidationError as e:
        print(f"Error: {e}")
    except StorageError as e:
        print(f"Error: {e}")


def cmd_list(args) -> None:
    """
    Handle the 'list' command.

    Args:
        args: Parsed command-line arguments.
    """
    try:
        tasks = operations.list_tasks(
            args.status,
            args.priority,
            args.sort_by
        )

        if not tasks:
            print("No tasks found.")
        else:
            print(format_task_list(tasks))
    except Exception as e:
        print(f"Error: {e}")


def cmd_complete(args) -> None:
    """
    Handle the 'complete' command.

    Args:
        args: Parsed command-line arguments.
    """
    try:
        operations.update_task_status(args.task_id, Status.COMPLETED)
        print(f"Task {args.task_id} marked as completed successfully.")
    except TaskNotFoundError as e:
        print(f"Error: Task not found - {e}")
    except Exception as e:
        print(f"Error: {e}")


def cmd_incomplete(args) -> None:
    """
    Handle the 'incomplete' command.

    Args:
        args: Parsed command-line arguments.
    """
    try:
        operations.update_task_status(args.task_id, Status.ACTIVE)
        print(f"Task {args.task_id} marked as active successfully.")
    except TaskNotFoundError as e:
        print(f"Error: Task not found - {e}")
    except Exception as e:
        print(f"Error: {e}")


def cmd_delete(args) -> None:
    """
    Handle the 'delete' command.

    Args:
        args: Parsed command-line arguments.
    """
    try:
        operations.delete_task(args.task_id)
        print(f"Task {args.task_id} deleted successfully.")
    except TaskNotFoundError as e:
        print(f"Error: Task not found - {e}")
    except Exception as e:
        print(f"Error: {e}")


def cmd_clear(args) -> None:
    """
    Handle the 'clear' command.

    Args:
        args: Parsed command-line arguments.
    """
    try:
        count = operations.clear_completed_tasks()
        if count == 0:
            print("No completed tasks to clear.")
        else:
            print(f"{count} completed task(s) cleared successfully.")
    except Exception as e:
        print(f"Error: {e}")


def main(argv=None) -> int:
    """
    Main entry point for the CLI application.

    Args:
        argv: Command-line arguments (for testing).

    Returns:
        Exit code (0 for success, 1 for error).
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    # Command dispatch
    commands = {
        'add': cmd_add,
        'list': cmd_list,
        'complete': cmd_complete,
        'incomplete': cmd_incomplete,
        'delete': cmd_delete,
        'clear': cmd_clear,
    }

    handler = commands.get(args.command)
    if handler:
        handler(args)
        return 0
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
