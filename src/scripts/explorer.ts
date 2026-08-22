import {
	LngLatBounds,
	Map,
	NavigationControl,
	type ExpressionSpecification,
	type MapGeoJSONFeature,
} from 'maplibre-gl';

type MetricManifest = {
	label: string;
	parent_label: string;
	breaks: number[];
	child_breaks: number[];
};

type MapManifest = {
	metrics: Record<string, MetricManifest>;
	channel_codes: Record<string, string>;
};

type FeatureCollection = {
	type: 'FeatureCollection';
	features: Array<{ type: 'Feature'; properties: Record<string, unknown>; geometry: unknown }>;
};

const root = document.querySelector<HTMLElement>('.explorer-page');
if (!root) throw new Error('Explorer root not found');
const base = root.dataset.base ?? '/';

const metricSelect = document.querySelector<HTMLSelectElement>('#map-metric')!;
const areaSelect = document.querySelector<HTMLSelectElement>('#lad-search')!;
const clearButton = document.querySelector<HTMLButtonElement>('#clear-area')!;
const legend = document.querySelector<HTMLElement>('#map-legend')!;
const profile = document.querySelector<HTMLElement>('#area-profile')!;
const loading = document.querySelector<HTMLElement>('#map-loading')!;

const channelLabels: Record<string, string> = {
	co: 'Co-op',
	mo: 'Morrisons fast',
	sa: "Sainsbury's fast",
	ic: 'Iceland',
};
const channelColors = ['#203c39', '#8f897e', '#b6412f', '#ddd8cc', '#6f6b63'];
const continuousColors = ['#e4e0d5', '#b9cbc5', '#77a59c', '#2f7069', '#173f3c'];
const gbBounds: [[number, number], [number, number]] = [[-8.9, 49.7], [2.2, 59.2]];

let manifest: MapManifest;
let parents: FeatureCollection;
let selectedParent: string | null = null;
let selectedParentFeature: FeatureCollection['features'][number] | null = null;

function escapeHTML(value: unknown): string {
	return String(value ?? '')
		.replaceAll('&', '&amp;')
		.replaceAll('<', '&lt;')
		.replaceAll('>', '&gt;')
		.replaceAll('"', '&quot;')
		.replaceAll("'", '&#039;');
}

function formatNumber(value: unknown, digits = 0): string {
	const number = Number(value);
	return Number.isFinite(number)
		? number.toLocaleString('en-GB', { maximumFractionDigits: digits })
		: 'Not available';
}

function formatPercent(value: unknown, inputIsShare = false): string {
	const number = Number(value);
	if (!Number.isFinite(number)) return 'Not available';
	return `${(inputIsShare ? number * 100 : number).toFixed(1)}%`;
}

function continuousExpression(property: string, breaks: number[]): ExpressionSpecification {
	const stops: Array<string | number | ExpressionSpecification> = [];
	breaks.forEach((value, index) => stops.push(value, continuousColors[index]));
	return ['interpolate', ['linear'], ['coalesce', ['to-number', ['get', property]], breaks[0]], ...stops] as ExpressionSpecification;
}

function categoryExpression(property: string): ExpressionSpecification {
	return [
		'match',
		['to-number', ['get', property]],
		0, channelColors[0],
		1, channelColors[1],
		2, channelColors[2],
		3, channelColors[3],
		4, channelColors[4],
		'#ddd8cc',
	] as ExpressionSpecification;
}

function currentMetric() {
	return metricSelect.value;
}

function paintExpression(): ExpressionSpecification {
	const metric = currentMetric();
	if (metric in channelLabels) {
		return selectedParent
			? categoryExpression(metric)
			: continuousExpression(`${metric}_je`, [0, 5, 10, 20, 35]);
	}
	const config = manifest.metrics[metric];
	return continuousExpression(metric, selectedParent ? config.child_breaks : config.breaks);
}

