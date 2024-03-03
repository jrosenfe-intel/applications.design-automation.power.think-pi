<script>
	import MainPanes from '$lib/components/MainPanes.svelte'
	import SelectLayout from '$lib/components/SelectLayout.svelte'
	import ServerButton from '$lib/components/ServerButton.svelte'
	import LogMessages from '$lib/components/LogMessages.svelte'
</script>

<main>
	<MainPanes>
		<svelte:fragment slot="select-layout">
			<SelectLayout />
		</svelte:fragment>
		<svelte:fragment slot="server-button">
			<ServerButton />
		</svelte:fragment>
		<svelte:fragment slot="main-pane">
			<slot />
		</svelte:fragment>
		<svelte:fragment slot="aux-menu">
			<LogMessages />
		</svelte:fragment>
		<!-- <svelte:fragment slot="server-modal">
			<ServerModal />
		</svelte:fragment>
		<svelte:fragment slot="file-explorer-modal">
			<FileExplorerModal />
		</svelte:fragment> -->
	</MainPanes>
</main>
