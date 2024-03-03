<script>
	import { spdDataStore, activeLayoutStore } from '../../store/stores.js';
	import { onMount } from 'svelte';
	let layoutNames = ['Select spd layout file'];
	let fullPaths = [];
	let activeLayoutIdx;
    let numLayouts = 0;

	function updateTooltip() {
		let tooltip = bootstrap.Tooltip.getInstance('#three-dots');
		tooltip._config.title = fullPaths[activeLayoutIdx];
		tooltip.update();
	}

	function copyToClipboard() {
		navigator.clipboard.writeText(fullPaths[activeLayoutIdx]);
	}

	$: if (Object.keys($spdDataStore).length > numLayouts) {
			layoutNames = [];
			fullPaths = [];
			for (let spdPath of Object.keys($spdDataStore)) {
				layoutNames.push(spdPath.split('/').slice(-1));
				fullPaths.push(spdPath);
			}
            activeLayoutIdx = numLayouts;
            numLayouts++;
		}

	$: activeLayoutStore.set(fullPaths[activeLayoutIdx]);

	onMount(() => {
		document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach((tooltip) => {
			new bootstrap.Tooltip(tooltip);
		});
	});
</script>

<select class="form-select" aria-label="Default select" bind:value={activeLayoutIdx}>
	{#each layoutNames as layoutName, idx (idx)}
		<option value={idx}>{layoutName}</option>
	{/each}
</select>
<button
	on:click={copyToClipboard}
	on:mouseenter={updateTooltip}
	type="button"
	id="three-dots"
	class="btn btn-light ms-2"
	data-bs-toggle="tooltip"
	data-bs-placement="top"
	data-bs-title="never to be seen"
>
	<i class="bi bi-three-dots-vertical"></i>
</button>
