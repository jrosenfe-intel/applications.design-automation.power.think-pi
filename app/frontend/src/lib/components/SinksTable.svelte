<script>
	import EditSinksTable from '$lib/components/EditSinksTable.svelte';
	import { selectedServerInfoStore, activeLayoutStore } from '../../store/stores.js';
	import { sinksFileStore, fileExplorerParamsStore } from '../../store/stores.js';
	import { invalidateAll } from '$app/navigation';
	import { onMount } from 'svelte';

	export let compData;

	let formData = {
		csvFileName: $sinksFileStore,
		startIdx: null,
		endIdx: null,
		newSinkName: null,
		countStart: null,
		current: null,
		voltage: null,
		model: 'Equal current'
	};
	let formSubmitDisabled = false;
	let formValidation = {
		csvFileName: 'is-invalid',
		startIdx: 'valid',
		endIdx: 'valid',
		newSinkName: 'valid',
		countStart: 'valid',
		current: 'valid',
		voltage: 'valid',
		model: 'valid'
	};
	let toastElem;

	function updateLayer(propName, propVal, startIdx, endIdx) {
		let newProps = compData[propName];

		if (startIdx === null) startIdx = 0;
		if (endIdx === null) endIdx = compData[propName].length - 1;

		let nameIdx = formData.countStart === null ? 0 : formData.countStart;
		for (let idx in newProps) {
			if (idx >= startIdx && idx <= endIdx) {
				if (propName === 'New name' && propVal !== null) {
					newProps[idx] = propVal + nameIdx++;
				} else {
					newProps[idx] = propVal;
				}
			}
		}
		compData[propName] = newProps;
	}

	function updateSinksTable() {
		if (formData.newSinkName === '0') {
			updateLayer('New name', null, formData.startIdx, formData.endIdx);
		} else if (formData.newSinkName !== '') {
			updateLayer('New name', formData.newSinkName, formData.startIdx, formData.endIdx);
		}
		if (formData.current !== null) {
			updateLayer('Current [A]', formData.current, formData.startIdx, formData.endIdx);
		}
		if (formData.voltage !== null) {
			updateLayer('Nominal Voltage [V]', formData.voltage, formData.startIdx, formData.endIdx);
		}

		updateLayer('Model', formData.model, formData.startIdx, formData.endIdx);
	}

	function setFileType(ftype, route) {
		fileExplorerParamsStore.set({ loadFileType: ftype, gotoRoute: route });
	}

	// Form validation
	$: {
		formData.csvFileName.split('.').slice(-1)[0] === 'csv'
			? (formValidation.csvFileName = 'valid')
			: (formValidation.csvFileName = 'is-invalid');

		formData.startIdx >= 0 &&
		compData.Name !== undefined &&
		formData.startIdx <= compData.Name.length - 1
			? (formValidation.startIdx = 'valid')
			: (formValidation.startIdx = 'is-invalid');

		formData.endIdx >= 0 &&
		compData.Name !== undefined &&
		formData.endIdx <= compData.Name.length - 1
			? (formValidation.endIdx = 'valid')
			: (formValidation.endIdx = 'is-invalid');

		formData.countStart >= 0
			? (formValidation.countStart = 'valid')
			: (formValidation.countStart = 'is-invalid');

		formData.current >= 0
			? (formValidation.current = 'valid')
			: (formValidation.current = 'is-invalid');

		formData.voltage >= 0
			? (formValidation.voltage = 'valid')
			: (formValidation.voltage = 'is-invalid');
	}

	$: for (let fieldValid of Object.values(formValidation).slice(1)) {
		if (fieldValid === 'is-invalid') {
			formSubmitDisabled = true;
			break;
		} else formSubmitDisabled = false;
	}

	$: {
		if ($sinksFileStore !== '') {
			formData.csvFileName = $sinksFileStore;
			invalidateAll();
		}
	}

	async function saveSinkSetup() {
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

	function loadFromLayout() {
		sinksFileStore.set('');
		invalidateAll();
	}

	async function applyToLayout() {
		await fetch(
			`http://${$selectedServerInfoStore.ip_address}:${$selectedServerInfoStore.port}/modify-sink-info`,
			{
				method: 'POST',
				body: JSON.stringify({
					layout_fname: $activeLayoutStore,
					csv_fname: formData.csvFileName,
					sink_info: compData
				}),
				headers: {
					'Content-Type': 'application/json'
				}
			}
		);

		const toastBootstrap = bootstrap.Toast.getOrCreateInstance(toastElem);
		toastBootstrap.show();
	}

	onMount(() => {
		document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach((tooltip) => {
			new bootstrap.Tooltip(tooltip);
		});
	});
</script>

<div class="toast-container position-fixed bottom-0 end-0 p-3">
	<div
		bind:this={toastElem}
		class="toast text-bg-success"
		role="alert"
		aria-live="assertive"
		aria-atomic="true"
	>
		<div class="toast-header">
			<strong class="me-auto">Sink setup message</strong>
			<button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
		</div>
		<div class="toast-body">Layout sinks have been successfully updated</div>
	</div>
</div>

<div class="container text-center pt-3">
	<div class="row justify-content-start">
		<div class="col col-9">
			<div class="card">
				<div class="card-header d-flex flex-row">
					<button
						on:click={() => {
							setFileType('csv', '/sink-setup');
						}}
						data-bs-toggle="modal"
						data-bs-target="#file-list"
						type="button"
						class="btn btn-sm btn-primary mx-1">Load csv file</button
					>
					<button
						on:click={saveSinkSetup}
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
					<EditSinksTable {compData} />
				</div>
			</div>
		</div>
		<div class="col col-3">
			<div class="card">
				<div class="card-header">
					<button
						on:click={updateSinksTable}
						type="button"
						class="btn btn-sm btn-secondary mx-1"
						disabled={formSubmitDisabled}>Update sinks</button
					>
				</div>
				<div class="card-body display-height">
					<form class="form-floating py-1">
						<input
							bind:value={formData.csvFileName}
							type="text"
							class="form-control {formValidation.csvFileName}"
							id="csvFileName"
							placeholder="csvFileName"
							required
						/>
						<label for="csvFileName">Sinks csv file name</label>
					</form>
					<hr />

					<div class="row">
						<div class="col-6">
							<form class="form-floating py-1">
								<input
									bind:value={formData.startIdx}
									type="number"
									class="form-control {formValidation.startIdx}"
									id="startIdx"
									placeholder="startIdx"
									required
								/>
								<label for="startIdx">Start index</label>
							</form>
						</div>
						<div class="col-6">
							<form class="form-floating py-1">
								<input
									bind:value={formData.endIdx}
									type="number"
									class="form-control {formValidation.endIdx}"
									id="endIdx"
									placeholder="endIdx"
									required
								/>
								<label for="endIdx">End index</label>
							</form>
						</div>
					</div>

					<div class="row">
						<div class="col-7">
							<div class="input-group">
								<form class="form-floating py-1">
									<input
										bind:value={formData.newSinkName}
										type="text"
										class="form-control"
										id="newPortName"
										placeholder="newPortName"
									/>
									<label for="newPortName">New name</label>
								</form>
								<span
									class="input-group-text my-1"
									data-bs-toggle="tooltip"
									data-bs-placement="right"
									data-bs-title="Use 0 to clear"><i class="bi bi-question-circle"></i></span
								>
							</div>
						</div>
						<div class="col-5">
							<form class="form-floating py-1">
								<input
									bind:value={formData.countStart}
									type="number"
									class="form-control {formValidation.countStart}"
									id="newPortName"
									placeholder="newPortName"
								/>
								<label for="newPortName">Count start</label>
							</form>
						</div>
					</div>

					<div class="row">
						<div class="col-6">
							<form class="form-floating py-1">
								<input
									bind:value={formData.current}
									type="number"
									class="form-control {formValidation.current}"
									id="current"
									placeholder="current"
								/>
								<label for="current">Current [A]</label>
							</form>
						</div>

						<div class="col-6">
							<form class="form-floating py-1">
								<input
									bind:value={formData.voltage}
									type="number"
									class="form-control {formValidation.voltage}"
									id="voltage"
									placeholder="voltage"
								/>
								<label for="voltage">Voltage [V]</label>
							</form>
						</div>
					</div>

					<div class="form-floating py-1">
						<select bind:value={formData.model} class="form-select" id="modelSelect">
							<option value="Equal current">Equal current</option>
							<option value="Equal voltage">Equal voltage</option>
							<option value="Unequal current">Unequal current</option>
						</select>
						<label for="modelSelect">Select model</label>
					</div>
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
