<script>
    import { selectedServerInfoStore } from '../../store/stores.js'
    import { activeLayoutStore } from '../../store/stores.js';
	import { preprocessFormStore } from '../../store/formState.js';
	import NetSelect from '$lib/components/NetSelect.svelte';
	import NetDisplay from '$lib/components/NetDisplay.svelte';
	import PreprocessForm from '$lib/components/PreprocessForm.svelte';
	
	let copiedNetNames;
    let selectedNetType;
    let gndNetName = $preprocessFormStore.gndNetName;
	let netsToReport = $preprocessFormStore.netsToReport;
	let preprocessStatus = $preprocessFormStore.preprocessStatus;
	let toastElem;
    export const compData = null;

	async function preprocessLayout(formData) {
		preprocessFormStore.update((formStat) => {
			formStat.preprocessStatus = true;

			return formStat;
		});
		const response = await fetch(`http://${$selectedServerInfoStore.ip_address}:${$selectedServerInfoStore.port}/preprocess`, {
			method: 'POST',
			body: JSON.stringify({
				layout_fname: $activeLayoutStore,
  				power_nets: netsToReport,
  				ground_nets: gndNetName,
  				stackup_fname: formData.stackupFname === '' ? null : formData.stackupFname,
  				padstack_fname: formData.padstackFname === '' ? null : formData.padstackFname,
  				material_fname: formData.materialFname === '' ? null : formData.materialFname,
  				default_conduct: formData.defaultConduct,
  				cut_margin: (formData.cut_margin*1e-3).toString(), // Converting from mm to m
  				post_processed_fname: formData.processedFname === '' ? null : formData.processedFname,
				delete_unused_nets: formData.deleteUnusedNets
			}),
			headers: {
				'Content-Type': 'application/json'
			}
		});

		let res = await response.json();
		const toastBootstrap = bootstrap.Toast.getOrCreateInstance(toastElem);
		toastBootstrap.show();
		
		preprocessFormStore.update((formStat) => {
			formStat.preprocessStatus = false;

			return formStat;
		});
	}

	$: preprocessStatus = $preprocessFormStore.preprocessStatus;

	function preprocess(event) {
		let formData = event.detail;
		preprocessLayout(formData);
	}
</script>

<div class="toast-container position-fixed bottom-0 end-0 p-3">
	<div bind:this={toastElem} class="toast text-bg-success" role="alert" aria-live="assertive" aria-atomic="true">
		<div class="toast-header">
			<strong class="me-auto">Port setup message</strong>
			<button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
		</div>
		<div class="toast-body">Layout ports have been successfully updated</div>
	</div>
</div>

<div class="container-fluid pt-3">
	<div class="row">
		<div class="col-2">
			<NetSelect
				bind:copiedNetNames
                bind:selectedNetType
                netTypes={['power', 'ground']}
			/>
		</div>
		<div class="col-2">
			<NetDisplay
				bind:copiedNetNames
                bind:selectedNetType
				bind:netsToReport
				bind:gndNetName
				title="Selected nets"
                groundNet={true}
				submitButton={false}
			/>
		</div>
		<div class="col-8">
			<PreprocessForm
				on:preprocess-layout={preprocess}
				bind:gndNetName
				bind:netsToReport
				bind:preprocessStatus
			/>
		</div>
	</div>
</div>
