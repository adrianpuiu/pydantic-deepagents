#!/usr/bin/env python3
"""Real-World Example: Comprehensive Security Audit Pipeline.

This example demonstrates using distributed agents to perform a thorough
security audit of an application, including code analysis, dependency scanning,
configuration review, and penetration testing recommendations.

Business Scenario:
A company needs to perform regular security audits of their applications.
The process involves:
- Static code analysis for vulnerabilities
- Dependency vulnerability scanning
- Security configuration review
- API security assessment
- Authentication/authorization review
- Data protection compliance check
- Penetration testing guidance
- Remediation planning

This automated pipeline ensures comprehensive security coverage.
"""

import asyncio

from pydantic_deep import StateBackend
from pydantic_deep.types import SubAgentConfig

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from orchestrator import DistributedOrchestrator, TaskPriority


# Define specialized security audit workers
SECURITY_WORKERS = [
    SubAgentConfig(
        name="code-scanner",
        description="Performs static code analysis for security vulnerabilities",
        instructions="""You are a static code analysis security expert.

Scan for OWASP Top 10 vulnerabilities:
1. Injection flaws (SQL, NoSQL, OS, LDAP)
2. Broken authentication
3. Sensitive data exposure
4. XML external entities (XXE)
5. Broken access control
6. Security misconfiguration
7. Cross-site scripting (XSS)
8. Insecure deserialization
9. Using components with known vulnerabilities
10. Insufficient logging & monitoring

For each finding provide:
- Severity (Critical/High/Medium/Low)
- CWE reference
- Location (file and line)
- Proof of concept
- Remediation guidance""",
    ),
    SubAgentConfig(
        name="dependency-scanner",
        description="Scans dependencies for known vulnerabilities",
        instructions="""You are a dependency vulnerability specialist.

Responsibilities:
1. Analyze all dependencies
2. Check against CVE databases
3. Identify outdated packages
4. Find known vulnerabilities
5. Assess exploit probability
6. Recommend updates

For each vulnerability:
- CVE ID and CVSS score
- Affected versions
- Fixed versions
- Exploit availability
- Remediation priority
- Update path""",
    ),
    SubAgentConfig(
        name="auth-security-specialist",
        description="Reviews authentication and authorization implementations",
        instructions="""You are an authentication/authorization security expert.

Review areas:
1. Password policies and storage
2. Session management
3. Token handling (JWT, OAuth)
4. Multi-factor authentication
5. Password reset flows
6. Authorization logic
7. Privilege escalation risks
8. API authentication

Check for:
- Weak password policies
- Insecure storage (plaintext, weak hashing)
- Session fixation risks
- CSRF vulnerabilities
- Improper access controls
- Token leakage""",
    ),
    SubAgentConfig(
        name="api-security-specialist",
        description="Audits API security",
        instructions="""You are an API security specialist.

Audit checklist:
1. Authentication mechanisms
2. Authorization enforcement
3. Input validation
4. Rate limiting
5. CORS configuration
6. API versioning
7. Error handling (information leakage)
8. Encryption (TLS)

OWASP API Security Top 10:
- Broken object level authorization
- Broken user authentication
- Excessive data exposure
- Lack of resources & rate limiting
- Broken function level authorization
- Mass assignment
- Security misconfiguration
- Injection
- Improper assets management
- Insufficient logging & monitoring""",
    ),
    SubAgentConfig(
        name="data-protection-specialist",
        description="Reviews data protection and privacy compliance",
        instructions="""You are a data protection and privacy specialist.

Review areas:
1. Data classification
2. Encryption at rest
3. Encryption in transit
4. PII handling
5. Data retention policies
6. GDPR/CCPA compliance
7. Data minimization
8. Backup security

Compliance checks:
- Right to erasure implementation
- Data portability
- Consent management
- Privacy by design
- Data breach procedures
- Third-party data sharing""",
    ),
    SubAgentConfig(
        name="infrastructure-security-specialist",
        description="Reviews infrastructure and configuration security",
        instructions="""You are an infrastructure security specialist.

Review areas:
1. Cloud security configurations
2. Network segmentation
3. Firewall rules
4. Secrets management
5. Container security
6. CI/CD pipeline security
7. Monitoring and alerting
8. Incident response readiness

Check for:
- Exposed credentials
- Overly permissive IAM roles
- Unencrypted storage
- Public S3 buckets
- Missing security headers
- Disabled security features""",
    ),
]


