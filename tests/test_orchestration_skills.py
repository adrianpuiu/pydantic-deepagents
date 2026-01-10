"""Tests for skill integration with orchestration."""

import tempfile
from pathlib import Path

import pytest
from pydantic_ai.models.test import TestModel

from pydantic_deep import (
    StateBackend,
    TaskDefinition,
    TaskOrchestrator,
    WorkflowDefinition,
    create_deep_agent,
    create_default_deps,
)
from pydantic_deep.orchestration.skill_manager import SkillManager


class TestSkillManager:
    """Tests for SkillManager."""

    def test_skill_manager_initialization(self) -> None:
        """Test skill manager initialization."""
        manager = SkillManager()
        assert manager.skill_directories is not None
        assert not manager._discovered

    def test_skill_manager_with_custom_directories(self) -> None:
        """Test initialization with custom directories."""
        dirs = [{"path": "/custom/path", "recursive": True}]
        manager = SkillManager(dirs)
        assert manager.skill_directories == dirs

    def test_discover_skills_empty_directory(self, tmp_path: Path) -> None:
        """Test skill discovery in empty directory."""
        manager = SkillManager([{"path": str(tmp_path)}])
        manager.discover_skills()

        assert manager._discovered
        assert len(manager.get_all_skills()) == 0

    def test_discover_skills_with_skill(self, tmp_path: Path) -> None:
        """Test skill discovery with actual skill."""
        # Create skill directory
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()

        skill_content = """---
name: test-skill
description: A test skill
tags:
  - testing
version: 1.0
---

# Test Skill Instructions

This is a test skill for demonstration.
"""
        (skill_dir / "SKILL.md").write_text(skill_content)

        # Discover skills
        manager = SkillManager([{"path": str(tmp_path), "recursive": True}])
        manager.discover_skills()

        # Verify discovery
        assert manager._discovered
        skills = manager.get_all_skills()
        assert len(skills) == 1
        assert skills[0]["name"] == "test-skill"
        assert skills[0]["description"] == "A test skill"

    def test_get_required_skills(self, tmp_path: Path) -> None:
        """Test getting required skills for a task."""
        # Create skill
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        skill_content = """---
name: test-skill
description: A test skill
---
Instructions here.
"""
        (skill_dir / "SKILL.md").write_text(skill_content)

        # Create manager and discover
        manager = SkillManager([{"path": str(tmp_path), "recursive": True}])
        manager.discover_skills()

        # Create task requiring skill
        task = TaskDefinition(
            id="test-task",
            description="Test task",
            required_skills=["test-skill"],
        )

        # Get required skills
        skills = manager.get_required_skills(task)
        assert len(skills) == 1
        assert skills[0]["name"] == "test-skill"

    def test_get_required_skills_not_found(self) -> None:
        """Test error when required skill not found."""
        manager = SkillManager([])
        manager.discover_skills()

        task = TaskDefinition(
            id="test-task",
            description="Test task",
            required_skills=["nonexistent-skill"],
        )

        with pytest.raises(ValueError, match="Required skill.*not found"):
            manager.get_required_skills(task)

    def test_get_skill(self, tmp_path: Path) -> None:
        """Test getting specific skill by name."""
        # Create skill
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        skill_content = """---
name: my-skill
description: My skill
---
Instructions.
"""
        (skill_dir / "SKILL.md").write_text(skill_content)

        manager = SkillManager([{"path": str(tmp_path), "recursive": True}])
        manager.discover_skills()

        skill = manager.get_skill("my-skill")
        assert skill is not None
        assert skill["name"] == "my-skill"

        not_found = manager.get_skill("nonexistent")
        assert not_found is None

    def test_get_skill_summary(self, tmp_path: Path) -> None:
        """Test getting skill summary for task."""
        # Create skills
        skill_dir1 = tmp_path / "skill1"
        skill_dir1.mkdir()
        (skill_dir1 / "SKILL.md").write_text("""---
name: skill1
description: First skill
tags:
  - test
---
Instructions.
""")

        skill_dir2 = tmp_path / "skill2"
        skill_dir2.mkdir()
        (skill_dir2 / "SKILL.md").write_text("""---
name: skill2
description: Second skill
---
Instructions.
""")

        manager = SkillManager([{"path": str(tmp_path), "recursive": True}])
        manager.discover_skills()

        # Task with no skills
        task_no_skills = TaskDefinition(id="task1", description="No skills")
        summary = manager.get_skill_summary(task_no_skills)
        assert "No skills required" in summary

        # Task with skills
        task_with_skills = TaskDefinition(
            id="task2",
            description="With skills",
            required_skills=["skill1", "skill2"],
        )
        summary = manager.get_skill_summary(task_with_skills)
        assert "skill1" in summary
        assert "skill2" in summary
        assert "First skill" in summary
        assert "Second skill" in summary


