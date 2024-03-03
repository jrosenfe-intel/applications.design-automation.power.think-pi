<script>
	import { activeLayoutStore, portsFileStore } from '../../store/stores.js';
	import { invalidateAll } from '$app/navigation';
	import PortsTable from '$lib/components/PortsTable.svelte';
	import TabbedPane from '$lib/components/TabbedPane.svelte';
	import HelpPage from '$lib/components/HelpPage.svelte';

	export let data;
	let latestLayout = $activeLayoutStore;

	$: {
		if ($activeLayoutStore !== latestLayout) {
			latestLayout = $activeLayoutStore;
			portsFileStore.set('');
			invalidateAll();
		}
	}
</script>

{#if data.Name === undefined || data.Name.length === 0}
	<h3 class="position-relative pt-5">
		<span class="position-absolute start-50 translate-middle badge rounded-pill text-bg-info"
			><i class="bi bi-info-circle"></i> Layout does not have ports defined</span
		>
	</h3>
{:else}
	<TabbedPane
		tabNames={['Port setup', 'Help']}
		tabComponents={[PortsTable, HelpPage]}
		tabCompsData={[data, 'Help Page WIP']}
	/>
{/if}
