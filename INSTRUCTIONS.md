# TD-AID Instructions for AI Assistant

You are operating under Test-Driven AI Development (TD-AID) methodology. This file contains your operating instructions for this project.

## Core Principles

### Fundamental TD-AID Rules

1. **Test-First Development**: You must ALWAYS write tests before implementation code. No exceptions. If asked to implement a feature, first ask for test requirements or write tests based on the specifications.

2. **Minimal Implementation**: Write only the code necessary to make tests pass. Do not add features, methods, or capabilities not required by existing tests.

3. **Test Preservation**: Never delete or modify tests to make them pass. If a test fails, fix the implementation, not the test. Tests represent requirements and must be preserved.

4. **Phase Discipline**: Complete each phase fully before moving to the next. A phase is not complete until all tests pass and refactoring is done.

5. **Documentation Tracking**: Update STAGES.md after each significant action:
   - Test creation
   - Implementation completion  
   - Refactoring performed
   - Issues encountered and resolved

## Command Definitions

Any time the user writes "design the software", you must develop a comprehensive software design document. The software design document should be sectioned into logical sections that break down the software requirements into discrete categories:
- User Requirements: What end users need to accomplish
- Business Rules: Core logic and constraints of the system  
- Non-Functional Requirements: Performance, security, scalability needs
- Technical Requirements: Technology stack, integration points, APIs
- Architecture Design: High-level system structure and component relationships
The design document should be written in DESIGN.md and serve as the authoritative reference for all implementation decisions.

Any time the user writes "plan the software", take the software design document in DESIGN.md and create an implementation plan (PLAN.md) that plans out how to construct the software design in phases (0-10). Each phase MUST:
- Produce a compilable, testable artifact
- Begin by implementing all unit tests for that phase
- Follow the iterative process of writing minimal code to satisfy tests
- Include a refactoring stage before marking complete
- Be documented as DONE in STAGES.md upon completion
Each phase should build upon previous phases while maintaining all existing tests.

Any time the user writes "begin phase [N]" where N is a phase number:
1. First consult PLAN.md to understand the requirements for phase N
2. Create all test files specified for this phase BEFORE any implementation
3. Write comprehensive tests that cover:
   - Happy path scenarios
   - Error conditions and edge cases  
   - Boundary value testing
   - Integration with previous phases
4. Run tests to verify they fail appropriately (Red phase)
5. Only after ALL tests are written, begin minimal implementation
6. Implement only enough code to make each test pass (Green phase)
7. Refactor for clarity while maintaining passing tests (Refactor phase)
8. Update STAGES.md with completion status

Any time the user writes "realign tests to the project plan":
1. First scan all existing test files in the codebase
2. Cross-reference found tests with the current phase requirements in PLAN.md
3. Create a comprehensive report showing:
   - Tests that exist in code but not in PLAN.md
   - Tests specified in PLAN.md but missing from code
   - Tests that match between code and plan
4. Present any discrepancies in a clear table format:
   | Test Name | In Code | In Plan | Action Required |
5. For missing tests: implement them immediately
6. For extra tests: ask user whether to keep or remove
7. Never delete tests without explicit user confirmation
8. Update STAGES.md with the realignment results

Any time the user writes "test status":
1. Analyze all test files in the current project
2. Run the test suite and capture results
3. Generate a comprehensive report including:
   - Total number of tests written
   - Pass/fail status for each test
   - Code coverage percentage if available
   - List of any untested functions or code paths
   - Comparison against PLAN.md requirements
4. Identify any gaps in test coverage
5. Suggest specific tests that should be added

Any time the user writes "refactor with tests":
1. Ensure all tests are currently passing
2. Identify code that could benefit from refactoring:
   - Duplicated code
   - Long methods or functions
   - Poor naming conventions
   - Violations of SOLID principles
3. Make one small refactoring change at a time
4. Run tests after each change to ensure nothing breaks
5. If tests fail, immediately revert the change
6. Document refactoring decisions in STAGES.md
7. Never modify test expectations during refactoring

Any time the user writes "refresh project session":
1. Re-read and internalize INSTRUCTIONS.md to restore all TD-AID rules and commands
2. Load DESIGN.md to understand the project vision and architecture
3. Study PLAN.md to understand the phased implementation approach
4. Review STAGES.md to determine current progress and what has been completed
5. If CLAUDE.md exists, load project-specific instructions
6. Scan the codebase to understand current implementation state
7. Identify which phase is currently active based on STAGES.md
8. Report back with:
   - Current phase and its objectives
   - Tests completed vs tests remaining
   - Any pending tasks from the last session
   - Ready to continue from where the project left off
This command is essential after conversation history compaction to restore full project context.

## Error Handling Patterns

When tests fail:
1. Do not modify the failing test
2. Analyze why the test is failing
3. Fix the implementation to satisfy the test
4. If the test seems incorrect, ask the user before making changes
5. Document the issue and resolution in STAGES.md

When implementation is difficult:
1. Do not skip tests or add placeholder code
2. Break down the problem into smaller tests
3. Implement incrementally, one test at a time
4. Ask for clarification if requirements are unclear

## File Structure
- DESIGN.md: Contains the software design document
- PLAN.md: Contains the phased implementation plan  
- STAGES.md: Tracks progress and completion
- INSTRUCTIONS.md: This file (your operating manual)
- CLAUDE.md: Project-specific customizations

## Workflow
1. Design Phase: "design the software"
2. Planning Phase: "plan the software"  
3. Implementation: "begin phase N"
4. Verification: "test status"
5. Maintenance: "realign tests to plan"
6. Improvement: "refactor with tests"
7. Recovery: "refresh project session" (after history compaction)

## Remember
- Tests are specifications written in code
- Every line of implementation must serve a test
- Quality comes from constraints, not features
- You are forbidden from writing implementation before tests
- You are forbidden from deleting tests to fix failures
- You are required to update STAGES.md throughout the process
