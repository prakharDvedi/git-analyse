import 'dotenv/config';
import { generateObject } from 'ai';
import { createOpenRouter } from '@openrouter/ai-sdk-provider';
import { Langfuse } from 'langfuse';
import { z } from 'zod';

const openrouter = createOpenRouter({ apiKey: process.env.OPENROUTER_API_KEY });

const langfuse = new Langfuse({
  publicKey: process.env.LANGFUSE_PUBLIC_KEY,
  secretKey: process.env.LANGFUSE_SECRET_KEY,
  baseUrl: process.env.LANGFUSE_BASE_URL || process.env.LANGFUSE_HOST,
});

// ── schemas ───────────────────────────────────────────────────────────────────

const IntentSchema = z.object({
  action: z.enum(['buy', 'sell', 'analyse', 'unknown']),
  token: z.string(),
  confidence: z.number().min(0).max(1),
});

const AnalysisSchema = z.object({
  recommendation: z.string(),
  riskLevel: z.enum(['low', 'medium', 'high']),
  reasoning: z.string(),
});

// ── pipeline ──────────────────────────────────────────────────────────────────

async function tradingPipeline(userQuery: string) {
  // FIX 3: attach metadata to root trace — userId + raw query
  const trace = langfuse.trace({
    name: 'full-trading-pipeline',
    metadata: {
      userQuery,
      environment: process.env.NODE_ENV ?? 'development',
    },
  });

  // ── Step 1: parse intent ────────────────────────────────────────────────────

  const intentPrompt = `Parse this trading query and extract intent.
Query: "${userQuery}"
Return action (buy/sell/analyse/unknown), the token symbol, and your confidence 0-1.
If the query is vague or no real token is mentioned, return action=unknown and low confidence.`;

  // FIX 1: log input on generation before the call
  const intentSpan = trace.generation({
    name: 'parse-intent',
    model: 'openrouter/auto',
    input: intentPrompt,  // ← now visible in Langfuse
  });

  let intent: z.infer<typeof IntentSchema>;

  try {
    const result = await generateObject({
      model: openrouter('openrouter/auto'),
      schema: IntentSchema,
      prompt: intentPrompt,
    });

    intent = result.object;

    // FIX 2: log token usage
    intentSpan.end({
      output: intent,
      usage: {
        promptTokens: result.usage?.promptTokens,
        completionTokens: result.usage?.completionTokens,
      },
    });

  } catch (err: any) {
    // FIX 5: log error on the span so Langfuse shows it red
    intentSpan.end({
      level: 'ERROR',
      statusMessage: `parse-intent failed: ${err.message}`,
      output: null,
    });
    await langfuse.flushAsync();
    throw new Error(`Pipeline aborted — parse-intent failed: ${err.message}`);
  }

  // ── Step 2: confidence check ────────────────────────────────────────────────

  // FIX 4: log the actual confidence score as output
  if (intent.confidence < 0.7) {
    trace.span({ name: 'confidence-check' }).end({
      level: 'WARNING',
      statusMessage: `Low confidence: ${intent.confidence} — flagging for review`,
      output: {               // ← now visible in Langfuse
        confidence: intent.confidence,
        threshold: 0.7,
        action: intent.action,
        token: intent.token,
      },
    });
  }

  // FIX 6: abort early if intent is unknown — no point analysing garbage input
  if (intent.action === 'unknown' || intent.confidence < 0.4) {
    trace.span({ name: 'pipeline-aborted' }).end({
      level: 'WARNING',
      statusMessage: 'Aborting — intent unknown or confidence too low to proceed',
      output: { reason: 'low_confidence', intent },
    });
    await langfuse.flushAsync();
    return {
      recommendation: 'Cannot generate analysis — query too vague. Please specify a token and action.',
      riskLevel: 'high' as const,
      reasoning: `Intent parsing returned action=${intent.action} with confidence=${intent.confidence}`,
    };
  }

  // ── Step 3: generate analysis ───────────────────────────────────────────────

  const analysisPrompt = `You are a DeFi trading analyst. Be concise.
Action: ${intent.action}
Token: ${intent.token}
Confidence in user intent: ${intent.confidence}

Provide a brief recommendation, risk level, and reasoning.`;

  // FIX 1: log input on generation
  const analysisSpan = trace.generation({
    name: 'generate-analysis',
    model: 'openrouter/auto',
    input: analysisPrompt,  // ← now visible in Langfuse
  });

  let analysis: z.infer<typeof AnalysisSchema>;

  try {
    const result = await generateObject({
      model: openrouter('openrouter/auto'),
      schema: AnalysisSchema,
      prompt: analysisPrompt,
    });

    analysis = result.object;

    // FIX 2: log token usage
    analysisSpan.end({
      output: analysis,
      usage: {
        promptTokens: result.usage?.promptTokens,
        completionTokens: result.usage?.completionTokens,
      },
    });

  } catch (err: any) {
    // FIX 5: log error
    analysisSpan.end({
      level: 'ERROR',
      statusMessage: `generate-analysis failed: ${err.message}`,
      output: null,
    });
    await langfuse.flushAsync();
    throw new Error(`Pipeline aborted — generate-analysis failed: ${err.message}`);
  }

  // log final result on root trace so output column is populated
  trace.update({ output: analysis });

  await langfuse.flushAsync();
  return analysis;
}

// ── main ──────────────────────────────────────────────────────────────────────

async function main() {
  console.log('--- TRACE 1: High Confidence ---');
  const run1 = await tradingPipeline('I want to long ETH with 10x leverage');
  console.log(JSON.stringify(run1, null, 2));

  console.log('\n--- TRACE 2: Low Confidence ---');
  const run2 = await tradingPipeline('maybe do something with crypto idk');
  console.log(JSON.stringify(run2, null, 2));

  console.log('\n--- TRACE 3: Unknown action abort ---');
  const run3 = await tradingPipeline('idk man just do whatever');
  console.log(JSON.stringify(run3, null, 2));
}

main().catch(console.error);