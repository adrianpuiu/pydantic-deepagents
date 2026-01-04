#!/usr/bin/env python3
"""
Simple example of using pydantic-deepagents.

This demonstrates the core features:
- Creating a deep agent with default toolsets
- Task management with TODO lists
- File operations
- Basic agent interaction
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Any
from datetime import datetime

# Import the deep agent components
from pydantic_ai_backends import StateBackend
from pydantic_ai import RunContext
from pydantic_deep import FilesystemBackend, create_deep_agent, create_default_deps


def _running_in_streamlit() -> bool:
    if any(k.startswith('STREAMLIT_') for k in os.environ):
        return True
    argv = ' '.join(sys.argv).lower()
    return 'streamlit' in argv


def _should_run_demo(argv: list[str]) -> bool:
    return '--demo' in argv or '--examples' in argv


def _run_async(coro: Any) -> Any:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    else:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


async def get_current_time(ctx: RunContext[Any]) -> str:
    return datetime.now().isoformat()


async def calculator(ctx: RunContext[Any], expression: str) -> str:
    allowed = set('0123456789+-*/(). %')
    if any(ch not in allowed for ch in expression):
        return 'Error: expression contains unsupported characters'
    try:
        result = eval(expression, {'__builtins__': {}}, {})
    except Exception as e:
        return f'Error: {e}'
    return str(result)


def streamlit_chat_app() -> None:
    import streamlit as st

    st.set_page_config(page_title='Deep Agent Chat', layout='centered')
    st.title('Deep Agent Chat')

    with st.sidebar:
        model = st.text_input('Model', value='openai:gpt-4o-mini')

        st.subheader('Toolsets')
        include_todo = st.checkbox('Todo', value=True)
        include_filesystem = st.checkbox('Filesystem', value=True)
        include_skills = st.checkbox('Skills', value=True)
        include_subagents = st.checkbox('Subagents', value=True)
        include_execute = st.checkbox('Execute', value=False)

        st.subheader('Backend')
        backend_kind = st.selectbox('Backend', ['in-memory', 'filesystem'], index=0)
        workspace_root = st.text_input('Workspace dir', value=str(Path.cwd() / 'workspace'))
        virtual_mode = st.checkbox('Virtual mode', value=True)

        st.subheader('Skills')
        skills_dir = st.text_input('Skills dir', value=str(Path(workspace_root) / 'skills'))
        skills_recursive = st.checkbox('Skills recursive', value=True)

        st.subheader('Custom tools')
        enable_time_tool = st.checkbox('get_current_time', value=True)
        enable_calc_tool = st.checkbox('calculator', value=True)

        st.subheader('Internet tools')
        enable_tavily = st.checkbox('Tavily web search', value=False)
        tavily_api_key = st.text_input(
            'TAVILY_API_KEY',
            value=os.getenv('TAVILY_API_KEY', ''),
            type='password',
            help='Required for Tavily web search tool',
        )
        enable_web_fetch = st.checkbox(
            'Web fetch (builtin)',
            value=False,
            help='Provider-dependent (may require OpenAI Responses / Gateway).',
        )

        config = {
            'model': model,
            'include_todo': include_todo,
            'include_filesystem': include_filesystem,
            'include_skills': include_skills,
            'include_subagents': include_subagents,
            'include_execute': include_execute,
            'backend_kind': backend_kind,
            'workspace_root': workspace_root,
            'virtual_mode': virtual_mode,
            'skills_dir': skills_dir,
            'skills_recursive': skills_recursive,
            'enable_time_tool': enable_time_tool,
            'enable_calc_tool': enable_calc_tool,
            'enable_tavily': enable_tavily,
            'tavily_api_key': bool(tavily_api_key),
            'enable_web_fetch': enable_web_fetch,
        }

        if st.button('Reset chat'):
            for k in ('agent', 'deps', 'message_history', 'chat_messages', 'config'):
                st.session_state.pop(k, None)
            st.rerun()

    should_rebuild = st.session_state.get('config') != config
    if should_rebuild:
        st.session_state.pop('agent', None)
        st.session_state.pop('deps', None)
        st.session_state.pop('message_history', None)
        st.session_state.pop('chat_messages', None)
        st.session_state.config = config

    if 'deps' not in st.session_state:
        if backend_kind == 'filesystem':
            backend = FilesystemBackend(Path(workspace_root), virtual_mode=virtual_mode)
            st.session_state.deps = create_default_deps(backend)
        else:
            st.session_state.deps = create_default_deps(StateBackend())

    if 'agent' not in st.session_state:
        custom_tools = []
        if enable_time_tool:
            custom_tools.append(get_current_time)
        if enable_calc_tool:
            custom_tools.append(calculator)

        builtin_tools = None
        if enable_web_fetch:
            try:
                from pydantic_ai import WebFetchTool

                builtin_tools = [WebFetchTool()]
            except Exception as e:
                st.sidebar.error('WebFetchTool unavailable in this environment.')
                st.sidebar.caption(str(e))

        if enable_tavily:
            if not tavily_api_key:
                st.sidebar.error('Tavily enabled but TAVILY_API_KEY is missing.')
            else:
                try:
                    from pydantic_ai.common_tools.tavily import tavily_search_tool

                    tavily_tool = tavily_search_tool(tavily_api_key)
                    if builtin_tools is None:
                        builtin_tools = []
                    builtin_tools.append(tavily_tool)
                except Exception as e:
                    st.sidebar.error(
                        'Tavily tool unavailable. Install pydantic-ai-slim[tavily] and restart.'
                    )
                    st.sidebar.caption(str(e))

        skill_directories = None
        if include_skills:
            Path(skills_dir).mkdir(parents=True, exist_ok=True)
            skill_directories = [
                {
                    'path': str(Path(skills_dir).resolve()),
                    'recursive': skills_recursive,
                }
            ]

        instructions = (
            'When the user asks you to create/build/design a new agent (deepagent), '
            'first consult the skill `nl-to-deepagent` and follow its output contract. '
            'Use that skill to produce an agent spec and runnable code. '
            'If that skill file is not available, ask the user where the skills directory is. '
        )

        st.session_state.agent = create_deep_agent(
            model=model,
            instructions=instructions,
            include_todo=include_todo,
            include_filesystem=include_filesystem,
            include_skills=include_skills,
            include_subagents=include_subagents,
            include_execute=include_execute,
            tools=custom_tools or None,
            skill_directories=skill_directories,
            builtin_tools=builtin_tools,
        )
    if 'message_history' not in st.session_state:
        st.session_state.message_history = []
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []

    chat_tab, skills_tab = st.tabs(['Chat', 'Skills'])

    with chat_tab:
        has_chat_ui = hasattr(st, 'chat_input') and hasattr(st, 'chat_message')

        user_input: str | None = None
        placeholder = None
        submitted = False

        if has_chat_ui:
            for m in st.session_state.chat_messages:
                with st.chat_message(m['role']):
                    st.markdown(m['content'])

            user_input = st.chat_input('Message')
            submitted = bool(user_input)

            if submitted:
                st.session_state.chat_messages.append({'role': 'user', 'content': user_input})
                with st.chat_message('user'):
                    st.markdown(user_input)

                with st.chat_message('assistant'):
                    placeholder = st.empty()
                    placeholder.markdown('...')
        else:
            st.warning(
                'Streamlit chat components not available. Upgrade Streamlit for a nicer UI, '
                'or use the fallback input below.'
            )

            st.subheader('Conversation')
            for m in st.session_state.chat_messages:
                st.markdown(f"**{m['role']}**: {m['content']}")

            with st.form('send_form'):
                user_input = st.text_area('Message', key='fallback_message')
                submitted = st.form_submit_button('Send')

            if submitted:
                user_input = (user_input or '').strip()
                if user_input:
                    st.session_state.chat_messages.append({'role': 'user', 'content': user_input})
                    placeholder = st.empty()
                    placeholder.markdown('...')
                else:
                    submitted = False

        if submitted and user_input:
            result = _run_async(
                st.session_state.agent.run(
                    user_input,
                    deps=st.session_state.deps,
                    message_history=st.session_state.message_history,
                )
            )

            assistant_text = str(result.output)
            if placeholder is None:
                placeholder = st.empty()
            if has_chat_ui:
                placeholder.markdown(assistant_text)
            else:
                placeholder.markdown(f"**assistant**: {assistant_text}")

            st.session_state.chat_messages.append({'role': 'assistant', 'content': assistant_text})
            st.session_state.message_history = list(result.all_messages())  # type: ignore[assignment]

    with skills_tab:
        st.subheader('Skill Editor')
        skills_path = Path(skills_dir)
        skills_path.mkdir(parents=True, exist_ok=True)

        existing = sorted([p.name for p in skills_path.glob('*.md')])
        selected = st.selectbox('Select skill', ['(new)'] + existing)

        new_name = ''
        if selected == '(new)':
            new_name = st.text_input('New skill filename', value='my-skill.md')
            file_name = new_name.strip() or 'my-skill.md'
        else:
            file_name = selected

        file_path = skills_path / file_name
        if 'skill_editor_path' not in st.session_state or st.session_state.skill_editor_path != str(
            file_path
        ):
            st.session_state.skill_editor_path = str(file_path)
            st.session_state.skill_editor_text = (
                file_path.read_text() if file_path.exists() else '# New Skill\n\nDescribe the skill here.\n'
            )

        st.session_state.skill_editor_text = st.text_area(
            'Skill markdown',
            value=st.session_state.skill_editor_text,
            height=420,
        )

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button('Save skill'):
                file_path.write_text(st.session_state.skill_editor_text)
                st.success(f'Saved: {file_path}')
        with c2:
            if st.button('Auto-improve skill'):
                prompt = (
                    'Improve this skill markdown for a deep agent. '\
                    'Keep it as markdown, add clear title, purpose, triggers/when to use, '\
                    'step-by-step procedure, and constraints. Do not add any extra commentary.\n\n'
                    f'CURRENT SKILL FILE: {file_name}\n\n'
                    f'{st.session_state.skill_editor_text}'
                )
                improved = _run_async(st.session_state.agent.run(prompt, deps=st.session_state.deps))
                st.session_state.skill_editor_text = str(improved.output)
                file_path.write_text(st.session_state.skill_editor_text)
                st.success(f'Improved and saved: {file_path}')
        with c3:
            if st.button('Reload from disk'):
                st.session_state.skill_editor_text = (
                    file_path.read_text() if file_path.exists() else st.session_state.skill_editor_text
                )
                st.rerun()


async def basic_example():
    """Basic deep agent example."""
    print("=== Basic Deep Agent Example ===\n")
    
    # Create a deep agent with default configuration
    # This includes: todo, filesystem, subagents, skills toolsets
    agent = create_deep_agent(
        model="openai:gpt-4o-mini",  # Use a cheaper model for demo
    )
    
    # Create dependencies with in-memory backend
    deps = create_default_deps(StateBackend())
    
    # Simple task
    result = await agent.run(
        "Create a simple Python script that says 'Hello, World!' and save it to workspace/hello.py",
        deps=deps
    )
    
    print("Agent response:")
    print(result.output)
    print()


async def todo_management_example():
    """Example showing TODO management."""
    print("=== TODO Management Example ===\n")
    
    agent = create_deep_agent(model="openai:gpt-4o-mini")
    deps = create_default_deps(StateBackend())
    
    # Task that requires planning
    result = await agent.run(
        "Plan and create a simple data analysis project structure with README, main.py, and requirements.txt",
        deps=deps
    )
    
    print("Agent response:")
    print(result.output)
    
    # Check the TODO list
    print("\nCurrent TODOs:")
    for todo in deps.todos:
        print(f"- [{todo.status}] {todo.content}")
    print()


async def file_operations_example():
    """Example showing file operations."""
    print("=== File Operations Example ===\n")
    
    agent = create_deep_agent(model="openai:gpt-4o-mini")
    deps = create_default_deps(StateBackend())
    
    # Upload a file to work with
    sample_data = """name,age,city
