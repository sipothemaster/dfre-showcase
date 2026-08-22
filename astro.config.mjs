// @ts-check
import { defineConfig } from 'astro/config';

// https://astro.build/config
export default defineConfig({
	site: 'https://sipothemaster.github.io',
	base: '/dfre-showcase',
	vite: {
		optimizeDeps: {
			exclude: ['maplibre-gl'],
		},
	},
});
