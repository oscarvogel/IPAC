const PRINT_TARGETS = new Set(['receipt', 'cash-summary'])

export function printDocument(target) {
  if (!PRINT_TARGETS.has(target) || typeof window === 'undefined') return

  const root = document.documentElement
  root.dataset.printTarget = target
  const clearTarget = () => {
    if (root.dataset.printTarget === target) {
      delete root.dataset.printTarget
    }
  }

  window.addEventListener('afterprint', clearTarget, { once: true })
  window.print()
}
