<script>
	import { createEventDispatcher } from 'svelte';
	let dispatch = createEventDispatcher();
	export let capFinder = false;
	export let groundNet = false;
	export let submitButton = true;
	export let capWildcards = 'C*';
	export let title;
	export let copiedNetNames = [];
	export let selectedNetType = 'power';
	export let gndNetName;
	export let netsToReport = [];

	function handleClearClick() {
		netsToReport = [];
	}

	function deleteNet(netName) {
		netsToReport = netsToReport.filter((item) => {
			return item !== netName;
		});
	}

	$: {
		if (selectedNetType === 'ground') {
			gndNetName = copiedNetNames.pop();
		} else {
			netsToReport = [...netsToReport, ...copiedNetNames];
			netsToReport = [...new Set(netsToReport)];
			copiedNetNames = [];
		}
	}
</script>

<div class="card">
	<div class="card-header">{title}</div>
	<div class="card-body">
		<div class="display-height border">
			<table class="table table-sm table-borderless">
				<tbody>
					{#each netsToReport as netName, idx (netName)}
						<tr>
							<td
								><button
									on:click={() => {
										deleteNet(netName);
									}}
									class="btn btn-light me-1"
								>
									<i class="bi bi-trash3"></i>
								</button>{netName}
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
		{#if capFinder}
			<form class="form-floating pt-3">
				<input type="text" class="form-control" id="capFinderValue" bind:value={capWildcards} />
				<label for="capFinderValue">Find capacitors</label>
			</form>
		{/if}
		{#if groundNet}
			<form class="form-floating pt-3">
				<input type="text" class="form-control" id="gndNetNameValue" bind:value={gndNetName} />
				<label for="gndNetNameValue">Ground net name</label>
			</form>
		{/if}
		<div class="pt-2">
			{#if submitButton}
				<button
					on:click={() => {dispatch('create-report', netsToReport);}}
					type="button"
					class="btn btn-sm btn-primary"
					disabled={netsToReport.length === 0 || (groundNet && !gndNetName)}>Submit</button
				>
			{/if}
			<button on:click={handleClearClick} type="button" class="btn btn-sm btn-secondary"
				>Remove</button
			>
		</div>
	</div>
</div>

<style>
	.display-height {
		height: 445px;
		overflow: auto;
	}
</style>
