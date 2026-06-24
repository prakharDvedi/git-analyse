import 'dotenv/config';
import { generateObject } from 'ai';
import { createOpenRouter } from '@openrouter/ai-sdk-provider';
import { z } from 'zod';

const openrouter = createOpenRouter({
  apiKey: process.env.OPENROUTER_API_KEY,
});

async function main() {
  const { object } = await generateObject({
model: openrouter('openrouter/auto'),
    schema: z.object({
      bugs: z.array(z.object({
        location: z.string(),
        severity: z.enum(['low', 'medium', 'high', 'critical']),
        description: z.string(),
      })),
      summary: z.string(),
    }),
    prompt: 'analyse this TypeScript snippet for bugs: const x = undefined; console.log(x.toString())',
  });

  console.log(JSON.stringify(object, null, 2));
}

main().catch(console.error);