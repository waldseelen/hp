#!/usr/bin/env python3
"""
Task Protocol Parser

This script parses the task.txt YAML file and provides utilities for working with the Claude Code protocol.
"""

import os
from typing import Any, Dict, List, Optional

import yaml


class TaskProtocolParser:
    def __init__(self, task_file_path: str = None):
        if task_file_path is None:
            # Default to task.txt in the same directory as this script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            task_file_path = os.path.join(script_dir, "..", "task.txt")

        self.task_file_path = task_file_path
        self.data = self._load_yaml()

    def _load_yaml(self) -> Dict[str, Any]:
        """Load the YAML data from task.txt"""
        try:
            with open(self.task_file_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Task file not found: {self.task_file_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in task file: {e}")

    def get_title(self) -> str:
        """Get the protocol title"""
        return self.data.get("title", "")

    def get_identity(self) -> Dict[str, str]:
        """Get identity and purpose information"""
        return self.data.get("identity_and_purpose", {})

    def get_roadmap_source(self) -> List[str]:
        """Get roadmap source information"""
        return self.data.get("roadmap_source", [])

    def get_workflow_description(self) -> str:
        """Get workflow loop description"""
        workflow = self.data.get("workflow_loop", {})
        return workflow.get("description", "")

    def get_steps(self) -> Dict[str, Dict[str, Any]]:
        """Get all workflow steps"""
        workflow = self.data.get("workflow_loop", {})
        return workflow.get("steps", {})

    def get_step(self, step_number: int) -> Optional[Dict[str, Any]]:
        """Get a specific step by number (1-5)"""
        steps = self.get_steps()
        step_key = f"step{step_number}"
        return steps.get(step_key)

    def get_step_title(self, step_number: int) -> str:
        """Get the title of a specific step"""
        step = self.get_step(step_number)
        if step:
            return step.get("title", "")
        return ""

    def get_step_actions(self, step_number: int) -> List[str]:
        """Get the actions for a specific step"""
        step = self.get_step(step_number)
        if step:
            return step.get("actions", [])
        return []

    def get_interaction_rules(self) -> List[str]:
        """Get interaction rules"""
        return self.data.get("interaction_rules", [])

    def get_protocol_initiation(self) -> str:
        """Get protocol initiation message"""
        return self.data.get("protocol_initiation", "")

    def validate_structure(self) -> List[str]:
        """Validate the YAML structure and return any issues"""
        issues = []

        required_keys = [
            "title",
            "identity_and_purpose",
            "roadmap_source",
            "workflow_loop",
            "interaction_rules",
            "protocol_initiation",
        ]
        for key in required_keys:
            if key not in self.data:
                issues.append(f"Missing required key: {key}")

        if "workflow_loop" in self.data:
            workflow = self.data["workflow_loop"]
            if "steps" not in workflow:
                issues.append("Missing 'steps' in workflow_loop")
            else:
                expected_steps = [f"step{i}" for i in range(1, 6)]
                actual_steps = list(workflow["steps"].keys())
                if set(actual_steps) != set(expected_steps):
                    issues.append(
                        f"Expected steps {expected_steps}, found {actual_steps}"
                    )

        return issues


def main():
    """Example usage"""
    parser = TaskProtocolParser()

    print(f"Title: {parser.get_title()}")
    print(f"Identity: {parser.get_identity()}")

    print("\nWorkflow Steps:")
    for i in range(1, 6):
        title = parser.get_step_title(i)
        actions = parser.get_step_actions(i)
        print(f"Step {i}: {title}")
        for action in actions:
            print(f"  - {action}")

    issues = parser.validate_structure()
    if issues:
        print(f"\nValidation Issues: {issues}")
    else:
        print("\nYAML structure is valid.")


if __name__ == "__main__":
    main()
