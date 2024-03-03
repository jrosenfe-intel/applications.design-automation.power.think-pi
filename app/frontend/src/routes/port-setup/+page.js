import { get } from 'svelte/store';
import {
	selectedServerInfoStore,
	activeLayoutStore,
	portsFileStore
} from '../../store/stores.js';

export const load = async ({ fetch }) => {
	const serverInfo = get(selectedServerInfoStore);
	const portsFileName = get(portsFileStore);

    const response = await fetch(`http://${serverInfo.ip_address}:${serverInfo.port}/get-port-info`, {
        method: 'POST',
        body: JSON.stringify({
            layout_fname: get(activeLayoutStore),
            csv_fname: portsFileName === '' ? null : portsFileName
        }),
        headers: {
            'Content-Type': 'application/json'
        }
    });

    return await response.json();
}