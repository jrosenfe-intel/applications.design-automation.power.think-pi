<script>
	import { activeLayoutStore, fileExplorerParamsStore } from '../../store/stores.js';
	import { invalidateAll } from '$app/navigation';
	import PadstackTable from '$lib/components/PadstackTable.svelte';
	import TabbedPane from '$lib/components/TabbedPane.svelte';
    import HelpPage from '$lib/components/HelpPage.svelte';

	export let data;
	let latestLayout;

	$: {
		if ($activeLayoutStore !== latestLayout) {
			latestLayout = $activeLayoutStore;
            fileExplorerParamsStore.set({ loadFileType: 'spd', gotoRoute: '/load-spd' });
			invalidateAll();
		}
	}
</script>

<TabbedPane
	tabNames={['Padstack', 'Help']}
	tabComponents={[PadstackTable, HelpPage]}
	tabCompsData={[data, 'Help Page WIP']}
/>

