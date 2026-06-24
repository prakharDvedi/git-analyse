import 'dotenv/config';
import { Langfuse } from 'langfuse';

const langfuse = new Langfuse({
  publicKey: process.env.LANGFUSE_PUBLIC_KEY,
  secretKey: process.env.LANGFUSE_SECRET_KEY,
  baseUrl: process.env.LANGFUSE_BASE_URL || process.env.LANGFUSE_HOST,
});

async function simulateBrokenPipeline() {
  const trace = langfuse.trace({ 
    name: 'trading-pipeline', 
    metadata: { tradeId: 'T-001' } 
  });

  const step1 = trace.span({ name: 'fetch-market-data' });
  step1.end({ output: { price: 3241.50, volume: 1200000 } });

  const step2 = trace.span({ name: 'run-strategy' });
  // Simulate a failure: The AI model returned bad JSON
  step2.end({
    level: 'ERROR',
    statusMessage: 'Strategy model returned malformed JSON — missing closing brace',
    output: null,
  });

  const step3 = trace.span({ name: 'execute-trade' });
  // Downstream effect: The trade is skipped because the strategy failed
  step3.end({
    level: 'WARNING',
    statusMessage: 'Skipped — upstream strategy failed',
    output: null,
  });

  await langfuse.flushAsync();
  console.log("Broken pipeline simulated! Check your Langfuse dashboard.");
}

simulateBrokenPipeline().catch(console.error);
