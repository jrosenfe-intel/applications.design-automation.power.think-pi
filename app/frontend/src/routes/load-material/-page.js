import { selectedServerInfoStore, materialFileStore } from '../../store/stores.js'
import { get } from 'svelte/store';

export const load = async ({ fetch }) => {
    const serevrInfo = get(selectedServerInfoStore);

    const response = await fetch(
		`http://${serevrInfo.ip_address}:${serevrInfo.port}/load-material-data`,
			{
				method: 'POST',
				body: JSON.stringify({
					filename: get(materialFileStore)
				}),
				headers: {
					'Content-Type': 'application/json'
				}
			}
		);
	
	return await response.json()
}