<script>
	import { spdDataStore, activeLayoutStore } from '../../store/stores.js';

	
	export let copiedNetNames = [];
	export let netTypes = ['Power', 'Ground'];
	export let selectedNetNames = [];
	export let selectedNetType;
	let netNames = [];
	let searchTerm = '*';
	let matches;
	let selectedRows = {};
	
	function findMatches(netNames, pattern) {
		const regexPattern = new RegExp('^' + pattern.replace(/\?/g, '.').replace(/\*/g, '.*') + '$');
		return netNames.filter((term) => regexPattern.test(term));
	}

	function handleSelectClick(idx) {
		if (idx in selectedRows) {
			delete selectedRows[idx];
			selectedRows = selectedRows;
		} else if (selectedNetType !== 'ground' || Object.keys(selectedRows).length === 0) {
			selectedRows[idx] = idx;
		}
	}

	function handleClearClick() {
		selectedRows = {};
	}

	function handleCopyClick() {
		if (Object.keys(selectedRows).length !== 0) {
			selectedNetNames = [];
			for (let idx of Object.keys(selectedRows)) {
				selectedNetNames.push(matches[idx]);
			}
		} else {
			selectedNetNames = [...matches];
		}
		copiedNetNames = [...selectedNetNames];
	}

	$: {
		netNames = $spdDataStore[$activeLayoutStore]
					?.netNames[selectedNetType] || []

		matches = findMatches(netNames, searchTerm);
		handleClearClick();
	}

</script>

<div class="card">
	<div class="form-floating">
		<select bind:value={selectedNetType} class="form-select" id="floatingSelect">
			{#each netTypes as netType, idx (idx)}
				<option value={netType}>{netType}</option>
			{/each}
		</select>
		<label for="floatingSelect">Select net type</label>
	</div>
	<div class="card-body">
		<div class="input-group mb-3">
			<span class="input-group-text" id="input-search"><i class="bi bi-search"></i></span>
			<input
				type="text"
				class="form-control"
				aria-label="input-search"
				aria-describedby="input-search"
				bind:value={searchTerm}
			/>
		</div>

		<div class="table-height border">
			<table class="table table-sm table-hover table-borderless">
				<tbody>
					{#each matches as match, idx (idx)}
						<tr
							on:click={() => handleSelectClick(idx)}
							class:table-active={selectedRows[idx] === idx}
						>
							<td>{match}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
		<div class="pt-2">
			<button on:click={handleCopyClick} type="button" class="btn btn-sm btn-primary">Copy</button>
			<button on:click={handleClearClick} type="button" class="btn btn-sm btn-secondary"
				>Clear</button
			>
		</div>
	</div>
</div>

<style>
	.table-height {
		height: 450px;
		overflow: auto;
	}
</style>
