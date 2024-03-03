<script>
	import { selectedServerInfoStore, fileExplorerParamsStore } from '../../store/stores.js';
	import { changedServerStore } from '../../store/stores.js';
	import {
		stackupFileStore,
		padstackFileStore,
		loadFileFolderStore,
		materialFileStore,
		portsFileStore,
		sinksFileStore,
		vrmsFileStore
	} from '../../store/stores.js';
	import { goto } from '$app/navigation';

	let loadFileType;
	let gotoRoute;
	let selectedDrive;
	let loadFileName;
	let selectedRow = -1;
	let dismiss = '';
	let refreshContent = true;
	let currentPath;
	let pathContent = { dirs: [], files: [] };

	async function refresh() {
		const response = await fetch(
			`http://${$selectedServerInfoStore.ip_address}:${$selectedServerInfoStore.port}/path`,
			{
				method: 'POST',
				body: JSON.stringify({
					path: currentPath.join('/') + '/'
				}),
				headers: {
					'Content-Type': 'application/json'
				}
			}
		);
		pathContent = await response.json();
	}

	function handleDblClick(dirName) {
		currentPath.push(dirName);
		currentPath = currentPath;
		refreshContent = true;
	}

	function handleHomeClick() {
		currentPath = [currentPath[0]];
		dismiss = '';
		refreshContent = true;
	}

	function handlePathClick(idx = -2) {
		currentPath = currentPath.slice(0, idx + 1);
		dismiss = '';
		refreshContent = true;
	}

	function handleRefreshClick() {
		dismiss = '';
		refreshContent = true;
	}

	function handleFileClick(fname, rowNum) {
		if (fname.split('.').pop() === loadFileType) {
			selectedRow = rowNum;
			loadFileName = [...currentPath];
			loadFileName.push(fname);
			loadFileName = loadFileName.join('/');

			dismiss = 'modal';
		}
	}

	function fileSelectClick() {
		if (dismiss === 'modal') {
			if (gotoRoute.includes('load-spd')) {
				loadFileFolderStore.set(loadFileName);
			} else if (gotoRoute.includes('load-material')) {
				materialFileStore.set(loadFileName);
			} else if (gotoRoute.includes('create-stackup')) {
				stackupFileStore.set(loadFileName);
			} else if (gotoRoute.includes('create-padstack')) {
				padstackFileStore.set(loadFileName);
			} else if (gotoRoute.includes('port-setup')) {
				portsFileStore.set(loadFileName);
			} else if (gotoRoute.includes('sink-setup')) {
				sinksFileStore.set(loadFileName);
			} else if (gotoRoute.includes('vrm-setup')) {
				vrmsFileStore.set(loadFileName);
			}
			selectedRow = -1;
			goto(gotoRoute);
		}
	}

	$: {
		loadFileType = $fileExplorerParamsStore.loadFileType;
		gotoRoute = $fileExplorerParamsStore.gotoRoute;
	}

	$: {
		if ($changedServerStore) {
			selectedDrive = $selectedServerInfoStore.drives[0];
			selectedRow = -1;
			refreshContent = true;
			changedServerStore.set(false);
		}
	}

	$: {
		currentPath = [selectedDrive];
		selectedRow = -1;
		refreshContent = true;
	}

	$: {
		if (refreshContent && $selectedServerInfoStore !== null) {
			selectedRow = -1;
			refresh();
			refreshContent = false;
		}
	}
</script>

<!-- Modal -->
<div
	class="modal fade"
	id="file-list"
	data-bs-backdrop="static"
	data-bs-keyboard="false"
	tabindex="-1"
	aria-labelledby="ModalLabel"
	aria-hidden="true"
>
	<div class="modal-dialog modal-dialog-scrollable modal-xl">
		<div class="modal-content">
			<div class="modal-header p-1 bg-body-tertiary">
				<div class="vstack">
					<div class="hstack">
						<div>
							<button on:click={handleHomeClick} type="button" class="btn btn-light">
								<i class="bi bi-house-door" style="font-size: 20px" />
							</button>
							<button on:click={() => handlePathClick()} type="button" class="btn btn-light">
								<i class="bi bi-arrow-up" style="font-size: 20px" />
							</button>
							<button on:click={handleRefreshClick} type="button" class="btn btn-light">
								<i class="bi bi-arrow-clockwise" style="font-size: 20px" />
							</button>
							<button type="button" class="btn btn-light">
								<i class="bi bi-folder-plus" style="font-size: 20px" />
							</button>
							<button type="button" class="btn btn-light">
								<i class="bi bi-pencil-square" style="font-size: 20px" />
							</button>
							<button type="button" class="btn btn-light">
								<i class="bi bi-trash3" style="font-size: 20px" />
							</button>
						</div>

						<h6 class="px-3 pt-2">Select drive</h6>
						{#if $selectedServerInfoStore !== null}
							<select
								bind:value={selectedDrive}
								class="form-select form-select-sm"
								style="width: auto;"
							>
								{#each $selectedServerInfoStore.drives as drive, idx (idx)}
									<option value={drive}>{drive}</option>
								{/each}
							</select>
						{/if}
					</div>
					<hr />
					<nav aria-label="breadcrumb">
						<ol class="breadcrumb">
							{#each currentPath as path, idx (idx)}
								<li class="breadcrumb-item active" aria-current="page">
									<button
										on:click={() => handlePathClick(idx)}
										class="btn btn-outline-secondary btn-sm border-0">{path}</button
									>
								</li>
							{/each}
						</ol>
					</nav>
				</div>
			</div>

			<div class="modal-body pt-0">
				<!-- Folder table content -->
				<table class="table table-sm table-hover table-borderless">
					<thead class="border-bottom sticky-top top-0">
						<tr>
							<th scope="col">Name</th>
							<th scope="col">Size</th>
							<th scope="col">Date Modified</th>
						</tr>
					</thead>
					<tbody class="table-group-divider">
						{#each pathContent.dirs as dir, idx (idx)}
							<tr on:dblclick={() => handleDblClick(dir.name)}>
								<td><i class="bi bi-folder" /> {dir.name}</td>
								<td></td>
								<td>{dir.date_modified}</td>
							</tr>
						{/each}
						{#each pathContent.files as file, idx (idx)}
							<tr
								class:table-active={selectedRow === idx}
								on:click={() => handleFileClick(file.name, idx)}
							>
								<td><i class="bi bi-file-earmark" /> {file.name}</td>
								<td>{file.size}</td>
								<td>{file.date_modified}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>

			<div class="modal-footer">
				<button
					on:click={() => {
						selectedRow = -1;
					}}
					type="button"
					class="btn btn-secondary"
					data-bs-dismiss="modal">Close</button
				>
				<button
					on:click={fileSelectClick}
					type="button"
					class="btn btn-primary"
					data-bs-dismiss={dismiss}>Select {loadFileType} file</button
				>
			</div>
		</div>
	</div>
</div>
