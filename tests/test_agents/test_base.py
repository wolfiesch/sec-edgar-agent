"""Tests for agent base classes and models."""


from src.agents.base import (
    AgentContext,
    AgentResponse,
    AgentRole,
    Plan,
    Task,
    TaskStatus,
)


class TestAgentRole:
    """Tests for AgentRole enum."""

    def test_agent_roles_exist(self) -> None:
        """Test that all expected agent roles are defined."""
        assert AgentRole.PLANNER == "planner"
        assert AgentRole.EXECUTOR == "executor"
        assert AgentRole.VALIDATOR == "validator"
        assert AgentRole.SYNTHESIZER == "synthesizer"

    def test_agent_role_values(self) -> None:
        """Test agent role string values."""
        roles = [role.value for role in AgentRole]
        assert "planner" in roles
        assert "executor" in roles
        assert "validator" in roles
        assert "synthesizer" in roles


class TestTaskStatus:
    """Tests for TaskStatus enum."""

    def test_task_statuses_exist(self) -> None:
        """Test that all expected task statuses are defined."""
        assert TaskStatus.PENDING == "pending"
        assert TaskStatus.IN_PROGRESS == "in_progress"
        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.FAILED == "failed"
        assert TaskStatus.NEEDS_VALIDATION == "needs_validation"


class TestTask:
    """Tests for Task model."""

    def test_task_minimal(self) -> None:
        """Test creating a task with minimal required fields."""
        task = Task(id="task-1", description="Get company info")

        assert task.id == "task-1"
        assert task.description == "Get company info"
        assert task.tool_hint is None
        assert task.status == TaskStatus.PENDING
        assert task.result is None
        assert task.error is None
        assert task.dependencies == []

    def test_task_full(self) -> None:
        """Test creating a task with all fields."""
        task = Task(
            id="task-2",
            description="Search filings",
            tool_hint="search_filings",
            status=TaskStatus.COMPLETED,
            result={"count": 5},
            error=None,
            dependencies=["task-1"],
        )

        assert task.id == "task-2"
        assert task.description == "Search filings"
        assert task.tool_hint == "search_filings"
        assert task.status == TaskStatus.COMPLETED
        assert task.result == {"count": 5}
        assert task.dependencies == ["task-1"]

    def test_task_status_transitions(self) -> None:
        """Test task status can be updated."""
        task = Task(id="task-1", description="Test task")

        assert task.status == TaskStatus.PENDING

        task.status = TaskStatus.IN_PROGRESS
        assert task.status == TaskStatus.IN_PROGRESS

        task.status = TaskStatus.COMPLETED
        assert task.status == TaskStatus.COMPLETED

    def test_task_with_error(self) -> None:
        """Test task with error state."""
        task = Task(
            id="task-1",
            description="Failing task",
            status=TaskStatus.FAILED,
            error="API timeout",
        )

        assert task.status == TaskStatus.FAILED
        assert task.error == "API timeout"

    def test_task_with_dependencies(self) -> None:
        """Test task with dependencies."""
        task = Task(
            id="task-3",
            description="Compare data",
            dependencies=["task-1", "task-2"],
        )

        assert len(task.dependencies) == 2
        assert "task-1" in task.dependencies
        assert "task-2" in task.dependencies


class TestPlan:
    """Tests for Plan model."""

    def test_plan_minimal(self) -> None:
        """Test creating a plan with minimal fields."""
        plan = Plan(query="What is Apple's revenue?", reasoning="Need to fetch 10-K")

        assert plan.query == "What is Apple's revenue?"
        assert plan.reasoning == "Need to fetch 10-K"
        assert plan.tasks == []
        assert plan.is_simple is False

    def test_plan_with_tasks(self) -> None:
        """Test creating a plan with tasks."""
        task1 = Task(id="task-1", description="Get company info")
        task2 = Task(id="task-2", description="Search 10-K filings", dependencies=["task-1"])

        plan = Plan(
            query="Apple financials",
            reasoning="Multi-step query",
            tasks=[task1, task2],
        )

        assert len(plan.tasks) == 2
        assert plan.tasks[0].id == "task-1"
        assert plan.tasks[1].id == "task-2"

    def test_plan_simple_query(self) -> None:
        """Test simple query plan."""
        plan = Plan(
            query="Get Apple info",
            reasoning="Direct company lookup",
            is_simple=True,
            tasks=[Task(id="task-1", description="Get company info", tool_hint="get_company_info")],
        )

        assert plan.is_simple is True
        assert len(plan.tasks) == 1


