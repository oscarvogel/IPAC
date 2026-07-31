import { flushPromises, mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import { describe, expect, it } from 'vitest'
import AppShell from './AppShell.vue'

describe('transiciones entre vistas', () => {
  it('mantiene el shell y reemplaza el contenido mediante una transición breve', async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/uno', name: 'uno', component: { template: '<section class="view-one">Uno</section>' } },
        { path: '/dos', name: 'dos', component: { template: '<section class="view-two">Dos</section>' } },
      ],
    })

    await router.push('/uno')
    await router.isReady()

    const wrapper = mount(AppShell, {
      global: {
        plugins: [router],
        stubs: { AppSidebar: true, AppTopbar: true },
      },
    })

    const transition = wrapper.get('transition-stub[name="route-view"]')
    expect(transition.attributes('mode')).toBe('out-in')
    expect(wrapper.find('.view-one').exists()).toBe(true)

    await router.push('/dos')
    await flushPromises()

    expect(wrapper.find('.view-two').exists()).toBe(true)
    expect(wrapper.find('.view-one').exists()).toBe(false)
  })
})
