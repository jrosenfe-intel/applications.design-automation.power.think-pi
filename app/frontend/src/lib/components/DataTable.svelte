<script>
    export let compData;
    let headers;

    $: headers = Object.keys(compData);
</script>

<table class="table table-hover table-sm">
	<thead style="position: sticky; top: 0;">
		<tr>
			{#each headers as header (header)}
				<th scope="col">{header}</th>
			{/each}
		</tr>
	</thead>
	<tbody class="table-group-divider">
        {#each compData[headers[0]] as data, idx (idx)}
            <tr>
                {#each headers as header (header)}
                    <td>{compData[header][idx]}</td>
                {/each}
            </tr>
        {/each}
	</tbody>
</table>
