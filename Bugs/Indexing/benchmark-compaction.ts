// Micro-benchmark: serial vs batched-concurrent chunk summarization pattern.
// This mirrors the change made to compaction-chunks.ts.

import { Effect } from "effect"

const CONCURRENCY = 3
const CHUNK_COUNT = 9
const CHUNK_DELAY_MS = 100

function summarize(index: number): Effect.Effect<string> {
  return Effect.promise(
    () => new Promise<string>((resolve) => setTimeout(() => resolve(`summary-${index}`), CHUNK_DELAY_MS)),
  )
}

function serial(): Effect.Effect<string[]> {
  return Effect.gen(function* () {
    const partial: string[] = []
    for (let i = 0; i < CHUNK_COUNT; i++) {
      const result = yield* summarize(i)
      partial.push(result)
    }
    return partial
  })
}

function batchedConcurrent(): Effect.Effect<string[]> {
  return Effect.gen(function* () {
    const chunks = Array.from({ length: CHUNK_COUNT }, (_, i) => i)
    const partial: string[] = []
    for (let i = 0; i < chunks.length; i += CONCURRENCY) {
      const batch = chunks.slice(i, i + CONCURRENCY)
      const results = yield* Effect.forEach(batch, (index) => summarize(index), { concurrency: batch.length })
      partial.push(...results)
    }
    return partial
  })
}

async function measure(name: string, program: Effect.Effect<string[]>) {
  const start = performance.now()
  const result = await Effect.runPromise(program)
  const elapsed = performance.now() - start
  console.log(`${name}: ${elapsed.toFixed(1)} ms for ${result.length} chunks`)
  return elapsed
}

async function main() {
  console.log(`Chunks: ${CHUNK_COUNT}, concurrency: ${CONCURRENCY}, simulated chunk latency: ${CHUNK_DELAY_MS} ms`)
  console.log(`Expected serial time: ~${CHUNK_COUNT * CHUNK_DELAY_MS} ms`)
  console.log(`Expected batched-concurrent time: ~${Math.ceil(CHUNK_COUNT / CONCURRENCY) * CHUNK_DELAY_MS} ms`)
  console.log("")

  const serialMs = await measure("Serial (old regression)", serial())
  const concurrentMs = await measure("Batched concurrent (fix)", batchedConcurrent())

  console.log("")
  console.log(`Speedup: ${(serialMs / concurrentMs).toFixed(2)}×`)
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
