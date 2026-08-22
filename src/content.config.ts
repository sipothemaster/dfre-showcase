import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const analyses = defineCollection({
	loader: glob({ pattern: '**/*.md', base: './src/content/analyses' }),
	schema: z.object({
		title: z.string(),
		dek: z.string(),
		order: z.number().int().positive(),
		status: z.enum(['published', 'draft']),
		claimStatus: z.enum(['descriptive', 'associational', 'illustrative']),
		geography: z.string(),
		period: z.string(),
		primaryMetric: z.string(),
		figure: z.string().optional(),
		figureAlt: z.string().optional(),
		sourceRepository: z.string(),
		limitations: z.array(z.string()).min(1),
	}),
});

export const collections = { analyses };
