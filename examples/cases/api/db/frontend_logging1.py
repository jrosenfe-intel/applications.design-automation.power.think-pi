import sys
sys.path.append(r"..\..\..\..\..\applications.design-automation.power.think-pi")

from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import asyncio
from multiprocessing import Process, Queue
import queue
import concurrent

from thinkpi import logger
from thinkpi.operations import speed as spd

class UserMessages:

    def __init__(self):

        '''
        logger.add(self.put,
                   format="[{time:DD-MM-YYYY HH:mm:ss}] [{function}] {message}",
                   level="DEBUG")
        '''
        self.queue = queue.Queue()
        self.ws = None
        self.loop = None
    
    def put(self, message):
        
        self.queue.put(message)


app = FastAPI()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
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

note = UserMessages()

@app.get("/test")
def test():
    '''
    loop = asyncio.get_event_loop()
    with concurrent.futures.ProcessPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, load_test)
    return result
    '''
    db = spd.Database(r'C:\Users\jrosenfe\OneDrive - Intel Corporation\Documents\Python Scripts\PI\thinkpi_test_db\OKS\db\dmr_ap_pwr_vcciose_cfcmem_23ww07p5_odb.spd',
                      note.queue)
    db.load_flags['plots'] = False
    db.load_data()

@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        try:
            data = note.queue.get_nowait()
            await websocket.send_text(data)
        except queue.Empty:
            await asyncio.sleep(1)
            
    
        


    
        