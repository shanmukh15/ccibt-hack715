# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import logging
import os
import time

from locust import HttpUser, between, task

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

base_url = os.environ.get("CLOUD_RUN_BASE_URL", "http://localhost:8000")
stream_path = "/chat/stream"

logger.info("Using Cloud Run base URL: %s", base_url)


class ChatStreamUser(HttpUser):
    """Simulates a user interacting with the Cloud Run chat API."""

    wait_time = between(1, 3)
    host = base_url

    def on_start(self) -> None:
        self.session_id = None
        payload = {"user_id": "test-user"}
        response = self.client.post("/session", json=payload)
        if response.ok:
            self.session_id = response.json().get("session_id")
            logger.info("Started session %s", self.session_id)
        else:
            logger.error("Failed to create session: %s", response.text)

    @task
    def chat_stream(self) -> None:
        if not self.session_id:
            return

        headers = {"Content-Type": "application/json"}
        data = {
            "session_id": self.session_id,
            "user_id": "test-user",
            "message": "Hi!",
        }

        start_time = time.time()
        with self.client.post(
            stream_path,
            headers=headers,
            json=data,
            catch_response=True,
            name="/chat/stream",
            stream=True,
        ) as response:
            if response.status_code == 200:
                events = []
                has_error = False
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode("utf-8")
                        events.append(line_str)

                        if "429 Too Many Requests" in line_str:
                            self.environment.events.request.fire(
                                request_type="POST",
                                name=f"{url_path} rate_limited 429s",
                                response_time=0,
                                response_length=len(line),
                                response=response,
                                context={},
                            )

                        # Check for error responses in the JSON payload
                        try:
                            event_data = json.loads(line_str)
                            if isinstance(event_data, dict) and "code" in event_data:
                                # Flag any non-2xx codes as errors
                                if event_data["code"] >= 400:
                                    has_error = True
                                    error_msg = event_data.get(
                                        "message", "Unknown error"
                                    )
                                    response.failure(f"Error in response: {error_msg}")
                                    logger.error(
                                        "Received error response: code=%s, message=%s",
                                        event_data["code"],
                                        error_msg,
                                    )
                        except json.JSONDecodeError:
                            # If it's not valid JSON, continue processing
                            pass

                end_time = time.time()
                total_time = end_time - start_time

                # Only fire success event if no errors were found
                if not has_error:
                    self.environment.events.request.fire(
                        request_type="POST",
                        name="/chat/stream end",
                        response_time=total_time * 1000,
                        response_length=len(events),
                        response=response,
                        context={},
                    )
            else:
                response.failure(f"Unexpected status code: {response.status_code}")
