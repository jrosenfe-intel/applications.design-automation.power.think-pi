<script>
	import {
		selectedServerInfoStore,
		fileExplorerParamsStore,
		activeLayoutStore,
		materialFileStore
	} from '../../store/stores.js';
	import ServerModal from '$lib/components/ServerModal.svelte';
	import AboutModal from '$lib/components/AboutModal.svelte';
	import ContrModal from '$lib/components/ContrModal.svelte';
	import FileExplorerModal from '$lib/components/FileExplorerModal.svelte';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	let hsdLink =
		'https://hsdes.intel.com/appstore/article/#/server_platf.support/create?support.business_unit=PHED%20(CED)&server_platf.support.issue_class=bug&notify=danang,dgarciam,jrosenfe,iwilkins&priority=3-medium&server_platf.support.project_name=ThinkPI&status=open';
	let serverNotSelected;
	let layoutNotLoaded;
	let materialNotLoaded;

	function setFileType(ftype, route) {
		fileExplorerParamsStore.set({ loadFileType: ftype, gotoRoute: route });
	}

	$: {
		serverNotSelected = $selectedServerInfoStore === null ? 'disabled' : '';
		layoutNotLoaded = $activeLayoutStore === undefined ? 'disabled' : '';
		materialNotLoaded = $materialFileStore === '' ? 'disabled' : '';
	}

	onMount(() => {
		document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach((tooltip) => {
			new bootstrap.Tooltip(tooltip);
		});
	});
</script>

