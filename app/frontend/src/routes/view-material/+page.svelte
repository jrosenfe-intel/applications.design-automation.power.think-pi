<script>
	import { materialDataStore, materialFileStore } from '../../store/stores.js';
	import DataTable from '$lib/components/DataTable.svelte';
	import LayerCheckSelect from '$lib/components/LayerCheckSelect.svelte';
	import TabbedPane from '$lib/components/TabbedPane.svelte';

	let materialList;
	let activeMaterialName;
	let materialPropertyNames;
	let tabComps;
	let tabData;

	function changeMaterial(event) {
		activeMaterialName = event.detail;
	}

	$: {
		materialList = Object.keys($materialDataStore);
		activeMaterialName = materialList[0];
	}

	$: {
		materialPropertyNames = Object.keys($materialDataStore[activeMaterialName]);
		tabComps = [];
		tabData = [];
		for (let propName of materialPropertyNames) {
			tabComps.push(DataTable);
			tabData.push($materialDataStore[activeMaterialName][propName]);
		}
	}
</script>

<div class="container text-center">
	<div class="row">
		<div class="col col-11 pt-3">
			<TabbedPane
				tabNames={materialPropertyNames}
				tabComponents={tabComps}
				tabCompsData={tabData}
			/>
		</div>
		<div class="col col-1 pt-3">
			<LayerCheckSelect
				on:change-layer={changeMaterial}
				layerNames={materialList}
				currentLayer={activeMaterialName}
				title={`${$materialFileStore.split('/').slice(-1)[0]}`}
			/>
		</div>
	</div>
</div>
