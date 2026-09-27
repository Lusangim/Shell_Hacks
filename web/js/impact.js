// Summary of the pairs currently shown in the ranked list.

const currency = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });

function roundedUsd(value) {
  return currency.format(Math.round(value / 1000) * 1000);
}

export function renderImpact(pairs) {
  const card = document.getElementById("impact-card");
  const line = document.getElementById("impact-line");
  if (!pairs.length) {
    line.textContent = "No pairs match these filters.";
    card.querySelector("details").hidden = true;
  } else {
    const ranges = pairs.filter((pair) => pair.savings?.status === "range");
    const low = ranges.reduce((sum, pair) => sum + pair.savings.low_usd, 0);
    const high = ranges.reduce((sum, pair) => sum + pair.savings.high_usd, 0);
    const utilityPairs = new Map();
    for (const pair of pairs) {
      const names = [pair.a_utility, pair.b_utility].sort();
      const key = JSON.stringify(names);
      utilityPairs.set(key, (utilityPairs.get(key) || 0) + 1);
    }
    const [top, count] = [...utilityPairs].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))[0];
    const names = JSON.parse(top);
    const savings = ranges.length
      ? `possible savings of ${roundedUsd(low)} to ${roundedUsd(high)} across ${ranges.length} pairs`
      : "no savings ranges in these pairs";
    line.textContent = `${pairs.length} pairs · ${pairs.filter((pair) => pair.cross_state).length} across the state line · ${savings} · most pairs: ${names[0]} and ${names[1]} (${count})`;
    card.querySelector("details").hidden = false;
  }
  card.hidden = false;
}
