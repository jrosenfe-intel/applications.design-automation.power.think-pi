import { get } from 'svelte/store';
import {
	selectedServerInfoStore,
	activeLayoutStore,
	vrmsFileStore
} from '../../store/stores.js';

export const load = async ({ fetch }) => {
	const serverInfo = get(selectedServerInfoStore);
	const vrmsFileName = get(vrmsFileStore);

    const response = await fetch(`http://${serverInfo.ip_address}:${serverInfo.port}/get-vrm-info`, {
        method: 'POST',
        body: JSON.stringify({
            layout_fname: get(activeLayoutStore),
            csv_fname: vrmsFileName === '' ? null : vrmsFileName
        }),
        headers: {
            'Content-Type': 'application/json'
        }
    });

    return await response.json();
}