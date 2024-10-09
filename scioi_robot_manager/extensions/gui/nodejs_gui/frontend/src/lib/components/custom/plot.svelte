<script>
  import { stream, botList } from "$lib/stores/stream";
  import { currentBot } from "$lib/stores/main";
  import UPlot from "$lib/components/custom/uplot.svelte";

  const keys = [
    "estimation.state.v",

    //"consensus.dist_from_ref",
  ];

  const bots = ["twipr1", "twipr2","twipr3","twipr4","twipr5", "twipr6"]


  $: dataGetter = stream.requestGetter([Object.keys($botList)], keys);
</script>

<UPlot {dataGetter}  bots={bots}/>
