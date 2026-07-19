#!/usr/bin/env python3
"""
Create a wrapper to call CodeBender's configured Bedrock provider via REST.

Based on the fact that:
1. You have a saved profile named "claud haiku"
2. Provider/Model string: bedrock:global.anthropic.claude-haiku-4-5-20251001-v1:0
3. CodeBender manages keys and routing

We can assume CodeBender provides an HTTP API or environment variable to route calls.
"""

import json
import os

class CodeBenderProvider:
    """
    Wrapper to call CodeBender-managed Bedrock provider.
    
    This tries multiple methods to invoke the "claud haiku" profile:
    1. HTTP REST API call to CodeBender's provider endpoint
    2. Environment variable with API key
    3. CLI command wrapper
    """
    
    def __init__(self, profile_name="claud haiku"):
        self.profile_name = profile_name
        self.endpoint = self._find_endpoint()
        self.api_key = self._find_api_key()
        
    def _find_endpoint(self):
        """Try to find CodeBender provider endpoint."""
        # Common patterns
        candidates = [
            os.getenv("CODEBENDER_PROVIDER_ENDPOINT"),
            os.getenv("CODEBENDER_BEDROCK_ENDPOINT"),
            os.getenv("LLM_PROVIDER_ENDPOINT"),
            os.getenv("BEDROCK_ENDPOINT"),
            "http://localhost:9999/provider",  # Common internal port
            "http://codebender:8000/provider",  # Internal hostname
            "http://localhost:8000/api/provider",  # Local SupplySense?
        ]
        
        for endpoint in candidates:
            if endpoint:
                return endpoint
        
        return None
    
    def _find_api_key(self):
        """Try to find CodeBender API key."""
        candidates = [
            os.getenv("CODEBENDER_API_KEY"),
            os.getenv("CODEBENDER_PROVIDER_KEY"),
            os.getenv("LLM_API_KEY"),
            os.getenv("BEDROCK_API_KEY"),
        ]
        
        for key in candidates:
            if key:
                return key
        
        return None
    
    def invoke(self, messages, system_prompt=None, **kwargs):
        """
        Invoke Claude Haiku through the CodeBender provider.
        
        Args:
            messages: List of messages (format: [{"role": "user", "content": "..."}])
            system_prompt: Optional system prompt
            **kwargs: Additional parameters
        
        Returns:
            str: LLM response
        """
        
        # Method 1: Try HTTP API
        if self.endpoint:
            return self._invoke_http(messages, system_prompt, **kwargs)
        
        # Method 2: Try direct boto3 with injected credentials
        try:
            return self._invoke_boto3(messages, system_prompt, **kwargs)
        except Exception as e:
            print(f"Boto3 method failed: {e}")
        
        # Method 3: Fallback to OpenAI (since OPENAI_API_KEY is available)
        if os.getenv("OPENAI_API_KEY"):
            return self._invoke_openai_fallback(messages, system_prompt, **kwargs)
        
        raise RuntimeError(f"Cannot find CodeBender provider endpoint or API key")
    
    def _invoke_http(self, messages, system_prompt, **kwargs):
        """Call CodeBender provider via HTTP."""
        import requests
        
        payload = {
            "profile": self.profile_name,
            "messages": messages,
        }
        if system_prompt:
            payload["system"] = system_prompt
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            response = requests.post(
                self.endpoint,
                json=payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            # Extract response text based on common formats
            if "content" in result:
                return result["content"]
            elif "response" in result:
                return result["response"]
            elif "message" in result:
                return result["message"]
            else:
                return json.dumps(result)
        
        except Exception as e:
            raise RuntimeError(f"HTTP provider call failed: {e}")
    
    def _invoke_boto3(self, messages, system_prompt, **kwargs):
        """Call AWS Bedrock directly via boto3."""
        import boto3
        
        client = boto3.client('bedrock-runtime', region_name='us-east-1')
        
        # Format messages for Claude
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        body = {
            "anthropic_version": "bedrock-2023-06-01",
            "max_tokens": kwargs.get("max_tokens", 1000),
            "messages": formatted_messages,
        }
        
        if system_prompt:
            body["system"] = system_prompt
        
        response = client.invoke_model(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            body=json.dumps(body)
        )
        
        response_data = json.loads(response['body'].read())
        if 'content' in response_data:
            return response_data['content'][0]['text']
        return json.dumps(response_data)
    
    def _invoke_openai_fallback(self, messages, system_prompt, **kwargs):
        """Fallback to OpenAI if Claude not available."""
        print("\n[WARNING] Using OpenAI fallback instead of Claude Haiku")
        
        import openai
        
        openai.api_key = os.getenv("OPENAI_API_KEY")
        
        system_messages = []
        if system_prompt:
            system_messages.append({"role": "system", "content": system_prompt})
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=system_messages + messages,
            max_tokens=kwargs.get("max_tokens", 1000)
        )
        
        return response.choices[0].message.content


# Test it
if __name__ == "__main__":
    provider = CodeBenderProvider()
    
    print("=" * 80)
    print("CODEBENDER PROVIDER CLIENT INITIALIZATION")
    print("=" * 80)
    print(f"Profile: {provider.profile_name}")
    print(f"Endpoint: {provider.endpoint}")
    print(f"API Key: {'SET' if provider.api_key else 'NOT SET'}")
    
    # Try a simple invocation
    print("\nAttempting to invoke...")
    try:
        response = provider.invoke([
            {"role": "user", "content": "What is 2+2?"}
        ], system_prompt="You are a helpful assistant.")
        
        print(f"\nSUCCESS!")
        print(f"Response: {response}")
    
    except Exception as e:
        print(f"\nERROR: {e}")