<div class="sticky-top">
	<nav class="navbar navbar-expand-lg bg-body-tertiary border-bottom border-warning pb-0 pt-0">
		<div class="container-fluid">
			<a class="navbar-brand fw-bold" href="/">ThinkPI</a>
			<button
				class="navbar-toggler"
				type="button"
				data-bs-toggle="collapse"
				data-bs-target="#navbarSupportedContent"
				aria-controls="navbarSupportedContent"
				aria-expanded="false"
				aria-label="Toggle navigation"
			>
				<span class="navbar-toggler-icon"></span>
			</button>
			<div class="collapse navbar-collapse" id="navbarSupportedContent">
				<ul class="navbar-nav">
					<!-- File menu -->
					<li class="nav-item dropdown px-2">
						<a
							class="nav-link dropdown-toggle btn btn-light"
							href="/"
							role="button"
							data-bs-toggle="dropdown"
							aria-expanded="false"
						>
							File
						</a>
						<ul class="dropdown-menu">
							<li>
								<a
									on:click={() => {
										setFileType('spd', '/load-spd');
									}}
									class="dropdown-item {serverNotSelected}"
									data-bs-toggle="modal"
									data-bs-target="#file-list"
									href="/">Load layout</a
								>
							</li>
							<li>
								<a class="dropdown-item {layoutNotLoaded}" href="/view-spd">View layout</a>
							</li>
							<li>
								<a
									on:click={() => {
										setFileType('txt', '/load-material');
									}}
									class="dropdown-item {layoutNotLoaded}"
									data-bs-toggle="modal"
									data-bs-target="#file-list"
									href="/">Load material</a
								>
							</li>
							<li>
								<a class="dropdown-item {materialNotLoaded}" href="/view-material">View material</a>
							</li>
							<li><hr class="dropdown-divider" /></li>
							<li><a class="dropdown-item disabled" href="/">Load waveforms</a></li>
						</ul>
					</li>
					<!-- Layout Flows -->
					<li class="nav-item dropdown px-2">
						<a
							class="nav-link dropdown-toggle btn btn-light"
							href="/"
							role="button"
							data-bs-toggle="dropdown"
							aria-expanded="false"
						>
							Layout Flows
						</a>
						<ul class="dropdown-menu">
							<li>
								<a class="dropdown-item {layoutNotLoaded}" href="/create-stackup">Create stackup</a>
							</li>
							<li>
								<a class="dropdown-item {layoutNotLoaded}" href="/create-padstack"
									>Create padstack</a
								>
							</li>
							<li>
								<a class="dropdown-item {layoutNotLoaded}" href="/preprocess">Preprocess</a>
							</li>
						</ul>
					</li>
					<!-- Port Flows -->
					<li class="nav-item dropdown px-2">
						<a
							class="nav-link dropdown-toggle btn btn-light"
							href="/"
							role="button"
							data-bs-toggle="dropdown"
							aria-expanded="false"
						>
							Port Flows
						</a>
						<ul class="dropdown-menu">
							<li><a class="dropdown-item disabled" href="/">Port setup</a></li>
							<li><hr class="dropdown-divider" /></li>
							<li><a class="dropdown-item disabled" href="/">Package ports</a></li>
							<li><a class="dropdown-item disabled" href="/">Motherboard ports</a></li>
							<li><hr class="dropdown-divider" /></li>
							<li><a class="dropdown-item disabled" href="/">Auto port copy</a></li>
							<li><a class="dropdown-item disabled" href="/">port copy</a></li>
							<li><hr class="dropdown-divider" /></li>
							<li><a class="dropdown-item disabled" href="/">Auto port placement</a></li>
							<li><a class="dropdown-item disabled" href="/">Boxes to ports</a></li>
							<li><a class="dropdown-item disabled" href="/">Sinks/VRMs to ports</a></li>
							<li><a class="dropdown-item disabled" href="/">Auto VRM ports</a></li>
						</ul>
					</li>
					<!-- Sinks/VRMs Flows -->
					<li class="nav-item dropdown px-2">
						<a
							class="nav-link dropdown-toggle btn btn-light"
							href="/"
							role="button"
							data-bs-toggle="dropdown"
							aria-expanded="false"
						>
							Sink/VRM Flows
						</a>
						<ul class="dropdown-menu">
							<li><a class="dropdown-item disabled" href="/">Sinks/VRMs/LDOs setup</a></li>
							<li><a class="dropdown-item disabled" href="/">Ports to sinks/VRMs</a></li>
							<li><a class="dropdown-item disabled" href="/">Place sinks</a></li>
							<li><a class="dropdown-item disabled" href="/">Place VRMs</a></li>
							<li><a class="dropdown-item disabled" href="/">Copy sinks/VRMs</a></li>
						</ul>
					</li>
					<!-- Help menu -->
					<li class="nav-item dropdown px-2">
						<a
							class="nav-link dropdown-toggle btn btn-light"
							href="/"
							role="button"
							data-bs-toggle="dropdown"
							aria-expanded="false"
						>
							Help
						</a>
						<ul class="dropdown-menu">
							<li><a class="dropdown-item" href={hsdLink} target="_blank">Report bug</a></li>
							<li><a class="dropdown-item disabled" href="/">Documentation</a></li>
							<li><a class="dropdown-item disabled" href="/">Request account</a></li>
							<li><hr class="dropdown-divider" /></li>
							<li>
								<a
									class="dropdown-item"
									data-bs-toggle="modal"
									data-bs-target="#about-modal"
									href="/">About</a
								>
							</li>
							<li>
								<a
									class="dropdown-item"
									data-bs-toggle="modal"
									data-bs-target="#contr-modal"
									href="/">Developers and contributors</a
								>
							</li>
						</ul>
					</li>
				</ul>
			</div>
		</div>
	</nav>

	<div class="container-fluid bg-body-tertiary border-bottom border-warning py-1">
		<div class="row">
			<div class="col d-flex justify-content-start">
				<div>
					<button
						on:click={() => {
							setFileType('spd', '/load-spd');
						}}
						type="button"
						class="btn btn-light"
						disabled={serverNotSelected === 'disabled'}
					>
						<span
							data-bs-toggle="tooltip"
							data-bs-placement="bottom"
							data-bs-html="true"
							data-bs-title="open spd layout"
						>
							<i
								class="bi bi-folder2-open"
								style="font-size: 20px"
								data-bs-toggle="modal"
								data-bs-target="#file-list"
							></i></span
						>
					</button>
					<button
						on:click={() => {
							goto('/view-spd');
						}}
						type="button"
						class="btn btn-light"
						disabled={layoutNotLoaded === 'disabled'}
					>
						<span
							data-bs-toggle="tooltip"
							data-bs-placement="bottom"
							data-bs-html="true"
							data-bs-title="view spd layout"
						>
							<i class="bi bi-eye" style="font-size: 20px"></i>
						</span></button
					>
					<button
						on:click={() => {
							window.open(hsdLink, '_blank');
						}}
						type="button"
						class="btn btn-light"
					>
						<span
							data-bs-toggle="tooltip"
							data-bs-placement="bottom"
							data-bs-html="true"
							data-bs-title="report error"
						>
							<i class="bi bi-bug" style="font-size: 20px"></i>
						</span></button
					>
					<button type="button" class="btn btn-light" disabled>
						<span
							data-bs-toggle="tooltip"
							data-bs-placement="bottom"
							data-bs-html="true"
							data-bs-title="help"
						>
							<i class="bi bi-question-circle" style="font-size: 20px"></i>
						</span></button
					>
					<button type="button" class="btn btn-light" disabled>
						<span
							data-bs-toggle="tooltip"
							data-bs-placement="bottom"
							data-bs-html="true"
							data-bs-title="switch between light and dark mode"
						>
							<i class="bi bi-moon-stars" style="font-size: 20px"></i>
						</span></button
					>
				</div>
			</div>
			<div class="col d-flex justify-content-center">
				<slot name="select-layout" />
			</div>
			<div class="col d-flex justify-content-end">
				<slot name="server-button" />
			</div>
		</div>
	</div>
