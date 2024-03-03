import { get } from 'svelte/store';
import {
	selectedServerInfoStore,
	activeLayoutStore,
	fileExplorerParamsStore,
	padstackFileStore
} from '../../store/stores.js';

export const load = async ({ fetch }) => {
	const serverInfo = get(selectedServerInfoStore);
	const fileInfo = get(fileExplorerParamsStore);

	if (fileInfo.gotoRoute === '/create-padstack') {
		const response = await fetch(`http://${serverInfo.ip_address}:${serverInfo.port}/load-stackup`, {
			method: 'POST',
			body: JSON.stringify({
				fname: get(padstackFileStore)
			}),
			headers: {
				'Content-Type': 'application/json'
			}
		});

        return await response.json();
	} else {
		const response = await fetch(`http://${serverInfo.ip_address}:${serverInfo.port}/get-padstack`, {
			method: 'POST',
			body: JSON.stringify({
				session_id: '',
				layout_fname: get(activeLayoutStore)
			}),
			headers: {
				'Content-Type': 'application/json'
			}
		});

        return await response.json();
	}
};
