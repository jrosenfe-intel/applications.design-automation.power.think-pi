import sys
sys.path.append(r"..\..\..\..\..\applications.design-automation.power.think-pi")

from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import asyncio
import queue

from thinkpi.backend_api import api

app = FastAPI()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Messages</h1>
        <ul style="list-style-type:none" id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:8000/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""

que = queue.Queue()
db_api = api.DbApi(r'C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\OKS\db\dmr_ap_pwr_vcciose_cfcmem_23ww07p5_odb.spd',
                    que)

@app.get("/load_data")
def load_data():
    
    return db_api.load_data()
    
@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        try:
            data = que.get_nowait()
            await websocket.send_text(data)
        except queue.Empty:
            await asyncio.sleep(1)


    
        