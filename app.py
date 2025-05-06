from flask import Flask, render_template
import asyncio
import json
import os
import websockets
from google import genai
import base64
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Load API key from environment
os.environ['GOOGLE_API_KEY'] = "AIzaSyBhCB1cO0ZUzRB0DYBCz4zcMwS9kVy_ruU"
MODEL = "gemini-2.0-flash-exp"

client = genai.Client(
    http_options={
        'api_version': 'v1alpha',
    }
)

async def gemini_session_handler(client_websocket: websockets.WebSocketServerProtocol):
    logger.info("New client connected to WebSocket.")
    try:
        config_message = await client_websocket.recv()
        logger.info(f"Received initial config message: {config_message}")
        config_data = json.loads(config_message)
        config = config_data.get("setup", {})

        config["system_instruction"] = "You are daily life assistant"
        logger.info(f"System instruction set: {config['system_instruction']}")

        async with client.aio.live.connect(model=MODEL, config=config) as session:
            logger.info("Connected to Gemini API session.")

            async def send_to_gemini():
                logger.info("send_to_gemini task started.")
                try:
                    async for message in client_websocket:
                        logger.info(f"Received message from client: {message}")
                        try:
                            data = json.loads(message)
                            if "realtime_input" in data:
                                for chunk in data["realtime_input"]["media_chunks"]:
                                    logger.info(f"Processing media chunk: {chunk['mime_type']}")
                                    if chunk["mime_type"] == "audio/pcm":
                                        logger.info("Sending audio chunk to Gemini.")
                                        await session.send({"mime_type": "audio/pcm", "data": chunk["data"]})
                                    elif chunk["mime_type"] == "image/jpeg":
                                        logger.info("Sending image chunk to Gemini.")
                                        await session.send({"mime_type": "image/jpeg", "data": chunk["data"]})
                        except Exception as e:
                            logger.error(f"Error sending message to Gemini: {e}")
                    logger.info("Client WebSocket closed (send task).")
                except Exception as e:
                    logger.error(f"send_to_gemini loop error: {e}")
                finally:
                    logger.info("send_to_gemini task terminated.")

            async def receive_from_gemini():
                logger.info("receive_from_gemini task started.")
                try:
                    while True:
                        try:
                            logger.info("Waiting for Gemini response...")
                            async for response in session.receive():
                                logger.info(f"Received response: {response}")

                                if response.server_content is None:
                                    logger.info("Empty server_content received. Continuing.")
                                    continue

                                model_turn = response.server_content.model_turn
                                if model_turn:
                                    logger.info("Processing model_turn content.")
                                    for part in model_turn.parts:
                                        if hasattr(part, 'text') and part.text is not None:
                                            logger.info(f"Sending text to client: {part.text}")
                                            await client_websocket.send(json.dumps({"text": part.text}))
                                        elif hasattr(part, 'inline_data') and part.inline_data is not None:
                                            base64_audio = base64.b64encode(part.inline_data.data).decode('utf-8')
                                            logger.info("Sending audio to client.")
                                            await client_websocket.send(json.dumps({"audio": base64_audio}))

                                if response.server_content.turn_complete:
                                    logger.info("<Turn complete>")
                        except websockets.exceptions.ConnectionClosedOK:
                            logger.info("Client WebSocket closed normally (receive task).")
                            break
                        except Exception as e:
                            logger.error(f"Error in receive loop: {e}")
                            break
                except Exception as e:
                    logger.error(f"receive_from_gemini outer exception: {e}")
                finally:
                    logger.info("receive_from_gemini task terminated.")

            send_task = asyncio.create_task(send_to_gemini())
            receive_task = asyncio.create_task(receive_from_gemini())
            logger.info("Started send and receive tasks.")
            await asyncio.gather(send_task, receive_task)

    except Exception as e:
        logger.error(f"Gemini session handler error: {e}")
    finally:
        logger.info("Gemini session handler terminated.")

async def main() -> None:
    try:
        async with websockets.serve(gemini_session_handler, "localhost", 9082):
            logger.info("WebSocket server running on ws://localhost:9082")
            await asyncio.Future()
    except Exception as e:
        logger.error(f"WebSocket server error: {e}")
    finally:
        logger.info("WebSocket server stopped.")

@app.route('/')
def index():
    logger.info("Serving index.html to client.")
    return render_template('index.html')

if __name__ == "__main__":
    import threading
    logger.info("Starting WebSocket server thread.")
    threading.Thread(target=lambda: asyncio.run(main())).start()
    logger.info("Starting Flask app on http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000)
