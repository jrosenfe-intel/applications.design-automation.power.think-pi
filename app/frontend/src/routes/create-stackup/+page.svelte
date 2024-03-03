<script>
	import { activeLayoutStore, fileExplorerParamsStore } from '../../store/stores.js';
	import { invalidateAll } from '$app/navigation';
	import StackupTable from '$lib/components/StackupTable.svelte';
	import TabbedPane from '$lib/components/TabbedPane.svelte';
    import HelpPage from '$lib/components/HelpPage.svelte';

	export let data;
	let latestLayout = $activeLayoutStore;

	$: {
		if ($activeLayoutStore !== latestLayout) {
			latestLayout = $activeLayoutStore;
            fileExplorerParamsStore.set({ loadFileType: 'spd', gotoRoute: '/load-spd' });
			invalidateAll();
		}
	}
</script>

<TabbedPane
	tabNames={['Stackup', 'Help']}
	tabComponents={[StackupTable, HelpPage]}
	tabCompsData={[data, 'Help Page WIP']}
/>

