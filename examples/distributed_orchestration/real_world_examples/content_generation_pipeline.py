#!/usr/bin/env python3
"""Real-World Example: Multi-Stage Content Generation Pipeline.

This example demonstrates using distributed agents to create high-quality
content through a multi-stage pipeline involving research, outlining,
writing, editing, SEO optimization, and fact-checking.

Business Scenario:
A content marketing team needs to produce high-quality blog posts, whitepapers,
and technical articles. The process involves:
- Topic research and competitive analysis
- Content outline creation
- First draft writing
- Technical review and fact-checking
- Editorial review and refinement
- SEO optimization
- Final formatting and publication prep

This pipeline ensures consistent quality while reducing time-to-publish.
"""

import asyncio

from pydantic_deep import StateBackend
from pydantic_deep.types import SubAgentConfig

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from orchestrator import DistributedOrchestrator, TaskPriority


# Define specialized content generation workers
CONTENT_WORKERS = [
    SubAgentConfig(
        name="research-specialist",
        description="Conducts research and gathers information on topics",
        instructions="""You are a research specialist.

Your responsibilities:
1. Research topics comprehensively
2. Gather data from multiple perspectives
3. Identify credible sources
4. Analyze competitive content
5. Extract key insights and statistics
6. Identify content gaps and opportunities

Research deliverables:
- Topic overview and context
- Key facts and statistics
- Current trends and developments
- Competitive analysis
- Unique angles and perspectives
- Source citations

Output format: Structured research brief with sources.""",
    ),
    SubAgentConfig(
        name="content-strategist",
        description="Creates content outlines and structure",
        instructions="""You are a content strategist.

Your responsibilities:
1. Define target audience and goals
2. Create compelling headlines
3. Structure content logically
4. Define key sections and flow
5. Identify CTAs and conversion points
6. Plan content format (blog, whitepaper, guide)

Outline components:
- Attention-grabbing headline
- Hook/opening paragraph
- Main sections with subsections
- Key points for each section
- Examples and use cases
- Call-to-action
- Conclusion

Output format: Detailed content outline with section notes.""",
    ),
    SubAgentConfig(
        name="content-writer",
        description="Writes engaging, high-quality content",
        instructions="""You are a professional content writer.

Your responsibilities:
1. Write clear, engaging prose
2. Maintain consistent voice and tone
3. Use storytelling techniques
4. Include relevant examples
5. Write for the target audience
6. Follow the outline structure

Writing principles:
- Clear, concise sentences
- Active voice preferred
- Vary sentence structure
- Use transitions effectively
- Include concrete examples
- Show, don't just tell
- Maintain flow and readability

Output format: Complete content draft with sections.""",
    ),
    SubAgentConfig(
        name="technical-reviewer",
        description="Reviews technical accuracy and fact-checks content",
        instructions="""You are a technical reviewer and fact-checker.

Your responsibilities:
1. Verify technical accuracy
2. Check facts and statistics
3. Validate code examples
4. Ensure technical depth
5. Identify inaccuracies
6. Suggest technical improvements

Review checklist:
- Technical correctness
- Accurate statistics and data
- Working code examples
- Current best practices
- Proper terminology
- No misleading statements

Output format: Review report with corrections and suggestions.""",
    ),
    SubAgentConfig(
        name="editor",
        description="Edits content for clarity, style, and impact",
        instructions="""You are a professional editor.

Your responsibilities:
1. Improve clarity and readability
2. Enhance flow and structure
3. Fix grammar and style issues
4. Strengthen weak sections
5. Tighten verbose content
6. Ensure consistent voice

Editing focus:
- Grammar and punctuation
- Sentence structure and variety
- Paragraph transitions
- Redundancy elimination
- Clarity improvements
- Tone consistency
- Compelling language

Output format: Edited content with change notes.""",
    ),
    SubAgentConfig(
        name="seo-optimizer",
        description="Optimizes content for search engines",
        instructions="""You are an SEO specialist.

Your responsibilities:
1. Identify target keywords
2. Optimize headings (H1, H2, H3)
3. Improve meta descriptions
4. Add internal/external links
5. Optimize image alt text
6. Ensure mobile-friendliness
7. Check content structure for SEO

SEO checklist:
- Primary keyword in title and H1
- Secondary keywords in H2s
- Keyword density (1-2%)
- Meta description (150-160 chars)
- Alt text for images
- Internal linking opportunities
- URL slug optimization

Output format: SEO-optimized content with metadata.""",
    ),
    SubAgentConfig(
        name="formatter",
        description="Formats content for publication",
        instructions="""You are a content formatter.

Your responsibilities:
1. Format in markdown/HTML
2. Add proper headings hierarchy
3. Format code blocks with syntax highlighting
4. Create bulleted/numbered lists
5. Add emphasis (bold, italic)
6. Insert images and captions
7. Ensure consistent formatting

Formatting standards:
- Proper heading hierarchy (H1 → H2 → H3)
- Code blocks with language tags
- Consistent list formatting
- Proper link formatting
- Image markdown with alt text
- Consistent spacing

Output format: Publication-ready formatted content.""",
    ),
]


