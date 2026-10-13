"""
Builds the entity-resolution benchmark: labeled pairs of company records.

label 1 = same legal entity (including renames), label 0 = different entities.

Pair categories:
  positives  format     legal-suffix / casing / punctuation variants ("Microsoft Corp" vs "MICROSOFT CORPORATION")
             acronym    initialisms ("IBM" vs "International Business Machines")
             ticker     stock tickers ("MSFT" vs "Microsoft")
             typo       one-character typos
             rebrand    renamed companies ("Facebook Inc" vs "Meta Platforms")
  negatives  subsidiary parent vs subsidiary ("Microsoft" vs "LinkedIn") - related, not the same
             lookalike  similar names, different companies ("HP Inc" vs "Hewlett Packard Enterprise")
             competitor same industry ("Visa" vs "Mastercard")
             random     unrelated companies

Websites are dropped from one or both records for many pairs so a website
match can't solve the benchmark on its own.

The split is by ENTITY GROUP, not by pair: every pair whose first record
belongs to a dev entity is in dev, so names seen while tuning thresholds
never leak into the test set.

Run:  python -m src.evaluation.build_benchmark
"""
import csv
import random
from itertools import combinations
from pathlib import Path

SEED = 7
OUT = Path("data/benchmark/pairs.csv")

# key: (canonical name, website, [variants], ticker or None)
ENTITIES = {
    "microsoft": ("Microsoft Corporation", "microsoft.com", ["Microsoft Corp", "Microsoft", "MICROSOFT CORP."], "MSFT"),
    "alphabet": ("Alphabet Inc.", "abc.xyz", ["Alphabet", "Alphabet Inc"], "GOOGL"),
    "google": ("Google LLC", "google.com", ["Google", "Google Inc."], None),
    "amazon": ("Amazon.com, Inc.", "amazon.com", ["Amazon", "Amazon.com", "Amazon Inc"], "AMZN"),
    "aws": ("Amazon Web Services, Inc.", "aws.amazon.com", ["AWS", "Amazon Web Services"], None),
    "apple": ("Apple Inc.", "apple.com", ["Apple", "Apple Computer, Inc."], "AAPL"),
    "meta": ("Meta Platforms, Inc.", "meta.com", ["Meta", "Meta Platforms"], "META"),
    "instagram": ("Instagram, LLC", "instagram.com", ["Instagram"], None),
    "whatsapp": ("WhatsApp LLC", "whatsapp.com", ["WhatsApp", "Whats App"], None),
    "netflix": ("Netflix, Inc.", "netflix.com", ["Netflix"], "NFLX"),
    "nvidia": ("NVIDIA Corporation", "nvidia.com", ["Nvidia", "NVIDIA Corp"], "NVDA"),
    "intel": ("Intel Corporation", "intel.com", ["Intel", "Intel Corp"], "INTC"),
    "amd": ("Advanced Micro Devices, Inc.", "amd.com", ["AMD", "Advanced Micro Devices"], None),
    "ibm": ("International Business Machines Corporation", "ibm.com",
            ["IBM", "IBM Corp", "International Business Machines"], None),
    "oracle": ("Oracle Corporation", "oracle.com", ["Oracle", "Oracle Corp"], "ORCL"),
    "salesforce": ("Salesforce, Inc.", "salesforce.com", ["Salesforce", "Salesforce.com Inc"], "CRM"),
    "adobe": ("Adobe Inc.", "adobe.com", ["Adobe", "Adobe Systems Incorporated"], "ADBE"),
    "cisco": ("Cisco Systems, Inc.", "cisco.com", ["Cisco", "Cisco Systems"], "CSCO"),
    "hp": ("HP Inc.", "hp.com", ["HP", "Hewlett-Packard Company"], "HPQ"),
    "hpe": ("Hewlett Packard Enterprise Company", "hpe.com", ["HPE", "Hewlett Packard Enterprise"], None),
    "jnj": ("Johnson & Johnson", "jnj.com", ["Johnson and Johnson", "J&J", "Johnson & Johnson Inc"], "JNJ"),
    "johnson_controls": ("Johnson Controls International plc", "johnsoncontrols.com",
                         ["Johnson Controls"], "JCI"),
    "pg": ("The Procter & Gamble Company", "pg.com", ["Procter and Gamble", "P&G", "Procter & Gamble Co"], None),
    "ge": ("General Electric Company", "ge.com", ["GE", "General Electric"], None),
    "gm": ("General Motors Company", "gm.com", ["GM", "General Motors"], None),
    "general_mills": ("General Mills, Inc.", "generalmills.com", ["General Mills"], "GIS"),
    "delta": ("Delta Air Lines, Inc.", "delta.com", ["Delta Air Lines", "Delta Airlines"], "DAL"),
    "delta_faucet": ("Delta Faucet Company", "deltafaucet.com", ["Delta Faucet"], None),
    "american_airlines": ("American Airlines Group Inc.", "aa.com", ["American Airlines"], "AAL"),
    "amex": ("American Express Company", "americanexpress.com", ["American Express", "Amex"], "AXP"),
    "jpmorgan": ("JPMorgan Chase & Co.", "jpmorganchase.com", ["JPMorgan Chase", "JP Morgan Chase & Co"], "JPM"),
    "morgan_stanley": ("Morgan Stanley", "morganstanley.com", ["Morgan Stanley & Co."], None),
    "goldman": ("The Goldman Sachs Group, Inc.", "goldmansachs.com", ["Goldman Sachs", "Goldman Sachs Group"], None),
    "bofa": ("Bank of America Corporation", "bankofamerica.com", ["Bank of America", "BofA"], "BAC"),
    "coca_cola": ("The Coca-Cola Company", "coca-colacompany.com", ["Coca-Cola", "Coca Cola Co"], "KO"),
    "coca_cola_ep": ("Coca-Cola Europacific Partners plc", "cocacolaep.com",
                     ["Coca-Cola Europacific Partners"], "CCEP"),
    "pepsico": ("PepsiCo, Inc.", "pepsico.com", ["PepsiCo", "Pepsi Co"], "PEP"),
    "walmart": ("Walmart Inc.", "walmart.com", ["Walmart", "Wal-Mart Stores, Inc."], "WMT"),
    "target": ("Target Corporation", "target.com", ["Target", "Target Corp"], "TGT"),
    "target_hospitality": ("Target Hospitality Corp.", "targethospitality.com", ["Target Hospitality"], None),
    "openai": ("OpenAI", "openai.com", ["Open AI", "OpenAI Inc"], None),
    "anthropic": ("Anthropic PBC", "anthropic.com", ["Anthropic"], None),
    "tesla": ("Tesla, Inc.", "tesla.com", ["Tesla", "Tesla Motors"], "TSLA"),
    "spacex": ("Space Exploration Technologies Corp.", "spacex.com", ["SpaceX", "Space X"], None),
    "uber": ("Uber Technologies, Inc.", "uber.com", ["Uber"], "UBER"),
    "lyft": ("Lyft, Inc.", "lyft.com", ["Lyft"], "LYFT"),
    "visa": ("Visa Inc.", "visa.com", ["Visa"], None),
    "mastercard": ("Mastercard Incorporated", "mastercard.com", ["Mastercard", "MasterCard Inc"], "MA"),
    "block": ("Block, Inc.", "block.xyz", ["Block"], None),
    "square_enix": ("Square Enix Holdings Co., Ltd.", "square-enix.com", ["Square Enix"], None),
    "paypal": ("PayPal Holdings, Inc.", "paypal.com", ["PayPal", "Paypal Inc"], "PYPL"),
    "snowflake": ("Snowflake Inc.", "snowflake.com", ["Snowflake", "Snowflake Computing"], "SNOW"),
    "databricks": ("Databricks, Inc.", "databricks.com", ["Databricks"], None),
    "teradata": ("Teradata Corporation", "teradata.com", ["Teradata", "Teradata Corp"], "TDC"),
    "linkedin": ("LinkedIn Corporation", "linkedin.com", ["LinkedIn", "Linked In"], None),
    "github": ("GitHub, Inc.", "github.com", ["GitHub", "Github Inc"], None),
    "youtube": ("YouTube, LLC", "youtube.com", ["YouTube", "You Tube"], None),
    "deepmind": ("DeepMind Technologies Limited", "deepmind.google", ["DeepMind", "DeepMind Technologies"], None),
    "whole_foods": ("Whole Foods Market, Inc.", "wholefoodsmarket.com", ["Whole Foods", "Whole Foods Market"], None),
    "toyota": ("Toyota Motor Corporation", "toyota.com", ["Toyota", "Toyota Motor Corp"], "TM"),
    "ford": ("Ford Motor Company", "ford.com", ["Ford", "Ford Motor Co"], None),
    "boeing": ("The Boeing Company", "boeing.com", ["Boeing", "Boeing Co"], "BA"),
    "samsung": ("Samsung Electronics Co., Ltd.", "samsung.com", ["Samsung Electronics", "Samsung"], None),
    "sony": ("Sony Group Corporation", "sony.com", ["Sony", "Sony Corporation"], "SONY"),
    "accenture": ("Accenture plc", "accenture.com", ["Accenture"], "ACN"),
    "deloitte": ("Deloitte Touche Tohmatsu Limited", "deloitte.com", ["Deloitte", "Deloitte LLP"], None),
}

