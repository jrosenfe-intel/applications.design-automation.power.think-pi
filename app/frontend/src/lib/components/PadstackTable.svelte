<script>
	import EditPadstackTable from '$lib/components/EditPadstackTable.svelte';
	import { materialDataStore, materialFileStore } from '../../store/stores.js';
	import { selectedServerInfoStore, fileExplorerParamsStore } from '../../store/stores.js';
	import { activeLayoutStore, padstackFileStore } from '../../store/stores.js';
	import { invalidateAll } from '$app/navigation';

	export let compData;
	let loading = false;
	let unit = Object.keys(compData)[2].split('[')[1].slice(0, -1);
	let unitConv = { nm: 1e-9, um: 1e-6, mm: 1e-3, cm: 1e-2, m: 1, mil: 2.54e-5, inch: 0.0254 };
	let materialNames;
	let formData = {
		csvFileName: null,
		layoutType: 'board',
		material: 'Default',
		conduct: null,
		brdPlating: null,
		pkgGndPlating: null,
		pkgPwrPlating: null,
		innerFillMaterial: 'Default',
		outerThickness: null,
		outerCoatingMaterial: 'Default'
	};
	let formSubmitDisabled = false;
	let formValidation = {
		csvFileName: 'is-invalid',
		conduct: 'valid',
		brdPlating: 'valid',
		pkgGndPlating: 'valid',
		pkgPwrPlating: 'valid',
		outerThickness: 'valid'
	};
	let toastElem;

	async function savePadstack() {
		await fetch(
			`http://${$selectedServerInfoStore.ip_address}:${$selectedServerInfoStore.port}/save-stackup`,
			{
				method: 'POST',
				body: JSON.stringify({
					spd_filename: $activeLayoutStore,
					csv_fname: formData.csvFileName,
					stackup_data: compData
				}),
				headers: {
					'Content-Type': 'application/json'
				}
			}
		);
	}

	async function applyToLayout() {
		savePadstack();
		await new Promise((resolve) => setTimeout(resolve, 2000));
		await fetch(
			`http://${$selectedServerInfoStore.ip_address}:${$selectedServerInfoStore.port}/apply-padstack`,
			{
				method: 'POST',
				body: JSON.stringify({
					spd_fname: $activeLayoutStore,
					padstack_fname: formData.csvFileName,
					material_fname: $materialFileStore === '' ? null : $materialFileStore
				}),
				headers: {
					'Content-Type': 'application/json'
				}
			}
		);

		const toastBootstrap = bootstrap.Toast.getOrCreateInstance(toastElem);
		toastBootstrap.show();
	}

	async function updatePadstack() {
		loading = !loading;
		const response = await fetch(
			`http://${$selectedServerInfoStore.ip_address}:${$selectedServerInfoStore.port}/auto-setup-padstack`,
			{
				method: 'POST',
				body: JSON.stringify({
					unit: unit,
					layout_type: formData.layoutType,
					spd_fname: $activeLayoutStore,
					material: formData.material,
					inner_fill_material: formData.innerFillMaterial,
					outer_thickness: formData.outerThickness,
					conduct: formData.conduct,
					brd_plating: formData.brdPlating,
					pkg_gnd_plating: formData.pkgGndPlating,
					pkg_pwr_plating: formData.pkgPwrPlating,
					outer_coating_material: formData.outerCoatingMaterial
				}),

				headers: {
					'Content-Type': 'application/json'
				}
			}
		);

		compData = await response.json();
		loading = !loading;
		updatePadstackTable();
	}

	function loadFromLayout() {
		fileExplorerParamsStore.set({ loadFileType: 'spd', gotoRoute: '/load-spd' });
		invalidateAll();
	}

	function setFileType(ftype, route) {
		fileExplorerParamsStore.set({ loadFileType: ftype, gotoRoute: route });
	}

	const convertUnit = (val, preUnit) => {
		if (!val) return '';
		return (val * unitConv[preUnit]) / unitConv[unit];
	};

	function updateLayer(propName, propVal) {
		if (propVal === 'Default' || propVal === null) return;

		let newProps = [];
		for (let idx = 0; idx < compData[propName].length; idx++) {
			newProps.push(propVal);
		}
		compData[propName] = newProps;
	}

	function updatePadstackTable() {
		updateLayer('Inner fill material', formData.innerFillMaterial);
		updateLayer(`Outer coating thickness [${unit}]`, formData.outerThickness);
		updateLayer('Outer coating material', formData.outerCoatingMaterial);
	}

	let tableWidth = 9;
	function toggleForm() {
		if (tableWidth === 9) {
			tableWidth = 12;
		} else {
			tableWidth = 9;
		}
	}

	$: if ($materialDataStore === undefined) {
		materialNames = ['', 'Default'];
	} else {
		materialNames = ['', 'Default', ...Object.keys($materialDataStore)];
	}

	$: {
		const data = {};
		let preUnit;
		let headerWoUnit;
		for (let [header, values] of Object.entries(compData)) {
			if (header.includes('[') && !header.includes('Conductivity')) {
				preUnit = Object.keys(compData)[2].split('[')[1].slice(0, -1);
				headerWoUnit = header.split(' [')[0];
				data[`${headerWoUnit} [${unit}]`] = compData[header].map((item) =>
					convertUnit(item, preUnit)
				);
			} else {
				data[header] = values;
			}
		}
		compData = data;
	}

	$: formData.csvFileName = $padstackFileStore;

	// Form validation
	$: {
		if (formData.csvFileName !== null) {
			formData.csvFileName.split('.').slice(-1)[0] === 'csv'
				? (formValidation.csvFileName = 'valid')
				: (formValidation.csvFileName = 'is-invalid');
		}

		formData.conduct < 0
			? (formValidation.conduct = 'is-invalid')
			: (formValidation.conduct = 'invalid');

		formData.brdPlating < 0
			? (formValidation.brdPlating = 'is-invalid')
			: (formValidation.brdPlating = 'invalid');

		formData.pkgGndPlating < 0
			? (formValidation.pkgGndPlating = 'is-invalid')
			: (formValidation.pkgGndPlating = 'invalid');

		formData.pkgPwrPlating < 0
			? (formValidation.pkgPwrPlating = 'is-invalid')
			: (formValidation.pkgPwrPlating = 'invalid');

		formData.outerThickness < 0
			? (formValidation.outerThickness = 'is-invalid')
			: (formValidation.outerThickness = 'invalid');
	}

	$: for (let fieldValid of Object.values(formValidation).slice(1)) {
		if (fieldValid === 'is-invalid') {
			formSubmitDisabled = true;
			break;
		} else formSubmitDisabled = false;
	}
