<script>
	import TabbedPane from '$lib/components/TabbedPane.svelte';
	import TextReport from '$lib/components/TextReport.svelte';

	export let reports = [];
	let tabNames = [];
	let tabComps = [];
	let tabReports = [];
	let name;
	let report;

	$: {
		tabNames = [];
		tabReports = [];
		for ([name, report] of Object.entries(reports)) {
			tabNames.push(name);
			tabComps.push(TextReport);
			tabReports.push(report);
		}
		tabNames = tabNames;
		tabReports = tabReports;
	}
</script>

{#if tabNames.length > 0 && tabReports.length > 0}
	<TabbedPane {tabNames} tabComponents={tabComps} tabCompsData={tabReports} />
{:else}
	<h3>
		<span class="badge rounded-pill text-bg-info"
			><i class="bi bi-info-circle"></i> Select nets to create a report</span
		>
	</h3>
{/if}
