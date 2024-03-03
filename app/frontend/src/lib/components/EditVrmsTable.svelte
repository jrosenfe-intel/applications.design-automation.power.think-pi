<script>
	export let compData;
	let headers = ['#', ...Object.keys(compData)];

	let currentInput;
	const inputType = ['number', 'text', 'text', 'number', 'number', 'number', 'text', 'text'];

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

	let row;
	let fromRowId, toRowId;

	function start(e) {
		let children = Array.from(e.target.parentNode.children);

		row = e.target;
		fromRowId = children.indexOf(row);
	}

	function dragover(e) {
		e.preventDefault();

		let children = Array.from(e.target.parentNode.parentNode.children);

		if (children.indexOf(e.target.parentNode) > children.indexOf(row))
			e.target.parentNode.after(row);
		else e.target.parentNode.before(row);

		toRowId = children.indexOf(e.target.parentNode);
	}

	function dropRow(e) {
		let newCompData = compData;

		for (const [header, val] of Object.entries(compData)) {
			const item = val.splice(fromRowId, 1)[0];
			val.splice(toRowId, 0, item);
			newCompData[header] = val;
		}
		compData = newCompData;
	}
</script>

<table class="table table-striped table-sm">
	<thead class="sticky-top">
		<tr>
			{#each headers as header (header)}
				<th class="text-center align-middle" style="white-space: nowrap;" scope="col">{header}</th>
			{/each}
		</tr>
	</thead>
	<tbody class="table-group-divider">
		{#each compData[headers[1]] as data, vidx (data)}
			<tr draggable={true} on:dragstart={start} on:dragover={dragover} on:drop={dropRow}>
				{#each headers as header, hidx (header)}
					<td class="py-1 text-center align-middle">
						{#if hidx === 0}
							{vidx}
                        {:else if hidx === 1}
                            {compData[header][vidx]}
						{:else}
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
						{/if}
					</td>
				{/each}
			</tr>
		{/each}
	</tbody>
</table>

<style>
	.form-control {
		border: 0;
	}

	/* Chrome, Safari, Edge, Opera */
	input::-webkit-outer-spin-button,
	input::-webkit-inner-spin-button {
		-webkit-appearance: none;
		margin: 0;
	}

	tr {
		cursor: all-scroll;
	}

	table {
		border-collapse: collapse;
		-webkit-user-select: none; /* Safari */
		-ms-user-select: none; /* IE 10+ and Edge */
		user-select: none; /* Standard syntax */
	}
</style>
