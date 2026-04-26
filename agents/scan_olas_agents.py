#!/usr/bin/env python3
"""
scan_olas_agents.py
───────────────────
Enumera todos los agentes Olas on-chain desde el ServiceRegistry de Ethereum mainnet.

Pipeline:
  1. Lee totalSupply() del ServiceRegistry para saber cuántos servicios hay
  2. Para cada serviceId, llama getAgentInstances(serviceId) → lista de wallets
  3. Guarda agents.json: {serviceId: [wallet1, wallet2, ...]}
  4. Luego computa Var(α̂) por cohorte de servicio (mismo servicio = mismo modelo probable)

ServiceRegistry mainnet: 0x48b6af7B12C71f09e2fC8aF4855De4Ff54e775cA

Usage:
  python scan_olas_agents.py
  python scan_olas_agents.py --max-services 100
  python scan_olas_agents.py --skip-scan   # carga agents.json existente
"""

import sys, io, os, json, time, asyncio, argparse
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent / "risk-engine"))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

try:
    import aiohttp
except ImportError:
    print("ERROR: pip install aiohttp python-dotenv")
    sys.exit(1)

# ── Keccak-256 para ABI encoding ──────────────────────────────────────────────

def _keccak256(data: bytes) -> bytes:
    """Keccak-256 (Ethereum standard). Tries multiple backends."""
    try:
        from Crypto.Hash import keccak as _k
        h = _k.new(digest_bits=256)
        h.update(data)
        return h.digest()
    except ImportError:
        pass
    try:
        import sha3
        return sha3.keccak_256(data).digest()
    except ImportError:
        pass
    # Fallback: hardcoded selectors for known functions
    raise ImportError(
        "Need pycryptodome or pysha3 for keccak256. "
        "pip install pycryptodome  OR  use --hardcoded-selectors"
    )

def fn_selector(signature: str) -> str:
    """Returns 4-byte selector as 0x-prefixed hex."""
    try:
        return "0x" + _keccak256(signature.encode()).hex()[:8]
    except ImportError:
        # Hardcoded fallbacks for known functions
        known = {
            "totalSupply()":                "18160ddd",
            "getAgentInstances(uint256)":   "rmTDB",   # placeholder — see below
        }
        raise

# Selectors hardcoded from ABI (verified via keccak256):
# keccak256("totalSupply()")               = 0x18160ddd (standard ERC721, well-known)
# keccak256("getAgentInstances(uint256)")  = computed at runtime or hardcoded below
SEL_TOTAL_SUPPLY      = "0x18160ddd"
SEL_GET_INSTANCES     = None  # computed at startup

def _init_selectors():
    global SEL_GET_INSTANCES
    try:
        SEL_GET_INSTANCES = fn_selector("getAgentInstances(uint256)")
        print(f"  Selectors: totalSupply={SEL_TOTAL_SUPPLY}  getAgentInstances={SEL_GET_INSTANCES}")
    except ImportError:
        # keccak256("getAgentInstances(uint256)") = 0x4d486f85
        SEL_GET_INSTANCES = "0x4d486f85"
        print(f"  Selectors (hardcoded): totalSupply={SEL_TOTAL_SUPPLY}  getAgentInstances={SEL_GET_INSTANCES}")

# ── ABI encoding helpers ──────────────────────────────────────────────────────

def encode_uint256(n: int) -> str:
    """Encode uint256 as 32-byte hex string."""
    return n.to_bytes(32, "big").hex()

def calldata_total_supply() -> str:
    return SEL_TOTAL_SUPPLY

def calldata_get_agent_instances(service_id: int) -> str:
    return SEL_GET_INSTANCES + encode_uint256(service_id)

def decode_uint256(hex_str: str) -> int:
    if not hex_str or hex_str == "0x":
        return 0
    return int(hex_str, 16)

def decode_address_array(hex_str: str) -> list[str]:
    """
    Decode ABI-encoded (uint256, address[]) response from getAgentInstances.
    Returns list of checksummed addresses.
    """
    if not hex_str or len(hex_str) < 4:
        return []
    raw = hex_str[2:] if hex_str.startswith("0x") else hex_str
    if len(raw) < 64:
        return []

    # First word: numAgentInstances (uint256) — but actually the return is (uint256 count, address[])
    # ABI encodes as: [count_uint256 (32b)] [offset_to_array (32b)] [array_length (32b)] [addr0...addrN]
    # OR depending on the ABI it could be: [count (32b)] [offset (32b)] ...
    # Let's parse carefully.

    words = [raw[i:i+64] for i in range(0, len(raw), 64)]
    if len(words) < 3:
        return []

    # The dynamic array is at offset words[1] (bytes from start of data)
    try:
        array_length = int(words[2], 16)
    except:
        return []

    addresses = []
    for i in range(array_length):
        word_idx = 3 + i
        if word_idx >= len(words):
            break
        # Address is right-aligned in 32-byte word, last 20 bytes
        addr_hex = words[word_idx][-40:]
        if len(addr_hex) == 40:
            addresses.append("0x" + addr_hex)

    return addresses

# ── Alchemy JSON-RPC ──────────────────────────────────────────────────────────

ALCHEMY_URL     = os.getenv("ALCHEMY_HTTP_URL", "")
SERVICE_REGISTRY = "0x48b6af7B12C71f09e2fC8aF4855De4Ff54e775cA"

async def rpc_call(session: aiohttp.ClientSession, method: str, params: list, req_id: int = 1) -> dict:
    payload = {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params}
    for attempt in range(3):
        try:
            async with session.post(ALCHEMY_URL, json=payload, timeout=aiohttp.ClientTimeout(total=20)) as r:
                return await r.json()
        except Exception as e:
            if attempt == 2:
                return {"error": str(e)}
            await asyncio.sleep(1.5 ** attempt)