function updateLegend() {
	const metric = currentMetric();
	if (metric in channelLabels && selectedParent) {
		legend.innerHTML = `
			<p>${escapeHTML(channelLabels[metric])} channel</p>
			${Object.entries(manifest.channel_codes).map(([code, label]) => `
				<span><i style="background:${channelColors[Number(code)]}"></i>${escapeHTML(label)}</span>
			`).join('')}
		`;
		return;
	}
	const isChannel = metric in channelLabels;
	const config = isChannel ? null : manifest.metrics[metric];
	const breaks = isChannel ? [0, 5, 10, 20, 35] : (selectedParent ? config!.child_breaks : config!.breaks);
	const label = isChannel
		? `${channelLabels[metric]} · Just Eat-only share`
		: `${config!.label} · ${selectedParent ? 'small area' : config!.parent_label}`;
	legend.innerHTML = `
		<p>${escapeHTML(label)}</p>
		<div class="legend-ramp">${continuousColors.map((color) => `<i style="background:${color}"></i>`).join('')}</div>
		<div class="legend-values">${breaks.map((value) => `<span>${metric === 'ffs' ? formatPercent(value, true) : formatNumber(value, 1)}${isChannel ? '%' : ''}</span>`).join('')}</div>
	`;
}

function updatePaint() {
	const expression = paintExpression();
	if (selectedParent && map.getLayer('children-fill')) {
		map.setPaintProperty('children-fill', 'fill-color', expression);
	} else if (map.getLayer('parents-fill')) {
		map.setPaintProperty('parents-fill', 'fill-color', expression);
	}
	updateLegend();
}

function geometryBounds(geometry: unknown): LngLatBounds {
	const bounds = new LngLatBounds();
	const walk = (value: unknown) => {
		if (!Array.isArray(value)) return;
		if (value.length >= 2 && typeof value[0] === 'number' && typeof value[1] === 'number') {
			bounds.extend([value[0], value[1]]);
			return;
		}
		value.forEach(walk);
	};
	walk((geometry as { coordinates?: unknown })?.coordinates);
	return bounds;
}

function parentProfile(properties: Record<string, unknown>) {
	profile.innerHTML = `
		<p class="profile-kicker">Local authority overview</p>
		<h2>${escapeHTML(properties.name)}</h2>
		<p>${formatNumber(properties.n)} LSOA/Data Zone markets · population ${formatNumber(properties.pop)}</p>
		<dl class="profile-values">
			<div><dt>Median restaurants</dt><dd>${formatNumber(properties.r, 1)}</dd></div>
			<div><dt>Median fast food</dt><dd>${formatNumber(properties.ff, 1)}</dd></div>
			<div><dt>Fast-food share</dt><dd>${formatPercent(properties.ffs, true)}</dd></div>
			<div><dt>Median grocery listings</dt><dd>${formatNumber(properties.g, 1)}</dd></div>
		</dl>
		<p class="profile-note">Small-area polygons are now loaded. Select one on the map for its exact area profile.</p>
	`;
}

function childProfile(properties: Record<string, unknown>) {
	profile.innerHTML = `
		<p class="profile-kicker">${escapeHTML(properties.type)} market</p>
		<h2>${escapeHTML(properties.name)}</h2>
		<p>${escapeHTML(properties.id)} · population ${formatNumber(properties.pop)}</p>
		<dl class="profile-values">
			<div><dt>Deliverable restaurants</dt><dd>${formatNumber(properties.r)}</dd></div>
			<div><dt>Fast-food restaurants</dt><dd>${formatNumber(properties.ff)}</dd></div>
			<div><dt>Fast-food share</dt><dd>${formatPercent(properties.ffs, true)}</dd></div>
			<div><dt>Grocery listings</dt><dd>${formatNumber(properties.g)}</dd></div>
		</dl>
		<div class="profile-channels">
			${Object.entries(channelLabels).map(([key, label]) => `<p><span>${escapeHTML(label)}</span><strong>${escapeHTML(manifest.channel_codes[String(properties[key])])}</strong></p>`).join('')}
		</div>
	`;
}

async function selectParent(feature: FeatureCollection['features'][number]) {
	const id = String(feature.properties.id);
	loading.hidden = false;
	loading.textContent = `Loading ${feature.properties.name}…`;
	try {
		const response = await fetch(`${base}map/v1/children/${encodeURIComponent(id)}.geojson`);
		if (!response.ok) throw new Error(`Child data returned ${response.status}`);
		const childData = await response.json();
		if (map.getLayer('children-outline')) map.removeLayer('children-outline');
		if (map.getLayer('children-fill')) map.removeLayer('children-fill');
		if (map.getSource('children')) map.removeSource('children');
		selectedParent = id;
		selectedParentFeature = feature;
		map.addSource('children', { type: 'geojson', data: childData, promoteId: 'id' });
		map.addLayer({
			id: 'children-fill',
			type: 'fill',
			source: 'children',
			paint: { 'fill-color': paintExpression(), 'fill-opacity': 0.84 },
		});
		map.addLayer({
			id: 'children-outline',
			type: 'line',
			source: 'children',
			paint: { 'line-color': '#faf8f2', 'line-width': 0.55, 'line-opacity': 0.9 },
		});
		map.setPaintProperty('parents-fill', 'fill-opacity', 0.08);
		map.fitBounds(geometryBounds(feature.geometry), { padding: 64, maxZoom: 10, duration: 700 });
		areaSelect.value = id;
		clearButton.disabled = false;
		parentProfile(feature.properties);
		updateLegend();
	} finally {
		loading.hidden = true;
	}
}

