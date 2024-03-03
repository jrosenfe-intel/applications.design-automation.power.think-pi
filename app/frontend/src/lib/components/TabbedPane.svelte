<script>
	export let tabNames = [];
	export let tabComponents = [];
	export let tabCompsData = [];

	let tabId = [];

	$: {
		tabId = [];
		for (let tabName of tabNames) {
			tabId.push({
				name: tabName,
				buttId: `nav-${tabName.toLowerCase().replace(' ', '-')}-tab`,
				target: `#nav-${tabName.toLowerCase().replace(' ', '-')}`,
				aria: `nav-${tabName.toLowerCase().replace(' ', '-')}`
			});
		}
	}
</script>

<nav>
	<div class="nav nav-tabs" id="nav-tab" role="tablist">
		{#each tabId as { name, buttId, target, aria }, idx (name)}
			{#if idx === 0}
				<button
					class="nav-link active"
					id={buttId}
					data-bs-toggle="tab"
					data-bs-target={target}
					type="button"
					role="tab"
					aria-controls={aria}
					aria-selected="true">{name}</button
				>
			{:else}
				<button
					class="nav-link"
					id={buttId}
					data-bs-toggle="tab"
					data-bs-target={target}
					type="button"
					role="tab"
					aria-controls={aria}
					aria-selected="false">{name}</button
				>
			{/if}
		{/each}
	</div>
</nav>

<div class="tab-content" id="nav-tabContent">
	{#each tabId as { name, buttId, target, aria }, idx (name)}
		{#if idx === 0}
			<div
				class="tab-pane fade show active display-height"
				id={aria}
				role="tabpanel"
				aria-labelledby={buttId}
				tabindex="0"
			>
				<svelte:component this={tabComponents[idx]} compData={tabCompsData[idx]} />
			</div>
		{:else}
			<div class="tab-pane fade display-height" id={aria} role="tabpanel" aria-labelledby={buttId} tabindex="0">
				<svelte:component this={tabComponents[idx]} compData={tabCompsData[idx]} />
			</div>
		{/if}
	{/each}
</div>

<style>
	.display-height {
		height: 700px;
		overflow: auto;
	}
</style>
