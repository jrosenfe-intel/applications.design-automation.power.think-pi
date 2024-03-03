import { get } from 'svelte/store';
import {
	selectedServerInfoStore,
	activeLayoutStore,
	sinksFileStore
} from '../../store/stores.js';

export const load = async ({ fetch }) => {
	const serverInfo = get(selectedServerInfoStore);
	const sinksFileName = get(sinksFileStore);

    const response = await fetch(`http://${serverInfo.ip_address}:${serverInfo.port}/get-sink-info`, {
        method: 'POST',
        body: JSON.stringify({
            layout_fname: get(activeLayoutStore),
            csv_fname: sinksFileName === '' ? null : sinksFileName
        }),
        headers: {
            'Content-Type': 'application/json'
        }
    });

    return await response.json();
}