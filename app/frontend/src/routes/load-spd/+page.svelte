<script>
	import { selectedServerInfoStore, spdDataStore } from '../../store/stores.js';
	import { loadFileFolderStore, sessionId } from '../../store/stores.js';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';

	async function loadSpd() {
		const response = await fetch(
			`http://${$selectedServerInfoStore.ip_address}:${$selectedServerInfoStore.port}/load-spd-data`,
			{
				method: 'POST',
				body: JSON.stringify({
					session_id: $sessionId,
					layout_fname: $loadFileFolderStore
				}),
				headers: {
					'Content-Type': 'application/json'
				}
			}
		);

		const spdData = await response.json()

	    spdDataStore.update((layoutData) => {
	        layoutData[$loadFileFolderStore] = {
	            htmlLayers: {[spdData.layer_names[0]]: spdData.layer_html},
	            layerNames: spdData.layer_names,
	            currentLayer: spdData.layer_names[0],
	            netNames: spdData.net_names
	        }
	        return layoutData;
	    })
	    console.log($spdDataStore);
	    goto("/view-spd");
	}

	onMount(() => {
		loadSpd();
	});
</script>

<div class="container text-center position-absolute top-50 start-50 translate-middle">
	<div class="row">
		<div class="col">
			<h6 class="display-6 text-info-emphasis text-center">Loading...</h6>
			<div class="load-container text-center text-primary">
				<div class="spinner-border" role="status"></div>
			</div>
		</div>
	</div>
</div>
