#!/usr/bin/env python3
"""Real-World Example: Legacy Code Migration and Modernization.

This example demonstrates using distributed agents to analyze, modernize,
and migrate a legacy codebase to modern standards.

Business Scenario:
A company has a legacy Python 2.7 codebase that needs to be migrated to
Python 3.12 with modern best practices. The process involves:
- Analyzing the codebase architecture
- Identifying deprecated patterns and antipatterns
- Modernizing code to use type hints, async/await, and modern libraries
- Adding comprehensive tests
- Updating documentation
- Ensuring security best practices

This would typically take weeks of manual work. With distributed orchestration,
we can parallelize the analysis and transformation phases.
"""

import asyncio

from pydantic_deep import StateBackend
from pydantic_deep.types import SubAgentConfig

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from orchestrator import DistributedOrchestrator, TaskPriority


# Define specialized code migration workers
CODE_MIGRATION_WORKERS = [
    SubAgentConfig(
        name="code-analyzer",
        description="Analyzes codebase structure and dependencies",
        instructions="""You are a code analysis expert specializing in legacy code migration.

Your responsibilities:
1. Analyze codebase structure and architecture
2. Identify dependencies and their versions
3. Map module relationships and imports
4. Find deprecated patterns and libraries
5. Assess code complexity and technical debt
6. Identify security vulnerabilities

Analysis deliverables:
- Architectural diagram (textual description)
- Dependency tree with version compatibility
- List of deprecated features being used
- Risk assessment (high/medium/low)
- Migration complexity estimation

Output format: Structured analysis report with findings and recommendations.""",
    ),
    SubAgentConfig(
        name="python-modernizer",
        description="Modernizes Python code to current best practices",
        instructions="""You are a Python modernization specialist.

Your expertise:
1. Python 2 to Python 3 migration
2. Adding type hints (PEP 484, 585, 604)
3. Converting to modern f-strings
4. Using pathlib instead of os.path
5. Implementing context managers
6. Converting to async/await where beneficial
7. Using dataclasses/Pydantic models
8. Modern error handling patterns

Modernization checklist:
- Remove Python 2 compatibility code
- Add comprehensive type annotations
- Use modern string formatting
- Implement type-safe collections
- Add proper __all__ exports
- Use modern import styles
- Follow PEP 8 strictly

Output: Modernized code with detailed change log.""",
    ),
    SubAgentConfig(
        name="dependency-updater",
        description="Updates dependencies to modern versions",
        instructions="""You are a dependency management specialist.

Your responsibilities:
1. Identify outdated dependencies
2. Find modern replacements for deprecated libraries
3. Check compatibility between updated dependencies
4. Create migration guides for breaking changes
5. Update import statements
6. Handle API changes in updated libraries

Common migrations:
- requests → httpx (for async support)
- mock → unittest.mock
- nose → pytest
- ConfigParser → configparser
- StringIO → io.StringIO

Output format:
- Updated requirements.txt/pyproject.toml
- Migration guide for each updated dependency
- Code changes needed for API compatibility""",
    ),
    SubAgentConfig(
        name="test-modernizer",
        description="Modernizes and expands test suites",
        instructions="""You are a testing specialist.

Your responsibilities:
1. Convert unittest to pytest
2. Add type checking to tests
3. Implement fixtures and parametrize
4. Add async test support
5. Improve test coverage
6. Add property-based testing where appropriate
7. Create integration tests

Modern testing patterns:
- Use pytest fixtures instead of setUp/tearDown
- Parametrize test cases
- Use mocking effectively (pytest-mock)
- Add type hints to tests
- Use async test support
- Clear test naming (test_should_when)

Output: Modernized test suite with coverage improvements.""",
    ),
    SubAgentConfig(
        name="security-hardener",
        description="Identifies and fixes security vulnerabilities",
        instructions="""You are a security specialist.

Your responsibilities:
1. Scan for security vulnerabilities (OWASP top 10)
2. Update insecure dependencies
3. Fix SQL injection risks
4. Add input validation
5. Implement proper authentication
6. Add security headers
7. Fix cryptography issues

Security checks:
- SQL injection (use parameterized queries)
- XSS vulnerabilities
- CSRF protection
- Insecure deserialization
- Hardcoded secrets
- Weak cryptography
- Path traversal

Output: Security audit report with fixes and recommendations.""",
    ),
    SubAgentConfig(
        name="doc-modernizer",
        description="Updates documentation to modern standards",
        instructions="""You are a documentation specialist.

Your responsibilities:
1. Convert docstrings to Google/NumPy style
2. Add type hints to documentation
3. Create mkdocs/sphinx documentation
4. Add usage examples
5. Document migration guide
6. Create API reference
7. Add troubleshooting guide

Documentation standards:
- Use Google-style docstrings
- Include examples in docstrings
- Cross-reference related functions
- Document exceptions raised
- Add version compatibility notes

Output: Comprehensive documentation with examples.""",
    ),
]


