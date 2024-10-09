<script lang="ts">
	import uPlot, { type AlignedData, type TypedArray } from 'uplot';
	import { resize } from 'svelte-resize-observer-action';
	import 'uplot/dist/uPlot.min.css';
	import { onMount } from 'svelte';
  import { botColor } from '$lib/helpers/bot-colors';
  import { scale } from 'svelte/transition';




	let plotContainer: HTMLDivElement;

	export const timeScroll: boolean = true;
	export const windowSize: number = 10;
	export const refreshInterval: number = 100;

	export let dataGetter: () => AlignedData; // Function that returns the data to plot

	let width: number;
	let height: number;

	let plot: uPlot;

	export let bots = []

    export let keys = ['time', 'consensus error'];
	export let units = ['s', ' '];
	export let ranges = [
		[null, null],
		[-3, 3],
	];
	const colors = [
		'black',
		'black',
		'red',
		'green',
		'purple',
		'orange',
		'pink',
		'brown',
		'cyan',
		'magenta',
		'lightblue',
		'lightgreen',
		'lightyellow',
		'lightpurple',
		'lightorange',
		'lightpink',
		'lightbrown',
		'lightcyan',
		'lightmagenta'
	];


	function onResize(entry: ResizeObserverEntry) {
		width = entry.contentRect.width;
		height = entry.contentRect.height - 25; // subtract the height of the legend
		plot.setSize({ width, height });
	}

	function initPlot() {
        let series = [{}];
		let axes = [];
		let scales = {
					"x": {
						auto: false,
						time: true,
					},
					"C": { auto: false, range: [-3, 3] }
				};





		// push series for all bots
		for ( const bot of bots){
			series.push({
				label:bot,
				stroke: botColor(bot),
				scale: "C",
				width: 2,
				points: { show: false }
			});

		}

		console.log(series);

		const opts = {
			width: width,
			height: height,
			series: series,
			scales:scales,
			axes: [
				{},
				{
				scale: "C",
				label: "Consensus Error",
				}
			]
		};

		plot = new uPlot(opts, [], plotContainer);
	}

	function scroll() {
		if (timeScroll === false) {
			setTimeout(scroll, 100);
			return;
		}
		const currentTime = Date.now() / 1000;
		plot.setScale('x', {
			min: currentTime - windowSize, // Show last 10 seconds
			max: currentTime // start drawing off screen
		});
		requestAnimationFrame(scroll);
	}

	function updateData() {
        const data = dataGetter();

        if (data?.length && data[0]?.length && data[1]?.length){

			let ndata = data

			if (data.length > bots.length+1) {
				// data should only be as long as bots + 1
				ndata = ndata.slice(0, bots.length+1);

			} else if (ndata.length < bots.length+1) {
				// data should be as long as bots + 1

				// fill up with empty data
				for (let i = ndata.length; i < bots.length+1; i++) {
					ndata.push(new Array(ndata[0].length).fill(null));

				}
			}




            const currentTime = Date.now() / 1000;
			console.log(data)
		    plot.setData(data, false);

        }
	}

	onMount(async () => {
		initPlot();
		requestAnimationFrame(scroll);
		if (refreshInterval > 0) setInterval(updateData, refreshInterval);
	});
</script>

<div class="h-full w-full p-2">
	<div class="h-full w-full" bind:this={plotContainer} use:resize={onResize}></div>
</div>

<style>
	:global(.u-legend) {
		height: 28px !important;
		overflow: hidden !important;
		font-size: 14px !important;
	}

</style>