async def main():
    print("=" * 80)
    print("Real-World Use Case: Comprehensive Security Audit Pipeline")
    print("=" * 80)
    print()

    print("Initializing Security Audit Pipeline...")
    orchestrator = DistributedOrchestrator(
        model="openai:gpt-4o-mini",
        custom_workers=SECURITY_WORKERS,
        max_concurrent_workers=6,
    )
    print(f"✓ Orchestrator ready with {len(SECURITY_WORKERS)} security specialists")
    print()

    # Sample application code to audit
    sample_app = '''
from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# SECURITY ISSUE: Hardcoded secret key
app.config['SECRET_KEY'] = 'hardcoded-secret-123'

@app.route('/api/users/<user_id>')
def get_user(user_id):
    # SECURITY ISSUE: SQL Injection vulnerability
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    user = cursor.fetchone()
    return jsonify(user)

@app.route('/api/admin/users', methods=['POST'])
def create_user():
    # SECURITY ISSUE: No authentication check
    # SECURITY ISSUE: No input validation
    data = request.json
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                   (data['username'], data['password'], data.get('role', 'user')))
    conn.commit()
    return jsonify({'status': 'success'})

@app.route('/api/download')
def download_file():
    # SECURITY ISSUE: Path traversal vulnerability
    filename = request.args.get('filename')
    with open(f'/var/data/{filename}', 'r') as f:
        return f.read()

if __name__ == '__main__':
    # SECURITY ISSUE: Debug mode in production
    # SECURITY ISSUE: Binding to all interfaces
    app.run(debug=True, host='0.0.0.0', port=5000)
'''

    orchestrator.deps.backend.write("/app/main.py", sample_app)

    requirements = '''flask==1.1.2
sqlite3==2.6.0
requests==2.25.0
pyyaml==5.3.1'''

    orchestrator.deps.backend.write("/app/requirements.txt", requirements)

    print("✓ Sample application loaded for audit")
    print()

    # ============================================================================
    # PHASE 1: PARALLEL SECURITY SCANNING
    # ============================================================================
    print("PHASE 1: Comprehensive Security Scanning (Parallel)")
    print("=" * 80)
    print("Running all security scans in parallel...")
    print()

    scan_tasks = [
        """Perform static code analysis on /app/main.py

        Scan for all OWASP Top 10 vulnerabilities.
        For each issue found, provide:
        - Severity rating
        - CWE reference
        - Line number
        - Vulnerable code snippet
        - Exploit scenario
        - Remediation guidance

        Create detailed vulnerability report.""",

        """Scan dependencies in /app/requirements.txt

        Check for:
        - Known CVEs
        - Outdated versions
        - Deprecated packages
        - Security advisories

        Provide CVE IDs, CVSS scores, and update recommendations.""",

        """Review authentication and authorization in /app/main.py

        Check:
        - Secret key management
        - Password handling
        - Session security
        - Authorization enforcement
        - API authentication

        Identify all auth-related security issues.""",

        """Audit API security in /app/main.py

        Evaluate:
        - Input validation
        - Rate limiting
        - Error handling
        - CORS configuration
        - API authentication
        - Data exposure

        Provide API security assessment.""",

        """Review data protection practices in /app/main.py

        Check:
        - PII handling
        - Data encryption
        - Secure data storage
        - Information disclosure
        - Sensitive data in logs

        Assess data protection compliance.""",

        """Review infrastructure and configuration security

        Analyze:
        - Application configuration
        - Server binding (0.0.0.0)
        - Debug mode settings
        - Environment variables
        - Deployment security

        Identify configuration vulnerabilities.""",
    ]

    scan_results = await orchestrator.execute_parallel(
        scan_tasks,
        priority=TaskPriority.URGENT
    )

    print("✓ All security scans completed")
    print("\nScan Results Summary:")
    scan_types = [
        "Static Code Analysis",
        "Dependency Vulnerabilities",
        "Authentication/Authorization",
        "API Security",
        "Data Protection",
        "Infrastructure Security",
    ]

    for i, (scan_type, result) in enumerate(zip(scan_types, scan_results), 1):
        print(f"\n{i}. {scan_type}:")
        print(result[:350] + "..." if len(result) > 350 else result)
    print()

    # ============================================================================
    # PHASE 2: RISK ASSESSMENT & PRIORITIZATION
    # ============================================================================
    print("PHASE 2: Risk Assessment & Prioritization")
    print("=" * 80)
    print("Analyzing and prioritizing security findings...")
    print()

    risk_assessment_task = f"""Perform comprehensive risk assessment

    Compile findings from all scans:
    1. Code Analysis: {scan_results[0][:200]}
    2. Dependencies: {scan_results[1][:200]}
    3. Auth/Auth: {scan_results[2][:200]}
    4. API Security: {scan_results[3][:200]}
    5. Data Protection: {scan_results[4][:200]}
    6. Infrastructure: {scan_results[5][:200]}

    Risk assessment requirements:
    1. Categorize all findings by severity (Critical/High/Medium/Low)
    2. Calculate risk scores (likelihood × impact)
    3. Prioritize remediation order
    4. Identify quick wins vs complex fixes
    5. Estimate effort for each fix
    6. Highlight exploitable vulnerabilities

    Create risk matrix and prioritized remediation plan."""

    risk_assessment = await orchestrator.execute(
        risk_assessment_task,
        priority=TaskPriority.HIGH
    )

    print("✓ Risk assessment completed")
    print("\nRisk Assessment:")
    print(risk_assessment[:500] + "..." if len(risk_assessment) > 500 else risk_assessment)
    print()

    # ============================================================================
    # PHASE 3: REMEDIATION GUIDANCE
    # ============================================================================
    print("PHASE 3: Detailed Remediation Guidance")
    print("=" * 80)
    print("Generating remediation plans...")
    print()

    remediation_task = f"""Create detailed remediation guide

    Based on risk assessment:
    {risk_assessment[:300]}

    For each critical/high severity finding:
    1. Detailed explanation of the vulnerability
    2. Step-by-step fix instructions
    3. Code examples (before/after)
    4. Testing procedures
    5. Verification steps
    6. References to security standards

    Include:
    - Quick fixes (< 1 day)
    - Medium-term fixes (1-5 days)
    - Long-term improvements (> 5 days)
    - Security testing checklist
    - Secure coding guidelines

    Create comprehensive remediation playbook."""

    remediation_guide = await orchestrator.execute(remediation_task)

    print("✓ Remediation guide created")
    print("\nRemediation Guide:")
    print(remediation_guide[:500] + "..." if len(remediation_guide) > 500 else remediation_guide)
    print()

    # ============================================================================
    # PHASE 4: EXECUTIVE REPORT
    # ============================================================================
    print("PHASE 4: Executive Security Report")
    print("=" * 80)
    print("Generating executive report...")
    print()

    report_task = f"""Create executive security audit report

    Compile all findings:
    - Scan results from 6 specialist areas
    - Risk assessment: {risk_assessment[:200]}
    - Remediation guide: {remediation_guide[:200]}

    Report structure:
    1. Executive Summary
       - Overall security posture
       - Critical findings count
       - Risk level assessment

    2. Findings Overview
       - Vulnerability breakdown by severity
       - OWASP Top 10 coverage
       - Compliance gaps

    3. Critical Vulnerabilities
       - Detailed analysis of critical issues
       - Exploitation scenarios
       - Business impact

    4. Remediation Roadmap
       - Prioritized action plan
       - Timeline and effort estimates
       - Quick wins vs strategic fixes

    5. Compliance Status
       - OWASP compliance
       - Industry standards
       - Best practices gaps

    6. Recommendations
       - Security improvements
       - Process enhancements
       - Tools and automation

    Format: Professional markdown report for stakeholders."""

    executive_report = await orchestrator.execute(
        report_task,
        priority=TaskPriority.URGENT
    )

    print("✓ Executive report generated")
    print("\n" + "=" * 80)
    print("SECURITY AUDIT EXECUTIVE REPORT")
    print("=" * 80)
    print(executive_report)
    print()

    # ============================================================================
    # AUDIT SUMMARY
    # ============================================================================
    print("=" * 80)
    print("Security Audit Pipeline Summary")
    print("=" * 80)

    metrics = orchestrator.get_metrics()

    print(f"\nAudit Statistics:")
    print(f"  Total scans executed: {metrics['total_tasks']}")
    print(f"  Successfully completed: {metrics['completed_tasks']}")
    print(f"  Success rate: {metrics['success_rate']:.1%}")
    print()

    print("Security Specialist Utilization:")
    for worker_name, stats in metrics['workers'].items():
        if stats['tasks_completed'] > 0:
            print(f"  {worker_name}: {stats['tasks_completed']} tasks")
    print()

    print("=" * 80)
    print("✓ Security Audit completed successfully!")
    print("=" * 80)
    print()

    print("Audit Coverage:")
    print("  ✓ Static code analysis (OWASP Top 10)")
    print("  ✓ Dependency vulnerability scanning")
    print("  ✓ Authentication/Authorization review")
    print("  ✓ API security assessment")
    print("  ✓ Data protection compliance")
    print("  ✓ Infrastructure security configuration")
    print()

    print("Business Value:")
    print("  • Comprehensive security coverage in minutes vs days")
    print("  • Parallel scanning for faster results")
    print("  • Prioritized remediation based on risk")
    print("  • Detailed fix guidance for developers")
    print("  • Executive-ready reporting")
    print("  • Automated and repeatable process")
    print("  • Reduced security assessment costs by 10x")


if __name__ == "__main__":
    asyncio.run(main())
