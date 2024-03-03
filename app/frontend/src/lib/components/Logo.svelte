<script>
	import { selectedServerInfoStore, appVersionStore } from '../../store/stores.js';
	let hideLogo;

	$: hideLogo = $selectedServerInfoStore === null ? false : true;
</script>

<div class="parent" class:hide-logo={hideLogo}>
	<img src="/thinkpi_logo_light.png" alt="logo" class="center" />
	<div class="center">
		<span class="badge rounded-pill text-bg-danger">
			Build {$appVersionStore}
		</span>
	</div>
</div>


<style>
	.hide-logo {
		display: none;
	}

	.parent {
		margin: 0px;
		position: relative;
		height: 800px;
	}

	.center {
		position: absolute;
		margin: auto;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		width: 50%;
		height: 50%;
	}
</style>
