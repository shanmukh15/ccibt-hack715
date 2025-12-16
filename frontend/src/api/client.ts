// In development, Vite proxys /api to backend. 
// In production, we assume same origin or configured base URL.
const dev_url = "http://localhost:8000";
const prod_url = "https://us-central1-aiplatform.googleapis.com/v1/projects/ccibt-hack25ww7-715/locations/us-central1/reasoningEngines/8212069828928733184/";
const API_BASE_URL = process.env.NODE_ENV === "development" ? dev_url : prod_url;

export interface Message {
  role: "user" | "assistant";
  content: string;
}

export async function createSession(userId: string): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/session`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ user_id: userId }),
  });
  if (!response.ok) {
    throw new Error("Failed to create session");
  }
  const data = await response.json();
  return data.session_id;
}

export function streamChat(
  sessionId: string,
  userId: string,
  message: string,
  onDelta: (delta: string) => void,
  onFinal: (final: string) => void,
  onError: (error: any) => void
): EventSource {
  const url = `${API_BASE_URL}/chat/stream?session_id=${encodeURIComponent(
    sessionId
  )}&user_id=${encodeURIComponent(userId)}&q=${encodeURIComponent(message)}`;
  
  const eventSource = new EventSource(url);

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.delta) {
        onDelta(data.delta);
      }
      if (data.final) {
        onFinal(data.final);
        eventSource.close();
      }
    } catch (e) {
      onError(e);
      eventSource.close();
    }
  };

  eventSource.onerror = (err) => {
    onError(err);
    eventSource.close();
  };

  return eventSource;
}

