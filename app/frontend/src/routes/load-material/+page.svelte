<script>
	import { selectedServerInfoStore, loadFileFolderStore } from '../../store/stores.js';
    import { materialFileStore, materialDataStore } from '../../store/stores.js';
    import { onMount } from 'svelte';
	import { goto } from '$app/navigation';

	let data;
	
	async function loadMaterial() {
		const response = await fetch(
			`http://${$selectedServerInfoStore.ip_address}:${$selectedServerInfoStore.port}/load-material-data`,
			{
				method: 'POST',
				body: JSON.stringify({
					layout_fname: $loadFileFolderStore,
					material_fname: $materialFileStore
				}),
				headers: {
					'Content-Type': 'application/json'
				}
			}
		);
		data = await response.json();
        materialDataStore.set(data);
		goto('/view-material');
	}

	onMount(() => {
		loadMaterial();
	});
</script>