Alice,25,New York
Bob,30,San Francisco
Charlie,35,Chicago"""
    
    deps.upload_file("sample_data.csv", sample_data.encode())
    print("Uploaded sample_data.csv")
    
    # Ask agent to analyze the file
    result = await agent.run(
        "Read the uploaded CSV file and create a summary of the data",
        deps=deps
    )
    
    print("Agent response:")
    print(result.output)
    print()


async def structured_output_example():
    """Example showing structured output with Pydantic models."""
    print("=== Structured Output Example ===\n")
    
    from pydantic import BaseModel
    
    class TaskSummary(BaseModel):
        """Structured output for task analysis."""
        title: str
        description: str
        estimated_time: str
        difficulty: str
        steps: list[str]
    
    # Create agent with structured output
    agent = create_deep_agent(
        model="openai:gpt-4o-mini",
        output_type=TaskSummary,
    )
    
    deps = create_default_deps(StateBackend())
    
    result = await agent.run(
        "Analyze the task: 'Build a simple REST API with FastAPI'",
        deps=deps
    )
    
    print("Structured result:")
    summary = result.output  # This is a TaskSummary instance
    print(f"Title: {summary.title}")
    print(f"Description: {summary.description}")
    print(f"Estimated time: {summary.estimated_time}")
    print(f"Difficulty: {summary.difficulty}")
    print("Steps:")
    for i, step in enumerate(summary.steps, 1):
        print(f"  {i}. {step}")
    print()


async def subagent_example():
    """Example showing subagent delegation."""
    print("=== Subagent Example ===\n")
    
    from pydantic_deep.types import SubAgentConfig
    
    # Define a specialized subagent
    code_reviewer_config: SubAgentConfig = {
        "name": "code-reviewer",
        "description": "Reviews code for best practices, security, and style",
        "instructions": """You are a senior code reviewer.

