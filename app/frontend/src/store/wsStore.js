import { writable } from 'svelte/store';

export let messageStore = writable('');

// const socket = new WebSocket('ws://10.97.50.10:8000/ws');

// // Connection opened
// socket.addEventListener('open', function (event) {
//     console.log("Websocket is open");
// });

// // Listen for messages
// socket.addEventListener('message', function (event) {
//     messageStore.set(event.data);
// });

// const sendMessage = (message) => {
// 	if (socket.readyState <= 1) {
// 		socket.send(message);
// 	}
// }

// export default {
// 	subscribe: messageStore.subscribe,
// 	sendMessage
// }