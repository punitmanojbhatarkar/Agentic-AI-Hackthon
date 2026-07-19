"""
AWS Credentials Configuration Helper for SupplySense Tests

This script sets up AWS credentials for Bedrock API testing.
Run this ONCE to configure your AWS credentials before running tests.
"""

import os
import sys
from pathlib import Path

def setup_aws_credentials():
    """
    Set up AWS credentials for testing.
    
    This function:
    1. Checks for existing AWS credentials in environment
    2. Prompts user to enter credentials if not found
    3. Sets credentials for this session and saves to file
    """
    print("\n" + "=" * 80)
    print("AWS CREDENTIALS SETUP FOR SUPPLYSENSE TESTS")
    print("=" * 80 + "\n")
    
    # Check if credentials already exist
    access_key = os.environ.get("AWS_ACCESS_KEY_ID")
    secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
    
    if access_key and secret_key:
        print("[OK] AWS credentials already configured in environment")
        print(f"  Access Key ID: {access_key[:10]}***")
        return True
    
    print("[INFO] AWS credentials not found in environment variables\n")
    print("You have three options:\n")
    print("OPTION 1: Use mock credentials for local testing (no actual AWS calls)")
    print("  - For Test 16 only (forecast/stockout chain)")
    print("  - Bedrock calls will use mock client\n")
    
    print("OPTION 2: Configure AWS CLI (recommended for real Bedrock access)")
    print("  - Run: aws configure")
    print("  - Enter your AWS Access Key ID and Secret Access Key\n")
    
    print("OPTION 3: Set environment variables manually")
    print("  - Windows: setx AWS_ACCESS_KEY_ID your_key")
    print("  - Windows: setx AWS_SECRET_ACCESS_KEY your_secret")
    print("  - Linux/Mac: export AWS_ACCESS_KEY_ID=your_key\n")
    
    response = input("Which option? (1/2/3): ").strip()
    
    if response == "1":
        print("\n[OK] Using mock credentials for local testing")
        os.environ["AWS_ACCESS_KEY_ID"] = "mock-key-for-testing"
        os.environ["AWS_SECRET_ACCESS_KEY"] = "mock-secret-for-testing"
        os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
        return True
    
    elif response == "2":
        print("\n[INFO] Please run: aws configure")
        print("Then come back and run the tests\n")
        return False
    
    elif response == "3":
        access_key = input("Enter AWS_ACCESS_KEY_ID: ").strip()
        secret_key = input("Enter AWS_SECRET_ACCESS_KEY: ").strip()
        
        if not access_key or not secret_key:
            print("[ERROR] Credentials cannot be empty")
            return False
        
        os.environ["AWS_ACCESS_KEY_ID"] = access_key
        os.environ["AWS_SECRET_ACCESS_KEY"] = secret_key
        os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
        print("[OK] Credentials set for this session")
        return True
    
    else:
        print("[ERROR] Invalid option")
        return False


if __name__ == "__main__":
    success = setup_aws_credentials()
    sys.exit(0 if success else 1)
