<script>
	import { PUBLIC_MASTER_SERVER_IP, PUBLIC_MASTER_SERVER_PORT } from '$env/static/public';
	import { selectedServerInfoStore } from '../../store/stores.js';
	import { selectedServerNameStore } from '../../store/stores.js';
	import { changedServerStore } from '../../store/stores.js';
	import { refreshServerListStore } from '../../store/stores.js';

	let serverName = '';
	let selectedRow = -1;
	let serversInfo = [];

	async function refresh() {
		let p;
		let results = [];
		const allServers = [];

		let ipList = await fetch(`${PUBLIC_MASTER_SERVER_IP}:${PUBLIC_MASTER_SERVER_PORT}/get-ip-list`);
		ipList = await ipList.json();

		const getServerInfo = async (ip, port) => await fetch(`http://${ip}:${port}/get-server-info`);
		//const response = await fetch(`${PUBLIC_MASTER_SERVER_IP}:${PUBLIC_MASTER_SERVER_PORT}`);

		// const getServerInfo = async (ip, port, timeOut=3000) => {
		// 	//try {
		// 		const response = await fetch(`http://${ip}:${port}/get-server-info`,
		// 									{
      	// 										signal: AbortSignal.timeout(timeOut)
    	// 							});
		// 		const result = await response.json();
		// 		return result;
		// 	// } catch(error) {
		// 	// 	console.log(error);
		// 	// }
		// }

		for (let ip of ipList) {
			allServers.push(getServerInfo(ip, '8000'));
		}

		try {
			p = await Promise.allSettled(allServers);
		} catch (error) {
			console.log(error);
		}

		for (const [idx, result] of p.entries()) {
			if (result.status === 'fulfilled') {
				results.push(await result.value.json());
			} else {
				results.push(ipList[idx]);
			}
		}

		//const finalResults = await Promise.allSettled(results);
		const response = await fetch(
			`${PUBLIC_MASTER_SERVER_IP}:${PUBLIC_MASTER_SERVER_PORT}/servers-info`,
			{
				method: 'POST',
				body: JSON.stringify({
					info: results
				}),
				headers: {
					'Content-Type': 'application/json'
				}
			}
		);
		serversInfo = await response.json();
		refreshServerListStore.set(false);
	}

	function handleSelectClick() {
		selectedServerNameStore.set(serversInfo[selectedRow].host_name);
		selectedServerInfoStore.set(serversInfo[selectedRow]);
		changedServerStore.set(true);
	}

	function handleRowSelectClick(idx) {
		if (serversInfo[idx].score !== 'Connection error') {
			selectedRow = idx;
		}
	}

	$: {
		if ($refreshServerListStore) {
			refresh();
		}
	}
</script>

<!-- Modal -->
<div
	class="modal fade"
	id="server-list"
	data-bs-backdrop="static"
	data-bs-keyboard="false"
	tabindex="-1"
	aria-labelledby="ModalLabel"
	aria-hidden="true"
>
	<div class="modal-dialog modal-dialog-scrollable modal-xl">
		<div class="modal-content">
			<div class="modal-header">
				<h5 class="modal-title" id="ModalLabel">
					Select a server <span class="badge rounded-pill text-bg-primary">{serverName}</span>
				</h5>
				<div>
					<button
						on:click={() => {
							refreshServerListStore.set(true);
						}}
						type="button"
						class="btn btn-primary"
					>
						{#if $refreshServerListStore}
							<div class="spinner-border spinner-border-sm" role="status" />
						{:else}
							<i class="bi bi-arrow-clockwise"></i>
						{/if}
					</button>
					<button
						on:click={handleSelectClick}
						type="button"
						class="btn btn-primary"
						data-bs-dismiss="modal">Select</button
					>
				</div>
			</div>
			<div class="modal-body pt-0">
				<!-- Tabel with servers resource info -->
				<table class="table table-sm table-hover text-center">
					<thead class="sticky-top top-0">
						<tr>
							<th scope="col">Host Name</th>
							<th scope="col">CPU Usage [%]</th>
							<th scope="col">Number CPUs</th>
							<th scope="col">Total Memory [GB]</th>
							<th scope="col">Used Memory [GB]</th>
							<th scope="col">User Number</th>
							<th scope="col">Score</th>
						</tr>
					</thead>
					<tbody class="table-group-divider">
						{#each serversInfo as server, idx (server.host_name)}
							<tr
								on:click={() => handleRowSelectClick(idx)}
								class:table-active={selectedRow === idx}
							>
								<td>{server.host_name}</td>
								<td>{server.cpu_per}</td>
								<td>{server.num_cpus}</td>
								<td>{server.total_memory_GB}</td>
								<td>{server.used_memory_GB}</td>
								<td>{server.num_users}</td>
								<td>{server.score}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</div>
	</div>
</div>
