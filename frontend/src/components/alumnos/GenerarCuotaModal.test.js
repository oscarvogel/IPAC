import { flushPromises, mount } from '@vue/test-utils'
import { ref } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import GenerarCuotaModal from './GenerarCuotaModal.vue'

const generarCuota = vi.hoisted(() => vi.fn().mockResolvedValue({ id: 3 }))

vi.mock('@/composables/usePagos', () => ({
  usePagos: () => ({ generarCuota }),
}))

vi.mock('@/composables/useCatalogos', () => ({
  useCatalogos: () => ({ tiposDescuento: ref([]) }),
}))

vi.mock('@/composables/useToast', () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn() }),
}))

const alumno = { id: 12, nombre: 'Roman', apellido: 'Vogel', sucursal: 1 }
const conceptos = [{ id: 7, nombre: 'Cuota mensual', importe: '22000.00', sucursal: 1, activo: true }]

describe('GenerarCuotaModal', () => {
  beforeEach(() => vi.clearAllMocks())

  it('usa calendario para el mes y conserva solo año-mes para el backend', async () => {
    const wrapper = mount(GenerarCuotaModal, {
      props: { open: true, alumno, conceptos },
      global: { stubs: { Teleport: true } },
    })

    const dates = wrapper.findAll('input[type="date"]')
    expect(dates).toHaveLength(3)
    expect(wrapper.text()).toContain('Elegí cualquier fecha del mes al que corresponde la cuota')

    await dates[0].setValue('2026-08-05')
    await dates[1].setValue('2026-08-22')
    await dates[2].setValue('2026-08-31')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(generarCuota).toHaveBeenCalledWith(expect.objectContaining({
      periodo: '2026-08',
      fecha_emision: '2026-08-22',
      fecha_vencimiento: '2026-08-31',
    }))
  })
})
