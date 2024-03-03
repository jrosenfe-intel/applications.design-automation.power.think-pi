<script>
    import TabbedPane from '$lib/components/TabbedPane.svelte';
    import LayerView from '$lib/components/LayerView.svelte';
    import NetReport from '$lib/components/NetReport.svelte';
	import HelpPage from '$lib/components/HelpPage.svelte';

	let tabNames = ['Layout view', 'Report', 'Help'];
	let tabComps = [LayerView, NetReport, HelpPage];

</script>

<TabbedPane tabNames={tabNames} tabComponents={tabComps}/>

<!-- <div class="container text-center">
	<div class="row">
		<div class="col col-11 pt-5">
			<TabbedPane tabNames={tabNames} tabComponents={tabComps}/>
		</div>
	</div>
</div> -->