class TestAgentContext:
    """Tests for AgentContext model."""

    def test_context_minimal(self) -> None:
        """Test creating context with minimal fields."""
        context = AgentContext(query="Test query")

        assert context.query == "Test query"
        assert context.plan is None
        assert context.tool_results == []
        assert context.conversation_history == []
        assert context.citations == []
        assert context.step_count == 0
        assert context.max_steps == 20

    def test_context_with_plan(self) -> None:
        """Test context with a plan."""
        plan = Plan(query="Test", reasoning="Test reasoning")
        context = AgentContext(query="Test", plan=plan)

        assert context.plan is not None
        assert context.plan.query == "Test"

    def test_context_with_results(self) -> None:
        """Test context with tool results."""
        context = AgentContext(
            query="Test",
            tool_results=[{"tool": "get_company_info", "result": {"ticker": "AAPL"}}],
        )

        assert len(context.tool_results) == 1
        assert context.tool_results[0]["tool"] == "get_company_info"

    def test_context_step_tracking(self) -> None:
        """Test step count tracking."""
        context = AgentContext(query="Test", step_count=5, max_steps=10)

        assert context.step_count == 5
        assert context.max_steps == 10

    def test_context_with_citations(self) -> None:
        """Test context with citations."""
        from datetime import date

        from src.data.models import Citation

        citation = Citation(
            ticker="AAPL",
            form_type="10-K",
            filing_date=date(2024, 10, 31),
            accession_number="0000320193-24-000123",
        )

        context = AgentContext(query="Test", citations=[citation])

        assert len(context.citations) == 1
        assert context.citations[0].ticker == "AAPL"

    def test_context_conversation_history(self) -> None:
        """Test context with conversation history."""
        context = AgentContext(
            query="Test",
            conversation_history=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there"},
            ],
        )

        assert len(context.conversation_history) == 2
        assert context.conversation_history[0]["role"] == "user"
        assert context.conversation_history[1]["role"] == "assistant"


class TestAgentResponse:
    """Tests for AgentResponse model."""

    def test_response_success(self) -> None:
        """Test successful agent response."""
        response = AgentResponse(
            success=True,
            content={"data": "result"},
        )

        assert response.success is True
        assert response.content == {"data": "result"}
        assert response.error is None
        assert response.should_continue is True

    def test_response_failure(self) -> None:
        """Test failed agent response."""
        response = AgentResponse(
            success=False,
            content=None,
            error="Something went wrong",
            should_continue=False,
        )

        assert response.success is False
        assert response.error == "Something went wrong"
        assert response.should_continue is False

    def test_response_with_plan(self) -> None:
        """Test response containing a plan."""
        plan = Plan(
            query="Test",
            reasoning="Test reasoning",
            tasks=[Task(id="task-1", description="Test task")],
        )

        response = AgentResponse(success=True, content=plan)

        assert response.success is True
        assert isinstance(response.content, Plan)
        assert len(response.content.tasks) == 1


class TestWorkflowModels:
    """Integration tests for workflow models."""

    def test_complete_workflow_context(self) -> None:
        """Test a complete workflow context with all components."""
        from datetime import date

        from src.data.models import Citation

        # Create tasks
        task1 = Task(
            id="task-1",
            description="Get company info",
            tool_hint="get_company_info",
            status=TaskStatus.COMPLETED,
            result={"ticker": "AAPL", "name": "Apple Inc."},
        )

        task2 = Task(
            id="task-2",
            description="Get financials",
            tool_hint="get_income_statement",
            status=TaskStatus.IN_PROGRESS,
            dependencies=["task-1"],
        )

        # Create plan
        plan = Plan(
            query="What is Apple's revenue?",
            reasoning="Need company info and then financials",
            tasks=[task1, task2],
        )

        # Create citation
        citation = Citation(
            ticker="AAPL",
            form_type="10-K",
            filing_date=date(2024, 10, 31),
            accession_number="0000320193-24-000123",
        )

        # Create context
        context = AgentContext(
            query="What is Apple's revenue?",
            plan=plan,
            tool_results=[
                {
                    "tool_name": "get_company_info",
                    "result": {"ticker": "AAPL"},
                }
            ],
            citations=[citation],
            step_count=2,
            max_steps=20,
        )

        # Verify complete structure
        assert context.query == "What is Apple's revenue?"
        assert context.plan is not None
        assert len(context.plan.tasks) == 2
        assert context.plan.tasks[0].status == TaskStatus.COMPLETED
        assert context.plan.tasks[1].status == TaskStatus.IN_PROGRESS
        assert len(context.tool_results) == 1
        assert len(context.citations) == 1
        assert context.step_count == 2

    def test_task_dependency_chain(self) -> None:
        """Test creating a chain of dependent tasks."""
        task1 = Task(id="task-1", description="Step 1")
        task2 = Task(id="task-2", description="Step 2", dependencies=["task-1"])
        task3 = Task(id="task-3", description="Step 3", dependencies=["task-2"])

        plan = Plan(query="Multi-step", reasoning="Complex query", tasks=[task1, task2, task3])

        assert len(plan.tasks) == 3
        assert plan.tasks[0].dependencies == []
        assert plan.tasks[1].dependencies == ["task-1"]
        assert plan.tasks[2].dependencies == ["task-2"]
