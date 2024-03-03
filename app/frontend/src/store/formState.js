import { writable } from 'svelte/store';

export let preprocessFormStore = writable({
    stackupFname: '',
    padstackFname: '',
    materialFname: '',
    processedFname: '',
    defaultConduct: null,
    cutMargin: 0,
    deleteUnusedNets: false,
    netsToReport: [],
	gndNetName: undefined,
	preprocessStatus: false,
	formSubmitDisabled: true
});
