<script>
	import { activeLayoutStore, sinksFileStore } from '../../store/stores.js';
	import { invalidateAll } from '$app/navigation';
	import SinksTable from '$lib/components/SinksTable.svelte';
	import TabbedPane from '$lib/components/TabbedPane.svelte';
	import HelpPage from '$lib/components/HelpPage.svelte';

	export let data;
	let latestLayout = $activeLayoutStore;

	$: {
		if ($activeLayoutStore !== latestLayout) {
			latestLayout = $activeLayoutStore;
			sinksFileStore.set('');
			invalidateAll();
		}
	}
</script>

{#if data.Name === undefined || data.Name.length === 0}
	<h3 class="position-relative pt-5">
		<span class="position-absolute start-50 translate-middle badge rounded-pill text-bg-info"
			><i class="bi bi-info-circle"></i> Layout does not have sinks defined</span
		>
	</h3>
{:else}
	<TabbedPane
		tabNames={['Sink setup', 'Help']}
		tabComponents={[SinksTable, HelpPage]}
		tabCompsData={[data, 'Help Page WIP']}
	/>
{/if}