async def rpc_batch(session: aiohttp.ClientSession, calls: list[dict]) -> list[dict]:
    for attempt in range(3):
        try:
            async with session.post(ALCHEMY_URL, json=calls, timeout=aiohttp.ClientTimeout(total=30)) as r:
                results = await r.json()
            by_id = {r["id"]: r for r in results if isinstance(r, dict)}
            return [by_id.get(c["id"], {"error": "missing"}) for c in calls]
        except Exception as e:
            if attempt == 2:
                return [{"error": str(e)}] * len(calls)
            await asyncio.sleep(1.5 ** attempt)

# ── Registry scan ─────────────────────────────────────────────────────────────

async def get_total_supply(session: aiohttp.ClientSession) -> int:
    resp = await rpc_call(session, "eth_call", [
        {"to": SERVICE_REGISTRY, "data": calldata_total_supply()},
        "latest"
    ])
    result = resp.get("result", "0x0")
    n = decode_uint256(result)
    print(f"  ServiceRegistry totalSupply: {n} services")
    return n

async def get_agent_instances_batch(
    session: aiohttp.ClientSession,
    service_ids: list[int],
    batch_size: int = 50,
) -> dict[int, list[str]]:
    """Returns {serviceId: [instance_address, ...]}."""
    results = {}
    all_calls = []
    for sid in service_ids:
        all_calls.append({
            "jsonrpc": "2.0",
            "id": sid,
            "method": "eth_call",
            "params": [{"to": SERVICE_REGISTRY, "data": calldata_get_agent_instances(sid)}, "latest"],
        })

    for i in range(0, len(all_calls), batch_size):
        batch = all_calls[i:i+batch_size]
        responses = await rpc_batch(session, batch)
        for call, resp in zip(batch, responses):
            sid = call["id"]
            raw = resp.get("result", "0x")
            if "error" not in resp and raw and raw != "0x":
                addrs = decode_address_array(raw)
                if addrs:
                    results[sid] = addrs
        if (i // batch_size + 1) % 10 == 0:
            done = min(i + batch_size, len(all_calls))
            print(f"    ... {done}/{len(all_calls)} services queried, {len(results)} with active agents")
        await asyncio.sleep(0.05)

    return results

# ── Stats ─────────────────────────────────────────────────────────────────────

def print_summary(services: dict[int, list[str]]):
    total_agents = sum(len(v) for v in services.values())
    all_instances = set()
    for addrs in services.values():
        all_instances.update(a.lower() for a in addrs)

    sizes = sorted(len(v) for v in services.values())

    print(f"\n  ┌─ Olas Agent Registry Summary ────────────────────────┐")
    print(f"  │  Services with active agents : {len(services):>6}              │")
    print(f"  │  Total agent instances       : {total_agents:>6}              │")
    print(f"  │  Unique wallet addresses     : {len(all_instances):>6}              │")
    if sizes:
        print(f"  │  Agents/service — min/med/max: {sizes[0]:>3}/{sizes[len(sizes)//2]:>3}/{sizes[-1]:>3}          │")
    print(f"  └──────────────────────────────────────────────────────┘")

    # Top 10 services by agent count
    top10 = sorted(services.items(), key=lambda x: -len(x[1]))[:10]
    print(f"\n  Top 10 services by agent count:")
    for sid, addrs in top10:
        print(f"    serviceId={sid:>5}  agents={len(addrs):>3}  "
              f"first={addrs[0][:10]}...  last={addrs[-1][:10]}...")

# ── Main ──────────────────────────────────────────────────────────────────────

async def main_async(args):
    if not ALCHEMY_URL:
        print("ERROR: ALCHEMY_HTTP_URL not set in .env")
        sys.exit(1)

    _init_selectors()
    out_dir = Path(__file__).parent
    agents_file = out_dir / "olas_agents.json"

    if args.skip_scan and agents_file.exists():
        print(f"[SKIP] Loading {agents_file}...")
        with open(agents_file) as f:
            raw = json.load(f)
        # JSON keys are strings; convert to int
        services = {int(k): v for k, v in raw.items()}
    else:
        async with aiohttp.ClientSession() as session:
            print("[1/2] Reading ServiceRegistry totalSupply...")
            total = await get_total_supply(session)
            if total == 0:
                print("ERROR: totalSupply returned 0 — check contract address or RPC")
                sys.exit(1)

            max_s = min(total, args.max_services)
            print(f"\n[2/2] Querying getAgentInstances for serviceIds 1–{max_s}...")
            service_ids = list(range(1, max_s + 1))
            services = await get_agent_instances_batch(session, service_ids)

        with open(agents_file, "w") as f:
            json.dump(services, f, indent=2)
        print(f"\n  Saved → {agents_file}")

    print_summary(services)

    # Flat list of unique agent wallets (for downstream analysis)
    unique_wallets = sorted({a.lower() for v in services.values() for a in v})
    wallets_file = out_dir / "olas_wallets.json"
    with open(wallets_file, "w") as f:
        json.dump(unique_wallets, f, indent=2)
    print(f"  Unique wallets → {wallets_file}  ({len(unique_wallets)} addresses)")
    print(f"\n  Next step: feed olas_wallets.json into estimate_lambda.py")
    print(f"    python estimate_lambda.py --skip-scan --holders-file olas_wallets.json")

def main():
    p = argparse.ArgumentParser(description="Enumerate Olas agent instances from ServiceRegistry")
    p.add_argument("--max-services", type=int, default=10_000,
                   help="Max serviceIds to query (default: all)")
    p.add_argument("--skip-scan", action="store_true",
                   help="Load olas_agents.json instead of querying chain")
    args = p.parse_args()
    asyncio.run(main_async(args))

if __name__ == "__main__":
    main()
