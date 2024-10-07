
  <script>
  import { stream} from '$lib/stores/stream';
  import { currentBot  } from '$lib/stores/main';
  import UPlot from '$lib/components/custom/uplot.svelte';


  const keys = ["estimation.state.v","estimation.state.psi_dot","estimation.state.psi","estimation.state.theta_dot","estimation.state.theta","consensus.dist_from_ref"];
  $: dataGetter =  stream.requestGetter([$currentBot],keys);


</script>


<UPlot dataGetter={dataGetter}/>