Your task is to review code and provide constructive feedback.

Focus on:
1. Code quality and readability
2. Security best practices
3. Performance considerations
4. Style and formatting
5. Error handling

Provide specific, actionable recommendations.
Always be helpful and encouraging.""",
    }
    
    # Create agent with subagent
    agent = create_deep_agent(
        model="openai:gpt-4o-mini",
        subagents=[code_reviewer_config],
    )
    
    deps = create_default_deps(StateBackend())
    
    # Create some code to review
    sample_code = '''
def get_user(user_id):
    conn = sqlite3.connect("db.sqlite")
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
    return cursor.fetchone()
'''
    
    deps.upload_file("bad_code.py", sample_code.encode())
    
    result = await agent.run(
        "Review the code in bad_code.py and suggest improvements",
        deps=deps
    )
    
    print("Agent response:")
    print(result.output)
    print()


async def main():
    """Run all examples."""
    print("🚀 Deep Agents Examples\n")
    
    try:
        await basic_example()
        await todo_management_example()
        await file_operations_example()
        await structured_output_example()
        await subagent_example()
        
        print("✅ All examples completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nNote: Make sure you have OPENAI_API_KEY set in your environment")


if __name__ == "__main__":
    if _should_run_demo(sys.argv):
        asyncio.run(main())
    else:
        streamlit_chat_app()
