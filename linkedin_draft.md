# LinkedIn draft: beliefcollapse (ready to queue after repo goes live)

Your AI agents agree in public. What do they believe in private?

A paper this week showed that in a 10-agent debate, one bad actor confidently asserting a plausible lie made 44.8% of the honest agents privately believe it. Their public messages often still disagreed. The corruption never appears in the transcript.

Every audit tool I have seen measures what agents say. So I built the first open harness that measures what they believe: after each discussion round, every agent gets a hidden private probe its peers never see, and the harness reports private-vs-public contamination per agent.

beliefcollapse: run a 10-agent factual discussion with 0, 1, or 3 adversaries, get a contamination report. Swappable models (Gemini free tier, Groq, any OpenAI-compatible endpoint), 30-second mock demo, 25/25 tests green, honest eval configs included.

Pipeline validation recovers the paper's own rates (0.0% / 46.0% / 64.3% at k=0/1/3 vs their 0.6% / 44.8% / 60.5%), so the measurement is sound. Live-model numbers are next, on free tiers, $0 as always.

If you run multi-agent debate, review, or coding teams, this is the audit you did not know you needed.

github.com/habib-analyst/beliefcollapse