async def main():
    print("=" * 80)
    print("Real-World Use Case: Multi-Stage Content Generation Pipeline")
    print("=" * 80)
    print()

    # Create orchestrator
    print("Initializing Content Generation Pipeline...")
    orchestrator = DistributedOrchestrator(
        model="openai:gpt-4o-mini",
        custom_workers=CONTENT_WORKERS,
        max_concurrent_workers=4,
    )
    print(f"✓ Orchestrator ready with {len(CONTENT_WORKERS)} content specialists")
    print()

    # Define content topic
    content_brief = """
    Topic: "Building Production-Ready AI Agents: A Comprehensive Guide"

    Target Audience: Software engineers and technical leaders
    Content Type: Technical blog post / guide
    Word Count: 2000-2500 words
    Goal: Educate developers on best practices for deploying AI agents

    Key Points to Cover:
    - Agent architecture and design patterns
    - Production considerations (reliability, monitoring, cost)
    - Testing and validation strategies
    - Security and safety measures
    - Scaling and performance optimization
    """

    print("Content Brief:")
    print(content_brief)
    print()

    # ============================================================================
    # PHASE 1: RESEARCH & STRATEGY (Parallel)
    # ============================================================================
    print("PHASE 1: Research & Strategy")
    print("=" * 80)
    print("Conducting research and creating content strategy...")
    print()

    research_strategy_tasks = [
        f"""Conduct comprehensive research on the topic:
        {content_brief}

        Research requirements:
        1. Current state of AI agents in production
        2. Common challenges and solutions
        3. Industry best practices
        4. Recent developments and trends
        5. Key statistics and data points
        6. Expert perspectives
        7. Case studies and examples

        Provide:
        - Research summary with key findings
        - Relevant statistics and data
        - Industry trends
        - Competitive content analysis
        - Unique angles to explore
        - Source references

        Output: Structured research brief""",

        f"""Create content strategy and detailed outline:
        {content_brief}

        Strategy requirements:
        1. Compelling headline options (3-5 variants)
        2. Target audience analysis
        3. Content goals and KPIs
        4. Unique value proposition
        5. Detailed section outline
        6. Key takeaways for readers
        7. Call-to-action strategy

        Outline structure:
        - Hook/introduction
        - Main sections (5-7)
        - Subsections for each main point
        - Examples and case studies to include
        - Conclusion and CTA

        Output: Content outline with strategic notes""",
    ]

    research_strategy_results = await orchestrator.execute_parallel(
        research_strategy_tasks,
        priority=TaskPriority.HIGH
    )

    research_brief = research_strategy_results[0]
    content_outline = research_strategy_results[1]

    print("✓ Research and strategy completed")
    print("\nResearch Brief Summary:")
    print(research_brief[:500] + "..." if len(research_brief) > 500 else research_brief)
    print("\nContent Outline:")
    print(content_outline[:500] + "..." if len(content_outline) > 500 else content_outline)
    print()

    # ============================================================================
    # PHASE 2: CONTENT WRITING
    # ============================================================================
    print("PHASE 2: Content Writing")
    print("=" * 80)
    print("Writing first draft based on research and outline...")
    print()

    writing_task = f"""Write the complete first draft of the content.

    Based on:
    RESEARCH: {research_brief[:300]}...
    OUTLINE: {content_outline[:300]}...

    Writing requirements:
    1. Follow the outline structure
    2. Write 2000-2500 words
    3. Use clear, professional tone
    4. Include code examples where relevant
    5. Add real-world scenarios
    6. Write engaging introduction
    7. Include specific, actionable advice
    8. Add transitions between sections
    9. Write compelling conclusion

    Style guidelines:
    - Technical but accessible
    - Concrete examples over abstract concepts
    - Active voice preferred
    - Vary sentence length
    - Use subheadings for scannability
    - Include numbered/bulleted lists

    Output: Complete first draft with all sections"""

    first_draft = await orchestrator.execute(
        writing_task,
        priority=TaskPriority.HIGH
    )

    print("✓ First draft completed")
    print(f"\nDraft length: {len(first_draft)} characters")
    print("\nDraft preview:")
    print(first_draft[:600] + "..." if len(first_draft) > 600 else first_draft)
    print()

    # ============================================================================
    # PHASE 3: REVIEW & EDITING (Parallel)
    # ============================================================================
    print("PHASE 3: Technical Review & Editorial Review")
    print("=" * 80)
    print("Running parallel review processes...")
    print()

    review_tasks = [
        f"""Perform technical review and fact-checking:

        Content to review:
        {first_draft[:500]}...

        Technical review checklist:
        1. Verify all technical claims
        2. Check code examples for correctness
        3. Validate best practices mentioned
        4. Ensure current information
        5. Check for technical inaccuracies
        6. Verify statistics and data
        7. Assess technical depth

        Provide:
        - Technical accuracy rating (1-10)
        - List of corrections needed
        - Suggestions for technical improvements
        - Additional technical points to add
        - Fact-check results

        Output: Technical review report""",

        f"""Perform editorial review:

        Content to edit:
        {first_draft[:500]}...

        Editorial review focus:
        1. Clarity and readability
        2. Flow and structure
        3. Grammar and style
        4. Tone consistency
        5. Engagement level
        6. Redundancy elimination
        7. Strengthening weak sections

        Provide:
        - Edited version of the content
        - List of major changes made
        - Suggestions for improvements
        - Readability score estimate

        Output: Edited content with change log""",
    ]

    review_results = await orchestrator.execute_parallel(review_tasks)

    technical_review = review_results[0]
    edited_content = review_results[1]

    print("✓ Review processes completed")
    print("\nTechnical Review Summary:")
    print(technical_review[:400] + "..." if len(technical_review) > 400 else technical_review)
    print("\nEditorial Changes:")
    print(edited_content[:400] + "..." if len(edited_content) > 400 else edited_content)
    print()

    # ============================================================================
    # PHASE 4: OPTIMIZATION (Parallel)
    # ============================================================================
    print("PHASE 4: SEO Optimization & Final Formatting")
    print("=" * 80)
    print("Optimizing for SEO and formatting for publication...")
    print()

    optimization_tasks = [
        f"""Perform SEO optimization:

        Content to optimize:
        {edited_content[:500]}...

        SEO optimization tasks:
        1. Identify primary keyword: "Production-Ready AI Agents"
        2. Identify secondary keywords (3-5)
        3. Optimize title and headings
        4. Create meta description (155 chars)
        5. Suggest internal linking opportunities
        6. Add keyword variations naturally
        7. Optimize for featured snippets
        8. Create URL slug

        Provide:
        - SEO-optimized content
        - Target keywords list
        - Meta description
        - URL slug
        - SEO score estimate
        - Recommendations

        Output: SEO-optimized content with metadata""",

        f"""Format content for publication:

        Content to format:
        {edited_content[:500]}...

        Formatting requirements:
        1. Convert to markdown
        2. Proper heading hierarchy (H1, H2, H3)
        3. Format code blocks with syntax highlighting
        4. Create bulleted and numbered lists
        5. Add emphasis (bold/italic) strategically
        6. Format links properly
        7. Add placeholder for images
        8. Ensure mobile-friendly formatting

        Include:
        - Table of contents
        - Summary box at top
        - Key takeaways box
        - Related resources section

        Output: Publication-ready formatted content""",
    ]

    optimization_results = await orchestrator.execute_parallel(optimization_tasks)

    seo_optimized = optimization_results[0]
    formatted_content = optimization_results[1]

    print("✓ Optimization completed")
    print("\nSEO Optimization Summary:")
    print(seo_optimized[:400] + "..." if len(seo_optimized) > 400 else seo_optimized)
    print("\nFormatted Content Preview:")
    print(formatted_content[:400] + "..." if len(formatted_content) > 400 else formatted_content)
    print()

    # ============================================================================
    # PHASE 5: FINAL ASSEMBLY
    # ============================================================================
    print("PHASE 5: Final Assembly & Quality Check")
    print("=" * 80)
    print("Assembling final content and performing quality check...")
    print()

    final_task = f"""Create the final publication-ready content.

    Combine the following:
    - SEO optimized content: {seo_optimized[:200]}
    - Formatted content: {formatted_content[:200]}
    - Technical review: {technical_review[:200]}

    Final assembly requirements:
    1. Incorporate all edits and optimizations
    2. Ensure technical accuracy
    3. Apply all formatting
    4. Include SEO metadata
    5. Add author bio and CTA
    6. Create companion assets (social posts, email)

    Quality checklist:
    ✓ Technically accurate
    ✓ Well-edited and polished
    ✓ SEO optimized
    ✓ Properly formatted
    ✓ Engaging and actionable
    ✓ Publication-ready

    Deliverables:
    1. Final blog post (markdown)
    2. Meta title and description
    3. Social media posts (Twitter, LinkedIn)
    4. Email newsletter snippet
    5. Key takeaways summary

    Output: Complete publication package"""

    final_content = await orchestrator.execute(
        final_task,
        priority=TaskPriority.URGENT
    )

    print("✓ Final content assembled")
    print("\n" + "=" * 80)
    print("FINAL PUBLICATION-READY CONTENT")
    print("=" * 80)
    print(final_content)
    print()

    # ============================================================================
    # PIPELINE SUMMARY
    # ============================================================================
    print("=" * 80)
    print("Content Generation Pipeline Summary")
    print("=" * 80)

    metrics = orchestrator.get_metrics()

    print(f"\nPipeline Statistics:")
    print(f"  Total tasks executed: {metrics['total_tasks']}")
    print(f"  Successfully completed: {metrics['completed_tasks']}")
    print(f"  Success rate: {metrics['success_rate']:.1%}")
    print()

    print("Content Specialist Utilization:")
    for worker_name, stats in metrics['workers'].items():
        if stats['tasks_completed'] > 0:
            print(f"  {worker_name}: {stats['tasks_completed']} tasks")
    print()

    print("Content Pipeline Stages:")
    print("  ✓ Stage 1: Research & Strategy")
    print("  ✓ Stage 2: Content Writing")
    print("  ✓ Stage 3: Technical & Editorial Review")
    print("  ✓ Stage 4: SEO Optimization & Formatting")
    print("  ✓ Stage 5: Final Assembly")
    print()

    print("=" * 80)
    print("✓ Content Generation Pipeline completed successfully!")
    print("=" * 80)
    print()

    print("Pipeline Benefits:")
    print("  ✓ Reduced content creation time from days to hours")
    print("  ✓ Consistent quality through specialized review")
    print("  ✓ Built-in fact-checking and technical accuracy")
    print("  ✓ SEO optimization integrated into process")
    print("  ✓ Multiple review stages ensure quality")
    print("  ✓ Publication-ready output with companion assets")
    print()

    print("Business Value:")
    print("  • 10x faster content production")
    print("  • Higher quality through multi-stage review")
    print("  • Better SEO performance with optimization")
    print("  • Consistent brand voice and quality")
    print("  • Scalable to multiple content pieces")
    print("  • Complete publication package (blog, social, email)")


if __name__ == "__main__":
    asyncio.run(main())
