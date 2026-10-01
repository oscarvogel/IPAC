import { existsSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

// Regresion del Issue #56: por encima del breakpoint de 2000px, el toolbar de
// Alumnos vuelve a flex row y los chips de filtros activos comparten la fila con
// los filtros. Eso comprimia el campo de busqueda hasta 155px a 2001px, con
// recorte del texto tipeado.
//
// Este test NO puede medir el layout: jsdom no resuelve media queries ni calcula
// anchos. Lo que fija es el contrato CSS que sostiene la correccion, para que
// alguien no borre las reglas y reintroduzca el defecto sin avisar. La
// verificacion real de ancho se hace con Playwright sobre el build (ver las
// capturas de docs/screenshots/qa-issue-56-2026-10-01/).

// Bajo jsdom `import.meta.url` no es un file:// URL, asi que se resuelve desde
// el root del proyecto, con fallback por si el runner arranca desde otro lado.
const CSS_CANDIDATES = [
  resolve(process.cwd(), 'src/style.css'),
  resolve(process.cwd(), 'frontend/src/style.css'),
]
const cssPath = CSS_CANDIDATES.find((p) => existsSync(p))
if (!cssPath) {
  throw new Error(`No se encontro style.css. Buscado en: ${CSS_CANDIDATES.join(', ')}`)
}
const css = readFileSync(cssPath, 'utf-8').replace(/\/\*[\s\S]*?\*\//g, '')

function extractBlock(query, source) {
  const index = source.indexOf(query)
  if (index === -1) return ''
  const open = source.indexOf('{', index)
  let depth = 0
  for (let i = open; i < source.length; i += 1) {
    if (source[i] === '{') depth += 1
    if (source[i] === '}') {
      depth -= 1
      if (depth === 0) return source.slice(open + 1, i)
    }
  }
  return ''
}

describe('layout del toolbar de Alumnos (Issue #56)', () => {
  it('mantiene el layout columna que protege el campo de busqueda hasta 2000px', () => {
    const columnBlock = extractBlock('@media (max-width: 2000px)', css)
    expect(columnBlock).not.toBe('')
    expect(columnBlock).toMatch(/flex-direction:\s*column/)
    expect(columnBlock).toMatch(/grid-template-columns/)
  })

  it('permite que los filtros bajen de linea por encima de 2000px', () => {
    const wideBlock = extractBlock('@media (min-width: 2001px)', css)
    expect(wideBlock).not.toBe('')
    expect(wideBlock).toMatch(/flex-wrap:\s*wrap/)
  })

  it('fuerza los chips de filtros activos a ocupar su propia fila', () => {
    const wideBlock = extractBlock('@media (min-width: 2001px)', css)
    const chipsRule = extractBlock('.students-filter-chips', wideBlock)
    expect(chipsRule).toMatch(/flex:\s*0 0 100%/)
  })

  it('define un ancho minimo legible para el campo de busqueda', () => {
    const wideBlock = extractBlock('@media (min-width: 2001px)', css)
    const searchRule = extractBlock('.students-search-field', wideBlock)
    const minWidth = Number(searchRule.match(/min-width:\s*(\d+)px/)?.[1])
    expect(Number.isFinite(minWidth)).toBe(true)
    // Por debajo de 150px el texto tipeado se recorta (medido en Playwright).
    expect(minWidth).toBeGreaterThanOrEqual(150)
  })

  it('no toca el toolbar de Deudores, que lo redefine como grid', () => {
    const debtorsBlock = extractBlock('.debtors-toolbar', css)
    expect(debtorsBlock).toMatch(/display:\s*grid/)
  })
})
