<script>
    import TabbedPane from '$lib/components/TabbedPane.svelte';
    import PreprocessMenu from '$lib/components/PreprocessMenu.svelte';
	import HelpPage from '$lib/components/HelpPage.svelte';

	let tabNames = ['Preprocess form', 'Help'];
	let tabComps = [PreprocessMenu, HelpPage];
</script>

<TabbedPane tabNames={tabNames} tabComponents={tabComps}/>