const PRINT_TARGETS = new Set(['receipt', 'cash-summary'])

export function printDocument(target, element) {
  if (!PRINT_TARGETS.has(target) || typeof window === 'undefined') return

  const root = document.documentElement
  root.dataset.printTarget = target
  const documents = [...document.querySelectorAll(target === 'receipt' ? 'body > .print-recibo' : 'body > .cash-print-summary')]
  const selected = element || documents.find(node => node.dataset.hasReceipt === 'true') || documents[0]
  documents.forEach(node => { if (node !== selected) node.dataset.printExcluded = 'true' })
  const clearTarget = () => {
    if (root.dataset.printTarget === target) {
      delete root.dataset.printTarget
      documents.forEach(node => delete node.dataset.printExcluded)
    }
  }

  window.addEventListener('afterprint', clearTarget, { once: true })
  window.print()
}
