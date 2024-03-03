<script>
    import { appVersionStore } from '../store/stores.js';
    import Logo from '$lib/components/Logo.svelte';

    export let data;

    appVersionStore.set(data.result);
</script>

<!-- <NetSelect /> -->
<Logo />
<!-- <NetDisplay /> -->
<!-- <NetReport /> -->
