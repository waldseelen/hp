#!/usr/bin/env python3
"""
Task Protocol Validator

This script validates the task.txt YAML file structure and reports any issues.
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from task_parser import TaskProtocolParser


def validate_task_protocol(task_file_path: str = None) -> bool:
    """Validate the task protocol YAML file"""
    try:
        parser = TaskProtocolParser(task_file_path)
        issues = parser.validate_structure()

        if issues:
            print("❌ Validation failed with the following issues:")
            for issue in issues:
                print(f"  - {issue}")
            return False
        else:
            print("✅ Task protocol YAML structure is valid.")
            return True

    except Exception as e:
        print(f"❌ Error validating task protocol: {e}")
        return False


def main():
    """Main validation function"""
    task_file = None
    if len(sys.argv) > 1:
        task_file = sys.argv[1]

    success = validate_task_protocol(task_file)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
