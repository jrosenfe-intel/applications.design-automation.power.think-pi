<script>
	import { selectedServerInfoStore } from '../../store/stores.js';
	import { socketStore, sessionId } from '../../store/stores.js';

	$: {
		if ($socketStore === undefined && $selectedServerInfoStore !== null) {
			sessionId.set(Date.now().toString())
			socketStore.set(
				new WebSocket(
					`ws://${$selectedServerInfoStore.ip_address}:${$selectedServerInfoStore.port}/ws/${$sessionId}`
				)
			);

			$socketStore.onopen = (event) => {
				console.log(`websocket ${$sessionId} is open`);
			};

			$socketStore.onmessage = (event) => {
				let messageType;
				let message;
				let loggerElem = document.getElementById('logger');

				message = event.data.split('] ');
				if (message[1] === '[INFO') {
					messageType = 'text-info';
				} else if (message[1] === '[WARNING') {
					messageType = 'text-warning';
				} else {
					messageType = 'text-danger';
				}
				message = `${message[0]}] ${message.pop()}`;
				loggerElem.innerHTML += `<div class="${messageType}">${message}</div>`;
				loggerElem.scroll({ top: loggerElem.scrollHeight, behavior: 'smooth' });
				
			}

			$socketStore.onclose = (event) => {
				console.log(`websocket is closed ${event}`);
			}

			$socketStore.onerror = (event) => {
				console.log(`websocket has errored ${event}`);
			}
		}
	}
</script>

<h1 class="display-6 text-info-emphasis text-center">Log information</h1>
<pre class="log-stream border" id="logger"></pre>

<style>
	.log-stream {
		height: 700px;
		overflow: auto;
	}
</style>