class TestOrchestrationSkillIntegration:
    """Tests for skill integration with orchestration."""

    async def test_orchestrator_with_skills(self, tmp_path: Path) -> None:
        """Test orchestrator with skill integration."""
        # Create test skill
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        skill_content = """---
name: test-skill
description: Test skill for orchestration
---
# Test Skill
You are a test assistant.
"""
        (skill_dir / "SKILL.md").write_text(skill_content)

        # Create agent and orchestrator
        agent = create_deep_agent(model=TestModel())
        deps = create_default_deps(backend=StateBackend())

        orchestrator = TaskOrchestrator(
            agent,
            deps,
            skill_directories=[{"path": str(tmp_path), "recursive": True}]
        )

        # Create workflow with skill requirement
        workflow = WorkflowDefinition(
            id="test-workflow",
            name="Test Workflow",
            tasks=[
                TaskDefinition(
                    id="task1",
                    description="Task with skill",
                    required_skills=["test-skill"],
                    agent_type="general-purpose",
                )
            ],
        )

        # Execute workflow
        result = await orchestrator.execute_workflow(workflow)

        # Verify execution
        assert result.workflow_id == "test-workflow"
        assert len(result.task_results) >= 1

    async def test_workflow_with_multiple_skill_tasks(self, tmp_path: Path) -> None:
        """Test workflow with multiple tasks requiring different skills."""
        # Create multiple skills
        skill1_dir = tmp_path / "skill1"
        skill1_dir.mkdir()
        (skill1_dir / "SKILL.md").write_text("""---
name: skill1
description: First skill
---
Skill 1 instructions.
""")

        skill2_dir = tmp_path / "skill2"
        skill2_dir.mkdir()
        (skill2_dir / "SKILL.md").write_text("""---
name: skill2
description: Second skill
---
Skill 2 instructions.
""")

        # Create orchestrator
        agent = create_deep_agent(model=TestModel())
        deps = create_default_deps(backend=StateBackend())

        orchestrator = TaskOrchestrator(
            agent,
            deps,
            skill_directories=[{"path": str(tmp_path), "recursive": True}]
        )

        # Create workflow
        workflow = WorkflowDefinition(
            id="multi-skill-workflow",
            name="Multi-Skill Workflow",
            tasks=[
                TaskDefinition(
                    id="task1",
                    description="Task with skill1",
                    required_skills=["skill1"],
                    agent_type="general-purpose",
                ),
                TaskDefinition(
                    id="task2",
                    description="Task with skill2",
                    required_skills=["skill2"],
                    depends_on=["task1"],
                    agent_type="general-purpose",
                ),
            ],
        )

        # Execute
        result = await orchestrator.execute_workflow(workflow)

        # Verify
        assert result.workflow_id == "multi-skill-workflow"
        # At least first task should execute
        assert len(result.task_results) >= 1

    async def test_task_without_skills(self) -> None:
        """Test task execution without skill requirements."""
        agent = create_deep_agent(model=TestModel())
        deps = create_default_deps(backend=StateBackend())

        orchestrator = TaskOrchestrator(agent, deps)

        workflow = WorkflowDefinition(
            id="no-skills-workflow",
            name="No Skills Workflow",
            tasks=[
                TaskDefinition(
                    id="task1",
                    description="Task without skills",
                    agent_type="general-purpose",
                )
            ],
        )

        result = await orchestrator.execute_workflow(workflow)

        assert result.workflow_id == "no-skills-workflow"
        assert len(result.task_results) >= 1
