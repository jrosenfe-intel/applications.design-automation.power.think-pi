<script>
	import { selectedServerNameStore } from '../../store/stores.js'
	import { refreshServerListStore } from '../../store/stores.js'

	let isConnected;
	$: isConnected = $selectedServerNameStore !== 'Select server';

	function handleClick() {
		refreshServerListStore.set(true);
	}
</script>

<button
	on:click={handleClick}
	type="button"
	class="btn btn-outline-primary btn-sm"
	data-bs-toggle="modal"
	data-bs-target="#server-list"
>
	<span class="mb-1 spinner-grow {isConnected ? 'text-success' : 'text-danger'}" />
	<span role="status">{$selectedServerNameStore}</span>
</button>

<style>
	.spinner-grow {
		width: 8px;
		height: 8px;
	}
</style>
