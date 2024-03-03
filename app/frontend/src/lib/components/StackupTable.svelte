<script>
	import EditStackupTable from '$lib/components/EditStackupTable.svelte';
	import { materialDataStore, materialFileStore } from '../../store/stores.js';
	import { selectedServerInfoStore, fileExplorerParamsStore } from '../../store/stores.js';
	import { activeLayoutStore, stackupFileStore } from '../../store/stores.js';
	import { invalidateAll } from '$app/navigation';
	import { onMount } from 'svelte';

	export let compData;
	let unit = Object.keys(compData)[1].split('[')[1].slice(0, -1);
	let unitConv = { nm: 1e-9, um: 1e-6, mm: 1e-3, cm: 1e-2, m: 1, mil: 2.54e-5, inch: 0.0254 };
	let materialNames;
	let formData = {
		csvFileName: $stackupFileStore,
		dielectricThickness: null,
		metalThickness: null,
		conduct: null,
		coreThickness: null,
		er: null,
		fillin_er: null,
		lossTan: null,
		fillin_lossTan: null,
		dielectMaterial: 'Default',
		metalMaterial: 'Default',
		coreMaterial: 'Default',
		fillinDielectMaterial: 'Default'
	}
	let formSubmitDisabled = false;
	let formValidation = {
		csvFileName: 'is-invalid',
		dielectricThickness: 'valid',
		metalThickness: 'valid',
		conduct: 'valid',
		coreThickness: 'valid',
		er: 'valid',
		fillin_er: 'valid',
		lossTan: 'valid',
		fillin_lossTan: 'valid'
	}

	let isCore;
	let coreLayerName;
	let toastElem;

	$: {
		isCore = false;
		for (const [idx, layer] of compData['Layer Name'].entries()) {
			if (layer.includes('fco')) {
				isCore = true;
				coreLayerName = compData['Layer Name'][idx + 1];
			}
		}
	}

	$: {
		formData.csvFileName = $stackupFileStore;
		invalidateAll();
	}

	async function saveStackup() {
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
		saveStackup();
		await fetch(
			`http://${$selectedServerInfoStore.ip_address}:${$selectedServerInfoStore.port}/apply-stackup`,
			{
				method: 'POST',
				body: JSON.stringify({
					spd_fname: $activeLayoutStore,
					stackup_fname: formData.csvFileName,
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

	function loadFromLayout() {
		fileExplorerParamsStore.set({ loadFileType: 'spd', gotoRoute: '/load-spd' });
		invalidateAll();
	}

	function updateLayer(propName, propVal, layerTypes) {
		if (propVal === 'Default' || propVal === null) return;

		let newProps = compData[propName];
		let layerNames = compData['Layer Name'];

		for (const [idx, layerName] of layerNames.entries()) {
			let checkLayerTypes = [];
			layerTypes.forEach((elem) => checkLayerTypes.push(layerName.includes(elem)));
			if (checkLayerTypes.includes(true)) {
				if (propName === 'Conductivity [S/m]' && compData['Material'][idx] !== '' && propVal !== '')
					continue;
				if (
					(propName === 'Er' || propName === 'Loss Tangent') &&
					layerName.includes('Medium') &&
					compData['Material'][idx] !== '' &&
					propVal !== ''
				)
					continue;
				if (
					(propName === 'Er' || propName === 'Loss Tangent') &&
					compData['Fill-in Dielectric'][idx] !== '' &&
					propVal !== ''
				)
					continue;

				newProps[idx] = propVal;
			}
		}
		compData[propName] = newProps;
	}

	function updateStackupTable() {
		updateLayer(`Thickness [${unit}]`, formData.dielectricThickness, ['Medium']);
		updateLayer(`Thickness [${unit}]`, formData.metalThickness, ['Signal', 'Plane']);

		updateLayer('Material', formData.dielectMaterial, ['Medium']);
		updateLayer('Material', formData.metalMaterial, ['Signal', 'Plane']);

		if (formData.conduct === 0) {
			updateLayer('Conductivity [S/m]', '', ['Signal', 'Plane']);
		} else {
			updateLayer('Conductivity [S/m]', formData.conduct, ['Signal', 'Plane']);
		}

		if (formData.er === 0) {
			updateLayer('Er', '', ['Medium']);
		} else updateLayer('Er', formData.er, ['Medium']);
		if (formData.fillin_er === 0) {
			updateLayer('Er', '', ['Signal', 'Plane']);
		} else updateLayer('Er', formData.fillin_er, ['Signal', 'Plane']);

		if (formData.lossTan === 0) {
			updateLayer('Loss Tangent', '', ['Medium']);
		} else {
			updateLayer('Loss Tangent', formData.lossTan, ['Medium']);
		}
		if (formData.fillin_lossTan === 0) {
			updateLayer('Loss Tangent', '', ['Signal', 'Plane']);
		} else {
			updateLayer('Loss Tangent', formData.fillin_lossTan, ['Signal', 'Plane']);
		}

		updateLayer('Fill-in Dielectric', formData.fillinDielectMaterial, ['Signal', 'Plane']);

		if (isCore) {
			updateLayer(`Thickness [${unit}]`, formData.coreThickness, [coreLayerName]);
			updateLayer('Material', formData.coreMaterial, [coreLayerName]);
		}
	}

	function setFileType(ftype, route) {
		fileExplorerParamsStore.set({ loadFileType: ftype, gotoRoute: route });
	}

	const convertUnit = (val, preUnit) => {
		return (val * unitConv[preUnit]) / unitConv[unit];
	};

	$: if ($materialDataStore === undefined) {
		materialNames = ['', 'Default'];
	} else {
		materialNames = ['', 'Default', ...Object.keys($materialDataStore)];
	}

	$: {
		let layerThickness = `Thickness [${unit}]`;
		const data = {};
		let preUnit;
		for (let [header, values] of Object.entries(compData)) {
			if (header.includes('Thickness')) {
				preUnit = Object.keys(compData)[1].split('[')[1].slice(0, -1);
				values = values.map((item) => convertUnit(item, preUnit));
				data[layerThickness] = values;
			} else {
				data[header] = values;
			}
		}
		compData = data;

		for (let prop of ['dielectricThickness', 'metalThickness', 'coreThickness']) {
			if (formData[prop] !== null) {
				formData[prop] = convertUnit(formData[prop], preUnit);
			}
		}
	}

	// Form validation
	$: {
		formData.csvFileName.split('.').slice(-1)[0] === 'csv'
			? (formValidation.csvFileName = 'valid')
			: (formValidation.csvFileName = 'is-invalid');

		formData.dielectricThickness < 0
			? (formValidation.dielectricThickness = 'is-invalid')
			: (formValidation.dielectricThickness = 'invalid');

		formData.metalThickness < 0
			? (formValidation.metalThickness = 'is-invalid')
			: (formValidation.metalThickness = 'invalid');

		formData.coreThickness < 0
			? (formValidation.coreThickness = 'is-invalid')
			: (formValidation.coreThickness = 'invalid');

		formData.conduct < 0
			? (formValidation.conduct = 'is-invalid')
			: (formValidation.conduct = 'invalid');

		formData.er !== null && (formData.er < 1 || formData.er > 20) && formData.er !== 0
			? (formValidation.er = 'is-invalid')
			: (formValidation.er = 'invalid');

		formData.fillin_er !== null &&
		(formData.fillin_er < 1 || formData.fillin_er > 20) &&
		formData.fillin_er !== 0
			? (formValidation.fillin_er = 'is-invalid')
			: (formValidation.fillin_er = 'invalid');

		formData.lossTan < 0 || formData.lossTan > 0.2
			? (formValidation.lossTan = 'is-invalid')
			: (formValidation.lossTan = 'invalid');

		formData.fillin_lossTan < 0 || formData.fillin_lossTan > 0.2
			? (formValidation.fillin_lossTan = 'is-invalid')
			: (formValidation.fillin_lossTan = 'invalid');
	}

	$: for (let fieldValid of Object.values(formValidation).slice(1)) {
		if (fieldValid === 'is-invalid') {
			formSubmitDisabled = true;
			break;
		} else formSubmitDisabled = false;
	}

	onMount(() => {
		document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach((tooltip) => {
			new bootstrap.Tooltip(tooltip);
		});
	});
</script>

<div class="toast-container position-fixed bottom-0 end-0 p-3">
	<div bind:this={toastElem} class="toast text-bg-success" role="alert" aria-live="assertive" aria-atomic="true">
		<div class="toast-header">
			<strong class="me-auto">Stackup message</strong>
			<button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
		</div>
		<div class="toast-body">Layout stackup has been updated</div>
	</div>
</div>

<div class="container text-center pt-3">
	<div class="row justify-content-start">
		<div class="col col-9">
			<div class="card">
				<div class="card-header d-flex flex-row">
					<button
						on:click={() => {
							setFileType('csv', '/create-stackup');
						}}
						data-bs-toggle="modal"
						data-bs-target="#file-list"
						type="button"
						class="btn btn-sm btn-primary mx-1">Load csv file</button
					>
					<button
						on:click={saveStackup}
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
				</div>
				<div class="card-body display-height py-0">
					<EditStackupTable {compData} />
				</div>
			</div>
		</div>
		<div class="col col-3">
			<div class="card">
				<div class="card-header">
					<button
						on:click={updateStackupTable}
						type="button"
						class="btn btn-sm btn-secondary mx-1"
						disabled={formSubmitDisabled}>Update stackup</button
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
						<label for="csvFileName">Stackup csv file name</label>
					</form>
					<hr />

					<form class="form-floating py-1">
						<input
							bind:value={formData.dielectricThickness}
							type="number"
							class="form-control {formValidation.dielectricThickness}"
							id="dielectricThickness"
							placeholder="dielectricThickness"
						/>
						<label for="dielectricThickness">{`Dielectric layer thickness [${unit}]`}</label>
					</form>

					<form class="form-floating py-1">
						<input
							bind:value={formData.metalThickness}
							type="number"
							class="form-control {formValidation.metalThickness}"
							id="metalThickness"
							placeholder="metalThickness"
						/>
						<label for="metalThickness">{`Metal layer thickness [${unit}]`}</label>
					</form>

					{#if isCore}
						<form class="form-floating py-1">
							<input
								bind:value={formData.coreThickness}
								type="number"
								class="form-control {formValidation.coreThickness}"
								id="conduct"
								placeholder="coreThickness"
							/>
							<label for="coreThickness">{`Core layer thickness [${unit}]`}</label>
						</form>
					{/if}
					<hr />

					<div class="input-group">
						<div class="form-floating py-1">
							<input
								bind:value={formData.conduct}
								type="number"
								class="form-control {formValidation.conduct}"
								id="conduct"
								placeholder="conduct"
							/>
							<label for="conduct">Metal layer conductivity [S/m]</label>
						</div>
						<span
							class="input-group-text my-1"
							data-bs-toggle="tooltip"
							data-bs-placement="right"
							data-bs-title="Use 0 to clear"><i class="bi bi-question-circle"></i></span
						>
					</div>

					<div class="input-group">
						<div class="form-floating py-1">
							<input
								bind:value={formData.er}
								type="number"
								class="form-control {formValidation.er}"
								id="er"
								placeholder="er"
							/>
							<label for="er">Dielectric layer permittivity Er</label>
						</div>
						<span
							class="input-group-text my-1"
							data-bs-toggle="tooltip"
							data-bs-placement="right"
							data-bs-html="true"
							data-bs-title="Use 0 to clear <br> Valid range [1, 20]"
							><i class="bi bi-question-circle"></i></span
						>
					</div>

					<div class="input-group">
						<div class="form-floating py-1">
							<input
								bind:value={formData.fillin_er}
								type="number"
								class="form-control {formValidation.fillin_er}"
								id="fillin_er"
								placeholder="fillin_er"
							/>
							<label for="fillin_er">Fill-in dielectric permittivity Er</label>
						</div>
						<span
							class="input-group-text my-1"
							data-bs-toggle="tooltip"
							data-bs-placement="right"
							data-bs-html="true"
							data-bs-title="Use 0 to clear <br> Valid range [1, 20]"
							><i class="bi bi-question-circle"></i></span
						>
					</div>

					<div class="input-group">
						<div class="form-floating py-1">
							<input
								bind:value={formData.lossTan}
								type="number"
								class="form-control {formValidation.lossTan}"
								id="lossTan"
								placeholder="lossTan"
							/>
							<label for="lossTan">Dielectric layer loss tangent</label>
						</div>
						<span
							class="input-group-text my-1"
							data-bs-toggle="tooltip"
							data-bs-placement="right"
							data-bs-html="true"
							data-bs-title="Use 0 to clear <br> Valid range [0, 0.2]"
							><i class="bi bi-question-circle"></i></span
						>
					</div>

					<div class="input-group">
						<div class="form-floating py-1">
							<input
								bind:value={formData.fillin_lossTan}
								type="number"
								class="form-control {formValidation.fillin_lossTan}"
								id="fillin_lossTan"
								placeholder="fillin_lossTan"
							/>
							<label for="fillin_lossTan">Fill-in dielectric loss tangent</label>
						</div>
						<span
							class="input-group-text my-1"
							data-bs-toggle="tooltip"
							data-bs-placement="right"
							data-bs-html="true"
							data-bs-title="Use 0 to clear <br> Valid range [0, 0.2]"
							><i class="bi bi-question-circle"></i></span
						>
					</div>
					<hr />

					<div class="form-floating py-1">
						<select bind:value={formData.dielectMaterial} class="form-select" id="dielectMaterial">
							{#each materialNames as name (name)}
								<option value={name}>{name}</option>
							{/each}
						</select>
						<label for="dielectMaterial">Dielectric layer material</label>
					</div>

					<div class="form-floating py-1">
						<select bind:value={formData.metalMaterial} class="form-select" id="metalMaterial">
							{#each materialNames as name (name)}
								<option value={name}>{name}</option>
							{/each}
						</select>
						<label for="metalMaterial">Metal layer material</label>
					</div>

					<div class="form-floating py-1">
						<select
							bind:value={formData.fillinDielectMaterial}
							class="form-select"
							id="fillinDielectMaterial"
						>
							{#each materialNames as name (name)}
								<option value={name}>{name}</option>
							{/each}
						</select>
						<label for="fillinDielectMaterial">Fill-in dielectric material</label>
					</div>
					{#if isCore}
						<div class="form-floating py-1">
							<select bind:value={formData.coreMaterial} class="form-select" id="coreMaterial">
								{#each materialNames as name (name)}
									<option value={name}>{name}</option>
								{/each}
							</select>
							<label for="coreMaterial">Core layer material</label>
						</div>
					{/if}
				</div>
			</div>
		</div>
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
