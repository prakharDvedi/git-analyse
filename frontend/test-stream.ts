import 'dotenv/config';
import { streamText } from 'ai';
import { createOpenRouter } from '@openrouter/ai-sdk-provider';

const openrouter = createOpenRouter({
  apiKey: process.env.OPENROUTER_API_KEY,
});

async function main() {
  const result = await streamText({
    model: openrouter('meta-llama/llama-4-scout-17b-16e-instruct'),
    prompt: 'explain what a DeFi liquidity pool is in 3 sentences',
  });

  for await (const chunk of result.textStream) {
    process.stdout.write(chunk);
  }
}

main().catch(console.error);