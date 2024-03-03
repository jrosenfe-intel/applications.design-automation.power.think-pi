<script>
    import { selectedServerInfoStore } from '../../store/stores.js'
    import { spdDataStore, activeLayoutStore } from '../../store/stores.js';
	import NetSelect from '$lib/components/NetSelect.svelte';
	import NetDisplay from '$lib/components/NetDisplay.svelte';
	import ReportDisplay from '$lib/components/ReportDisplay.svelte';
	
	let copiedNetNames;
	let capWildcards;
    let reports = []
    export const compData = null;

	async function createReports(netNames, capFinder) {
		const response = await fetch(`http://${$selectedServerInfoStore.ip_address}:${$selectedServerInfoStore.port}/report`, {
			method: 'POST',
			body: JSON.stringify({
				layout_fname: $activeLayoutStore,
				cap_finder: capFinder,
				nets: netNames
			}),
			headers: {
				'Content-Type': 'application/json'
			}
		});

		reports = await response.json();
	}

	function report(event) {
		let netsToReport = event.detail;
		createReports(netsToReport, capWildcards);
	}

    // $: netsByType = $spdDataStore[$activeLayoutStore]
	// 				?.netNames[selectedNetType] || []
</script>

<div class="container-fluid pt-3">
	<div class="row">
		<div class="col-2">
			<NetSelect
				bind:copiedNetNames
                netTypes={['power']}
			/>
		</div>
		<div class="col-2">
			<NetDisplay
				on:create-report={report}
				bind:copiedNetNames
				bind:capWildcards
				title="Power nets"
				capFinder={true}
			/>
		</div>
		<div class="col-8">
			<ReportDisplay {reports} />
		</div>
	</div>
</div>
