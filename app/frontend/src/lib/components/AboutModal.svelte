<script>
	import { appVersionStore } from '../../store/stores.js';
</script>

<div class="modal fade" id="about-modal" tabindex="-1">
	<div class="modal-dialog modal-dialog-centered">
		<div class="modal-content">
			<div class="modal-header">
				<h1 class="modal-title fs-5">
					About ThinkPI <span class="fs-6">(Build {$appVersionStore})</span>
				</h1>
				<button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
			</div>
			<div class="modal-body">
				<em>ThinkPI framework</em> objective is to handle all power integrity design and analysis
				processes through automation of tedious and repetitive tasks and flows, thereby increasing
				throughput and efficiency while minimizing errors. ThinkPI is also tasked with management of
				compute resources as well as, but not limited to, data analysis and report generation.<br
				/><br />ThinkPI was conceived, nurtured, and internally developed with care within the
				datacenter power solutions (DPS) team to liberate power integrity (PI) engineers from time
				consuming tedious and repetitive tasks. By enabling this automation framework, moving from
				clicking to thinking is possible.<br /><br />We hope you will have fun using it. The ThinkPI
				team.
			</div>
			<div class="modal-footer">
				<button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
			</div>
		</div>
	</div>
</div>
