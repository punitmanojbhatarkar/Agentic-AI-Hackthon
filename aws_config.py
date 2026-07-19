"""
AWS Configuration for SupplySense

NOTE: This module is deprecated in CodeBender environment.
CodeBender uses spawn_agent to access configured providers, not raw boto3.

This file is kept for reference and fallback only. All LLM calls
(planner, composer, critic, sweep) now use CodeBender's spawn_agent,
which accesses your configured Amazon Bedrock provider directly.

No AWS credentials need to be set as environment variables.
"""

import logging

logger = logging.getLogger(__name__)


def get_bedrock_client():
    """
    DEPRECATED: Returns a mock client for backward compatibility.
    
    In CodeBender, all LLM calls should use spawn_agent instead:
    
        from nexen_agents import spawn_agent
        result = spawn_agent(agent_type="general", task="...")
    
    This function is kept only for backward compatibility with code
    that still references bedrock_client directly.
    
    Returns:
        MockBedrockClient (always - real Bedrock not needed in CodeBender)
    """
    logger.info("Using MockBedrockClient (CodeBender uses spawn_agent for LLM calls)")
    return MockBedrockClient()


class MockBedrockClient:
    """
    Mock Bedrock client for testing and fallback.
    
    Simulates Bedrock API responses without needing AWS credentials.
    In CodeBender, spawn_agent is the preferred way to call LLMs.
    """
    
    def invoke_model(self, modelId: str = None, system: str = None, messages: list = None, **kwargs) -> dict:
        """
        Mock implementation of Bedrock invoke_model.
        
        Args:
            modelId: Model ID (ignored in mock)
            system: System prompt (ignored in mock)
            messages: Message list (ignored in mock)
            **kwargs: Additional parameters (ignored in mock)
        
        Returns:
            Mock response dict with body.
        """
        import json
        from io import BytesIO
        
        # Return empty JSON structure
        response_content = json.dumps({
            "steps": [],
            "answer": "Mock response",
            "confidence": "low",
            "caveats": "Mock Bedrock client - use spawn_agent in CodeBender instead"
        })
        
        response_bytes = BytesIO(response_content.encode('utf-8'))
        return {"body": response_bytes}


def configure_test_environment():
    """
    Configure test environment (no-op in CodeBender).
    
    In CodeBender, provider configuration is handled through the platform UI:
    - Select Provider → Edit → Amazon Bedrock → Claude Haiku → Save
    
    This function is kept for reference only.
    """
    logger.info("Test environment already configured in CodeBender platform settings")
    return True
