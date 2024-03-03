<script>
	import { selectedServerInfoStore, spdDataStore } from '../../store/stores.js';
	import { activeLayoutStore } from '../../store/stores.js';
	import LayerCheckSelect from '$lib/components/LayerCheckSelect.svelte';

	let currentLayer;
	let htmlLayer;
	let layerNames;
    export const compData = null;

    $: {
        layerNames = $spdDataStore[$activeLayoutStore].layerNames;
    }

	$: {
		currentLayer = $spdDataStore[$activeLayoutStore].currentLayer;
		htmlLayer = $spdDataStore[$activeLayoutStore].htmlLayers[currentLayer];
	}

	async function loadLayer(layer) {
		const response = await fetch(
			`http://${$selectedServerInfoStore.ip_address}:${$selectedServerInfoStore.port}/load-spd-by-layer`,
			{
				method: 'POST',
				body: JSON.stringify({
					filename: $activeLayoutStore,
					layer: layer
				}),
				headers: {
					'Content-Type': 'application/json'
				}
			}
		);

		const layerData = await response.json();

		spdDataStore.update((layoutData) => {
			layoutData[$activeLayoutStore].htmlLayers[layer] = layerData;
			layoutData[$activeLayoutStore].currentLayer = layer;

			return layoutData;
		});
	}

	function changeLayer(event) {
		let layerName = event.detail;
		if (!(layerName in $spdDataStore[$activeLayoutStore].htmlLayers)) {
			loadLayer(layerName);
		}

		spdDataStore.update((layoutData) => {
			layoutData[$activeLayoutStore].currentLayer = layerName;

			return layoutData;
		});
	}
</script>

<div class="container text-center">
	<div class="row">
		<div class="col col-11 pt-3">
			<iframe title="htmlLayer" srcdoc={htmlLayer} height="800" width="1500"></iframe>
		</div>
		<div class="col col-1 pt-3">
			<LayerCheckSelect on:change-layer={changeLayer} {layerNames} {currentLayer} title="Layers"/>
		</div>
	</div>
</div>
