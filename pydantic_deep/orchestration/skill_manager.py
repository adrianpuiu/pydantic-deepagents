"""Skill management for orchestrated workflows.

This module provides automatic skill discovery and loading for tasks
that require specific skills.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from pydantic_deep.toolsets.skills import discover_skills, load_skill_instructions
from pydantic_deep.types import Skill, SkillDirectory

if TYPE_CHECKING:
    from pydantic_deep.deps import DeepAgentDeps
    from pydantic_deep.orchestration.models import TaskDefinition


class SkillManager:
    """Manages skill discovery and loading for orchestrated workflows."""

    def __init__(self, skill_directories: list[SkillDirectory] | None = None) -> None:
        """Initialize skill manager.

        Args:
            skill_directories: List of directories to search for skills.
                If None, uses default ~/.pydantic-deep/skills directory.
        """
        if skill_directories is None:
            # Use default skills directory
            default_dir = Path.home() / ".pydantic-deep" / "skills"
            skill_directories = [{"path": str(default_dir), "recursive": True}]

        self.skill_directories = skill_directories
        self._skill_cache: dict[str, Skill] = {}
        self._discovered = False

    def discover_skills(self, backend: object | None = None) -> None:
        """Discover all available skills from configured directories.

        Args:
            backend: Optional backend for file operations.
        """
        if self._discovered:
            return

        skills = discover_skills(self.skill_directories, backend)

        # Cache skills by name
        for skill in skills:
            self._skill_cache[skill["name"]] = skill

        self._discovered = True

    def get_required_skills(self, task: TaskDefinition) -> list[Skill]:
        """Get all skills required by a task.

        Args:
            task: Task definition.

        Returns:
            List of required skills.

        Raises:
            ValueError: If a required skill is not found.
        """
        if not task.required_skills:
            return []

        # Ensure skills are discovered
        if not self._discovered:
            self.discover_skills()

        skills = []
        for skill_name in task.required_skills:
            if skill_name not in self._skill_cache:
                raise ValueError(
                    f"Required skill '{skill_name}' not found. "
                    f"Available skills: {list(self._skill_cache.keys())}"
                )
            skills.append(self._skill_cache[skill_name])

        return skills

    def load_skill_instructions(self, skill_name: str, backend: object | None = None) -> str | None:
        """Load full instructions for a skill.

        Args:
            skill_name: Name of the skill.
            backend: Optional backend for file operations.

        Returns:
            Skill instructions or None if not found/loadable.
        """
        if skill_name not in self._skill_cache:
            return None

        skill = self._skill_cache[skill_name]

        # Load instructions if not already loaded
        if "instructions" not in skill or not skill.get("frontmatter_loaded", True):
            skill = load_skill_instructions(skill, backend)
            self._skill_cache[skill_name] = skill

        return skill.get("instructions")

    def get_all_skills(self) -> list[Skill]:
        """Get all discovered skills.

        Returns:
            List of all discovered skills.
        """
        if not self._discovered:
            self.discover_skills()

        return list(self._skill_cache.values())

    def get_skill(self, skill_name: str) -> Skill | None:
        """Get a specific skill by name.

        Args:
            skill_name: Name of the skill.

        Returns:
            Skill or None if not found.
        """
        if not self._discovered:
            self.discover_skills()

        return self._skill_cache.get(skill_name)

    def inject_skills_into_deps(
        self,
        task: TaskDefinition,
        deps: DeepAgentDeps,
    ) -> DeepAgentDeps:
        """Inject required skills into agent dependencies.

        This ensures skills are available when the task executes.

        Args:
            task: Task definition.
            deps: Agent dependencies.

        Returns:
            Updated dependencies with skills loaded.
        """
        required_skills = self.get_required_skills(task)

        if not required_skills:
            return deps

        # Load full instructions for required skills
        for skill in required_skills:
            # Ensure instructions are loaded
            self.load_skill_instructions(skill["name"], deps.backend)

        # Update skills in deps if it has a skills list
        if hasattr(deps, "skills") and isinstance(deps.skills, list):
            # Merge with existing skills, avoiding duplicates
            existing_names = {s["name"] for s in deps.skills}
            for skill in required_skills:
                if skill["name"] not in existing_names:
                    deps.skills.append(skill)
        elif hasattr(deps, "skills"):
            # Initialize skills list
            deps.skills = required_skills.copy()

        return deps

    def get_skill_summary(self, task: TaskDefinition) -> str:
        """Get summary of skills required by a task.

        Args:
            task: Task definition.

        Returns:
            Human-readable summary of required skills.
        """
        if not task.required_skills:
            return "No skills required"

        skills = self.get_required_skills(task)
        parts = [f"Required skills ({len(skills)}):"]

        for skill in skills:
            parts.append(f"  - {skill['name']}: {skill['description']}")
            if skill.get("tags"):
                parts.append(f"    Tags: {', '.join(skill['tags'])}")

        return "\n".join(parts)


def auto_discover_skills_from_workflow(
    workflow: object,
    skill_directories: list[SkillDirectory] | None = None,
) -> SkillManager:
    """Auto-discover all skills needed by a workflow.

    Args:
        workflow: Workflow definition.
        skill_directories: Optional list of skill directories.

    Returns:
        Configured skill manager with discovered skills.
    """
    manager = SkillManager(skill_directories)

    # Discover all available skills
    manager.discover_skills()

    return manager
