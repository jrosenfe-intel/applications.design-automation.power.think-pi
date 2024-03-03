<script>
	import { materialDataStore } from '../../store/stores.js';

	export let compData;
	let headers;
	let currentInput;
	const inputType = [
		'text',
		'text',
		'number',
		'number',
		'number',
		'text',
		'text',
        'number',
        'number',
        'text',
        'number',
        'number',
        'text',
        'number',
        'text'
	];
	let loadedMaterials;

	const onInput = (event, cellId) => {
		if (event.key === 'Enter' || event.type === 'blur') {
			event.target.blur();
			currentInput = document.getElementById(cellId).value;
			const vidx = parseInt(cellId.split(':').slice(1)[0]);
			const hidx = parseInt(cellId.split(':').slice(1)[1]);
			const colData = compData[headers[hidx]];
			colData[vidx] = currentInput;
			compData[headers[hidx]] = colData;
		}
	};

    let toggleColor = true;
	let prevPadName = null;
	function highlightBlock(padName, vidx) {
		if (padName != prevPadName) {
			toggleColor = !toggleColor;
			prevPadName = padName;
		}
	
		if (vidx === compData.Name.length - 1) {
			toggleColor = !toggleColor;
        	return !toggleColor ? '' : 'table-secondary'
		} else return toggleColor ? '' : 'table-secondary'
    }

	$: headers = Object.keys(compData);
	$: if ($materialDataStore !== undefined) {
		loadedMaterials = ['', ...Object.keys($materialDataStore)];
	} else {
		loadedMaterials = [];
	}
</script>

<table class="table table-sm">
	<thead class="sticky-top">
		<tr>
			{#each headers as header (header)}
				<th class="text-center align-middle" scope="col">{header}</th>
			{/each}
		</tr>
	</thead>
	<tbody class="table-group-divider">
		{#each compData[headers[0]] as padName, vidx (vidx)}
			<tr class="align-middle {highlightBlock(padName, vidx)}">
				{#each headers as header, hidx (header)}
					<td class="py-1">
						{#if hidx === 5 || hidx === 12 || hidx === 14}
							<select
								bind:value={compData[header][vidx]}
								class="form-select form-select-sm bg-transparent text-center"
							>
								<option selected>{compData[header][vidx]}</option>
								{#each loadedMaterials as material}
									<option value={material}>{material}</option>
								{/each}
							</select>
						{:else if hidx > 1}
							<input
								on:keydown={(event) => {
									onInput(event, `cell:${vidx}:${hidx}`);
								}}
								on:blur={(event) => {
									onInput(event, `cell:${vidx}:${hidx}`);
								}}
								id={`cell:${vidx}:${hidx}`}
								class="form-control form-control-sm bg-transparent text-center"
								type={inputType[hidx]}
								value={compData[header][vidx]}
							/>
						{:else}
							{compData[header][vidx]}
						{/if}
					</td>
				{/each}
			</tr>
		{/each}
	</tbody>
</table>

<style>
	.form-control,
	.form-select {
		border: 0;
	}

	/* Chrome, Safari, Edge, Opera */
	input::-webkit-outer-spin-button,
	input::-webkit-inner-spin-button {
		-webkit-appearance: none;
		margin: 0;
	}
</style>