# same legal entity under a former name
REBRANDS = [
    ("meta", "Facebook, Inc.", "facebook.com"),
    ("block", "Square, Inc.", "squareup.com"),
]
# acronym variants that are really initialisms of the full name
ACRONYM_VARIANTS = {"ibm": "IBM", "amd": "AMD", "ge": "GE", "gm": "GM", "hpe": "HPE",
                    "pg": "P&G", "jnj": "J&J", "aws": "AWS", "bofa": "BofA"}

SUBSIDIARIES = [("microsoft", "linkedin"), ("microsoft", "github"), ("alphabet", "google"),
                ("google", "youtube"), ("alphabet", "deepmind"), ("amazon", "aws"),
                ("amazon", "whole_foods"), ("meta", "instagram"), ("meta", "whatsapp")]
LOOKALIKES = [("hp", "hpe"), ("jnj", "johnson_controls"), ("ge", "gm"), ("ge", "general_mills"),
              ("gm", "general_mills"), ("delta", "delta_faucet"), ("american_airlines", "amex"),
              ("jpmorgan", "morgan_stanley"), ("coca_cola", "coca_cola_ep"), ("target", "target_hospitality"),
              ("block", "square_enix")]
COMPETITORS = [("visa", "mastercard"), ("uber", "lyft"), ("coca_cola", "pepsico"), ("walmart", "target"),
               ("intel", "amd"), ("goldman", "morgan_stanley"), ("snowflake", "databricks"),
               ("openai", "anthropic"), ("toyota", "ford"), ("nvidia", "amd"), ("oracle", "salesforce"),
               ("jpmorgan", "bofa"), ("sony", "samsung"), ("accenture", "deloitte"), ("paypal", "block")]


