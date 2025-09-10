import sys
import os
import docker
import uuid

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from agent.src.container import ContainerManager

def test_execution():
    print("--- Starting ContainerManager Isolation Test ---")
    try:
        docker_client = docker.from_env()
        agent_id = "test-agent"
        session_id = str(uuid.uuid4())

        container_manager = ContainerManager(
            client=docker_client, 
            container_identifier=f"{agent_id}-{session_id}", 
            host_cache_folder="/tmp/cache", 
            in_con_env={"PYTHONUNBUFFERED": "1"}
        )
        print("--- ContainerManager Initialized Successfully ---")

        test_code = "print('Hello from inside the container!')"

        print("\n--- Handing code to ContainerManager for execution... ---")
        execution_result = container_manager.run_code_in_con(test_code, "test")

        print("\n--- ContainerManager Execution Result: ---")
        print(execution_result)

    except Exception as e:
        print(f"--- AN ERROR OCCURRED: {e} ---")

if __name__ == "__main__":
    test_execution()
