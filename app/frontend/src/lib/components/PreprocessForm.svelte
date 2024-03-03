<script>
	import { onMount } from 'svelte';
	import { createEventDispatcher } from 'svelte';
	import { stackupFileStore, padstackFileStore, materialFileStore } from '../../store/stores.js';
    import { preprocessFormStore } from '../../store/formState.js';
    import { beforeNavigate } from '$app/navigation';

	export let netsToReport = $preprocessFormStore.netsToReport;
	export let gndNetName = $preprocessFormStore.gndNetName;
	export let preprocessStatus = $preprocessFormStore.preprocessStatus;
	let formSubmitDisabled = $preprocessFormStore.formSubmitDisabled;
	let formData = {
		stackupFname: $preprocessFormStore.stackupFname,
		padstackFname: $preprocessFormStore.padstackFname,
		materialFname: $preprocessFormStore.materialFname,
		processedFname: $preprocessFormStore.processedFname,
		defaultConduct: $preprocessFormStore.defaultConduct,
		cutMargin: $preprocessFormStore.cutMargin,
		deleteUnusedNets: $preprocessFormStore.deleteUnusedNets
	};
    let dispatch = createEventDispatcher();

    beforeNavigate (() => {
        preprocessFormStore.set({...formData, ...{netsToReport, gndNetName, preprocessStatus}});
    })

	let formValidation = {
		stackupFname: 'valid',
		padstackFname: 'valid',
		materialFname: 'valid',
		processedFname: 'valid',
		defaultConduct: 'valid',
		cutMargin: 'valid'
	};

	$: {
		if ($stackupFileStore !== '') formData.stackupFname = $stackupFileStore;
		if ($padstackFileStore !== '') formData.padstackFname = $padstackFileStore;
        if ($materialFileStore !== '') formData.materialFname = $materialFileStore;
	}

	// Form validation
	$: {
		formData.stackupFname === '' || formData.stackupFname.split('.').slice(-1)[0] === 'csv'
			? (formValidation.stackupFname = 'valid')
			: (formValidation.stackupFname = 'is-invalid');

		formData.padstackFname === '' || formData.padstackFname.split('.').slice(-1)[0] === 'csv'
			? (formValidation.padstackFname = 'valid')
			: (formValidation.padstackFname = 'is-invalid');

		formData.materialFname === '' || formData.materialFname.split('.').slice(-1)[0] === 'txt'
			? (formValidation.materialFname = 'valid')
			: (formValidation.materialFname = 'is-invalid');

		formData.processedFname === '' || formData.processedFname.split('.').slice(-1)[0] === 'spd'
			? (formValidation.processedFname = 'valid')
			: (formValidation.processedFname = 'is-invalid');

		formData.cutMargin >= 0 && formData.cutMargin !== null
			? (formValidation.cutMargin = 'valid')
			: (formValidation.cutMargin = 'is-invalid');

		formValidation.materialFname === 'valid' &&
		((formData.materialFname !== '' && formData.defaultConduct === null) ||
			formData.defaultConduct > 0)
			? (formValidation.defaultConduct = 'valid')
			: (formValidation.defaultConduct = 'is-invalid');

		for (let fieldValid of Object.values(formValidation).slice(1)) {
			if (fieldValid === 'is-invalid') {
				formSubmitDisabled = true;
				break;
			} else formSubmitDisabled = false;
		}
	}

	onMount(() => {
		document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach((tooltip) => {
			new bootstrap.Tooltip(tooltip);
		});
	});
</script>

<form class="row">
	<div class="col-1"></div>
	<div class="col-5 pb-4">
		<form class="form-floating pt-3">
			<input
				type="text"
				class="form-control {formValidation.stackupFname}"
				id="stackupFname"
				bind:value={formData.stackupFname}
			/>
			<label for="stackupFname">Stackup csv file name</label>
		</form>
	</div>
	<div class="col-5">
		<form class="form-floating pt-3">
			<input
				type="text"
				class="form-control {formValidation.padstackFname}"
				id="padstackFname"
				bind:value={formData.padstackFname}
			/>
			<label for="padstackFname">Padstack csv file name</label>
		</form>
	</div>
	<div class="col-1"></div>

	<div class="col-1"></div>
	<div class="col-5 pb-4">
		<form class="form-floating pt-3">
			<input
				type="text"
				class="form-control {formValidation.materialFname}"
				id="materialFname"
				bind:value={formData.materialFname}
			/>
			<label for="materialFname">Material txt file name</label>
		</form>
	</div>
	<div class="col-5">
		<div class="input-group">
			<form class="form-floating pt-3">
				<input
					type="text"
					class="form-control {formValidation.processedFname}"
					id="processedFname"
					bind:value={formData.processedFname}
				/>
				<label for="processedFname">Processed spd file name</label>
			</form>
			<span
				class="input-group-text mt-3"
				data-bs-toggle="tooltip"
				data-bs-placement="right"
				data-bs-html="true"
				data-bs-title="If not provided, the current layout file will be preprocessed"
				><i class="bi bi-question-circle"></i></span
			>
		</div>
	</div>
	<div class="col-1"></div>

	<div class="col-1"></div>
	<div class="col-4">
		<div class="input-group">
			<form class="form-floating pt-3">
				<input
					type="number"
					class="form-control {formValidation.cutMargin}"
					id="cut_margin"
					bind:value={formData.cutMargin}
				/>
				<label for="cut_margin">Layout cut margin [mm]</label>
			</form>
			<span
				class="input-group-text mt-3"
				data-bs-toggle="tooltip"
				data-bs-placement="bottom"
				data-bs-html="true"
				data-bs-title="Use 0 to avoid layout cut"><i class="bi bi-question-circle"></i></span
			>
		</div>
	</div>
	<div class="col-4">
		<div class="input-group">
			<form class="form-floating pt-3">
				<input
					type="number"
					class="form-control {formValidation.defaultConduct}"
					id="defaultConduct"
					bind:value={formData.defaultConduct}
				/>
				<label for="defaultConduct">Default conductivity [S/m]</label>
			</form>
			<span
				class="input-group-text mt-3"
				data-bs-toggle="tooltip"
				data-bs-placement="bottom"
				data-bs-html="true"
				data-bs-title="Mandatory only if material file is not specified"
				><i class="bi bi-question-circle"></i></span
			>
		</div>
	</div>
	<div class="col-2">
		<form class="form-floating pt-3">
			<select class="form-select" id="floatingSelect" bind:value={formData.deleteUnusedNets}>
				<option value={false}>No</option>
				<option value={true}>Yes</option>
			</select>
			<label for="floatingSelect">Delete unused nets</label>
		</form>
	</div>
	<div class="col-1"></div>

	<div class="col-12 position-relative mt-5 pt-5">
		<button
			on:click={() => {
				dispatch('preprocess-layout', formData);
			}}
			type="button"
			class="btn btn btn-primary position-absolute start-50 translate-middle"
			disabled={formSubmitDisabled || netsToReport.length === 0 || !gndNetName || preprocessStatus}
		>
			{#if preprocessStatus}
				<span class="spinner-border spinner-border-sm" aria-hidden="true"></span>
			{/if}
			<span role="status">Preprocess</span>
		</button>
	</div>
</form>

<style>
	/* Chrome, Safari, Edge, Opera */
	input::-webkit-outer-spin-button,
	input::-webkit-inner-spin-button {
		-webkit-appearance: none;
		margin: 0;
	}
</style>