</script>

<div class="toast-container position-fixed bottom-0 end-0 p-3">
	<div bind:this={toastElem} class="toast text-bg-success" role="alert" aria-live="assertive" aria-atomic="true">
		<div class="toast-header">
			<strong class="me-auto">Padstack message</strong>
			<button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
		</div>
		<div class="toast-body">Layout padstack has been updated</div>
	</div>
</div>

<div class="container text-center pt-3">
	<div class="row justify-content-start">
		<div class="col col-{tableWidth}">
			<div class="card">
				<div class="card-header d-flex flex-row">
					<button
						on:click={() => {
							setFileType('csv', '/create-padstack');
						}}
						data-bs-toggle="modal"
						data-bs-target="#file-list"
						type="button"
						class="btn btn-sm btn-primary mx-1 float-left">Load csv file</button
					>
					<button
						on:click={savePadstack}
						type="button"
						class="btn btn-sm btn-primary mx-1"
						disabled={formValidation.csvFileName === 'is-invalid'}>Save csv file</button
					>
					<button on:click={loadFromLayout} type="button" class="btn btn-sm btn-secondary mx-1"
						>Reload from layout</button
					>
					<button
						on:click={applyToLayout}
						type="button"
						class="btn btn-sm btn-secondary mx-1"
						disabled={formValidation.csvFileName === 'is-invalid'}>Apply to layout</button
					>
					<button on:click={toggleForm} type="button" class="btn btn-sm btn-secondary mx-1 ms-auto">
						<i class="bi bi-arrows-expand-vertical"></i>
					</button>
				</div>
				<div class="card-body display-height py-0">
					<EditPadstackTable {compData} />
				</div>
			</div>
		</div>

		{#if tableWidth === 9}
			<div class="col col-3">
				<div class="card">
					<div class="card-header">
						<button
							on:click={updatePadstack}
							type="button"
							class="btn btn-sm btn-secondary mx-1"
							disabled={formSubmitDisabled}
							>{#if loading}
								<div class="spinner-border spinner-border-sm" role="status"></div>
							{/if} Update padstack</button
						>
					</div>
					<div class="card-body display-height">
						<div class="form-floating py-1">
							<select bind:value={unit} class="form-select" id="unitSelect">
								<option value="nm">nm</option>
								<option value="um">um</option>
								<option value="mm">mm</option>
								<option value="cm">cm</option>
								<option value="m">m</option>
								<option value="mil">mil</option>
								<option value="inch">inch</option>
							</select>
							<label for="unitSelect">Select unit</label>
						</div>

						<form class="form-floating py-1">
							<input
								bind:value={formData.csvFileName}
								type="text"
								class="form-control {formValidation.csvFileName}"
								id="csvFileName"
								placeholder="csvFileName"
								required
							/>
							<label for="csvFileName">Padstack csv file name</label>
						</form>
						<hr />

						<div class="form-floating py-1">
							<select bind:value={formData.layoutType} class="form-select" id="layoutType">
								<option value="board">Board</option>
								<option value="package">Package</option>
							</select>
							<label for="layoutType">Select layout type</label>
						</div>

						{#if formData.layoutType === 'board'}
							<form class="form-floating py-1">
								<input
									bind:value={formData.brdPlating}
									type="number"
									class="form-control {formValidation.brdPlating}"
									id="brdPlating"
									placeholder="brdPlating"
								/>
								<label for="brdPlating">{`Board via plating [${unit}]`}</label>
							</form>
						{:else}
							<form class="form-floating py-1">
								<input
									bind:value={formData.pkgGndPlating}
									type="number"
									class="form-control {formValidation.pkgGndPlating}"
									id="pkgGndPlating"
									placeholder="pkgGndPlating"
								/>
								<label for="pkgGndPlating">{`Package ground PTH plating [${unit}]`}</label>
							</form>

							<form class="form-floating py-1">
								<input
									bind:value={formData.pkgPwrPlating}
									type="number"
									class="form-control {formValidation.pkgPwrPlating}"
									id="pkgPwrPlating"
									placeholder="pkgPwrPlating"
								/>
								<label for="pkgPwrPlating">{`Package power PTH plating [${unit}]`}</label>
							</form>
						{/if}

						<div class="form-floating py-1">
							<select bind:value={formData.material} class="form-select" id="material">
								{#each materialNames as name (name)}
									<option value={name}>{name}</option>
								{/each}
							</select>
							<label for="material">Via material</label>
						</div>

						<form class="form-floating py-1">
							<input
								bind:value={formData.conduct}
								type="number"
								class="form-control {formValidation.conduct}"
								id="conduct"
								placeholder="conduct"
							/>
							<label for="conduct">Via conductivity [S/m]</label>
						</form>
						<hr />

						<div class="form-floating py-1">
							<select
								bind:value={formData.innerFillMaterial}
								class="form-select"
								id="innerFillMaterial"
							>
								{#each materialNames as name (name)}
									<option value={name}>{name}</option>
								{/each}
							</select>
							<label for="innerFillMaterial">Inner fill material</label>
						</div>

						<form class="form-floating py-1">
							<input
								bind:value={formData.outerThickness}
								type="number"
								class="form-control {formValidation.outerThickness}"
								id="outerThickness"
								placeholder="outerThickness"
							/>
							<label for="outerThickness">{`Outer coating thickness [${unit}]`}</label>
						</form>

						<div class="form-floating py-1">
							<select
								bind:value={formData.outerCoatingMaterial}
								class="form-select"
								id="outerCoatingMaterial"
							>
								{#each materialNames as name (name)}
									<option value={name}>{name}</option>
								{/each}
							</select>
							<label for="outerCoatingMaterial">Outer coating material</label>
						</div>
					</div>
				</div>
			</div>
		{/if}
	</div>
</div>

<style>
	.display-height {
		height: 630px;
		overflow: auto;
	}

	/* Chrome, Safari, Edge, Opera */
	input::-webkit-outer-spin-button,
	input::-webkit-inner-spin-button {
		-webkit-appearance: none;
		margin: 0;
	}
</style>
