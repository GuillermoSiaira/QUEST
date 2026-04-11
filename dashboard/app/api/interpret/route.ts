import Anthropic from "@anthropic-ai/sdk";
import type { EpochStatus } from "@/lib/types";

const client = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
});

const SYSTEM_PROMPT = `You are QUEST, a macroprudential risk analyst for the Ethereum ecosystem.
You monitor validator slashing events and detect "Grey Zone" scenarios — situations where slashing losses
are masked by MEV/CL rewards, causing Lido's oracle to miss entering bunker mode (a documented vulnerability
in lido-oracle's safe_border.py).

When analyzing epoch data:
- Be concise: 2-4 sentences maximum
- Lead with the risk status
- If HEALTHY and no slashings: brief confirmation, mention key stats
- If GREY_ZONE: explain exactly why it's dangerous, what's being masked, and the mechanism
- If CRITICAL: clear alert, quantify the exposure
- Always mention Grey Zone Score and what it means in context
- Use plain language accessible to non-technical Ethereum users
- Do not repeat field names verbatim — translate them to human concepts
- Do not use markdown formatting, bold, or bullet points — plain prose only`;

function formatEpochForPrompt(epoch: EpochStatus): string {
  const score = epoch.risk.grey_zone_score;
  const scoreStr = score > 999 ? "infinite (extreme risk)" : score.toFixed(4);

  return `
Epoch: ${epoch.epoch}
Risk Level: ${epoch.risk.risk_level}
Grey Zone Score: ${scoreStr}
Active Validators: ${epoch.total_validators.toLocaleString()}
Total Staked: ${(epoch.total_active_balance_eth / 1e6).toFixed(2)}M ETH
Participation Rate: ${(epoch.participation_rate * 100).toFixed(2)}%
Slashed Validators: ${epoch.slashed_validators}
Gross Slashing Loss: ${epoch.risk.gross_slashing_loss_eth.toFixed(4)} ETH
CL Rewards: ${epoch.risk.has_rewards_data ? epoch.risk.cl_rewards_eth.toFixed(4) + " ETH" : "not yet available (first cycle)"}
Burned ETH (EIP-1559): ${epoch.risk.burned_eth.toFixed(4)} ETH
Net Rebase: ${epoch.net_rebase_eth !== null ? epoch.net_rebase_eth.toFixed(4) + " ETH" : "pending"}
Lido TVL: ${epoch.lido_tvl_eth.toLocaleString(undefined, { maximumFractionDigits: 0 })} ETH
Grey Zone Active: ${epoch.is_grey_zone}
`.trim();
}

export async function POST(request: Request) {
  try {
    const text = await request.text();
    if (!text || text.trim().length === 0) {
      return new Response("Empty body", { status: 400 });
    }
    const epoch: EpochStatus = JSON.parse(text);

    const stream = await client.messages.stream({
      model: "claude-haiku-4-5-20251001",
      max_tokens: 200,
      system: SYSTEM_PROMPT,
      messages: [
        {
          role: "user",
          content: `Analyze this epoch and give a brief risk assessment:\n\n${formatEpochForPrompt(epoch)}`,
        },
      ],
    });

    const encoder = new TextEncoder();
    const readable = new ReadableStream({
      async start(controller) {
        for await (const chunk of stream) {
          if (
            chunk.type === "content_block_delta" &&
            chunk.delta.type === "text_delta"
          ) {
            controller.enqueue(encoder.encode(chunk.delta.text));
          }
        }
        controller.close();
      },
    });

    return new Response(readable, {
      headers: {
        "Content-Type": "text/plain; charset=utf-8",
        "Transfer-Encoding": "chunked",
      },
    });
  } catch (err) {
    console.error("Interpret API error:", err);
    return new Response("Error generating interpretation", { status: 500 });
  }
}