function clearSelection() {
	if (map.getLayer('children-outline')) map.removeLayer('children-outline');
	if (map.getLayer('children-fill')) map.removeLayer('children-fill');
	if (map.getSource('children')) map.removeSource('children');
	selectedParent = null;
	selectedParentFeature = null;
	areaSelect.value = '';
	clearButton.disabled = true;
	map.setPaintProperty('parents-fill', 'fill-opacity', 0.78);
	map.fitBounds(gbBounds, { padding: 24, duration: 700 });
	profile.innerHTML = `
		<p class="profile-kicker">Great Britain overview</p>
		<h2>Select a local authority</h2>
		<p>Click the map or use the area selector to load small-area detail and exact values.</p>
		<div class="profile-method"><strong>How to read this map</strong><p>At national scale, colours summarise LAD-level values. After selection, the same control maps LSOA/Data Zone values or retailer channel states.</p></div>
	`;
	updatePaint();
}

const map = new Map({
	container: 'map',
	style: {
		version: 8,
		sources: {
			carto: {
				type: 'raster',
				tiles: ['https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png'],
				tileSize: 256,
				attribution: '© OpenStreetMap contributors © CARTO',
			},
		},
		layers: [{ id: 'carto', type: 'raster', source: 'carto', paint: { 'raster-opacity': 0.72 } }],
	},
	center: [-3.2, 54.7],
	zoom: 4.4,
	minZoom: 4,
	maxZoom: 13,
	maxBounds: [[-11.5, 48], [4.5, 61.5]],
	attributionControl: true,
});
map.addControl(new NavigationControl({ showCompass: false }), 'top-right');

map.on('load', async () => {
	try {
		[manifest, parents] = await Promise.all([
			fetch(`${base}map/v1/manifest.json`).then((response) => response.json()),
			fetch(`${base}map/v1/parents.geojson`).then((response) => response.json()),
		]);
		map.addSource('parents', { type: 'geojson', data: parents as never, promoteId: 'id' });
		map.addLayer({
			id: 'parents-fill',
			type: 'fill',
			source: 'parents',
			paint: { 'fill-color': paintExpression(), 'fill-opacity': 0.78 },
		});
		map.addLayer({
			id: 'parents-outline',
			type: 'line',
			source: 'parents',
			paint: { 'line-color': '#4d4d47', 'line-width': 0.65, 'line-opacity': 0.8 },
		});

		const options = parents.features
			.slice()
			.sort((a, b) => String(a.properties.name).localeCompare(String(b.properties.name)))
			.map((feature) => `<option value="${escapeHTML(feature.properties.id)}">${escapeHTML(feature.properties.name)}</option>`)
			.join('');
		areaSelect.innerHTML = `<option value="">Choose an area</option>${options}`;
		areaSelect.disabled = false;
		updateLegend();
		loading.hidden = true;
	} catch (error) {
		loading.textContent = 'The map data could not be loaded.';
		console.error(error);
	}
});

map.on('click', (event) => {
	const layers = ['children-fill', 'parents-fill'].filter((layer) => map.getLayer(layer));
	if (!layers.length) return;
	const [feature] = map.queryRenderedFeatures(event.point, { layers });
	if (!feature) return;
	if (feature.layer.id === 'children-fill' && feature.properties) {
		childProfile((feature as MapGeoJSONFeature).properties);
		return;
	}
	void selectParent(feature as unknown as FeatureCollection['features'][number]);
});

map.on('mousemove', (event) => {
	const layers = ['children-fill', 'parents-fill'].filter((layer) => map.getLayer(layer));
	map.getCanvas().style.cursor = layers.length && map.queryRenderedFeatures(event.point, { layers }).length
		? 'pointer'
		: '';
});

metricSelect.addEventListener('change', updatePaint);
areaSelect.addEventListener('change', () => {
	const feature = parents.features.find((item) => String(item.properties.id) === areaSelect.value);
	if (feature) void selectParent(feature);
});
clearButton.addEventListener('click', clearSelection);
