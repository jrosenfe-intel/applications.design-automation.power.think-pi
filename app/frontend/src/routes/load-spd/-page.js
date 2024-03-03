
import { spdDataStore } from '../../store/stores.js'
import { get } from 'svelte/store';
import { goto } from '$app/navigation';

export const load = async (loadEvent) => {
    const { fetch } = loadEvent;
    console.log(get(spdDataStore))

	
    const response = await fetch(
		'http://10.39.135.137:8000/load-spd-data',
			{
				method: 'POST',
				body: JSON.stringify({
					filename: "D:/jrosenfe/thinkpi_env/spd_files/brd_DPS_pk187_080421.spd"
				}),
				headers: {
					'Content-Type': 'application/json'
				}
			}
		);
	
	return await response.json()
	
}
