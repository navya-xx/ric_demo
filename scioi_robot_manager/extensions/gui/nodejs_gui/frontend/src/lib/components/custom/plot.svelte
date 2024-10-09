<script>
  import { stream, botList } from "$lib/stores/stream";
  import { currentBot } from "$lib/stores/main";
  import UPlot from "$lib/components/custom/uplot.svelte";

  const keys = [
    "estimation.state.psi",

    //"consensus.dist_from_ref",
  ];

  const bots = ["twipr1", "twipr2","twipr3","twipr4","twipr5"]


  $: dataGetter = stream.requestGetter([Object.keys($botList)], keys);
</script>

<UPlot {dataGetter}  bots={bots}/>
