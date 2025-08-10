#!/usr/bin/env python3
"""
Workflow Orchestrator - MarTech Integration Hub

Advanced workflow orchestration system for marketing technology integrations.
Coordinates complex multi-step workflows across marketing platforms.

Author: Sotirios Spyrou
Portfolio: https://verityai.co
LinkedIn: https://www.linkedin.com/in/sspyrou/

🚀 THE RARE TECHNICAL MARKETING LEADER 🚀
Combining C-suite strategy with hands-on AI implementation.

DISCLAIMER: This is demonstration code showcasing technical capabilities.
"""

import asyncio
import json
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

class WorkflowStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"

class StepType(Enum):
    DATA_SYNC = "data_sync"
    EMAIL_CAMPAIGN = "email_campaign"
    LEAD_SCORING = "lead_scoring"
    AUDIENCE_SYNC = "audience_sync"
    REPORTING = "reporting"
    CUSTOM = "custom"

@dataclass
class WorkflowStep:
    step_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    step_type: StepType = StepType.CUSTOM
    function: Optional[Callable] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    status: WorkflowStatus = WorkflowStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

@dataclass
class Workflow:
    workflow_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    steps: List[WorkflowStep] = field(default_factory=list)
    status: WorkflowStatus = WorkflowStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class WorkflowOrchestrator:
    """
    Advanced workflow orchestration system for MarTech integrations.
    
    🎯 ENTERPRISE CAPABILITIES:
    - Multi-step workflow coordination
    - Dependency management and parallel execution
    - Error handling and retry mechanisms
    - Real-time workflow monitoring
    - Cross-platform integration orchestration
    
    🔗 Learn more: https://verityai.co
    💼 Connect: https://www.linkedin.com/in/sspyrou/
    """
    
    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
        self.active_workflows: Dict[str, Workflow] = {}
        self.metrics = {
            'workflows_created': 0,
            'workflows_completed': 0,
            'workflows_failed': 0,
            'steps_executed': 0,
            'total_execution_time': 0
        }
    
    def create_workflow(self, name: str, description: str = "") -> str:
        """Create a new workflow."""
        workflow = Workflow(
            name=name,
            description=description
        )
        self.workflows[workflow.workflow_id] = workflow
        self.metrics['workflows_created'] += 1
        return workflow.workflow_id
    
    def add_step(self, workflow_id: str, name: str, step_type: StepType, 
                function: Optional[Callable] = None, parameters: Dict[str, Any] = None,
                dependencies: List[str] = None) -> str:
        """Add a step to a workflow."""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        step = WorkflowStep(
            name=name,
            step_type=step_type,
            function=function,
            parameters=parameters or {},
            dependencies=dependencies or []
        )
        
        self.workflows[workflow_id].steps.append(step)
        return step.step_id
    
    def get_ready_steps(self, workflow: Workflow) -> List[WorkflowStep]:
        """Get steps that are ready to execute (all dependencies completed)."""
        ready_steps = []
        completed_step_ids = {s.step_id for s in workflow.steps if s.status == WorkflowStatus.COMPLETED}
        
        for step in workflow.steps:
            if (step.status == WorkflowStatus.PENDING and 
                all(dep_id in completed_step_ids for dep_id in step.dependencies)):
                ready_steps.append(step)
        
        return ready_steps
    
    async def execute_step(self, step: WorkflowStep) -> bool:
        """Execute a single workflow step."""
        try:
            step.status = WorkflowStatus.RUNNING
            step.started_at = datetime.now()
            
            if step.function:
                if asyncio.iscoroutinefunction(step.function):
                    result = await step.function(**step.parameters)
                else:
                    result = step.function(**step.parameters)
                
                if result is False:
                    raise Exception(f"Step {step.name} returned False")
            
            step.status = WorkflowStatus.COMPLETED
            step.completed_at = datetime.now()
            self.metrics['steps_executed'] += 1
            return True
            
        except Exception as e:
            step.error_message = str(e)
            step.retry_count += 1
            
            if step.retry_count < step.max_retries:
                step.status = WorkflowStatus.PENDING
                return False
            else:
                step.status = WorkflowStatus.FAILED
                return False
    
    async def execute_workflow(self, workflow_id: str) -> bool:
        """Execute a complete workflow."""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow = self.workflows[workflow_id]
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.now()
        self.active_workflows[workflow_id] = workflow
        
        try:
            while True:
                ready_steps = self.get_ready_steps(workflow)
                
                if not ready_steps:
                    pending_steps = [s for s in workflow.steps if s.status == WorkflowStatus.PENDING]
                    if not pending_steps:
                        break
                    else:
                        await asyncio.sleep(1)
                        continue
                
                tasks = [self.execute_step(step) for step in ready_steps]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for step, result in zip(ready_steps, results):
                    if isinstance(result, Exception) or result is False:
                        if step.status == WorkflowStatus.FAILED:
                            workflow.status = WorkflowStatus.FAILED
                            self.metrics['workflows_failed'] += 1
                            return False
            
            failed_steps = [s for s in workflow.steps if s.status == WorkflowStatus.FAILED]
            if failed_steps:
                workflow.status = WorkflowStatus.FAILED
                self.metrics['workflows_failed'] += 1
                return False
            
            workflow.status = WorkflowStatus.COMPLETED
            workflow.completed_at = datetime.now()
            self.metrics['workflows_completed'] += 1
            
            execution_time = (workflow.completed_at - workflow.started_at).total_seconds()
            self.metrics['total_execution_time'] += execution_time
            
            return True
            
        finally:
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get detailed workflow status."""
        if workflow_id not in self.workflows:
            return {}
        
        workflow = self.workflows[workflow_id]
        
        step_stats = defaultdict(int)
        for step in workflow.steps:
            step_stats[step.status.value] += 1
        
        execution_time = None
        if workflow.started_at:
            end_time = workflow.completed_at or datetime.now()
            execution_time = (end_time - workflow.started_at).total_seconds()
        
        return {
            'workflow_id': workflow_id,
            'name': workflow.name,
            'status': workflow.status.value,
            'total_steps': len(workflow.steps),
            'step_status': dict(step_stats),
            'execution_time_seconds': execution_time,
            'created_at': workflow.created_at.isoformat(),
            'started_at': workflow.started_at.isoformat() if workflow.started_at else None,
            'completed_at': workflow.completed_at.isoformat() if workflow.completed_at else None
        }
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get overall system metrics."""
        active_count = len(self.active_workflows)
        avg_execution_time = (
            self.metrics['total_execution_time'] / max(self.metrics['workflows_completed'], 1)
        )
        
        return {
            'workflows_created': self.metrics['workflows_created'],
            'workflows_completed': self.metrics['workflows_completed'],
            'workflows_failed': self.metrics['workflows_failed'],
            'active_workflows': active_count,
            'steps_executed': self.metrics['steps_executed'],
            'avg_execution_time_seconds': avg_execution_time,
            'success_rate_percent': (
                self.metrics['workflows_completed'] / 
                max(self.metrics['workflows_completed'] + self.metrics['workflows_failed'], 1)
            ) * 100
        }