</div>

<div class="container-fluid">
	<div class="row row-height">
		<div id="col-left" class="col-1 border p-0">
			<h1 class="display-6 text-info-emphasis text-center pt-2 pb-4">Flows</h1>
			<div class="accordion" id="accordion-flows">
				<!-- Layout flow -->
				<div class="accordian-item">
					<h1 class="accordion-header">
						<button
							class="accordion-button collapsed border-top border-bottom"
							type="button"
							data-bs-toggle="collapse"
							data-bs-target="#layouts"
							aria-expanded="true"
							aria-controls="layouts"
						>
							Layouts
						</button>
					</h1>
					<div id="layouts" class="accordion-collapse collapse" data-bs-parent="#accordion-flows">
						<div class="accordion-body d-grid p-1">
							<button
								on:click={() => {
									setFileType('spd', '/load-spd');
								}}
								type="button"
								class="btn btn-outline-primary btn-sm"
								disabled={serverNotSelected}
								data-bs-toggle="modal"
								data-bs-target="#file-list">Load SPD layout</button
							>
						</div>
						<div class="accordion-body d-grid p-1">
							<button
								on:click={() => {
									goto('/view-spd');
								}}
								type="button"
								class="btn btn-outline-primary btn-sm"
								disabled={layoutNotLoaded === 'disabled'}>View SPD layout</button
							>
						</div>
						<div class="accordion-body d-grid p-1">
							<button
								on:click={() => {
									setFileType('txt', '/load-material');
								}}
								type="button"
								class="btn btn-outline-primary btn-sm"
								disabled={layoutNotLoaded === 'disabled'}
								data-bs-toggle="modal"
								data-bs-target="#file-list">Load material</button
							>
						</div>
						<div class="accordion-body d-grid p-1">
							<button
								on:click={() => {
									goto('/view-material');
								}}
								type="button"
								class="btn btn-outline-primary btn-sm"
								disabled={materialNotLoaded === 'disabled'}>View material</button
							>
						</div>
						<div class="accordion-body d-grid p-1">
							<button
								on:click={() => {
									goto('/create-stackup');
								}}
								type="button"
								class="btn btn-outline-primary btn-sm"
								disabled={layoutNotLoaded === 'disabled'}>Create stackup</button
							>
						</div>
						<div class="accordion-body d-grid p-1">
							<button
								on:click={() => {
									goto('/create-padstack');
								}}
								type="button"
								class="btn btn-outline-primary btn-sm"
								disabled={layoutNotLoaded === 'disabled'}>Create padstack</button
							>
						</div>
						<div class="accordion-body d-grid p-1">
							<button
								on:click={() => {
									goto('/preprocess');
								}}
								type="button"
								class="btn btn-outline-primary btn-sm"
								disabled={layoutNotLoaded === 'disabled'}>Preprocess</button
							>
						</div>
					</div>
				</div>
				<!-- Ports flow -->
				<div class="accordian-item">
					<h1 class="accordion-header">
						<button
							class="accordion-button collapsed border-bottom"
							type="button"
							data-bs-toggle="collapse"
							data-bs-target="#ports"
							aria-expanded="true"
							aria-controls="ports"
						>
							Ports/Sources
						</button>
					</h1>
					<div id="ports" class="accordion-collapse collapse" data-bs-parent="#accordion-flows">
						<div class="accordion-body d-grid p-1">
							<button
								on:click={() => {
									goto('/port-setup');
								}}
								type="button"
								class="btn btn-outline-success btn-sm"
								disabled={layoutNotLoaded === 'disabled'}>Port setup</button
							>
						</div>
						<div class="accordion-body d-grid p-1">
							<button
								on:click={() => {
									goto('/sink-setup');
								}}
								type="button"
								class="btn btn-outline-success btn-sm"
								disabled={layoutNotLoaded === 'disabled'}>Sink setup</button
							>
						</div>
						<div class="accordion-body d-grid p-1">
							<button
								on:click={() => {
									goto('/vrm-setup');
								}}
								type="button"
								class="btn btn-outline-success btn-sm"
								disabled={layoutNotLoaded === 'disabled'}>VRM setup</button
							>
						</div>
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-success btn-sm" disabled
								>LDO setup</button
							>
						</div>
						<div><hr /></div>
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-success btn-sm" disabled
								>Package flow</button
							>
						</div>
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-success btn-sm" disabled
								>Motherboard flow</button
							>
						</div>
						<div><hr /></div>
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-success btn-sm" disabled
								>Auto copy</button
							>
						</div>
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-success btn-sm" disabled
								>Ports copy</button
							>
						</div>
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-success btn-sm" disabled
								>Array copy</button
							>
						</div>
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-success btn-sm" disabled
								>Mirror copy</button
							>
						</div>
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-success btn-sm" disabled
								>Rotate copy</button
							>
						</div>
						<div><hr /></div>
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-success btn-sm" disabled
								>Auto ports</button
							>
						</div>
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-success btn-sm" disabled
								>Auto socket ports</button
							>
						</div>
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-success btn-sm" disabled
								>Transfer socket ports</button
							>
						</div>
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-success btn-sm" disabled
								>Component ports</button
							>
						</div>
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-success btn-sm" disabled
								>Boxes to ports</button
							>
						</div>
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-success btn-sm" disabled
								>Reduce ports</button
							>
						</div>
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-success btn-sm" disabled
								>Sinks/VRMs to ports</button
							>
						</div>
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-success btn-sm" disabled
								>Auto VRM ports</button
							>
						</div>
						<div><hr /></div>
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-success btn-sm" disabled
								>Ports to sinks/VRMs</button
							>
						</div>
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-success btn-sm" disabled
								>Place sinks</button
							>
						</div>
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-success btn-sm" disabled
								>Place VRMs</button
							>
						</div>
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-success btn-sm" disabled
								>Copy sinks/VRMs</button
							>
						</div>
					</div>
				</div>
				<!-- Macromodeling flow -->
				<div class="accordian-item">
					<h1 class="accordion-header">
						<button
							class="accordion-button collapsed border-bottom"
							type="button"
							data-bs-toggle="collapse"
							data-bs-target="#macromodel"
							aria-expanded="true"
							aria-controls="macromodel"
						>
							Macromodel
						</button>
					</h1>
					<div
						id="macromodel"
						class="accordion-collapse collapse"
						data-bs-parent="#accordion-flows"
					>
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-danger btn-sm" disabled
								>Create termination</button
							>
						</div>
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-danger btn-sm" disabled
								>IdEM optimization</button
							>
						</div>
					</div>
				</div>
				<!-- HSPICE -->
				<div class="accordian-item">
					<h1 class="accordion-header">
						<button
							class="accordion-button collapsed border-bottom"
							type="button"
							data-bs-toggle="collapse"
							data-bs-target="#hspice"
							aria-expanded="true"
							aria-controls="hspice"
						>
							HSPICE
						</button>
					</h1>
					<div id="hspice" class="accordion-collapse collapse" data-bs-parent="#accordion-flows">
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-secondary btn-sm" disabled
								>Create deck</button
							>
						</div>
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-secondary btn-sm" disabled>Result</button
							>
						</div>
					</div>
				</div>
				<!-- PowerDC flow -->
				<div class="accordian-item">
					<h1 class="accordion-header">
						<button
							class="accordion-button collapsed border-bottom"
							type="button"
							data-bs-toggle="collapse"
							data-bs-target="#powerdc"
							aria-expanded="true"
							aria-controls="powerdc"
						>
							PowerDC
						</button>
					</h1>
					<div id="powerdc" class="accordion-collapse collapse" data-bs-parent="#accordion-flows">
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-info btn-sm" disabled>Merge</button>
						</div>
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-info btn-sm" disabled
								>Place sinks/VRMs</button
							>
						</div>
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-info btn-sm" disabled
								>Setup sinks/VRMs</button
							>
						</div>
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-info btn-sm" disabled
								>Setup simulation</button
							>
						</div>
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-info btn-sm" disabled
								>Result analysis</button
							>
						</div>
					</div>
				</div>
				<!-- PowerSI -->
				<div class="accordian-item">
					<h1 class="accordion-header">
						<button
							class="accordion-button collapsed border-bottom"
							type="button"
							data-bs-toggle="collapse"
							data-bs-target="#powersi"
							aria-expanded="true"
							aria-controls="powersi"
						>
							PowerSI
						</button>
					</h1>
					<div id="powersi" class="accordion-collapse collapse" data-bs-parent="#accordion-flows">
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-warning btn-sm" disabled
								>Setup simulation</button
							>
						</div>
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-warning btn-sm" disabled
								>Result analysis</button
							>
						</div>
					</div>
				</div>
				<!-- Clarity -->
				<div class="accordian-item">
					<h1 class="accordion-header">
						<button
							class="accordion-button collapsed border-bottom"
							type="button"
							data-bs-toggle="collapse"
							data-bs-target="#clarity"
							aria-expanded="true"
							aria-controls="clarity"
						>
							Clarity
						</button>
					</h1>
					<div id="clarity" class="accordion-collapse collapse" data-bs-parent="#accordion-flows">
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-primary btn-sm" disabled
								>Preprocess</button
							>
						</div>
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-primary btn-sm" disabled
								>Net merging</button
							>
						</div>
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-primary btn-sm" disabled
								>Result analysis</button
							>
						</div>
					</div>
				</div>
				<!-- Electro-thermal -->
				<div class="accordian-item">
					<h1 class="accordion-header">
						<button
							class="accordion-button collapsed border-bottom"
							type="button"
							data-bs-toggle="collapse"
							data-bs-target="#electrothermal"
							aria-expanded="true"
							aria-controls="electrothermal"
						>
							Electro-thermal
						</button>
					</h1>
					<div
						id="electrothermal"
						class="accordion-collapse collapse"
						data-bs-parent="#accordion-flows"
					>
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-success btn-sm" disabled
								>Package inductor</button
							>
						</div>
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-success btn-sm" disabled
								>Full system</button
							>
						</div>
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-success btn-sm" disabled
								>Components</button
							>
						</div>
					</div>
				</div>
				<!-- Waveforms -->
				<div class="accordian-item">
					<h1 class="accordion-header">
						<button
							class="accordion-button collapsed border-bottom"
							type="button"
							data-bs-toggle="collapse"
							data-bs-target="#waveforms"
							aria-expanded="true"
							aria-controls="waveforms"
						>
							Waveforms
						</button>
					</h1>
					<div id="waveforms" class="accordion-collapse collapse" data-bs-parent="#accordion-flows">
						<div class="accordion-body d-grid p-1">
							<button
								type="button"
								class="btn btn-outline-danger btn-sm"
								disabled
								data-bs-toggle="modal"
								data-bs-target="#file-list">Load waveforms</button
							>
						</div>
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-danger btn-sm" disabled
								>View waveforms</button
							>
						</div>
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-danger btn-sm" disabled
								>Icc(t) tunning</button
							>
						</div>
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-danger btn-sm" disabled
								>Icc(t) report</button
							>
						</div>
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-danger btn-sm" disabled
								>Measurements</button
							>
						</div>
					</div>
				</div>
				<!-- FIVR -->
				<div class="accordian-item">
					<h1 class="accordion-header">
						<button
							class="accordion-button collapsed border-bottom"
							type="button"
							data-bs-toggle="collapse"
							data-bs-target="#fivr"
							aria-expanded="true"
							aria-controls="fivr"
						>
							FIVR
						</button>
					</h1>
					<div id="fivr" class="accordion-collapse collapse" data-bs-parent="#accordion-flows">
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-secondary btn-sm" disabled
								>Setup library</button
							>
						</div>
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-secondary btn-sm" disabled
								>Setup parameters</button
							>
						</div>
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-secondary btn-sm" disabled
								>Create symbol</button
							>
						</div>
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-secondary btn-sm" disabled
								>Result analysis</button
							>
						</div>
					</div>
				</div>
				<!-- SIMPLIS -->
				<div class="accordian-item">
					<h1 class="accordion-header">
						<button
							class="accordion-button collapsed border-bottom"
							type="button"
							data-bs-toggle="collapse"
							data-bs-target="#simplis"
							aria-expanded="true"
							aria-controls="simplis"
						>
							SIMPLIS
						</button>
					</h1>
					<div id="simplis" class="accordion-collapse collapse" data-bs-parent="#accordion-flows">
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-info btn-sm" disabled
								>Setup parameters</button
							>
						</div>
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-info btn-sm" disabled
								>Create schematic</button
							>
						</div>
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-info btn-sm" disabled
								>Result analysis</button
							>
						</div>
					</div>
				</div>
				<!-- database -->
				<div class="accordian-item">
					<h1 class="accordion-header">
						<button
							class="accordion-button collapsed border-bottom"
							type="button"
							data-bs-toggle="collapse"
							data-bs-target="#database"
							aria-expanded="true"
							aria-controls="database"
						>
							Databases
						</button>
					</h1>
					<div id="database" class="accordion-collapse collapse" data-bs-parent="#accordion-flows">
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-warning btn-sm" disabled>PDDB</button>
						</div>
						<div class="accordion-body d-grid p-1">
							<button type="button" class="btn btn-outline-warning btn-sm" disabled
								>Component browser</button
							>
						</div>
					</div>
				</div>
			</div>
		</div>

		<div id="col-center" class="col-9 border">
			<slot name="main-pane" />
		</div>
		<div id="col-right" class="col-2 border">
			<slot name="aux-menu" />
		</div>
	</div>
</div>

<ServerModal />
<FileExplorerModal />
<AboutModal />
<ContrModal />

<style>
	#col-left,
	#col-center,
	#col-right {
		max-height: 100vh;
		overflow-y: scroll;
	}

	::-webkit-scrollbar {
		width: 0px;
		background: transparent;
	}
	* {
		-ms-overflow-style: none !important;
	}
</style>
