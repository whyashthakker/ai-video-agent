import time
from celery import Celery
import os
from dotenv import load_dotenv
import logging
import subprocess
from graphqlclient import GraphQLClient
from dotenv import load_dotenv
import json

load_dotenv()

railway_endpoint = os.environ.get("RAILWAY_API_ENDPOINT")

railway_token = os.environ.get("RAILWAY_API_TOKEN")


# Initialize the GraphQL client
client = GraphQLClient(railway_endpoint)
client.inject_token(f"Bearer {railway_token}")

# Step 1: Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

load_dotenv()
BROKER_URL = os.environ.get("REDIS_URL") or os.environ.get("BROKER_URL")
celery_app = Celery("celery_monitor", broker=BROKER_URL)


def restart_service(deployment_id):
    query = """
    mutation DeploymentRestart($id: String!) {
        deploymentRestart(id: $id)
    }
    """
    variables = {"id": deployment_id}
    result = client.execute(query, variables)

    # Parse JSON if result is a string
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except json.JSONDecodeError:
            logging.error(f"Failed to decode JSON: {result}")
            return

    if "errors" in result:
        logging.error(f"Failed to restart the service: {result['errors']}")
    else:
        logging.info("Successfully restarted the service.")


def restart_celery():
    try:
        subprocess.run(["supervisorctl", "restart", "celery_worker"], check=True)
        logging.info("Restarted the Celery application.")
    except subprocess.CalledProcessError:
        logging.error("Failed to restart the Celery application.")


def monitor_workers(idle_duration=60):
    logging.info("Starting to monitor workers...")
    while True:
        insp = celery_app.control.inspect()
        active_tasks = insp.active() or {}

        # Check if all workers are idle
        all_workers_idle = all(not tasks for tasks in active_tasks.values())

        if all_workers_idle:
            logging.info("All workers are idle. Considering for shutdown...")
            time.sleep(idle_duration)

            # Re-check worker status after sleep
            active_tasks = insp.active() or {}
            all_workers_idle = all(not tasks for tasks in active_tasks.values())

            if all_workers_idle:
                logging.info("All workers are still idle. Proceeding to shut down.")

                deployment_id = os.environ.get(
                    "RAILWAY_DEPLOYMENT_ID", os.environ.get("RAILWAY_DEPLOYMENT_ID")
                )

                # Restart the service using GraphQL API
                restart_service(deployment_id)

                # If you also want to restart the Celery application
                # restart_celery()
        else:
            logging.info("Not all workers are idle. Skipping shutdown.")

        time.sleep(10)


if __name__ == "__main__":
    monitor_workers()