async def demo_sample_task(name: str) -> bool:
    """Sample task for demonstration."""
    await asyncio.sleep(0.1)  # Simulate work
    return True

async def demo_workflow_orchestration():
    """Demonstrate workflow orchestration capabilities."""
    print("🚀 WORKFLOW ORCHESTRATOR DEMO")
    
    orchestrator = WorkflowOrchestrator()
    
    # Create a sample marketing workflow
    workflow_id = orchestrator.create_workflow(
        "Email Campaign Launch",
        "Automated email campaign with lead scoring and audience sync"
    )
    
    # Add workflow steps with dependencies
    step1_id = orchestrator.add_step(
        workflow_id, "Data Validation", StepType.DATA_SYNC,
        demo_sample_task, {'name': 'validate_data'}
    )
    
    step2_id = orchestrator.add_step(
        workflow_id, "Lead Scoring", StepType.LEAD_SCORING,
        demo_sample_task, {'name': 'score_leads'},
        dependencies=[step1_id]
    )
    
    step3_id = orchestrator.add_step(
        workflow_id, "Audience Sync", StepType.AUDIENCE_SYNC,
        demo_sample_task, {'name': 'sync_audience'},
        dependencies=[step2_id]
    )
    
    orchestrator.add_step(
        workflow_id, "Email Campaign", StepType.EMAIL_CAMPAIGN,
        demo_sample_task, {'name': 'send_campaign'},
        dependencies=[step3_id]
    )
    
    orchestrator.add_step(
        workflow_id, "Generate Report", StepType.REPORTING,
        demo_sample_task, {'name': 'generate_report'},
        dependencies=[step3_id]  # Can run in parallel with email
    )
    
    # Execute workflow
    success = await orchestrator.execute_workflow(workflow_id)
    
    # Display results
    status = orchestrator.get_workflow_status(workflow_id)
    metrics = orchestrator.get_system_metrics()
    
    print(f"\nWorkflow: {status['name']}")
    print(f"Status: {status['status']}")
    print(f"Steps: {status['total_steps']}")
    print(f"Execution Time: {status['execution_time_seconds']:.2f}s")
    print(f"System Success Rate: {metrics['success_rate_percent']:.1f}%")
    
    print("\n🔗 Visit: https://verityai.co")
    print("💼 Connect: https://www.linkedin.com/in/sspyrou/")

if __name__ == "__main__":
    asyncio.run(demo_workflow_orchestration())