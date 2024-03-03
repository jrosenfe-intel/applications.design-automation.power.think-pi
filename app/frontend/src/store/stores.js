import { writable } from 'svelte/store';

export let appVersionStore = writable();
export let sessionId = writable();

export let fileExplorerParamsStore = writable({ loadFileType: 'spd', gotoRoute: '/load-spd' });

export let selectedServerNameStore = writable('Select server');
export let selectedServerInfoStore = writable(null);
export let refreshServerListStore = writable(false);
export let changedServerStore = writable(false);

export let spdDataStore = writable({});
export let activeLayoutStore = writable();

export let loadFileFolderStore = writable('');
export let materialFileStore = writable('');
export let stackupFileStore = writable('');
export let padstackFileStore = writable('');
export let portsFileStore = writable('');
export let sinksFileStore = writable('');
export let vrmsFileStore = writable('');
export let ldosFileStore = writable('');

export let materialDataStore = writable();

export let socketStore = writable();