def _typo(rng, name):
    """One realistic typo: drop, swap, or double a letter inside a word."""
    letters = [i for i, ch in enumerate(name) if ch.isalpha()]
    if len(letters) < 5:
        return None
    i = rng.choice(letters[1:-1])
    op = rng.choice(["drop", "swap", "double"])
    if op == "drop":
        return name[:i] + name[i + 1:]
    if op == "swap" and name[i + 1].isalpha():
        return name[:i] + name[i + 1] + name[i] + name[i + 2:]
    return name[:i] + name[i] + name[i:]


def _records(key):
    canonical, site, variants, ticker = ENTITIES[key]
    return [canonical] + variants, site, ticker


def _maybe_site(rng, site, keep_prob):
    return site if rng.random() < keep_prob else ""


def build(seed: int = SEED):
    rng = random.Random(seed)
    rows, seen = [], set()

    def add(key_a, name_a, key_b, name_b, label, category, site_a="", site_b=""):
        pair = tuple(sorted([name_a.lower(), name_b.lower()]))
        if name_a.lower() == name_b.lower() or pair in seen:
            return
        seen.add(pair)
        rows.append({"group": key_a, "a_name": name_a, "a_website": site_a, "b_name": name_b,
                     "b_website": site_b, "label": label, "category": category})

    for key in ENTITIES:
        names, site, ticker = _records(key)

        # format variants: every pair of known names, website often missing on one side
        for a, b in combinations(names, 2):
            category = "acronym" if ACRONYM_VARIANTS.get(key) in (a, b) else "format"
            add(key, a, key, b, 1, category, _maybe_site(rng, site, 0.5), _maybe_site(rng, site, 0.3))

        if ticker:
            add(key, names[0], key, ticker, 1, "ticker", _maybe_site(rng, site, 0.4), "")

        typo = _typo(rng, rng.choice(names[:2]))
        if typo:
            add(key, names[0], key, typo, 1, "typo", "", _maybe_site(rng, site, 0.3))

    for key, old_name, old_site in REBRANDS:
        names, site, _ = _records(key)
        add(key, names[0], key, old_name, 1, "rebrand", _maybe_site(rng, site, 0.5), old_site or "")

    for category, pairs in (("subsidiary", SUBSIDIARIES), ("lookalike", LOOKALIKES),
                            ("competitor", COMPETITORS)):
        for ka, kb in pairs:
            names_a, site_a, _ = _records(ka)
            names_b, site_b, _ = _records(kb)
            for _ in range(2):  # two name variants per related pair
                add(ka, rng.choice(names_a), kb, rng.choice(names_b), 0, category,
                    _maybe_site(rng, site_a, 0.4), _maybe_site(rng, site_b, 0.4))

    keys = list(ENTITIES)
    related = {frozenset(p) for p in SUBSIDIARIES + LOOKALIKES + COMPETITORS}
    target_random = 120
    while sum(r["category"] == "random" for r in rows) < target_random:
        ka, kb = rng.sample(keys, 2)
        if frozenset((ka, kb)) in related:
            continue
        add(ka, rng.choice(_records(ka)[0]), kb, rng.choice(_records(kb)[0]), 0, "random",
            _maybe_site(rng, ENTITIES[ka][1], 0.3), _maybe_site(rng, ENTITIES[kb][1], 0.3))

    # group split: half the entities are dev, half test
    groups = sorted({r["group"] for r in rows})
    rng.shuffle(groups)
    dev_groups = set(groups[: len(groups) // 2])
    for r in rows:
        r["split"] = "dev" if r["group"] in dev_groups else "test"
    return rows


def write(rows, path: Path = OUT):
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["group", "split", "category", "label", "a_name", "a_website", "b_name", "b_website"]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def load(path: Path = OUT):
    with open(path) as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["label"] = int(r["label"])
    return rows


if __name__ == "__main__":
    rows = build()
    write(rows)
    from collections import Counter
    print(f"{len(rows)} pairs -> {OUT}")
    print("labels:", Counter(r["label"] for r in rows))
    print("splits:", Counter(r["split"] for r in rows))
    print("categories:", dict(Counter(r["category"] for r in rows)))