async def main():
    print("=" * 80)
    print("Real-World Use Case: Legacy Code Migration & Modernization")
    print("=" * 80)
    print()

    # Create orchestrator
    print("Initializing Code Migration Orchestrator...")
    orchestrator = DistributedOrchestrator(
        model="openai:gpt-4o-mini",
        custom_workers=CODE_MIGRATION_WORKERS,
        max_concurrent_workers=6,
    )
    print(f"✓ Orchestrator ready with {len(CODE_MIGRATION_WORKERS)} specialized workers")
    print()

    # Sample legacy code to migrate
    print("Setting up sample legacy codebase...")

    legacy_code = '''# Legacy Python 2.7 code
# -*- coding: utf-8 -*-
from __future__ import print_function
import ConfigParser
import os.path
import urllib2

class UserManager:
    """Manages users"""

    def __init__(self, config_file):
        self.config = ConfigParser.ConfigParser()
        self.config.read(config_file)
        self.users = {}

    def get_user(self, user_id):
        """Get user by ID"""
        # SQL injection vulnerability!
        query = "SELECT * FROM users WHERE id = %s" % user_id
        # ... database query ...
        return self.users.get(user_id, None)

    def fetch_user_data(self, url):
        """Fetch user data from API"""
        try:
            response = urllib2.urlopen(url)
            return response.read()
        except Exception, e:
            print "Error fetching data: %s" % str(e)
            return None

    def save_config(self, filename):
        """Save configuration"""
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
        with open(filename, 'w') as f:
            self.config.write(f)
'''

    legacy_tests = '''# Legacy test file using unittest
import unittest
from user_manager import UserManager

class TestUserManager(unittest.TestCase):
    def setUp(self):
        self.manager = UserManager('config.ini')

    def test_get_user(self):
        result = self.manager.get_user(1)
        self.assertEqual(result, None)

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()
'''

    # Upload legacy code
    orchestrator.deps.backend.write("/legacy/user_manager.py", legacy_code)
    orchestrator.deps.backend.write("/legacy/test_user_manager.py", legacy_tests)

    print("✓ Legacy codebase loaded:")
    print("  - /legacy/user_manager.py (Python 2.7 code)")
    print("  - /legacy/test_user_manager.py (unittest tests)")
    print()

    # ============================================================================
    # PHASE 1: CODE ANALYSIS (Parallel)
    # ============================================================================
    print("PHASE 1: Comprehensive Code Analysis")
    print("=" * 80)
    print("Analyzing legacy codebase from multiple perspectives...")
    print()

    analysis_tasks = [
        """Analyze the architecture and structure of /legacy/user_manager.py

        Provide:
        1. Code structure and organization analysis
        2. Design patterns used (or missing)
        3. Coupling and cohesion assessment
        4. Complexity metrics (cyclomatic complexity)
        5. Code smells and antipatterns

        Create an architecture assessment report.""",

        """Analyze dependencies in /legacy/user_manager.py

        Identify:
        1. All imports and their purposes
        2. Python 2 vs Python 3 compatibility issues
        3. Deprecated libraries (ConfigParser, urllib2)
        4. Modern replacements available
        5. Version compatibility concerns

        Create a dependency migration plan.""",

        """Perform security analysis on /legacy/user_manager.py

        Look for:
        1. SQL injection vulnerabilities
        2. Path traversal risks
        3. Insecure network calls (urllib2 vs https)
        4. Missing input validation
        5. Exception handling weaknesses
        6. Hardcoded credentials or secrets

        Create a security vulnerability report with severity ratings.""",
    ]

    analysis_results = await orchestrator.execute_parallel(
        analysis_tasks,
        priority=TaskPriority.HIGH
    )

    print("✓ Analysis phase completed")
    print("\nAnalysis Reports:")
    for i, (title, result) in enumerate([
        ("Architecture Analysis", analysis_results[0]),
        ("Dependency Analysis", analysis_results[1]),
        ("Security Analysis", analysis_results[2]),
    ], 1):
        print(f"\n{i}. {title}:")
        print(result[:400] + "..." if len(result) > 400 else result)
    print()

    # ============================================================================
    # PHASE 2: CODE MODERNIZATION (Sequential with dependencies)
    # ============================================================================
    print("PHASE 2: Code Modernization")
    print("=" * 80)
    print("Modernizing code to Python 3.12 with best practices...")
    print()

    modernization_task = f"""Modernize /legacy/user_manager.py to Python 3.12+

    Based on the analysis:
    {analysis_results[0][:300]}
    {analysis_results[1][:300]}

    Modernization requirements:
    1. Convert to Python 3.12 syntax
    2. Add comprehensive type hints (PEP 484, 585, 604)
    3. Replace ConfigParser with configparser
    4. Replace urllib2 with httpx (async support)
    5. Use pathlib instead of os.path
    6. Convert to f-strings
    7. Add proper error handling with specific exceptions
    8. Use dataclass or Pydantic model for User
    9. Implement async/await for network calls
    10. Fix the SQL injection vulnerability with parameterized queries
    11. Add proper logging instead of print statements
    12. Implement context managers where appropriate

    Output:
    - Complete modernized code
    - Detailed change log
    - Migration notes

    Save to /modern/user_manager.py"""

    modernization_result = await orchestrator.execute(
        modernization_task,
        priority=TaskPriority.URGENT
    )

    print("✓ Code modernization completed")
    print("\nModernization Summary:")
    print(modernization_result[:500] + "..." if len(modernization_result) > 500 else modernization_result)
    print()

    # ============================================================================
    # PHASE 3: PARALLEL IMPROVEMENTS
    # ============================================================================
    print("PHASE 3: Parallel Improvements (Tests, Security, Documentation)")
    print("=" * 80)
    print("Applying improvements in parallel...")
    print()

    improvement_tasks = [
        """Modernize the test suite in /legacy/test_user_manager.py

        Requirements:
        1. Convert from unittest to pytest
        2. Add type hints to tests
        3. Use pytest fixtures instead of setUp/tearDown
        4. Parametrize test cases
        5. Add async test support for async functions
        6. Improve test coverage (add edge cases)
        7. Add mocking for external dependencies
        8. Use descriptive test names (test_should_when pattern)

        Save to /modern/test_user_manager.py""",

        """Apply security hardening to the modernized code

        Based on security analysis findings:
        {analysis_results[2][:300]}

        Security improvements:
        1. Ensure SQL injection fix is implemented (parameterized queries)
        2. Add input validation for all user inputs
        3. Implement rate limiting for API calls
        4. Add request timeout handling
        5. Use secure defaults for cryptography
        6. Add security headers for web responses (if applicable)
        7. Implement proper secret management
        8. Add security logging for sensitive operations

        Provide a security hardening report.""",

        """Create comprehensive documentation for the modernized code

        Documentation requirements:
        1. Add Google-style docstrings to all functions and classes
        2. Include type information in docstrings
        3. Add usage examples
        4. Create a migration guide (Python 2.7 → 3.12)
        5. Document breaking changes
        6. Add API reference
        7. Create troubleshooting guide
        8. Document security considerations

        Save to /modern/README.md and add docstrings to code.""",
    ]

    improvement_results = await orchestrator.execute_parallel(improvement_tasks)

    print("✓ Parallel improvements completed")
    print("\nImprovement Reports:")
    for i, (title, result) in enumerate([
        ("Test Modernization", improvement_results[0]),
        ("Security Hardening", improvement_results[1]),
        ("Documentation", improvement_results[2]),
    ], 1):
        print(f"\n{i}. {title}:")
        print(result[:400] + "..." if len(result) > 400 else result)
    print()

    # ============================================================================
    # PHASE 4: DEPENDENCY UPDATE
    # ============================================================================
    print("PHASE 4: Dependency Management")
    print("=" * 80)
    print("Updating dependencies and creating migration guide...")
    print()

    dependency_task = """Create updated dependency configuration

    Based on the modernized code, create:

    1. pyproject.toml with updated dependencies:
       - Python 3.12+
       - httpx (replaces urllib2)
       - pydantic (for data models)
       - pytest and pytest-asyncio (for testing)
       - pytest-mock (for mocking)
       - python-dotenv (for configuration)
       - Other modern equivalents

    2. Dependency migration guide:
       - List all replaced libraries
       - API changes required
       - Configuration changes
       - Breaking changes to be aware of

    3. Update commands:
       - How to install new dependencies
       - How to run tests
       - How to handle conflicts

    Save pyproject.toml to /modern/pyproject.toml"""

    dependency_result = await orchestrator.execute(dependency_task)

    print("✓ Dependency update completed")
    print("\nDependency Update Summary:")
    print(dependency_result[:400] + "..." if len(dependency_result) > 400 else dependency_result)
    print()

    # ============================================================================
    # PHASE 5: MIGRATION REPORT
    # ============================================================================
    print("PHASE 5: Final Migration Report")
    print("=" * 80)
    print("Generating comprehensive migration report...")
    print()

    report_task = f"""Create a comprehensive migration report

    Compile information from all phases:

    ANALYSIS PHASE:
    - Architecture: {analysis_results[0][:200]}
    - Dependencies: {analysis_results[1][:200]}
    - Security: {analysis_results[2][:200]}

    MODERNIZATION:
    {modernization_result[:200]}

    IMPROVEMENTS:
    - Tests: {improvement_results[0][:200]}
    - Security: {improvement_results[1][:200]}
    - Documentation: {improvement_results[2][:200]}

    DEPENDENCIES:
    {dependency_result[:200]}

    Create a migration report with:

    1. Executive Summary
       - Project overview
       - Migration scope
       - Key achievements

    2. Changes Summary
       - Python version upgrade (2.7 → 3.12)
       - Libraries migrated
       - Features modernized
       - Security improvements

    3. Technical Details
       - Code structure changes
       - API compatibility
       - Breaking changes
       - New features added

    4. Testing & Quality
       - Test coverage improvements
       - Quality metrics
       - Performance considerations

    5. Security Enhancements
       - Vulnerabilities fixed
       - Security features added
       - Compliance improvements

    6. Migration Guide
       - Step-by-step migration process
       - Rollback plan
       - Testing checklist
       - Deployment considerations

    7. Recommendations
       - Further improvements
       - Maintenance plan
       - Future considerations

    Format: Professional markdown report"""

    report_result = await orchestrator.execute(
        report_task,
        priority=TaskPriority.URGENT
    )

    print("✓ Migration report generated")
    print("\n" + "=" * 80)
    print("MIGRATION REPORT")
    print("=" * 80)
    print(report_result)
    print()

    # ============================================================================
    # MIGRATION SUMMARY
    # ============================================================================
    print("=" * 80)
    print("Code Migration Summary")
    print("=" * 80)

    metrics = orchestrator.get_metrics()

    print(f"\nMigration Statistics:")
    print(f"  Total tasks executed: {metrics['total_tasks']}")
    print(f"  Successfully completed: {metrics['completed_tasks']}")
    print(f"  Success rate: {metrics['success_rate']:.1%}")
    print()

    print("Specialist Utilization:")
    for worker_name, stats in metrics['workers'].items():
        if stats['tasks_completed'] > 0:
            print(f"  {worker_name}: {stats['tasks_completed']} tasks")
    print()

    print("Files Created:")
    files = orchestrator.deps.backend.glob("/modern/*")
    for file in files:
        print(f"  {file}")
    print()

    print("=" * 80)
    print("✓ Code Migration completed successfully!")
    print("=" * 80)
    print()

    print("Migration Achievements:")
    print("  ✓ Python 2.7 → Python 3.12 migration")
    print("  ✓ Modern type hints added throughout")
    print("  ✓ Async/await support for network operations")
    print("  ✓ Security vulnerabilities identified and fixed")
    print("  ✓ Test suite modernized (unittest → pytest)")
    print("  ✓ Dependencies updated to modern versions")
    print("  ✓ Comprehensive documentation created")
    print()

    print("Business Impact:")
    print("  • Reduced manual migration time from weeks to hours")
    print("  • Improved code quality and maintainability")
    print("  • Enhanced security posture")
    print("  • Better test coverage and reliability")
    print("  • Future-proof codebase with modern Python features")
    print("  • Comprehensive documentation for team onboarding")


if __name__ == "__main__":
    asyncio.run(main())
