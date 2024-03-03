<script>
	import { spdDataStore } from '../../store/stores.js';
	import { createEventDispatcher } from 'svelte';

	let dispatch = createEventDispatcher();
	export let layerNames;
	export let currentLayer;
	export let title;

	function handleClick(idx) {
		dispatch('change-layer', layerNames[idx]);
	}
</script>

<h5><span class="fw-light badge bg-secondary">{title}</span></h5>

<div class="border-top display-height">
	<div class="btn-group-vertical pt-2" role="group" aria-label="Vertical radio toggle button group">
		{#each layerNames as layerName, idx (layerName)}
			<input
				on:click={() => {
					handleClick(idx);
				}}
				type="radio"
				class="btn-check"
				name="vbtn-radio"
				id={layerName}
				autocomplete="off"
				checked={layerName === currentLayer}
			/>
			<label class="btn btn-outline-secondary btn-sm" for={layerName}>{layerName}</label>
		{/each}
	</div>
</div>

<!-- <div class="form-check">
	{#each layerNames as layerName, idx (layerName)}
		<input
			on:click={() => {
				handleClick(idx);
			}}
			class="form-check-input"
			type="radio"
			name={layerName}
			id={layerName}
			value={layerName}
			checked={layerName === currentLayer}
		/>
		<label class="form-check-label" for={layerName}> {layerName} </label>
	{/each}
</div> -->

<style>
	.display-height {
		height: 655px;
		width: 300px;
		overflow: auto;
	}
</style>
